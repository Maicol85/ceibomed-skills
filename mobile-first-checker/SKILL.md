---
name: mobile-first-checker
description: Detecta elementos de una app de CeiboMed que se rompen o quedan incómodos en celular o tablet, con análisis estático del HTML/CSS. Encuentra cuatro clases de problema: (1) touch targets menores a 44px (botones/enlaces con alto o padding chico, o ausencia de una regla min-height:44px), (2) anchos fijos en px grandes que no se adaptan a pantalla chica, (3) texto demasiado chico para móvil (font-size <12px), y (4) falta de breakpoints responsive (pocas media-queries, sin 480px ni 768px). Por cada hallazgo reporta el elemento, la línea aproximada, la severidad (ALTA/MEDIA/BAJA) y un fix sugerido. Usá esta skill cuando el usuario mencione "mobile", "celular", "teléfono", "tablet", "responsive", "se ve mal en el celular", "antes de compartir" o "antes de publicar". Es de solo lectura: no modifica archivos.
---

# mobile-first-checker

Las apps de CeiboMed se usan al lado de la cama, muchas veces desde un celular o una tablet. Si un botón es más chico que la yema de un dedo, si una tabla se desborda, o si el texto es ilegible, la herramienta falla justo cuando más se la necesita. Esta skill revisa —de forma estática, sin abrir el navegador— los problemas más comunes de adaptación a pantallas chicas.

Detecta:

1. **Touch targets < 44px** — el mínimo recomendado (WCAG 2.5.5 / Apple HIG). Marca botones y enlaces con alto o padding chico, y la ausencia de una regla global `min-height:44px`.
2. **Anchos fijos no adaptativos** — `width:NNNpx` grandes sin `max-width`, que desbordan en móvil.
3. **Texto demasiado chico** — `font-size` < 12px en la UI (los tamaños chicos en `pt` para el PDF no se penalizan).
4. **Falta de breakpoints** — pocas `@media`, o sin breakpoint de tablet (~768px) y móvil (~480px).

## Cuándo usarla

- Antes de compartir o publicar una app.
- Cuando el usuario dice que algo "se ve mal en el celular / la tablet".
- Al mencionar "mobile", "responsive", "touch", "pantalla chica".

## Cómo ejecutarla

```bash
# Una app:
python3 <skill-dir>/scripts/check_mobile.py ~/Desktop/APLICACIONES/marcapaso/index.html

# Toda la suite:
python3 <skill-dir>/scripts/check_mobile.py ~/Desktop/APLICACIONES
```

Código de salida **1 si hay hallazgos de severidad ALTA** (touch targets o falta de breakpoints), **0** si no. Los hallazgos MEDIA/BAJA son mejoras recomendadas, no bloqueantes.

## Cómo interpretar y actuar

Cada hallazgo trae `[SEVERIDAD] elemento (línea) → detalle → fix`. Priorizá:

- **ALTA** — touch targets <44px y ausencia de breakpoints: afectan la usabilidad real en el dispositivo. Resolvé primero.
- **MEDIA** — anchos fijos, breakpoints faltantes puntuales.
- **BAJA** — texto chico: revisar caso por caso (puede ser un pie de tabla aceptable).

Fixes típicos que ya usa la suite:

- Touch targets: `.btn,button,.tab{min-height:44px;min-width:44px}` (excluyendo botones del header que no pueden agrandarse).
- Breakpoints: `@media(max-width:768px){...}` (tablet) y `@media(max-width:480px){...}` (móvil), colapsando grillas a una columna y compactando tabs/paneles.
- Anchos: cambiar `width:600px` por `max-width:600px;width:100%`.

No apliques los fixes en silencio: mostrá el hallazgo y proponé el cambio.

## Ejemplo de uso

**Input (el usuario dice):**
> "Antes de mandarle MarcapasoControl a un colega, ¿anda bien en el celular?"

**Acción:** correr `check_mobile.py ~/Desktop/APLICACIONES/marcapaso/index.html`.

**Output (reporte):**
```
▶ marcapaso  —  ✅ sin problemas altos  (5 hallazgo/s)
   [MEDIA] breakpoint móvil  (CSS global)
        no hay breakpoint <=480px
        fix: agregar @media(max-width:480px){...}
   [BAJA] font-size:10px  (línea ~43)
        texto muy chico para móvil
        fix: usar >=12px en UI (o rem)...
```

**Respuesta al usuario:** "MarcapasoControl no tiene problemas de severidad ALTA (los touch targets ya están en 44px). Como mejora media, **le falta un breakpoint de móvil (≤480px)**: en pantallas muy chicas conviene colapsar las grillas a una columna. ¿Lo agrego?"

## Notas

- Es heurístico: puede haber falsos positivos (p. ej. un `width:400px` dentro de un contenedor que ya es responsive) y falsos negativos. Verificá el contexto de la línea señalada.
- No reemplaza probar en un dispositivo real o en las devtools responsive del navegador; acelera el primer barrido.
- Ajustá los umbrales (44px, 12px, breakpoints) en el script si CeiboMed fija un estándar distinto.
