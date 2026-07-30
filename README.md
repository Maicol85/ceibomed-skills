# CeiboMed Skills

Tres skills de [Claude Code](https://claude.com/claude-code) para el desarrollo seguro y ordenado de la suite clínica **CeiboMed** — un conjunto de herramientas de apoyo a la decisión médica construidas como aplicaciones HTML de un solo archivo.

Cada skill automatiza un control que, hecho a mano, es fácil de olvidar en cada release: verificar los avisos médico-legales, cazar credenciales expuestas antes de publicar, y dejar registrado qué cambió en la jornada.

## Las skills

### 🩺 `clinical-disclaimer-guard`
Verifica que una app tenga el **disclaimer médico-legal** correcto antes de compartirla o publicarla. Comprueba tres cosas: (1) disclaimer visible en el HTML, (2) disclaimer en el pie del PDF generado, y (3) aviso al usuario de que los datos se guardan localmente. Reporta qué falta y en qué línea.

**Cuándo:** antes de compartir, publicar o entregar una app a un colega o paciente.

### 🔑 `api-key-protector`
Detecta **API keys, contraseñas y credenciales expuestas** en el código fuente antes de un `git push` o de publicar. Encuentra keys de proveedor (sk-, ghp_, AKIA…, AIza…, Bearer), contraseñas hardcodeadas, URLs con credenciales y secretos guardados en `localStorage`. Reporta severidad, línea exacta y remediación.

**Cuándo:** antes de cada `git push`, release, o al empezar a trabajar con APIs/claves externas.

### 📝 `changelog-auto`
Genera un **CHANGELOG.md acumulativo** al cierre de sesión, leyendo los commits git del día de todos los repos de la suite y organizándolos por app y por tipo (Seguridad, Clínico, UX/A11y, Config/Feature, Fix). No destructivo e idempotente.

**Cuándo:** al final de cada sesión de trabajo.

## Instalación

### Opción A — Claude Code (skills de proyecto)
Cloná el repo dentro de la carpeta de skills de tu proyecto (o de tu perfil):

```bash
# skills a nivel proyecto
git clone https://github.com/maicol85/ceibomed-skills.git .claude/skills-tmp
cp -r .claude/skills-tmp/clinical-disclaimer-guard \
      .claude/skills-tmp/api-key-protector \
      .claude/skills-tmp/changelog-auto  .claude/skills/
rm -rf .claude/skills-tmp
```

O a nivel usuario (disponibles en todos tus proyectos):

```bash
git clone https://github.com/maicol85/ceibomed-skills.git /tmp/ceibomed-skills
cp -r /tmp/ceibomed-skills/{clinical-disclaimer-guard,api-key-protector,changelog-auto} ~/.claude/skills/
```

Reiniciá Claude Code y las tres quedan disponibles como `/clinical-disclaimer-guard`, `/api-key-protector` y `/changelog-auto`.

### Opción B — archivo `.skill`
En la sección [Releases](https://github.com/maicol85/ceibomed-skills/releases) hay un `.skill` de cada una. Desde Claude (Cowork / claude.ai) podés abrir el archivo y usar **"Save skill"** para instalarla en tu perfil.

## Estructura

```
ceibomed-skills/
├── clinical-disclaimer-guard/
│   ├── SKILL.md
│   └── scripts/check_disclaimer.py
├── api-key-protector/
│   ├── SKILL.md
│   └── scripts/scan_secrets.py
└── changelog-auto/
    ├── SKILL.md
    └── scripts/gen_changelog.py
```

Cada skill es autocontenida: un `SKILL.md` con las instrucciones y un script Python (sin dependencias externas, solo la librería estándar) que hace el trabajo determinista.

## Uso rápido (sin Claude, directo por CLI)

Los scripts funcionan también standalone:

```bash
# Verificar disclaimers de una app o de toda la suite
python3 clinical-disclaimer-guard/scripts/check_disclaimer.py ~/Desktop/APLICACIONES

# Escanear credenciales antes de un push
python3 api-key-protector/scripts/scan_secrets.py mi-app/index.html

# Generar el changelog del día
python3 changelog-auto/scripts/gen_changelog.py --root ~/Desktop/APLICACIONES
```

## Requisitos

- Python 3.8+ (solo librería estándar).
- Para `changelog-auto`: `git` disponible en el PATH.

## Licencia

MIT.

---

*Hecho para la suite CeiboMed · Dr. M. Dos Santos.*
