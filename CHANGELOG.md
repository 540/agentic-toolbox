# Changelog

Todos los cambios notables del marketplace `540/agentic-toolbox` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado sigue [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Plugin `no-comments` (nuevo, 0.1.0): configuración opcional por proyecto en `.no-comments.json`, con `ignore` (globs de rutas exentas) y `allow` (regex de comentarios permitidos).
- Plugin `no-comments` (nuevo, 0.1.0): versión agnóstica al lenguaje del hook. Deduce la sintaxis de comentario de la extensión (familias `#`, `//`, `--`, `<!-- -->`) y deja pasar lo que no reconoce.

### Changed

- El plugin `no-comments` pasa a llamarse `no-comments-ruby`: su escáner siempre fue específico de Ruby y el nombre genérico queda libre para la versión agnóstica al lenguaje. Quien lo tuviera instalado debe reinstalarlo con el nombre nuevo.

## [0.2.0] - 2026-09-01

### Added

- Plugin `no-comments` (nuevo, 0.1.0): hook PreToolUse que bloquea los comentarios que el agente añade a ficheros Ruby (`.rb`/`.rake`); exime los pragmas de máquina (frozen_string_literal, sorbet, rubocop).
- Skill `release` (`.claude/`, no se distribuye en plugins): flujo de release del marketplace, trasladado desde 540-claude-toolkit.

## [0.1.0] - 2026-09-01

### Added

- Plugin `gauntlet-audit`: audita la red de verificación de un repo (9 campos con madurez 0-4, score global y roadmap) y responde "¿puedo confiar en código escrito por agentes sin leerlo?".
- Estructura inicial del marketplace: `plugins/`, `resources/`, licencia MIT.

[Unreleased]: https://github.com/540/agentic-toolbox/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/540/agentic-toolbox/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/540/agentic-toolbox/releases/tag/v0.1.0
