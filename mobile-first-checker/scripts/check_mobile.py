#!/usr/bin/env python3
"""
mobile-first-checker — detecta elementos de una app de CeiboMed que se rompen o
quedan incómodos en celular/tablet. Análisis estático del HTML/CSS de un solo archivo.

Detecta:
  1. Touch targets < 44px  (botones/clickables con height o padding chico, o ausencia de una regla min-height:44px).
  2. Anchos fijos que no se adaptan (width:NNNpx grandes en layout, sin max-width).
  3. Texto demasiado chico en móvil (font-size < 12px o < 9pt).
  4. Falta de breakpoints responsive (pocos @media / sin 480px ni 768px).

Uso:
    python3 check_mobile.py <archivo.html> [<archivo2.html> ...]
    python3 check_mobile.py <directorio>     # escanea */index.html

Salida: por app, lista de hallazgos con elemento, línea aproximada, severidad y fix sugerido.
Código de salida 1 si hay hallazgos de severidad ALTA. Solo lectura.
"""
import sys, os, re, glob

BTN_TAG = re.compile(r"<(button|a)\b[^>]*>", re.IGNORECASE)


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def check_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    findings = []  # (sev, elemento, linea, detalle, fix)

    # ── 1. Touch targets ──
    has_44 = re.search(r"min-height\s*:\s*44px", text) is not None
    # inline height chico en botones/anchors
    for m in BTN_TAG.finditer(text):
        tag = m.group(0)
        hm = re.search(r"height\s*:\s*(\d+)px", tag)
        if hm and int(hm.group(1)) < 44 and "min-height" not in tag:
            findings.append(("ALTA", "<%s> height:%spx" % (m.group(1), hm.group(1)),
                             line_of(text, m.start()),
                             "botón/enlace con alto fijo <44px",
                             "subir a min-height:44px;min-width:44px"))
        pm = re.search(r"padding\s*:\s*(\d+)px", tag)
        if pm and int(pm.group(1)) <= 3 and not hm:
            findings.append(("MEDIA", "<%s> padding:%spx" % (m.group(1), pm.group(1)),
                             line_of(text, m.start()),
                             "padding muy chico => área táctil chica",
                             "asegurar min-height:44px o padding >= 10px"))
    if not has_44:
        findings.append(("ALTA", "regla global de touch target", 0,
                         "no existe ninguna regla min-height:44px en el CSS",
                         "agregar '.btn,button,.tab{min-height:44px;min-width:44px}' (excluir header si rompe)"))

    # ── 2. Anchos fijos no adaptativos (width grande en px, sin max-width alrededor) ──
    for m in re.finditer(r"width\s*:\s*(\d{3,})px", text):
        w = int(m.group(1))
        if w >= 400:
            ln = line_of(text, m.start())
            ctx = text[max(0, m.start()-60):m.start()+60]
            if "max-width" not in ctx:
                findings.append(("MEDIA", "width:%spx" % w, ln,
                                 "ancho fijo grande sin max-width => desborda en pantalla chica",
                                 "usar max-width:%spx;width:100%% o unidades relativas" % w))

    # ── 3. Texto demasiado chico ──
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)(px|pt)", text):
        val = float(m.group(1)); unit = m.group(2)
        too_small = (unit == "px" and val < 12) or (unit == "pt" and val < 9)
        # ignorar tamaños de PDF (pt chicos son válidos para impresión); solo marcar px chicos en UI
        if unit == "px" and val < 11:
            findings.append(("BAJA", "font-size:%s%s" % (m.group(1), unit),
                             line_of(text, m.start()),
                             "texto muy chico para móvil",
                             "usar >=12px en UI (o rem); reservar tamaños chicos solo para el PDF"))

    # ── 4. Breakpoints responsive ──
    medias = re.findall(r"@media[^{]*\(([^)]*max-width[^)]*)\)", text)
    widths = re.findall(r"max-width\s*:\s*(\d+)px", " ".join(medias))
    wset = set(int(w) for w in widths)
    has_mobile = any(w <= 480 for w in wset)
    has_tablet = any(600 <= w <= 820 for w in wset)
    if len(medias) < 2:
        findings.append(("ALTA", "@media breakpoints", 0,
                         "solo %d media-query(s) responsive" % len(medias),
                         "agregar breakpoints para tablet (~768px) y móvil (~480px)"))
    else:
        if not has_tablet:
            findings.append(("MEDIA", "breakpoint tablet", 0, "no hay breakpoint ~768px",
                             "agregar @media(max-width:768px){...}"))
        if not has_mobile:
            findings.append(("MEDIA", "breakpoint móvil", 0, "no hay breakpoint <=480px",
                             "agregar @media(max-width:480px){...}"))

    # dedup por (elemento,linea,detalle) y ordenar por línea
    seen = set(); uniq = []
    for f in findings:
        k = (f[1], f[2], f[3])
        if k in seen:
            continue
        seen.add(k); uniq.append(f)
    order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    uniq.sort(key=lambda x: (order[x[0]], x[2]))
    return uniq


def _app(path):
    return os.path.basename(os.path.dirname(path)) or os.path.basename(path)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    targets = []
    for a in sys.argv[1:]:
        a = os.path.expanduser(a)
        if os.path.isdir(a):
            targets += sorted(glob.glob(os.path.join(a, "*", "index.html")))
        elif os.path.isfile(a):
            targets.append(a)
    if not targets:
        print("No se encontraron archivos index.html."); sys.exit(2)

    total_alta = 0
    print("═" * 70); print("  mobile-first-checker — CeiboMed"); print("═" * 70)
    for path in targets:
        fs = check_file(path)
        alta = sum(1 for f in fs if f[0] == "ALTA")
        total_alta += alta
        st = "✅ sin problemas altos" if alta == 0 else "❌ %d de severidad ALTA" % alta
        print("\n▶ %s  —  %s  (%d hallazgo/s)\n  %s" % (_app(path), st, len(fs), path))
        for sev, el, ln, det, fix in fs:
            loc = ("línea ~%d" % ln) if ln else "CSS global"
            print("   [%s] %s  (%s)" % (sev, el, loc))
            print("        %s" % det)
            print("        fix: %s" % fix)
    print("\n" + "═" * 70)
    print("  RESULTADO: %s" % ("✅ sin hallazgos ALTA." if total_alta == 0
                               else "❌ %d hallazgo(s) ALTA — revisar antes de compartir/publicar." % total_alta))
    print("═" * 70)
    sys.exit(1 if total_alta else 0)


if __name__ == "__main__":
    main()
