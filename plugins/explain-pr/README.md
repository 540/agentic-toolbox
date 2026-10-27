# explain-pr

Parte de [540 Agentic Toolbox](https://github.com/540/agentic-toolbox).

Skill que explica una pull request de GitHub a quien la va a revisar sin leer el código. Devuelve un comentario Markdown listo para publicar en la PR, con el que el revisor puede aprobarla o rechazarla. La regla de fondo: cada afirmación sale de una fuente que el revisor puede comprobar, o va marcada como inferencia.

## Qué contiene el comentario

- **Riesgo** (bajo, medio o alto) con el riesgo principal, y **tamaño** separando ficheros de producción y de tests.
- **1. Qué cambia para cada actor**: un escenario por fila, con los valores reales de los tests o del ticket.
- **2. Cómo funciona**: un mapa Mermaid de los componentes que toca (con las capas del repo si las tiene), la secuencia en runtime y el diff del flujo. Sin nombres de ficheros, clases ni métodos en los diagramas.
- **3. Efectos secundarios**: qué escribe, envía, borra o despliega (CI al mergear incluido), si se puede deshacer y en qué orden revertir.
- **4. Contraste con las fuentes**: cada criterio de aceptación y cada decisión de diseño, con la evidencia que lo prueba.
- **5. Decisiones que nadie aprobó**: elecciones del código que no cubren ni el ticket ni el diseño, formuladas para responder sí o no.
- **6. ¿Lo prueban los tests?**: escenario contra test, leyendo el cuerpo del test y no solo su nombre.
- **7. Si falla en producción, ¿quién se entera?**: cada fallo posible y la señal que lo avisa, o que no lo avisa.
- **Fuentes** en un bloque plegado. Las rutas de ficheros solo aparecen ahí.

Las secciones mantienen siempre su número, así que quien ha leído un comentario se orienta en el siguiente. La forma exacta está en [`references/comment-template.md`](skills/explain-pr/references/comment-template.md).

## Cómo se usa

```
Explícame https://github.com/<owner>/<repo>/pull/<n>, no voy a leer el código
```

La skill escribe el comentario en `pr-<n>-explained.md` y te da la línea de riesgo y las preguntas de la sección 5. Solo lo publica en la PR si le dices que sí.

## Instalación

En Claude Code, como plugin:

```
/plugin marketplace add 540/agentic-toolbox
/plugin install explain-pr@540
```

En cualquier otro agente compatible con [skills.sh](https://skills.sh):

```
npx skills add 540/agentic-toolbox
```

Requiere `gh` autenticado con acceso al repo de la PR. Para leer el ticket usa el CLI o el MCP de tu tracker (`gh issue view` para GitHub Issues, `acli` o el MCP de Atlassian para Jira, el de Linear…). Con un clon local del repo lee el código alrededor del diff sin tocar tu árbol de trabajo. Sin clon, lo lee con la API de GitHub.
