#!/usr/bin/env python3
"""
skill-discovery — propone skills nuevas relevantes para el desarrollo de CeiboMed
(seguridad médica, PDF, accesibilidad, testing) que TODAVÍA no estén instaladas.

Cómo trabaja:
  - Lee las skills ya instaladas en el directorio de skills (por defecto ~/Desktop/APLICACIONES/.claude/skills).
  - Compara contra un catálogo curado de skills/controles útiles para una suite clínica.
  - Reporta, para cada candidata NO instalada: nombre, categoría, para qué sirve,
    por qué es útil para CeiboMed y cómo instalarla/crearla.

Uso:
    python3 discover_skills.py [<dir-skills>] [--cat seguridad|pdf|accesibilidad|testing|all]

Solo lectura. No instala ni modifica nada: sugiere.
"""
import sys, os, re

# Catálogo curado. Cada entrada: relevancia para CeiboMed y cómo obtenerla.
CATALOG = [
    # ── Seguridad médica ──
    dict(name="hardening-checklist", cat="seguridad",
         desc="Checklist de endurecimiento previo a compartir: CSP, sanitización de innerHTML, escape de todo dato de paciente, cuota de localStorage.",
         why="Refuerza el trabajo de api-key-protector y clinical-disclaimer-guard con un barrido de superficie de ataque XSS/almacenamiento.",
         how="Crear con skill-creator siguiendo el patrón de api-key-protector; o buscar en registros de plugins de seguridad."),
    dict(name="phi-leak-detector", cat="seguridad",
         desc="Detecta datos de paciente (nombre, CI, HC) que salgan a logs, URLs, analytics o servicios externos.",
         why="Las apps son offline-first; esta skill verifica que ningún dato clínico se filtre a la red por error.",
         how="Crear con skill-creator; regex sobre fetch/XHR/console con campos de paciente."),
    dict(name="dependency-cdn-audit", cat="seguridad",
         desc="Audita los <script src> de CDN (jsPDF, XLSX, qrcode): versión, integridad (SRI) y disponibilidad.",
         why="Las apps cargan librerías desde CDN; sin SRI un CDN comprometido inyecta código en un contexto clínico.",
         how="Crear con skill-creator; parsear <script src> y sugerir integrity=."),
    # ── PDF ──
    dict(name="pdf-accessibility-tagger", cat="pdf",
         desc="Verifica que el PDF tenga estructura accesible (títulos, idioma, orden de lectura) además de texto seleccionable.",
         why="Complementa pdf-quality-guard: no solo que el PDF esté completo, sino que sea accesible/archivable.",
         how="Crear con skill-creator; heurística sobre la construcción jsPDF (uso de headings, metadata)."),
    dict(name="pdf-visual-diff", cat="pdf",
         desc="Compara el PDF generado contra un baseline para detectar regresiones de layout (footer corrido, QR tapado).",
         why="Cada cambio de footer/QR puede romper el layout del informe sin que se note; esto lo caza.",
         how="Requiere render headless (p. ej. Playwright); crear como skill con script Node."),
    # ── Accesibilidad ──
    dict(name="contrast-checker", cat="accesibilidad",
         desc="Calcula el ratio de contraste de los tokens de color (claro y oscuro) contra WCAG AA/AAA.",
         why="Las apps tienen dark mode con tokens; esta skill garantiza legibilidad en ambos temas.",
         how="Crear con skill-creator; parsear variables --bg/--text de :root y [data-theme=dark]."),
    dict(name="aria-linter", cat="accesibilidad",
         desc="Linter de ARIA: roles válidos, labels en controles solo-ícono, foco de modales, live-regions.",
         why="Extiende el trabajo de accesibilidad ya hecho (role=dialog, aria-live) con verificación continua.",
         how="Crear con skill-creator; o adaptar axe-core en un runner headless."),
    dict(name="keyboard-nav-audit", cat="accesibilidad",
         desc="Detecta elementos clickables no accesibles por teclado (div[onclick] sin role/tabindex/handler).",
         why="Ya se corrigieron a mano; esta skill evita que vuelvan a aparecer en cada release.",
         how="Crear con skill-creator; regex sobre <div onclick> sin role=button."),
    # ── Testing ──
    dict(name="smoke-test-runner", cat="testing",
         desc="Abre cada app en un navegador headless y verifica que carga sin errores de consola y que el PDF se genera.",
         why="Un `node --check` valida sintaxis pero no runtime; esto detecta errores reales al cargar/exportar.",
         how="Crear como skill con Playwright/Puppeteer; correr antes de cada release."),
    dict(name="localstorage-schema-test", cat="testing",
         desc="Valida que import/export de JSON respeten el esquema y que los datos sobrevivan un round-trip.",
         why="Varias apps hacen backup/restore; un cambio de esquema puede corromper datos del usuario.",
         how="Crear con skill-creator; casos de import válidos/ inválidos por app."),
]

CATS = ["seguridad", "pdf", "accesibilidad", "testing"]


def installed_skills(skills_dir):
    names = set()
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            p = os.path.join(skills_dir, entry)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "SKILL.md")):
                names.add(entry.lower())
            # también leer el name: del frontmatter si difiere del dir
            md = os.path.join(p, "SKILL.md")
            if os.path.isfile(md):
                try:
                    with open(md, encoding="utf-8", errors="replace") as f:
                        head = f.read(600)
                    m = re.search(r"^name:\s*(.+)$", head, re.MULTILINE)
                    if m:
                        names.add(m.group(1).strip().lower())
                except Exception:
                    pass
    return names


def main():
    args = [a for a in sys.argv[1:]]
    cat = "all"
    if "--cat" in args:
        i = args.index("--cat"); cat = args[i+1] if i+1 < len(args) else "all"; del args[i:i+2]
    skills_dir = args[0] if args else os.path.expanduser("~/Desktop/APLICACIONES/.claude/skills")

    inst = installed_skills(skills_dir)
    print("═" * 70); print("  skill-discovery — CeiboMed"); print("═" * 70)
    print("  Directorio de skills: %s" % skills_dir)
    print("  Skills ya instaladas: %s" % (", ".join(sorted(inst)) if inst else "(ninguna detectada)"))
    print("═" * 70)

    shown = 0
    for c in (CATS if cat == "all" else [cat]):
        cands = [s for s in CATALOG if s["cat"] == c and s["name"].lower() not in inst]
        if not cands:
            continue
        print("\n### %s" % c.upper())
        for s in cands:
            shown += 1
            print("\n  • %s" % s["name"])
            print("    Qué hace : %s" % s["desc"])
            print("    Por qué  : %s" % s["why"])
            print("    Cómo     : %s" % s["how"])

    print("\n" + "═" * 70)
    if shown == 0:
        print("  RESULTADO: ✅ No hay candidatas nuevas para esa categoría (o ya están instaladas).")
    else:
        print("  RESULTADO: %d skill(s) candidata(s) NO instalada(s). Evaluar cuáles crear/instalar." % shown)
    print("  Nota: crear una skill nueva → usar skill-creator siguiendo el patrón de las existentes.")
    print("═" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
