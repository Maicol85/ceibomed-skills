---
name: clinical-disclaimer-guard
description: Verifica que una app clínica de CeiboMed tenga el disclaimer médico-legal correcto y visible antes de compartirla o publicarla. Comprueba tres cosas: (1) que exista texto de disclaimer en el HTML ("apoyo clínico", "no reemplaza el juicio médico" o similar), (2) que el disclaimer aparezca en el pie del PDF generado, y (3) que haya un aviso al usuario de que los datos se guardan localmente (localStorage). Usá esta skill SIEMPRE que vayas a compartir, publicar, exportar o entregar una app de CeiboMed a un colega o paciente, o cuando el usuario mencione "compartir la app", "está lista para publicar", "revisar antes de mandar", "disclaimer", "aviso médico-legal" o "responsabilidad legal". Reporta qué falta y en qué línea aproximada.
---

# clinical-disclaimer-guard

Las apps de CeiboMed son herramientas de apoyo a la decisión clínica. Antes de compartirlas con colegas o pacientes, cada una debe dejar en claro tres cosas, por seguridad médico-legal del autor y del usuario:

1. **Es una herramienta de apoyo, no un diagnóstico.** Tiene que haber un disclaimer visible en la interfaz.
2. **El disclaimer viaja con el informe.** El PDF que la app genera debe llevar el disclaimer en el pie, porque el PDF sale de la app y circula solo.
3. **Los datos son locales y responsabilidad del usuario.** Si la app guarda datos en `localStorage`, el usuario debe estar avisado de que la información vive en su dispositivo y su respaldo/confidencialidad son su responsabilidad.

Esta skill automatiza esa verificación para no depender de la memoria en cada release.

## Cuándo usarla

- Antes de compartir una app con un colega, un paciente o publicarla.
- Como paso previo a un `git push` "de release".
- Cuando el usuario pregunta "¿está lista para compartir?" o menciona disclaimer / aviso legal.

Es una verificación de solo lectura: no modifica archivos.

## Cómo ejecutarla

Corré el script bundled, que hace el análisis determinista y reporta líneas exactas:

```bash
# Una app puntual:
python3 <skill-dir>/scripts/check_disclaimer.py ~/Desktop/APLICACIONES/ecosmart/index.html

# Varias:
python3 <skill-dir>/scripts/check_disclaimer.py ecosmart/index.html marcapaso/index.html

# Toda la suite (escanea */index.html bajo el directorio):
python3 <skill-dir>/scripts/check_disclaimer.py ~/Desktop/APLICACIONES
```

El script devuelve código de salida **1 si falta algún requisito** (útil para bloquear un release) y **0 si todo está OK**.

## Cómo interpretar y actuar

El reporte marca cada requisito con `✅` (presente), `❌` (falta) o `➖` (no aplica, ej: la app no genera PDF o no usa localStorage). Para cada `✅` cita la línea y el fragmento encontrado; para cada `❌` explica qué agregar.

Cuando haya un `❌`, no lo arregles en silencio: mostrá al usuario qué falta y en qué archivo/línea, y ofrecé el texto sugerido. Ejemplos de texto que satisface cada requisito:

- **Disclaimer HTML/PDF:** "Herramienta de apoyo clínico. No reemplaza el juicio médico del profesional tratante."
- **Aviso de datos locales:** "Los datos se almacenan localmente en este dispositivo. El usuario es responsable de su confidencialidad y respaldo."

El disclaimer del PDF suele ir en la función de generación (jsPDF `doc.text(...)` en el footer, o el template de `document.write` de impresión). Si el script detectó la generación de PDF pero no encontró disclaimer cercano, indicá agregarlo al pie de cada página.

## Ejemplo de uso

**Input (el usuario dice):**
> "Terminé InfectSmart, quiero compartirla con el equipo de infectología. ¿Está todo en orden legalmente?"

**Acción:** correr `check_disclaimer.py ~/Desktop/APLICACIONES/infectsmart/index.html`.

**Output (reporte):**
```
▶ infectsmart  —  ❌ 1 faltante(s)
   ✅ Disclaimer médico-legal en HTML
      línea 612: "herramienta de apoyo clínico, no reemplaza el juicio médico"
   ❌ Disclaimer en el pie del PDF
      generación de PDF en línea ~3459 sin disclaimer cercano — agregar al footer
   ✅ Aviso de datos locales (localStorage)
      línea 640: "los datos se guardan en este dispositivo..."
```

**Respuesta al usuario:** "InfectSmart tiene el disclaimer en pantalla y el aviso de datos locales ✅, pero el **PDF exportado no lleva el disclaimer en el pie** (la generación está en la línea ~3459). Antes de compartirla conviene agregar al footer del PDF: *'Herramienta de apoyo clínico. No reemplaza el juicio médico del profesional tratante.'* ¿Lo agrego?"

## Notas

- La detección es heurística (regex sobre patrones frecuentes en español). Un `❌` en el PDF puede ser un falso negativo si el disclaimer está redactado de forma inusual o lejos del código de generación — en la duda, verificá manualmente la línea que el script señala.
- Ampliá `DISCLAIMER_PATTERNS` / `LOCAL_DATA_PATTERNS` en el script si CeiboMed adopta una redacción estándar nueva.
