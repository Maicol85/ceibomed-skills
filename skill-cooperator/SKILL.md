---
name: skill-cooperator
description: Orquesta automáticamente las skills correctas de CeiboMed según el contexto de cada sesión. Al inicio de una sesión (o cuando se lo pide) detecta el tipo de tarea —seguridad, UX, clínico, deploy, pre-lanzamiento o inicio— a partir de una descripción o palabras clave, y propone qué skills activar y en qué orden óptimo, usando solo las skills que están instaladas. Ejemplo: en una sesión de pre-lanzamiento activa, en orden, clinical-disclaimer-guard + api-key-protector + mobile-first-checker + pdf-quality-guard + changelog-auto. Usá esta skill al inicio de sesión, o cuando el usuario diga "qué skills usar", "coordiná las skills", "cooperador", "por dónde empiezo", "organizá el trabajo" o describa el tipo de tarea que va a hacer. Es de solo lectura: arma el plan, no ejecuta las skills.
---

# skill-cooperator

Tener muchas skills sirve poco si en cada sesión hay que acordarse de cuáles correr y en qué orden. Esta skill es el director de orquesta: mira el tipo de tarea de la sesión y arma el plan — qué skills activar, en qué secuencia y por qué — usando solamente las que ya tenés instaladas.

## Tipos de tarea y plan sugerido

| Tipo | Plan (orden) |
|---|---|
| `inicio` | changelog-auto → skill-discovery |
| `seguridad` | api-key-protector → clinical-disclaimer-guard |
| `ux` | mobile-first-checker |
| `clinico` | pdf-quality-guard → clinical-disclaimer-guard |
| `deploy` | api-key-protector → clinical-disclaimer-guard → pdf-quality-guard → changelog-auto |
| `pre-lanzamiento` | clinical-disclaimer-guard → api-key-protector → mobile-first-checker → pdf-quality-guard → changelog-auto |

El orden no es arbitrario: primero lo que puede **bloquear** una entrega (avisos legales, credenciales), después lo que mejora la calidad (móvil, PDF), y al final el registro del día (changelog).

## Cuándo usarla

- Al **inicio de cada sesión**, para orientar el trabajo.
- Cuando el usuario pregunta "¿qué skills uso?", "¿por dónde empiezo?", "coordiná las skills".
- Antes de una etapa concreta (pre-lanzamiento, deploy) para no saltarse un control.

## Cómo ejecutarla

```bash
# Detectar el tipo desde una descripción:
python3 <skill-dir>/scripts/cooperate.py "voy a compartir InfectSmart con el equipo"

# Forzar un tipo:
python3 <skill-dir>/scripts/cooperate.py --type pre-lanzamiento

# Ver todos los tipos y las skills instaladas:
python3 <skill-dir>/scripts/cooperate.py --list
```

El script detecta el tipo por palabras clave, cruza el plan con las skills instaladas (marca las que faltan) y siempre sale con código 0 (es un planificador, no un validador).

## Cómo interpretar y actuar

El reporte da la **secuencia numerada** de skills a activar y una línea de por qué cada una. Actuá así:

1. Corré las skills en ese orden (cada una es de solo lectura y no bloquea por sí misma).
2. Resolvé los `❌` que reporte una etapa **antes** de pasar a la siguiente (p. ej. no sigas a "PDF" si `api-key-protector` encontró una credencial expuesta).
3. Si el plan lista skills **no instaladas**, ofrecé crearlas con `skill-creator` o correr `skill-discovery`.

No ejecutes las skills en silencio ni cambies archivos: esta skill sólo dice qué hacer y en qué orden.

## Ejemplo de uso

**Input (el usuario dice):**
> "Arranco sesión de pre-lanzamiento de la suite, quiero dejar todo listo para publicar."

**Acción:** correr `cooperate.py --type pre-lanzamiento` (o pasando la frase).

**Output:**
```
  Tipo de tarea: pre-lanzamiento
  Orden de ejecución sugerido:
   1. /clinical-disclaimer-guard  — garantizar los avisos médico-legales
   2. /api-key-protector          — cazar credenciales antes de exponer código
   3. /mobile-first-checker       — que ande en celular/tablet
   4. /pdf-quality-guard          — que el informe PDF salga completo
   5. /changelog-auto             — registrar/leer el estado del día
```

**Respuesta al usuario:** "Para el pre-lanzamiento, el orden sería: **1)** disclaimer médico-legal, **2)** credenciales expuestas, **3)** revisión móvil, **4)** que el PDF salga completo, **5)** changelog del día. Arranco por `clinical-disclaimer-guard` sobre las apps prioritarias — si algo sale ❌, lo resolvemos antes de seguir. ¿Dale?"

## Notas

- El mapeo tipo→plan y las palabras clave viven en `PLANS` y `KEYWORDS` del script; ajustalos si cambian los flujos de CeiboMed.
- Es la contraparte de `skill-discovery`: cooperator organiza lo que ya tenés; discovery busca lo que falta.
- No reemplaza el criterio: si la sesión es mixta, corré el plan del tipo dominante y sumá skills sueltas según haga falta.
