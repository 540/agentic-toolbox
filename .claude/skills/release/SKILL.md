---
name: release
description: >-
  Corta una release del marketplace 540/agentic-toolbox: decide el bump semver
  por plugin, redacta la entrada del CHANGELOG y delega la mecánica (versiones,
  changelog, commit, tag, push atómico) en scripts/release.py. USAR cuando el
  usuario diga "haz release", "publica versión", "corta release del toolbox",
  "saca la X.Y.Z", "release del marketplace" o "commitea, pushea y crea
  release" — también desde una rama o worktree — en este repo. NO USAR para
  releases de otros repos.
user-invocable: true
allowed-tools: Read, Edit, Bash, AskUserQuestion
metadata:
  internal: true
---

# Release del marketplace 540/agentic-toolbox

Separación de responsabilidades: **tú (skill)** aportas el juicio — qué cambió,
qué bump toca, cómo se redacta la entrada — y **el script** ejecuta la mecánica
de forma determinista (validaciones, JSON, changelog, commit, tag, push atómico).
Nunca hagas a mano lo que hace el script.

El script: `python3 .claude/skills/release/scripts/release.py` (desde la raíz del repo).

Si el encargo llega estando en una rama o worktree, eso ya autoriza aterrizarla
en main: hazlo sin advertir ni pedir confirmación por el merge (el OK del Paso 5
sigue aplicando). Ejecuta el script del checkout principal por ruta absoluta:
REPO se deriva de la ruta del script, no del cwd.

## Paso 1: Diagnóstico

```bash
python3 .claude/skills/release/scripts/release.py check
```

- Si sale con error de desincronización (versiones incoherentes, tags sin
  pushear, o el fallo clásico: versión publicada sin tag), muestra el problema al
  usuario y aplica con él la reparación que imprime el propio script **antes** de
  cualquier release nuevo.
- Si no hay commits desde el último tag, no hay nada que releasear: dilo y para.

## Paso 2: Detectar qué cambió

El `check` ya agrupa los commits desde el último tag por plugin. Complementa con
diff si hace falta:

```bash
git log --oneline v<último>..HEAD -- plugins/<plugin>
git log --oneline v<último>..HEAD -- . ':!plugins'   # cambios de raíz
```

- Cambios **solo de raíz** (README, .claude/, resources/, docs): normalmente no
  exigen release — los usuarios consumen vía git y `/plugin update` los trae
  igual. Señálalo y pregunta al usuario si aun así quiere cortar versión.

## Paso 3: Proponer bumps (reglas 0.x)

| Cambio | Bump del plugin |
|---|---|
| Skill/hook nuevo, feature nueva, cambio de comportamiento, breaking (renombrados, convenciones) | MINOR |
| Fix, ajuste de texto, actualización de recursos/datos | PATCH |

- El **marketplace** (`metadata.version`) bumpea en **cada release** con la
  magnitud del mayor bump de plugin (release train: el tag y la sección del
  CHANGELOG cuelgan de él). Un plugin nuevo también bumpea el marketplace (MINOR).
- Los plugins no tocados no se bumpean.

## Paso 4: Redactar la entrada del CHANGELOG

UNA línea por cambio, concisa, en castellano, bajo `### Added` / `### Changed` /
`### Fixed` según toque, con el formato ya usado en el fichero:

```markdown
- Plugin `gauntlet-audit`: nuevo campo de auditoría para contract testing.
```

Escríbela con Edit dentro de la sección `## [Unreleased]` de `CHANGELOG.md`.
No toques versiones ni enlaces.

## Paso 5: Confirmar con el usuario

Presenta y pide OK explícito antes de ejecutar nada:

- Tabla de versiones: cada plugin tocado `actual -> nueva` y marketplace `actual -> nueva`.
- El texto exacto de la entrada añadida a `[Unreleased]`.
- El tag que se creará (`vX.Y.Z`) y que el push es atómico (commit + tag).

## Paso 6: Ejecutar

Primero en seco, muestra la salida:

```bash
python3 .claude/skills/release/scripts/release.py run --version X.Y.Z --plugin nombre=X.Y.Z --dry-run
```

Si el plan impreso coincide con lo confirmado, ejecuta el real (mismo comando
sin `--dry-run`). Flags: `release.py run --help`.

## Paso 7: Verificar

Reporta al usuario: tag publicado, URL de compare (la imprime el script) y
recuerda que los consumidores actualizan con `/plugin update <plugin>@540`.

## Casos especiales

- **Varios plugins tocados**: un solo release con varios `--plugin`; cada bullet
  del changelog nombra su plugin; el marketplace toma el mayor bump.
- **Push fallido a medias**: el script deja commit y tag en local e imprime el
  comando de recuperación (solo re-pushear). No repitas el `run`.
- **Estado desincronizado**: lo detecta `check` — ver Paso 1.
- **`[Unreleased]` ya traía bullets** de un release anterior abortado: revísalos
  con el usuario (¿siguen siendo ciertos?) antes de añadir los nuevos.
