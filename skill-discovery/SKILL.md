---
name: skill-discovery
description: Encuentra skills nuevas relevantes para el desarrollo de CeiboMed (seguridad médica, generación de PDF, accesibilidad y testing) que todavía NO estén instaladas. Lee las skills ya presentes en el directorio de skills del proyecto, las compara contra un catálogo curado de controles útiles para una suite clínica offline-first, y reporta cada candidata no instalada con su nombre, categoría, para qué sirve, por qué es útil para CeiboMed y cómo instalarla o crearla. No sugiere skills que ya estén instaladas. Usá esta skill cuando el usuario pregunte "buscar skills", "hay algo nuevo", "qué skills existen", "qué skills me faltan", "skills nuevas", "discovery" o quiera ampliar el toolkit del proyecto. Es de solo lectura: sugiere, no instala.
---

# skill-discovery

El toolkit de CeiboMed crece con el proyecto. Esta skill responde la pregunta "¿qué me estaría faltando?" sin repetir lo que ya tenés: mira las skills instaladas y propone controles adicionales que tienen sentido para una suite de apps clínicas de un solo archivo, offline-first, que generan PDF e imprimen.

Cubre cuatro categorías:

- **Seguridad médica** — endurecimiento, fuga de datos de paciente (PHI), integridad de dependencias de CDN.
- **PDF** — accesibilidad/etiquetado del PDF, diff visual contra baseline.
- **Accesibilidad** — contraste de tokens (claro/oscuro), linter de ARIA, navegación por teclado.
- **Testing** — smoke tests headless, round-trip de import/export de localStorage.

## Cuándo usarla

- Cuando el usuario pregunta "¿hay skills nuevas?", "¿qué me falta?", "buscar skills", "discovery".
- Periódicamente (cada 2-3 sesiones) como revisión del toolkit.

## Cómo ejecutarla

```bash
# Todas las categorías, usando el directorio de skills por defecto:
python3 <skill-dir>/scripts/discover_skills.py

# Un directorio de skills explícito:
python3 <skill-dir>/scripts/discover_skills.py ~/Desktop/APLICACIONES/.claude/skills

# Filtrar por categoría:
python3 <skill-dir>/scripts/discover_skills.py --cat seguridad
```

El script detecta lo instalado leyendo cada subcarpeta con `SKILL.md` (y el `name:` de su frontmatter), y **excluye esas de las sugerencias**. Siempre sale con código 0 (es informativo).

## Cómo interpretar y actuar

Cada candidata trae **Qué hace / Por qué (para CeiboMed) / Cómo obtenerla**. No instala nada: es una lista para decidir. Para cada una que el usuario quiera adoptar:

- Si es una skill a crear, usá `skill-creator` siguiendo el patrón de las existentes (SKILL.md con frontmatter + `scripts/` + ejemplo).
- Si podría existir como plugin publicado, buscala en el registro de plugins/skills antes de crearla desde cero.

Presentá 2-3 candidatas priorizadas por impacto para el proyecto, no la lista entera, salvo que pidan todo.

## Ejemplo de uso

**Input (el usuario dice):**
> "¿Hay alguna skill nueva que me convenga para CeiboMed?"

**Acción:** correr `discover_skills.py`.

**Output (extracto):**
```
  Skills ya instaladas: api-key-protector, changelog-auto, clinical-disclaimer-guard,
                        mobile-first-checker, pdf-quality-guard, skill-cooperator, skill-discovery
### SEGURIDAD
  • phi-leak-detector
    Qué hace : Detecta datos de paciente que salgan a logs, URLs o servicios externos.
    Por qué  : Las apps son offline-first; verifica que ningún dato clínico se filtre a la red.
    Cómo     : Crear con skill-creator; regex sobre fetch/XHR/console con campos de paciente.
```

**Respuesta al usuario:** "Mirando lo que ya tenés, las tres que más suman para CeiboMed serían: **phi-leak-detector** (que ningún dato de paciente se escape a la red), **contrast-checker** (legibilidad del dark mode contra WCAG) y **smoke-test-runner** (que cada app cargue y exporte el PDF sin errores). ¿Querés que arme alguna con skill-creator?"

## Notas

- El catálogo es curado y local (no depende de la red). Ampliá la lista `CATALOG` en el script a medida que aparezcan controles nuevos relevantes.
- La detección de "ya instalada" usa el nombre de carpeta y el `name:` del frontmatter; si una skill se instaló con otro nombre, agregala al catálogo con su alias.
- Es la contraparte proactiva de `skill-cooperator`: discovery encuentra skills nuevas; cooperator orquesta las que ya tenés.
