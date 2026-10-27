# 540 Agentic Toolbox

Skills, hooks y recursos que surgen de nuestro trabajo real con agentes en [540](https://540deg.com) y compartimos.

## Instalación

En Claude Code, como plugin (puede incluir hooks, agentes, etc.):

```
/plugin marketplace add 540/agentic-toolbox
/plugin install gauntlet-audit@540
```

En cualquier otro agente compatible con [skills.sh](https://skills.sh) (solo skills):

```
npx skills add 540/agentic-toolbox
```

## Skills

| Skill | Qué hace |
|-------|----------|
| [gauntlet-audit](plugins/gauntlet-audit/) | Audita la red de verificación de un repo según el marco del gauntlet de [Uncle Bob](https://github.com/unclebob): 9 campos con madurez 0-4, score global y roadmap. Responde "¿puedo confiar en código escrito por agentes sin leerlo?". |
| [explain-pr](plugins/explain-pr/) | Explica una PR a quien la va a revisar sin leer el código: un comentario listo para publicar en la PR con el riesgo, qué cambia para cada actor, diagramas Mermaid, efectos secundarios y si se pueden deshacer, contraste con el ticket, decisiones que nadie aprobó, si los tests lo prueban y quién se entera si falla. Nunca publica sin tu sí. |

## Hooks

| Hook | Qué hace |
|------|----------|
| [no-comments](plugins/no-comments/) | Hook que bloquea los comentarios que el agente añade al código, en cualquier lenguaje. Exime los pragmas de máquina. |
| [no-comments-ruby](plugins/no-comments-ruby/) | Hook que bloquea los comentarios que el agente añade a ficheros Ruby: el código se explica solo. Exime los pragmas de máquina. |

## Licencia

[MIT](LICENSE)
