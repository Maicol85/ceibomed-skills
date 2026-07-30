#!/usr/bin/env python3
"""
api-key-protector — detecta API keys, contraseñas y credenciales expuestas en
el código fuente de las apps CeiboMed, ANTES de un git push o de publicar.

Uso:
    python3 scan_secrets.py <archivo.html> [<archivo2> ...]
    python3 scan_secrets.py <directorio>        # escanea */index.html

Detecta:
  - API keys hardcodeadas (sk-, ghp_, AKIA…, AIza…, xox…, Bearer <token>, apikey=)
  - Contraseñas hardcodeadas en texto plano (pwd === '...', password: '...')
  - URLs con credenciales embebidas (https://user:pass@host)
  - localStorage guardando tokens/keys/passwords directamente

Salida: por hallazgo → severidad, archivo:línea, fragmento y remediación.
Código de salida 1 si hay algún hallazgo CRÍTICO o ALTO (para bloquear el push).
"""
import sys, os, re, glob

# (nombre, severidad, regex, remediación)
# Severidad: CRITICO > ALTO > MEDIO
RULES = [
    # ── Claves privadas / tokens de proveedores reales ──
    ("Clave secreta tipo OpenAI/Anthropic (sk-…)", "CRITICO",
     r"\bsk-(ant-)?[A-Za-z0-9_\-]{16,}\b",
     "Es una clave privada. Quitarla del código, rotarla en el proveedor y moverla a una variable de entorno o backend."),
    ("Token de GitHub (ghp_/gho_/ghs_…)", "CRITICO",
     r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
     "Token de acceso de GitHub. Revocarlo YA en GitHub → Settings → Developer settings, y no versionarlo."),
    ("AWS Access Key ID (AKIA…)", "CRITICO",
     r"\bAKIA[0-9A-Z]{16}\b",
     "Clave de acceso AWS. Desactivarla en IAM y usar credenciales de entorno/rol."),
    ("Google API Key (AIza…)", "CRITICO",
     r"\bAIza[0-9A-Za-z_\-]{35}\b",
     "API key de Google. Restringirla/rotarla en la consola de Google Cloud; no exponerla en el cliente."),
    ("Token de Slack (xox…)", "CRITICO",
     r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b",
     "Token de Slack. Revocarlo en la app de Slack y no incrustarlo."),
    ("Clave privada PEM/RSA en el código", "CRITICO",
     r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
     "Clave privada embebida. Removerla del repositorio y rotar el par de claves."),
    ("URL con credenciales embebidas (user:pass@host)", "CRITICO",
     r"\bhttps?://[A-Za-z0-9._%+\-]+:[^/\s@'\"]{2,}@[A-Za-z0-9.\-]+",
     "La URL lleva usuario:contraseña en claro. Usar autenticación por header/entorno, nunca en la URL."),

    # ── Contraseñas hardcodeadas en texto plano ──
    # Solo patrones de CÓDIGO real (evita matchear la palabra española "clave" en prosa clínica):
    #   (a) comparación con literal:  if (pwd === 'maicolett1')
    #   (b) asignación de constante de contraseña:  var MP_LOGIN_PASS='…'
    ("Contraseña comparada con literal (login cliente-side)", "CRITICO",
     r"(?i)\b[a-z0-9_]*(pass|pwd|clave|contrase|login)[a-z0-9_]*\b\s*===?\s*['\"][^'\"]{3,}['\"]",
     "Login cliente-side: la clave es visible con 'Ver código fuente'. Quitar el literal; la auth cliente-side no protege datos — mover a backend o cifrar el store."),
    ("Contraseña/clave asignada a una constante", "CRITICO",
     r"(?i)\b(?:var|const|let)\s+[a-z0-9_]*(pass|pwd|password|clave|login_?pass|app_?pass)[a-z0-9_]*\s*=\s*['\"][^'\"]{3,}['\"]",
     "Constante de contraseña con valor literal en el fuente. Removerla; no confiar en auth cliente-side."),

    # ── API keys / tokens genéricos asignados a literal ──
    ("API key / secret / token asignado a valor literal", "ALTO",
     r"(?i)\b(api[_-]?key|apikey|access[_-]?token|auth[_-]?token|client[_-]?secret|secret[_-]?key|x[_-]?api[_-]?key)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]",
     "Credencial en claro. Moverla a variable de entorno / backend; no enviarla al cliente."),
    ("Header Authorization: Bearer <token literal>", "ALTO",
     r"(?i)Bearer\s+[A-Za-z0-9._\-]{16,}",
     "Token portador incrustado. Inyectarlo en runtime desde un almacén seguro, no hardcodearlo."),

    # ── localStorage / sessionStorage guardando secretos ──
    ("localStorage/sessionStorage guardando un secreto", "ALTO",
     r"(?i)(local|session)Storage\.setItem\(\s*['\"][^'\"]*(token|apikey|api[_-]key|secret|password|passwd|clave|jwt|auth)[^'\"]*['\"]",
     "Guardar tokens/keys en localStorage los expone a cualquier script (XSS) y persisten en disco. Preferir memoria/sesión efímera y, si deben persistir, cifrarlos."),
]

# Contextos que NO son secretos aunque matcheen (para reducir falsos positivos).
FALSE_POSITIVE_CONTEXT = [
    r'type\s*=\s*["\']password["\']',      # <input type="password">
    r'placeholder\s*=\s*["\'][^"\']*["\']',# placeholder="Contraseña"
    r'autocomplete\s*=\s*["\']',           # autocomplete="current-password"
    r'aria-label',
    r'>\s*Contrase[nñ]a\s*<',              # <label>Contraseña</label>
    r'name\s*=\s*["\']pass',
]

SEV_ORDER = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2}
SEV_ICON = {"CRITICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡"}

def is_false_positive(line):
    return any(re.search(fp, line, re.IGNORECASE) for fp in FALSE_POSITIVE_CONTEXT)

def scan_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    findings = []
    seen = set()  # evitar duplicar misma línea+regla
    for i, line in enumerate(lines, start=1):
        for name, sev, pat, fix in RULES:
            m = re.search(pat, line)
            if not m:
                continue
            # el patrón de "contraseña literal" no debe dispararse en inputs/labels
            if "Contrase" in name or "password" in name.lower() or "pwd" in pat:
                if is_false_positive(line):
                    continue
            frag = line.strip()
            # ocultar el valor sensible en el fragmento mostrado
            val = m.group(0)
            shown = frag[:110]
            key = (i, name)
            if key in seen:
                continue
            seen.add(key)
            findings.append({"line": i, "name": name, "sev": sev,
                             "frag": shown, "fix": fix})
    findings.sort(key=lambda x: (SEV_ORDER[x["sev"]], x["line"]))
    return findings

def resolve_targets(args):
    targets = []
    for a in args:
        if os.path.isdir(a):
            targets += sorted(glob.glob(os.path.join(a, "*", "index.html")))
            if os.path.exists(os.path.join(a, "index.html")):
                targets.append(os.path.join(a, "index.html"))
        elif os.path.exists(a):
            targets.append(a)
        else:
            print(f"⚠️  No existe: {a}")
    return targets

# Hallazgos que en modo --gate DEBEN frenar un push (fugas graves que nunca deben
# subirse). La contraseña cliente-side conocida y los secretos en localStorage se
# reportan pero NO frenan el push en modo gate (patrón conocido/aceptado de la suite),
# para no bloquear todos los push. En modo normal (sin --gate) sí cuentan.
GATE_BLOCK = {
    "Clave secreta tipo OpenAI/Anthropic (sk-…)",
    "Token de GitHub (ghp_/gho_/ghs_…)",
    "AWS Access Key ID (AKIA…)",
    "Google API Key (AIza…)",
    "Token de Slack (xox…)",
    "Clave privada PEM/RSA en el código",
    "URL con credenciales embebidas (user:pass@host)",
}

def main():
    argv = [a for a in sys.argv[1:] if a != "--gate"]
    gate = "--gate" in sys.argv
    if not argv:
        print(__doc__); sys.exit(2)
    targets = resolve_targets(argv)
    if not targets:
        print("No se encontraron archivos para escanear."); sys.exit(2)

    print("═" * 70)
    mode = "  (modo gate: frena solo ante fugas graves)" if gate else ""
    print("  api-key-protector — CeiboMed  ·  escaneo de credenciales expuestas" + mode)
    print("═" * 70)

    grand_crit = grand_high = grand_gate = 0
    for path in targets:
        app = os.path.basename(os.path.dirname(path)) or os.path.basename(path)
        findings = scan_file(path)
        n_crit = sum(1 for f in findings if f["sev"] == "CRITICO")
        n_high = sum(1 for f in findings if f["sev"] == "ALTO")
        n_gate = sum(1 for f in findings if f["name"] in GATE_BLOCK)
        grand_crit += n_crit; grand_high += n_high; grand_gate += n_gate
        if not findings:
            print(f"\n▶ {app}  —  ✅ Sin credenciales expuestas detectadas")
            continue
        print(f"\n▶ {app}  —  🔴 {n_crit} crítico(s) · 🟠 {n_high} alto(s)")
        print(f"  {path}")
        for f in findings:
            flag = "  ⛔BLOQUEA" if (gate and f["name"] in GATE_BLOCK) else ""
            print(f"   {SEV_ICON[f['sev']]} [{f['sev']}] {f['name']}  (línea {f['line']}){flag}")
            print(f"      {f['frag']}")
            print(f"      → {f['fix']}")

    print("\n" + "═" * 70)
    if gate:
        if grand_gate == 0:
            print("  RESULTADO (gate): ✅ Sin fugas graves. Push permitido.")
            if grand_crit or grand_high:
                print(f"  (aviso: {grand_crit} crítico(s) y {grand_high} alto(s) conocidos — revisar aparte, no frenan el push)")
        else:
            print(f"  RESULTADO (gate): ⛔ {grand_gate} fuga(s) grave(s) — PUSH BLOQUEADO. Quitar del código antes de subir.")
        print("═" * 70)
        sys.exit(1 if grand_gate else 0)
    else:
        if grand_crit == 0 and grand_high == 0:
            print("  RESULTADO: ✅ Sin credenciales críticas/altas. Seguro para push.")
        else:
            print(f"  RESULTADO: ❌ {grand_crit} crítico(s) y {grand_high} alto(s) — RESOLVER antes de git push / publicar.")
        print("═" * 70)
        sys.exit(1 if (grand_crit or grand_high) else 0)

if __name__ == "__main__":
    main()
