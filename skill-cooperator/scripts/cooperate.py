#!/usr/bin/env python3
"""
skill-cooperator — orquesta las skills de CeiboMed según el tipo de tarea de la sesión.
Detecta el tipo de tarea (por palabras clave o argumento), y propone qué skills activar
y en qué orden óptimo, usando SOLO las skills que están instaladas.

Uso:
    python3 cooperate.py "<descripción de la tarea>"    # detecta el tipo
    python3 cooperate.py --type pre-lanzamiento          # fuerza un tipo
    python3 cooperate.py --list                          # lista tipos y skills instaladas
    python3 cooperate.py --skills-dir <dir> ...

Tipos: seguridad | ux | clinico | deploy | pre-lanzamiento | inicio
Solo lectura: sugiere el plan, no ejecuta las skills.
"""
import sys, os, re

# Plan por tipo de tarea: secuencia ordenada de skills (por nombre).
PLANS = {
    "inicio":          ["changelog-auto", "skill-discovery"],
    "seguridad":       ["api-key-protector", "clinical-disclaimer-guard"],
    "ux":              ["mobile-first-checker"],
    "clinico":         ["pdf-quality-guard", "clinical-disclaimer-guard"],
    "deploy":          ["api-key-protector", "clinical-disclaimer-guard", "pdf-quality-guard", "changelog-auto"],
    "pre-lanzamiento": ["clinical-disclaimer-guard", "api-key-protector", "mobile-first-checker",
                        "pdf-quality-guard", "changelog-auto"],
}

# Por qué cada skill en el plan (para explicar el orden).
RATIONALE = {
    "changelog-auto": "registrar/leer el estado del día",
    "skill-discovery": "ver si hay controles nuevos que sumar",
    "api-key-protector": "cazar credenciales antes de exponer código",
    "clinical-disclaimer-guard": "garantizar los avisos médico-legales",
    "mobile-first-checker": "que ande en celular/tablet",
    "pdf-quality-guard": "que el informe PDF salga completo",
}

# Palabras clave → tipo de tarea.
KEYWORDS = {
    "pre-lanzamiento": ["pre-lanzamiento", "prelanzamiento", "antes de lanzar", "antes de publicar",
                        "release", "lanzar", "publicar", "salir a producción"],
    "deploy":          ["deploy", "compartir", "entregar", "mandar", "push de release", "distribuir"],
    "seguridad":       ["seguridad", "vulnerab", "xss", "secret", "credencial", "api key", "clave", "hardening"],
    "clinico":         ["pdf", "informe", "imprimir", "exportar informe", "paciente", "disclaimer", "firma"],
    "ux":              ["ux", "mobile", "celular", "tablet", "responsive", "accesib", "a11y", "diseño"],
    "inicio":          ["inicio de sesión", "empezar", "arranco", "arrancar", "coordina", "qué skills usar", "cooperador"],
}


def installed(skills_dir):
    names = set()
    if os.path.isdir(skills_dir):
        for e in os.listdir(skills_dir):
            if os.path.isfile(os.path.join(skills_dir, e, "SKILL.md")):
                names.add(e.lower())
    return names


def detect_type(text):
    t = text.lower()
    scores = {}
    for typ, kws in KEYWORDS.items():
        scores[typ] = sum(1 for k in kws if k in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "clinico"


def main():
    args = sys.argv[1:]
    skills_dir = os.path.expanduser("~/Desktop/APLICACIONES/.claude/skills")
    if "--skills-dir" in args:
        i = args.index("--skills-dir"); skills_dir = os.path.expanduser(args[i+1]); del args[i:i+2]
    inst = installed(skills_dir)

    print("═" * 70); print("  skill-cooperator — CeiboMed"); print("═" * 70)

    if "--list" in args:
        print("  Skills instaladas: %s" % (", ".join(sorted(inst)) or "(ninguna)"))
        print("\n  Tipos de tarea y plan sugerido:")
        for typ, seq in PLANS.items():
            print("   • %-16s → %s" % (typ, " → ".join(seq)))
        print("═" * 70); sys.exit(0)

    if "--type" in args:
        i = args.index("--type"); typ = args[i+1] if i+1 < len(args) else "clinico"; del args[i:i+2]
        typ = typ.lower()
        if typ not in PLANS:
            print("  Tipo desconocido '%s'. Válidos: %s" % (typ, ", ".join(PLANS))); sys.exit(2)
        desc = "(forzado)"
    else:
        desc = " ".join(args).strip() or "inicio de sesión"
        typ = detect_type(desc)

    print("  Contexto     : %s" % desc)
    print("  Tipo de tarea: %s" % typ)
    print("═" * 70)

    seq = PLANS[typ]
    plan_inst = [s for s in seq if s in inst]
    plan_missing = [s for s in seq if s not in inst]

    print("\n  Orden de ejecución sugerido:")
    if plan_inst:
        for n, s in enumerate(plan_inst, 1):
            print("   %d. /%-26s — %s" % (n, s, RATIONALE.get(s, "")))
    else:
        print("   (ninguna de las skills del plan está instalada)")

    if plan_missing:
        print("\n  Recomendadas para este tipo pero NO instaladas:")
        for s in plan_missing:
            print("   • %s — %s  (crear con skill-creator o instalar)" % (s, RATIONALE.get(s, "")))

    print("\n" + "═" * 70)
    print("  Sugerencia: activá las skills en ese orden. Cada una es de solo lectura")
    print("  y no bloquea; resolvé los ❌ que reporten antes de avanzar de etapa.")
    print("═" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
