# no-comments-ruby

Parte de [540 Agentic Toolbox](https://github.com/540/agentic-toolbox).

Hook `PreToolUse` para Claude Code. Bloquea `Write`, `Edit` y `MultiEdit` cuando el agente añade comentarios a un fichero Ruby (`.rb`/`.rake`). La premisa: el código dice lo que hace, y un comentario que lo repite caduca en cuanto uno de los dos cambia. Si un bloque parece pedir comentario, el problema es de naming: se extrae un método con buen nombre.

## Cómo funciona

- Solo cuentan los comentarios **añadidos**. Un comentario que ya estaba en el `old_string` viaja con su código: los refactors y los movimientos no disparan el hook.
- Exime los pragmas que lee una máquina: shebang, `frozen_string_literal`, encoding, sigilo de Sorbet, directivas de RuboCop, `:nodoc:`/`:nocov:`.
- El escáner sigue strings, interpolación `#{}`, literales `%w[]` y heredocs: un `#` dentro de datos no se lee como comentario. Los bloques `=begin`/`=end` cuentan como un comentario.
- Solo actúa si hay un `Gemfile` en el directorio de trabajo. Así no salta al editar fixtures o ejemplos en repos que no son Ruby.
- Ignora los scratchpads (`/tmp/`) y todo lo que viva bajo `.claude/`: la configuración del propio agente queda fuera de la regla.
- Fail-open: ante cualquier error inesperado, deja pasar. Es un guardarraíl de flujo, no una frontera de seguridad.

Cuando bloquea, el mensaje de deny instruye al agente: reemite el edit sin comentarios, o extrae un método con buen nombre. Si un comentario es de verdad imprescindible (un quirk de un sistema externo), el agente debe parar y pedir al usuario que apruebe esa línea.

## Instalación

```
/plugin marketplace add 540/agentic-toolbox
/plugin install no-comments-ruby@540
```

Requiere `/usr/bin/ruby` (el Ruby del sistema, presente en macOS y en la mayoría de Linux). Sin gemas: solo stdlib.

## Adaptarlo

- ¿Otro lenguaje? El escáner de `hooks/no-comments-ruby.rb` es específico de Ruby. La estructura (deny sobre lo añadido, pragmas exentos, fail-open) es reutilizable.
- ¿Otra política? El mensaje de deny vive al final del script; ajústalo a la convención de tu equipo.
