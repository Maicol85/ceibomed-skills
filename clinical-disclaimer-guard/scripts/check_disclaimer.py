#!/usr/bin/env python3
"""
clinical-disclaimer-guard — verifica que una app CeiboMed tenga el disclaimer
médico-legal correcto y visible, el disclaimer en el pie del PDF, y el aviso
de datos locales (localStorage).

Uso:
    python3 check_disclaimer.py <archivo.html> [<archivo2.html> ...]
    python3 check_disclaimer.py <directorio>        # escanea */index.html

Salida: reporte por app con ✅/❌ por cada requisito, línea aproximada del hallazgo
y qué falta. Código de salida 1 si alguna app tiene algún requisito faltante
(útil para bloquear un "compartir" o un push).
"""
import sys, os, re, glob

# Frases que cuentan como disclaimer médico-legal (case-insensitive, sin acentos-sensible).
# Se busca cualquiera de estas — no todas.
DISCLAIMER_PATTERNS = [
    r"apoyo cl[ií]nico",
    r"no reemplaza\s+el?\s*(juicio|criterio)\s*(m[eé]dico|cl[ií]nico|profesional)",
    r"no sustituye\s+(el\s+)?(juicio|criterio|la evaluaci[oó]n)",
    r"herramienta de apoyo",
    r"uso cl[ií]nico exclusivo",
    r"responsabilidad\s+(del|profesional)",
    r"juicio\s+(m[eé]dico|cl[ií]nico)\s+del\s+profesional",
    r"no constituye\s+(un\s+)?diagn[oó]stico",
]

# Aviso de datos locales al usuario (PROSA, no código). Se evita matchear llamadas
# a localStorage en el JS: los patrones apuntan a texto legible por el usuario.
LOCAL_DATA_PATTERNS = [
    r"almacena.{0,25}(datos|informaci[oó]n).{0,25}(local|dispositivo)",
    r"(datos|informaci[oó]n).{0,30}(en este dispositivo|localmente|de forma local)",
    r"no se env[ií]an?.{0,25}(a\s+)?(ning[uú]n\s+)?servidor",
    r"responsab.{0,45}(respaldo|resguardo|copia|confidencialidad).{0,45}(datos|informaci[oó]n)",
    r"los datos.{0,30}(viven|quedan|se guardan|se almacenan).{0,25}(local|este dispositivo|sesi[oó]n)",
    r"guardad[oa]s?\s+(solo\s+)?(en\s+)?(este\s+)?(dispositivo|navegador|localmente)",
]

# Detección de código de generación de PDF (jsPDF o document.write de impresión)
PDF_GEN_HINTS = [
    r"jsPDF", r"new\s+jspdf", r"\.save\(['\"].*\.pdf",
    r"generarPDF", r"exportarPDF", r"exportPDF", r"generarInforme",
    r"window\.print\(\)", r"document\.write\(",
]

def find_lines(text_lines, patterns):
    """Devuelve lista de (linea_1based, fragmento) para el primer match de cualquier patrón."""
    hits = []
    joined = "\n".join(text_lines)
    for pat in patterns:
        for m in re.finditer(pat, joined, re.IGNORECASE):
            # calcular número de línea
            line_no = joined.count("\n", 0, m.start()) + 1
            frag = text_lines[line_no-1].strip()
            hits.append((line_no, frag[:90]))
    hits.sort()
    return hits

def pdf_footer_has_disclaimer(text, lines):
    """
    Heurística: buscar disclaimer DENTRO del código de generación de PDF.
    Localiza la región de la función de PDF y comprueba si alguna frase de
    disclaimer aparece cerca (misma función / template de impresión).
    """
    # ubicar índices de líneas donde hay hints de PDF
    pdf_line_idx = [i for i, ln in enumerate(lines)
                    if any(re.search(h, ln, re.IGNORECASE) for h in PDF_GEN_HINTS)]
    if not pdf_line_idx:
        return None  # no hay generación de PDF detectada
    # ventana alrededor de cada bloque de PDF (±120 líneas) — busca disclaimer o "pie"/footer con texto legal
    for idx in pdf_line_idx:
        lo, hi = max(0, idx-40), min(len(lines), idx+160)
        window = "\n".join(lines[lo:hi])
        for pat in DISCLAIMER_PATTERNS:
            m = re.search(pat, window, re.IGNORECASE)
            if m:
                line_no = lo + window.count("\n", 0, m.start()) + 1
                return (True, line_no, lines[line_no-1].strip()[:90])
    return (False, pdf_line_idx[0]+1, "función PDF detectada, sin disclaimer cercano")

def check_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    lines = text.split("\n")

    report = {"path": path, "checks": [], "missing": 0}

    # 1) Disclaimer en el HTML
    dh = find_lines(lines, DISCLAIMER_PATTERNS)
    if dh:
        report["checks"].append(("Disclaimer médico-legal en HTML", True,
                                 f"línea {dh[0][0]}: “{dh[0][1]}”"))
    else:
        report["checks"].append(("Disclaimer médico-legal en HTML", False,
                                 "no se encontró texto de disclaimer (ej: “apoyo clínico”, “no reemplaza el juicio médico”)"))
        report["missing"] += 1

    # 2) Disclaimer en el pie del PDF
    pf = pdf_footer_has_disclaimer(text, lines)
    if pf is None:
        report["checks"].append(("Disclaimer en el pie del PDF", None,
                                 "no se detectó generación de PDF (no aplica, verificar manualmente)"))
    elif pf[0]:
        report["checks"].append(("Disclaimer en el pie del PDF", True,
                                 f"línea {pf[1]}: “{pf[2]}”"))
    else:
        report["checks"].append(("Disclaimer en el pie del PDF", False,
                                 f"generación de PDF en línea ~{pf[1]} sin disclaimer cercano — agregar al footer"))
        report["missing"] += 1

    # 3) Aviso de datos locales (localStorage)
    uses_ls = bool(re.search(r"localStorage", text))
    ld = find_lines(lines, LOCAL_DATA_PATTERNS)
    if ld:
        report["checks"].append(("Aviso de datos locales (localStorage)", True,
                                 f"línea {ld[0][0]}: “{ld[0][1]}”"))
    elif uses_ls:
        report["checks"].append(("Aviso de datos locales (localStorage)", False,
                                 "la app usa localStorage pero NO hay aviso al usuario de que los datos se guardan localmente"))
        report["missing"] += 1
    else:
        report["checks"].append(("Aviso de datos locales (localStorage)", None,
                                 "no usa localStorage (no aplica)"))
    return report

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

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    targets = resolve_targets(sys.argv[1:])
    if not targets:
        print("No se encontraron archivos index.html para verificar.")
        sys.exit(2)

    total_missing = 0
    print("═" * 68)
    print("  clinical-disclaimer-guard — CeiboMed")
    print("═" * 68)
    for path in targets:
        rep = check_file(path)
        total_missing += rep["missing"]
        app = os.path.basename(os.path.dirname(path)) or os.path.basename(path)
        status = "✅ OK" if rep["missing"] == 0 else f"❌ {rep['missing']} faltante(s)"
        print(f"\n▶ {app}  —  {status}")
        print(f"  {path}")
        for name, ok, detail in rep["checks"]:
            icon = "✅" if ok is True else ("❌" if ok is False else "➖")
            print(f"   {icon} {name}")
            print(f"      {detail}")

    print("\n" + "═" * 68)
    if total_missing == 0:
        print("  RESULTADO: ✅ Todas las apps verificadas tienen el disclaimer completo.")
    else:
        print(f"  RESULTADO: ❌ {total_missing} requisito(s) faltante(s) — resolver antes de compartir/publicar.")
    print("═" * 68)
    sys.exit(1 if total_missing else 0)

if __name__ == "__main__":
    main()
