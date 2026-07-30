#!/usr/bin/env python3
"""
pdf-quality-guard — verifica (análisis estático del HTML de la app) que el PDF
que genera una app de CeiboMed salga COMPLETO antes de entregárselo al paciente.

Comprueba cuatro cosas sobre el código de generación del PDF:
  1. Campos obligatorios: nombre del paciente, fecha, médico responsable.
  2. Firma del médico presente.
  3. Disclaimer médico-legal en el pie de página.
  4. QR presente si el toggle de QR está activado.

Uso:
    python3 check_pdf_quality.py <archivo.html> [<archivo2.html> ...]
    python3 check_pdf_quality.py <directorio>     # escanea */index.html

Salida: reporte por app con severidad (CRÍTICO / MAYOR / MENOR / OK) y remediación.
Código de salida 1 si hay algún faltante CRÍTICO o MAYOR (útil para bloquear la
entrega del informe). Es de solo lectura: no modifica archivos.
"""
import sys, os, re, glob

# ── Detección de que la app efectivamente genera un PDF ──
PDF_GEN_HINTS = [r"jsPDF", r"new\s+jspdf", r"\.save\(\s*['\"].*\.pdf",
                 r"generarPDF", r"exportarPDF", r"exportPDF", r"imprimirLimpio",
                 r"window\.print\(\)", r"document\.write\("]

# ── Campos obligatorios (se buscan referencias en el código, no valores) ──
FIELD_PATTERNS = {
    "Nombre del paciente": [r"\bp\.name\b", r"sv\(\s*['\"]nombre", r"getElementById\(['\"](p-?nombre|pn|nombre)",
                            r"['\"]?nombre['\"]?\s*[:=]", r"Paciente\s*:", r"\bp\.nombre\b"],
    "Fecha":              [r"sv\(\s*['\"]fecha", r"getElementById\(['\"](fecha|fe|p-?fecha)",
                            r"toLocaleDateString", r"fmtToday", r"\bfecha\b\s*[:=]", r"Fecha\s+de"],
    "Médico responsable": [r"medic[oa]", r"m[eé]dico", r"matr[ií]cula", r"firmante", r"profesional",
                            r"\bfn\b", r"cfg-inst", r"responsable"],
}
# ── Firma ──
FIRMA_PATTERNS = [r"firma", r"firmante", r"sello", r"pf-nombre", r"assets\.firma", r"firmaImg", r"updPrintFirma"]
# ── Disclaimer médico-legal ──
DISCLAIMER_PATTERNS = [r"apoyo cl[ií]nico", r"no reemplaza\s+el?\s*juicio", r"no constituye\s+(una\s+)?recomendaci[oó]n",
                       r"uso cl[ií]nico exclusivo", r"herramienta de apoyo"]
# ── QR ──
QR_DRAW_HINTS   = [r"eeQrDataURL", r"QR_MATRIX", r"QR_ROWS", r"ergoQrDataURL", r"ceibo-qr", r"addImage\([^)]*qr",
                   r"<img[^>]*qr", r"QRCode\("]
QR_TOGGLE_HINTS = [r"qr_enabled", r"qr-enabled", r"eeQrEnabled", r"cfg-qr", r"incluir.?qr", r"Incluir QR"]


def scan(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            line = text.count("\n", 0, m.start()) + 1
            return line
    return None


def check_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    checks = []
    genline = scan(text, PDF_GEN_HINTS)
    if genline is None:
        return {"app": _app(path), "path": path, "genera_pdf": False, "checks": [], "crit": 0, "major": 0}

    # 1. Campos obligatorios
    for label, pats in FIELD_PATTERNS.items():
        ln = scan(text, pats)
        sev = "CRÍTICO" if label != "Médico responsable" else "MAYOR"
        if ln:
            checks.append(("Campo: " + label, True, "OK", "línea %d" % ln))
        else:
            checks.append(("Campo: " + label, False, sev,
                           "no se detectó referencia al campo — verificar que el PDF lo incluya"))
    # 2. Firma
    ln = scan(text, FIRMA_PATTERNS)
    checks.append(("Firma del médico", ln is not None, "MAYOR" if ln is None else "OK",
                   ("línea %d" % ln) if ln else "sin referencia a firma/sello — agregar bloque de firma al PDF"))
    # 3. Disclaimer
    ln = scan(text, DISCLAIMER_PATTERNS)
    checks.append(("Disclaimer médico-legal", ln is not None, "CRÍTICO" if ln is None else "OK",
                   ("línea %d" % ln) if ln else "falta disclaimer en el pie — agregar a cada página del PDF"))
    # 4. QR (solo exigible si hay toggle de QR)
    qr_draw = scan(text, QR_DRAW_HINTS)
    qr_tog  = scan(text, QR_TOGGLE_HINTS)
    if qr_tog is None and qr_draw is None:
        checks.append(("QR en el PDF", None, "N/A", "la app no usa QR — no aplica"))
    elif qr_draw is not None:
        checks.append(("QR en el PDF", True, "OK", "generación de QR en línea %d" % qr_draw))
    else:
        checks.append(("QR en el PDF", False, "MENOR",
                       "hay toggle de QR (línea %d) pero no se detectó el dibujo del QR" % qr_tog))

    crit = sum(1 for _, ok, sev, _ in checks if ok is False and sev == "CRÍTICO")
    major = sum(1 for _, ok, sev, _ in checks if ok is False and sev == "MAYOR")
    return {"app": _app(path), "path": path, "genera_pdf": True, "checks": checks, "crit": crit, "major": major}


def _app(path):
    return os.path.basename(os.path.dirname(path)) or os.path.basename(path)


def resolve_targets(args):
    targets = []
    for a in args:
        a = os.path.expanduser(a)
        if os.path.isdir(a):
            targets += sorted(glob.glob(os.path.join(a, "*", "index.html")))
        elif os.path.isfile(a):
            targets.append(a)
    return targets


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    targets = resolve_targets(sys.argv[1:])
    if not targets:
        print("No se encontraron archivos index.html para verificar."); sys.exit(2)

    ICON = {True: "✅", False: "❌", None: "➖"}
    total_crit = total_major = 0
    print("═" * 70)
    print("  pdf-quality-guard — CeiboMed")
    print("═" * 70)
    for path in targets:
        rep = check_file(path)
        if not rep["genera_pdf"]:
            print("\n▶ %s  —  ➖ no genera PDF (no aplica)\n  %s" % (rep["app"], path)); continue
        total_crit += rep["crit"]; total_major += rep["major"]
        st = "✅ COMPLETO" if (rep["crit"] == 0 and rep["major"] == 0) else \
             "❌ %d crítico(s), %d mayor(es)" % (rep["crit"], rep["major"])
        print("\n▶ %s  —  %s\n  %s" % (rep["app"], st, path))
        for name, ok, sev, detail in rep["checks"]:
            tag = "" if ok is True or ok is None else "  [%s]" % sev
            print("   %s %s%s" % (ICON[ok], name, tag))
            print("      %s" % detail)
    print("\n" + "═" * 70)
    if total_crit == 0 and total_major == 0:
        print("  RESULTADO: ✅ Los PDF verificados están completos.")
    else:
        print("  RESULTADO: ❌ %d crítico(s) y %d mayor(es) — resolver antes de entregar el PDF." % (total_crit, total_major))
    print("═" * 70)
    sys.exit(1 if (total_crit or total_major) else 0)


if __name__ == "__main__":
    main()
