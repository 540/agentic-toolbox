# no-comments

Parte de [540 Agentic Toolbox](https://github.com/540/agentic-toolbox).

Hook `PreToolUse` para Claude Code. Bloquea `Write`, `Edit` y `MultiEdit` cuando el agente añade comentarios al código, en cualquier lenguaje. La premisa: el código dice lo que hace, y un comentario que lo repite caduca en cuanto uno de los dos cambia. Si un bloque parece pedir comentario, el problema es de naming: se extrae una función con buen nombre.

Es la versión agnóstica al lenguaje de [no-comments-ruby](../no-comments-ruby/). Instala uno de los dos, no ambos: en un proyecto Ruby los dos dispararían sobre el mismo edit.

## Cómo funciona

- Solo cuentan los comentarios **añadidos**. Un comentario que ya estaba en el `old_string` viaja con su código: los refactors y los movimientos no disparan el hook.
- La sintaxis de comentario se deduce de la extensión o del nombre del fichero, en cuatro familias: `#` (Python, Ruby, shell, YAML, TOML, Terraform, Elixir, Makefile, Dockerfile…), `//` con bloques `/* */` (JavaScript, TypeScript, Java, Kotlin, Go, Rust, C/C++, C#, Swift, PHP, Scala, Dart, SCSS…), `--` (SQL, Lua, Haskell, Elm) y `<!-- -->` (HTML, Vue, Svelte, XML, Astro). CSS solo admite bloques.
- Una extensión que no reconoce no se toca: el hook deja pasar en lugar de adivinar.
- Exime los pragmas que lee una máquina: shebang, `noqa`, `type: ignore`, `eslint-disable`, `@ts-`, `shellcheck`, `rubocop`, `nolint`, `nosec`, `biome-ignore`, `istanbul ignore`, directivas de preprocesador, cabeceras de licencia y copyright, `ponytail:`, entre otros.
- Antes de buscar el marcador de comentario descarta el contenido de los strings, para que un `#` dentro de una URL o un `//` dentro de un literal no se lean como comentario.
- No mira ficheros de datos ni documentación: Markdown, JSON, `.txt`, `.csv`, `.log`, `.svg`, lockfiles, snapshots y cualquier `.env*`. Tampoco entra en `docs/`, `doc/`, `node_modules/` ni `vendor/`.
- Ignora los scratchpads (`/tmp/`, `/private/tmp/`) y todo lo que viva bajo `.claude/`: la configuración del propio agente queda fuera de la regla.
- Fail-open: ante cualquier error inesperado, deja pasar. Es un guardarraíl de flujo, no una frontera de seguridad.

Cuando bloquea, el mensaje de deny instruye al agente: reemite el edit sin comentarios, o extrae una función con buen nombre. Si un comentario es de verdad imprescindible (un quirk de un sistema externo), el agente debe parar y pedir al usuario que apruebe esa línea.

## Instalación

```
/plugin marketplace add 540/agentic-toolbox
/plugin install no-comments@540
```

Requiere `python3` en el `PATH` (3.x, cualquier versión reciente). Sin dependencias: solo stdlib.

## Excepciones por proyecto

El hook se instala una vez y se usa en repos con convenciones distintas. Un fichero `.no-comments.json` opcional en la raíz del proyecto ajusta la regla sin tocar el plugin. Si no existe, se aplican los defaults.

```json
{
  "ignore": ["db/migrate/**", "spec/fixtures/**", "legacy/**"],
  "allow": ["@openapi", "CHECKSTYLE:", "JUSTIFICACIÓN:"]
}
```

- `ignore`: globs de rutas donde el hook no actúa. Se comparan contra la ruta relativa al directorio de trabajo y también contra la absoluta, así que sirven los dos estilos. Ojo: un `*` cruza separadores de directorio, de modo que `spec/*` ya cubre lo anidado.
- `allow`: expresiones regulares de comentarios permitidos, que se suman a los pragmas exentos de serie. Sirven para las anotaciones que un proyecto sí quiere en el código (un generador de documentación, un supresor de linter propio).

Va versionado con el repo: el acuerdo es del equipo, no de cada máquina. Si el fichero no es válido, el hook aplica los defaults en lugar de desactivarse, para que un error de sintaxis no deje la regla apagada sin avisar.

## Tests

```
python3 plugins/no-comments/hooks/test-no-comments.py
```

Los casos invocan el hook como lo hace Claude Code: payload JSON por stdin, decisión por stdout. Cubren una familia de sintaxis por bloque, los pragmas exentos y, sobre todo, los falsos positivos que bloquearían al agente sin motivo (una almohadilla dentro de una URL, `${#arr[@]}` en shell, `//` dentro de un string, `--` dentro de un literal SQL). Sin dependencias: stdlib y asserts.

## Adaptarlo

- ¿Otro lenguaje? Añade la extensión al conjunto de su familia (`HASH`, `SLASH`, `DASH`, `ANGLE`) en `hooks/no-comments.py`.
- ¿Otro pragma exento? Se añade a la expresión `EXEMPT`.
- ¿Otra política? El mensaje de deny vive en la función `deny`; ajústalo a la convención de tu equipo.
