---
name: pdf-quality-guard
description: Verifica que el PDF que genera una app clínica de CeiboMed esté COMPLETO antes de entregárselo al paciente o a un colega. Hace análisis estático del código de generación del PDF y comprueba cuatro cosas: (1) que estén los campos obligatorios (nombre del paciente, fecha, médico responsable), (2) que haya firma del médico, (3) que el disclaimer médico-legal aparezca en el pie de página, y (4) que el QR esté presente si el toggle de QR está activado. Reporta qué falta, con qué severidad (CRÍTICO / MAYOR / MENOR) y cómo remediarlo, citando la línea. Usá esta skill SIEMPRE que el usuario vaya a "generar PDF", "exportar informe", "descargar el informe", "imprimir", "antes de imprimir", "entregar el informe al paciente", o cuando mencione que un PDF salió incompleto o sin firma/disclaimer. Es de solo lectura: no modifica archivos.
---

# pdf-quality-guard

El PDF que genera una app de CeiboMed **sale de la app y circula solo**: se lo lleva el paciente, se adjunta a una historia clínica, se manda por mail. Si sale sin nombre, sin fecha, sin firma o sin el disclaimer médico-legal, el problema aparece cuando ya es tarde. Esta skill verifica —antes de generar/entregar— que el informe esté completo.

Comprueba cuatro requisitos sobre el código de generación del PDF:

1. **Campos obligatorios** — nombre del paciente, fecha y médico responsable. (Nombre y fecha son CRÍTICOS; médico es MAYOR.)
2. **Firma del médico** — bloque de firma/sello presente. (MAYOR.)
3. **Disclaimer médico-legal en el pie** — "apoyo clínico, no reemplaza el juicio médico…". (CRÍTICO.)
4. **QR** — si la app tiene toggle de QR, que el QR efectivamente se dibuje. (MENOR; si no hay QR en la app, no aplica.)

## Cuándo usarla

- Antes de generar/exportar/imprimir un informe para un paciente.
- Como paso previo a entregar o mandar un PDF.
- Cuando el usuario dice "generar PDF", "exportar informe", "antes de imprimir", o reporta un PDF incompleto.

## Cómo ejecutarla

```bash
# Una app puntual:
python3 <skill-dir>/scripts/check_pdf_quality.py ~/Desktop/APLICACIONES/ecosmart/index.html

# Varias:
python3 <skill-dir>/scripts/check_pdf_quality.py ecosmart/index.html ergosmart/index.html

# Toda la suite (escanea */index.html):
python3 <skill-dir>/scripts/check_pdf_quality.py ~/Desktop/APLICACIONES
```

El script devuelve **código de salida 1 si falta algo CRÍTICO o MAYOR** (útil para bloquear la entrega) y **0 si el PDF está completo**. Las apps que no generan PDF se marcan `➖ no aplica`.

## Cómo interpretar y actuar

Cada requisito se marca `✅` (presente), `❌` (falta, con su severidad) o `➖` (no aplica). Para un `✅` cita la línea; para un `❌` explica qué agregar.

Cuando haya un `❌`, no lo arregles en silencio: mostrá al usuario qué falta y dónde, y ofrecé el texto/bloque a agregar. Referencias de dónde suele ir cada cosa:

- **Disclaimer**: en el footer de la función de generación (jsPDF `doc.text(...)` en el loop `getNumberOfPages`, o el template de impresión). Texto estándar CeiboMed: *"Esta herramienta es de apoyo clínico. No reemplaza el juicio médico ni constituye una recomendación diagnóstica o terapéutica. CeiboMed © 2026"*.
- **Firma**: bloque con nombre + matrícula + institución del médico, alineado al pie.
- **Campos**: el nombre y la fecha del paciente deben imprimirse en el encabezado del informe.

## Ejemplo de uso

**Input (el usuario dice):**
> "Voy a generar el PDF de ErgoSmart para dárselo al paciente. ¿Está todo?"

**Acción:** correr `check_pdf_quality.py ~/Desktop/APLICACIONES/ergosmart/index.html`.

**Output (reporte):**
```
▶ ergosmart  —  ❌ 0 crítico(s), 1 mayor(es)
   ✅ Campo: Nombre del paciente        línea 3042
   ✅ Campo: Fecha                      línea 3044
   ✅ Campo: Médico responsable         línea 588
   ❌ Firma del médico  [MAYOR]
      sin referencia a firma/sello — agregar bloque de firma al PDF
   ✅ Disclaimer médico-legal           línea 2238
   ✅ QR en el PDF                      generación de QR en línea 3225
```

**Respuesta al usuario:** "El informe de ErgoSmart tiene nombre, fecha, disclaimer y QR ✅, pero **no detecté el bloque de firma del médico**. Antes de entregarlo conviene agregar al pie la firma (nombre + matrícula). ¿Lo agrego?"

## Notas

- La detección es heurística (regex sobre patrones frecuentes en las apps de la suite). Un `❌` puede ser un falso negativo si el campo está referenciado de una forma inusual — en la duda, verificá la línea que el script señala o la función de generación del PDF.
- Ampliá `FIELD_PATTERNS` / `DISCLAIMER_PATTERNS` / `QR_DRAW_HINTS` en el script si la suite adopta nuevas convenciones.
- Complementa a `clinical-disclaimer-guard`: aquélla mira la app entera antes de compartir; ésta se enfoca en que el PDF individual salga completo.
