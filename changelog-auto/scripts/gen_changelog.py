#!/usr/bin/env python3
"""
changelog-auto — genera/actualiza un CHANGELOG.md acumulativo de la suite CeiboMed
a partir de los commits git del día, organizados por app y por tipo de cambio.

Uso:
    python3 gen_changelog.py [--root DIR] [--date YYYY-MM-DD] [--days N] [--dry-run]

    --root    Directorio raíz de la suite (default: ~/Desktop/APLICACIONES)
    --date    Día a registrar (default: hoy)
    --days    En vez de un día, últimos N días (útil si la sesión cruzó medianoche)
    --dry-run Muestra el bloque generado sin escribir el archivo

Cada app de CeiboMed es su propio repo git (subcarpeta con .git). El script recorre
cada repo, toma los commits del período, los clasifica por tipo (Seguridad / UX-A11y /
Clínico / Config-Feature / Fix / General) y arma un bloque de fecha en CHANGELOG.md.

Es ACUMULATIVO y no destructivo: si ya existe un bloque para esa fecha lo regenera
en su lugar (por si corrés la skill varias veces el mismo día); los bloques de días
anteriores se conservan intactos.
"""
import sys, os, re, subprocess, datetime, argparse

# Clasificación por palabras clave, en orden de prioridad (primer match gana).
TYPE_RULES = [
    ("Seguridad",      r"segurid|security|xss|inject|csv\s*inject|credencial|password|api[_\s-]?key|eschtml|sanitiz|vulnerab|localstorage|import\s*(valid|schema)|escap"),
    ("UX/A11y",        r"a11y|accesib|ux|touch|focus|aria|heading|dark\s*mode|contrast|impeccable|reduced[_-]?motion|responsive|layout|tokens?\b|tema\b"),
    ("Clínico",        r"cl[ií]nic|disclaimer|diagn[oó]st|protocolo|severidad|umbral|dosis|gu[ií]a|score|nota clínica|paciente"),
    ("Config/Feature", r"config|feature|toggle|export|import|qr|panel|tab\b|módulo|modulo|c[aá]lcul|calendar|notas del mes"),
    ("Fix",            r"\bfix\b|bug|correcc|arreglo|hotfix|lock|revert"),
]
DEFAULT_TYPE = "General"

def classify(subject):
    s = subject.lower()
    for name, pat in TYPE_RULES:
        if re.search(pat, s):
            return name
    return DEFAULT_TYPE

def clean_subject(subject, app):
    """Quita el prefijo 'AppName — ' del subject para dejar la descripción breve."""
    s = subject.strip()
    # cortar 'Algo — ' o 'Algo - ' o 'Algo: ' al inicio
    s = re.sub(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9/ ]{2,30}\s[—:-]\s+", "", s)
    return s.strip()

def git(repo, *args):
    try:
        out = subprocess.run(["git", "-C", repo, *args],
                             capture_output=True, text=True, timeout=20)
        return out.stdout.strip()
    except Exception:
        return ""

def is_repo(path):
    return os.path.isdir(os.path.join(path, ".git"))

def commits_for(repo, since, until):
    fmt = "%h\x1f%s"
    raw = git(repo, "log", f"--since={since}", f"--until={until}",
              f"--pretty=format:{fmt}")
    commits = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))
    return commits

def build_block(root, date_label, since, until):
    apps = {}
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isdir(path) or not is_repo(path):
            continue
        cs = commits_for(path, since, until)
        if not cs:
            continue
        by_type = {}
        for sha, subj in cs:
            t = classify(subj)
            desc = clean_subject(subj, name)
            by_type.setdefault(t, []).append((sha, desc))
        apps[name] = by_type

    if not apps:
        return None, 0

    total = sum(len(v) for byt in apps.values() for v in byt.values())
    lines = [f"## {date_label}", ""]
    # orden de tipos para presentación
    type_order = ["Seguridad", "Clínico", "UX/A11y", "Config/Feature", "Fix", "General"]
    for app in sorted(apps):
        lines.append(f"### {app}")
        byt = apps[app]
        for t in type_order:
            if t not in byt:
                continue
            for sha, desc in byt[t]:
                lines.append(f"- **{t}** — {desc}  (`{sha}`)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", total

HEADER = "# CHANGELOG — CeiboMed\n\n> Registro acumulativo de cambios por sesión. Generado por la skill `changelog-auto`.\n"

def merge_into_changelog(out_path, date_label, block):
    """Inserta/reemplaza el bloque '## <fecha>' conservando el resto del historial."""
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = HEADER

    # asegurar header
    if not content.lstrip().startswith("# CHANGELOG"):
        content = HEADER + "\n" + content

    # separar header del cuerpo (todo lo que va desde el primer '## ')
    m = re.search(r"^## ", content, re.MULTILINE)
    if m:
        head = content[:m.start()].rstrip() + "\n\n"
        body = content[m.start():]
    else:
        head = content.rstrip() + "\n\n"
        body = ""

    # partir el body en bloques por fecha
    blocks = re.split(r"(?=^## )", body, flags=re.MULTILINE)
    blocks = [b for b in blocks if b.strip()]

    new_blocks = []
    replaced = False
    for b in blocks:
        if b.startswith(f"## {date_label}"):
            new_blocks.append(block.rstrip() + "\n")
            replaced = True
        else:
            new_blocks.append(b.rstrip() + "\n")
    if not replaced:
        # prepend el bloque de hoy arriba de los anteriores
        new_blocks.insert(0, block.rstrip() + "\n")

    result = head + "\n".join(new_blocks).rstrip() + "\n"
    return result

def main():
    ap = argparse.ArgumentParser(add_help=True, description="changelog-auto para CeiboMed")
    ap.add_argument("--root", default=os.path.expanduser("~/Desktop/APLICACIONES"))
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: hoy)")
    ap.add_argument("--days", type=int, default=None, help="últimos N días en vez de un día")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        print(f"No existe el directorio raíz: {root}"); sys.exit(2)

    if args.days:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=args.days-1)
        since = f"{start.isoformat()} 00:00:00"
        until = f"{end.isoformat()} 23:59:59"
        date_label = f"{start.isoformat()} → {end.isoformat()}"
    else:
        d = args.date or datetime.date.today().isoformat()
        since = f"{d} 00:00:00"
        until = f"{d} 23:59:59"
        date_label = d

    block, total = build_block(root, date_label, since, until)
    if block is None:
        print(f"No hay commits en el período ({date_label}). Nada que registrar.")
        sys.exit(0)

    out_path = os.path.join(root, "CHANGELOG.md")
    result = merge_into_changelog(out_path, date_label, block)

    if args.dry_run:
        print("── BLOQUE GENERADO (dry-run, no se escribió) ──\n")
        print(block)
        print(f"\n({total} commit(s) · destino: {out_path})")
        sys.exit(0)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ CHANGELOG actualizado: {out_path}")
    print(f"   Sesión {date_label} · {total} commit(s) registrados.")

if __name__ == "__main__":
    main()
