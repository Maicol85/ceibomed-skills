---
name: changelog-auto
description: Genera automáticamente un registro de cambios (CHANGELOG.md) al final de una sesión de desarrollo de CeiboMed, leyendo los commits git del día de todos los repos de la suite y organizándolos por app y por tipo (Seguridad, Clínico, UX/A11y, Config/Feature, Fix). Es acumulativo: agrega la sesión del día sin borrar el historial anterior. Usá esta skill al FINAL de una sesión de trabajo en CeiboMed, cuando el usuario diga "cerramos", "fin de sesión", "terminamos por hoy", "generá el changelog", "registrá los cambios de hoy", "qué hicimos hoy" o pida documentar/resumir el trabajo de la jornada. También cuando se prepare un resumen de release. Escribe el archivo en ~/Desktop/APLICACIONES/CHANGELOG.md.
---

# changelog-auto

Al final de una jornada de trabajo sobre la suite CeiboMed suele haber decenas de commits repartidos entre varios repos (cada app es su propio repositorio git). Reconstruir "qué se hizo hoy" a mano es tedioso y se pierde. Esta skill lo automatiza: lee los commits del día de todas las apps y arma un `CHANGELOG.md` acumulativo, legible y organizado.

## Cuándo usarla

- **Al cerrar la sesión** ("terminamos", "fin de sesión", "cerramos por hoy").
- Cuando el usuario pide "el changelog", "registrá los cambios" o "qué hicimos hoy".
- Al preparar notas de un release.

## Cómo ejecutarla

```bash
# Registrar la sesión de hoy (default):
python3 <skill-dir>/scripts/gen_changelog.py

# Ver qué se generaría sin escribir el archivo:
python3 <skill-dir>/scripts/gen_changelog.py --dry-run

# Un día puntual, o los últimos N días (si la sesión cruzó la medianoche):
python3 <skill-dir>/scripts/gen_changelog.py --date 2026-07-29
python3 <skill-dir>/scripts/gen_changelog.py --days 2
```

El script recorre cada subcarpeta con `.git` bajo `~/Desktop/APLICACIONES`, toma los commits del período, los clasifica por tipo y actualiza `~/Desktop/APLICACIONES/CHANGELOG.md`.

## Comportamiento clave

- **Acumulativo y no destructivo:** los bloques de días anteriores se conservan. El nuevo bloque de fecha se inserta arriba (lo más reciente primero).
- **Idempotente:** si corrés la skill varias veces el mismo día, regenera el bloque de esa fecha en su lugar en vez de duplicarlo. Así podés correrla al cierre aunque ya la hayas corrido antes.
- **Clasificación automática** por palabras clave del mensaje de commit:
  - **Seguridad** — XSS, escHtml, CSV/formula injection, credenciales, import schema, localStorage
  - **Clínico** — disclaimer, diagnóstico, protocolo, severidad, umbrales, dosis, guías
  - **UX/A11y** — a11y, ARIA, focus, headings, dark mode, contraste, touch targets, Impeccable
  - **Config/Feature** — tabs, toggles, export/import, QR, paneles, calculadoras
  - **Fix** — fix, bug, corrección, hotfix
  - **General** — el resto (ej. deploy, CNAME)

## Formato de salida

```markdown
# CHANGELOG — CeiboMed

## 2026-07-30
### ecosmart
- **Seguridad** — XSS Docencia, CSV injection, import validation, localStorage  (`f8c597f`)
- **UX/A11y** — headings semánticos, ARIA modales/toasts, div→button  (`890baa9`)
- **Config/Feature** — Config tab (básico/avanzado/toggles), skip intro, QR PDF  (`6d8db4e`)
### marcapaso
- **UX/A11y** — Impeccable P1/P2 (tokens, dark mode, headings, ARIA)  (`366e9f5`)

## 2026-07-29
### ...  (sesión anterior, intacta)
```

## Cómo actuar tras generarlo

Después de correr el script, resumí al usuario en 2-3 líneas lo más destacado de la jornada (ej. "Hoy: fixes de seguridad en 6 apps, dark mode + a11y en MarcapasoControl, tab Config en EcoSmart"). Si el usuario quiere versionarlo, ofrecé commitear el `CHANGELOG.md`, teniendo en cuenta que vive en la raíz `~/Desktop/APLICACIONES` (que puede no ser un repo git — en ese caso queda como archivo local de registro).

## Ejemplo de uso

**Input (el usuario dice):**
> "Listo, cerramos por hoy. Generá el changelog de la sesión."

**Acción:** correr `gen_changelog.py`.

**Output:**
```
✅ CHANGELOG actualizado: ~/Desktop/APLICACIONES/CHANGELOG.md
   Sesión 2026-07-30 · 48 commit(s) registrados.
```

**Respuesta al usuario:** "Changelog actualizado con los 48 commits de hoy. Lo más destacado: fixes de seguridad (XSS/CSV/import) en las 6 apps prioritarias, dark mode + accesibilidad completa en MarcapasoControl, y la tab de Configuración en EcoSmart. El historial de sesiones anteriores quedó intacto."

## Notas

- Si un commit queda mal clasificado (cae en "General" o en un tipo que no corresponde), ajustá los patrones en `TYPE_RULES` dentro del script — el orden importa (el primer match gana).
- Se relaciona con la skill `ceibo-continuidad` (que mantiene el contexto narrativo entre sesiones): esta skill es el registro **factual** de commits; la otra es la **bitácora** de decisiones. Pueden convivir.
