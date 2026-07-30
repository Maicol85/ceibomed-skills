---
name: api-key-protector
description: Detecta API keys, contraseñas y credenciales expuestas en el código fuente de las apps CeiboMed ANTES de hacer git push o publicar. Escanea buscando API keys hardcodeadas (patrones sk-, ghp_, AKIA…, AIza…, Bearer, apikey=, token=), contraseñas hardcodeadas en texto plano, URLs con credenciales embebidas (user:pass@host), y tokens/keys guardados directamente en localStorage. Usá esta skill SIEMPRE antes de un git push, un release, o de compartir/publicar una app de CeiboMed, y cuando el usuario mencione "revisar secretos", "buscar credenciales", "chequear API keys", "antes de subir a GitHub", "escanear contraseñas" o "seguridad antes del push". Reporta severidad, línea exacta y remediación sugerida.
---

# api-key-protector

Las apps de CeiboMed son archivos HTML de un solo fichero que se sirven al navegador y se versionan en GitHub. Cualquier credencial en el fuente queda **visible para cualquiera** que abra "Ver código fuente" o el repositorio. Esta skill hace un escaneo determinista para cazar esas exposiciones antes de que se publiquen.

Es especialmente relevante en esta suite porque el patrón habitual es un "login" cliente-side con una contraseña literal en el JS (`if (pwd === '...')` o `var APP_PASS='...'`): eso **no protege nada** y expone la clave. La skill lo detecta.

## Cuándo usarla

- **Antes de cada `git push`** de una app.
- Antes de compartir/publicar o mandar el archivo a un colega.
- Cuando el usuario pide "revisar credenciales/secretos" o menciona subir a GitHub.

Es de solo lectura: no modifica archivos.

## Qué detecta

| Categoría | Ejemplos | Severidad |
|---|---|---|
| Claves de proveedor | `sk-…`, `ghp_…`, `AKIA…`, `AIza…`, `xox…`, PEM privada | 🔴 CRÍTICO |
| URL con credenciales | `https://user:pass@host` | 🔴 CRÍTICO |
| Contraseña hardcodeada | `pwd === 'maicolett1'`, `var APP_PASS='...'` | 🔴 CRÍTICO |
| API key / secret / token literal | `apikey: 'abc123…'`, `Bearer eyJ…` | 🟠 ALTO |
| Secreto en localStorage | `localStorage.setItem('auth_token', …)` | 🟠 ALTO |

## Cómo ejecutarla

```bash
# Antes de pushear una app:
python3 <skill-dir>/scripts/scan_secrets.py ~/Desktop/APLICACIONES/ecosmart/index.html

# Varias / toda la suite:
python3 <skill-dir>/scripts/scan_secrets.py ~/Desktop/APLICACIONES
```

Devuelve código de salida **1 si hay algún hallazgo CRÍTICO o ALTO** — sirve para frenar un push automatizado.

## Cómo interpretar y actuar

Cada hallazgo trae severidad, `archivo:línea`, el fragmento y una remediación concreta. Prioridad:

1. **🔴 CRÍTICO primero.** Claves de proveedor → **rotarlas/revocarlas en el proveedor de inmediato** (asumir que ya están comprometidas si el archivo se compartió o está en un repo). Contraseñas hardcodeadas → quitarlas del fuente; recordar que un login cliente-side no protege datos que ya están en el DOM/localStorage (mover a backend o cifrar el store).
2. **🟠 ALTO.** Tokens/keys en localStorage → son legibles por cualquier XSS y persisten en disco; usar memoria efímera o cifrar.

No apliques los fixes en silencio en un escaneo pre-push: mostrá al usuario la lista por severidad con línea exacta y la remediación, y dejá que decida (algunos "secretos" pueden ser intencionales, como un flag `ett_auth='1'` que no es una credencial real — usá criterio).

## Ejemplo de uso

**Input (el usuario dice):**
> "Voy a subir MarcapasoControl a GitHub, fijate que no tenga nada sensible."

**Acción:** correr `scan_secrets.py ~/Desktop/APLICACIONES/marcapaso/index.html`.

**Output:**
```
▶ marcapaso  —  🔴 1 crítico(s) · 🟠 0 alto(s)
   🔴 [CRITICO] Contraseña/clave asignada a una constante  (línea 1869)
      var MP_LOGIN_PASS='maicolmarcapaso1'
      → Constante de contraseña con valor literal en el fuente. Removerla; no confiar en auth cliente-side.
```

**Respuesta al usuario:** "Antes de subir: MarcapasoControl tiene la contraseña `maicolmarcapaso1` **hardcodeada en la línea 1869** (`var MP_LOGIN_PASS='...'`). Al ser un HTML servido al navegador, cualquiera la ve en el código fuente, y el login cliente-side no protege los datos igual. Recomiendo quitarla del fuente antes del push. ¿La saco?"

## Notas y ajustes

- **Falsos positivos:** el escáner evita matchear la palabra española "clave" en prosa clínica (frecuente en estas apps) y los `<input type="password">`. Aun así, revisá cada hallazgo: un `localStorage.setItem('ett_auth','1')` es un flag de sesión, no una credencial — es 🟠 pero de bajo riesgo real.
- **Extensión:** agregá nuevos patrones de proveedor a `RULES` en el script si CeiboMed integra alguna API externa (ej. una key de un servicio de laboratorio).
- **Complementa** a `/sharp-edges` y `/cyber-neo`: esta skill es el chequeo rápido y específico de credenciales; las otras cubren el análisis de seguridad amplio.
