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

## Hooks

| Hook | Qué hace |
|------|----------|
| [no-comments-ruby](plugins/no-comments-ruby/) | Hook que bloquea los comentarios que el agente añade a ficheros Ruby: el código se explica solo. Exime los pragmas de máquina. |

## Licencia

[MIT](LICENSE)
