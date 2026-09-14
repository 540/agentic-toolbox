#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("no-comments.py")

failures = []


def decision(tool, cwd=None, mode="default", **tool_input):
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "permission_mode": mode})
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        failures.append(f"el hook salió con {result.returncode}: {result.stderr.strip()}")
        return "error"
    if not result.stdout.strip():
        return "allow"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def run(tool, cwd=None, **tool_input):
    return decision(tool, cwd=cwd, **tool_input) == "deny"


def as_text(value):
    if value is True:
        return "deny"
    if value is False:
        return "allow"
    return value


def check(label, expected, actual):
    if actual != expected:
        failures.append(f"{label}: esperaba {as_text(expected)}, obtuvo {as_text(actual)}")


def denies(label, path, old, new):
    check(label, True, run("Edit", file_path=path, old_string=old, new_string=new))


def allows(label, path, old, new):
    check(label, False, run("Edit", file_path=path, old_string=old, new_string=new))


denies("python inline", "/x/a.py", "x = 1", "x = 1  # asigna x")
denies("python línea entera", "/x/a.py", "x = 1", "# asigna x\nx = 1")
denies("shell", "/x/deploy.sh", "make", "# compila primero\nmake")
denies("yaml", "/x/ci.yml", "run: make", "# compila primero\nrun: make")
denies("toml", "/x/p.toml", "a = 1", "# ajuste\na = 1")
denies("terraform", "/x/main.tf", "count = 1", "# una sola\ncount = 1")
denies("Dockerfile por nombre", "/x/Dockerfile", "FROM a", "# imagen base\nFROM a")
denies("Makefile por nombre", "/x/Makefile", "all:", "# objetivo\nall:")
denies("typescript línea", "/x/a.ts", "const a = 1", "// calcula a\nconst a = 1")
denies("typescript bloque", "/x/a.ts", "const a = 1", "/* calcula a */\nconst a = 1")
denies("bloque multilínea", "/x/a.ts", "const a = 1", "/* calcula\n   la a */\nconst a = 1")
denies("go", "/x/a.go", "x := 1", "// calcula x\nx := 1")
denies("rust", "/x/a.rs", "let x = 1;", "// calcula x\nlet x = 1;")
denies("java", "/x/A.java", "int x = 1;", "// calcula x\nint x = 1;")
denies("css solo bloque", "/x/a.css", ".a { color: red }", "/* rojo */\n.a { color: red }")
denies("sql", "/x/q.sql", "select 1", "-- coge uno\nselect 1")
denies("lua", "/x/a.lua", "x = 1", "-- asigna\nx = 1")
denies("html", "/x/i.html", "<div/>", "<!-- contenedor -->\n<div/>")
denies("vue", "/x/A.vue", "<div/>", "<!-- contenedor -->\n<div/>")
denies("TODO cuenta como comentario", "/x/a.py", "x = 1", "x = 1  # TODO: revisar")
denies("comentario tras código válido", "/x/a.ts", "const a = 1", "const a = 1 // suma")

allows("comentario preexistente que se mueve", "/x/a.py", "# nota vieja\nx = 1", "y = 2\n# nota vieja\nx = 1")
allows("edit sin comentarios", "/x/a.py", "x = 1", "x = 2")
allows("borrar un comentario", "/x/a.py", "# nota\nx = 1", "x = 1")

allows("noqa", "/x/a.py", "", "import os  # noqa: F401")
allows("type ignore", "/x/a.py", "", "x = f()  # type: ignore")
allows("pragma no cover", "/x/a.py", "", "def f():  # pragma: no cover")
allows("fmt off", "/x/a.py", "", "# fmt: off")
allows("shebang", "/x/a.sh", "", "#!/usr/bin/env bash\nset -e")
allows("frozen_string_literal", "/x/a.rb", "", "# frozen_string_literal: true")
allows("rubocop", "/x/a.rb", "", "# rubocop:disable Metrics/AbcSize")
allows("eslint", "/x/a.ts", "", "// eslint-disable-next-line no-console\nconsole.log(1)")
allows("ts-expect-error", "/x/a.ts", "", "// @ts-expect-error\nf()")
allows("shellcheck", "/x/a.sh", "", "# shellcheck disable=SC2086\necho $x")
allows("nosec", "/x/a.py", "", "subprocess.run(c)  # nosec")
allows("biome-ignore", "/x/a.ts", "", "// biome-ignore lint: intencionado")
allows("licencia", "/x/a.ts", "", "// Copyright 2026 540deg. Licensed under MIT.")
allows("ponytail", "/x/a.py", "", "# ponytail: lock global, por cuenta si hace falta")
allows("modeline emacs", "/x/a.py", "", "# -*- coding: utf-8 -*-")
allows("preprocesador C", "/x/a.c", "", "#include <stdio.h>\n#define N 4")

allows("almohadilla en URL", "/x/a.py", "", "url = 'https://example.com/#frag'")
allows("almohadilla en clave", "/x/a.py", "", 'd = {"#": 1}')
allows("expansión de shell", "/x/a.sh", "", 'echo "${#arr[@]}" $#')
allows("barras en string", "/x/a.ts", "", 'const u = "https://example.com";')
allows("barras en URL sin comillas", "/x/a.ts", "", "import x from https://a.b")
allows("guiones dentro de string SQL", "/x/q.sql", "", "select * from t where n = 'a--b'")

allows("markdown", "/x/README.md", "", "# Título\n<!-- nota -->")
allows("json", "/x/data.json", "", '{"a": 1}')
allows("lockfile", "/x/yarn.lock", "", "# generado")
allows("dotenv", "/x/.env.local", "", "# secreto\nA=1")
allows("directorio docs", "/x/docs/guide.py", "", "# explicado")
allows("node_modules", "/x/node_modules/p/i.js", "", "// upstream")
allows("extensión desconocida", "/x/a.xyz", "", "# lo que sea")
allows("sin extensión", "/x/notas", "", "# lo que sea")

check("Write limpio", False, run("Write", file_path="/x/n.py", content="x = 1\n"))
check("Write con comentario", True, run("Write", file_path="/x/n.py", content="# nuevo\nx = 1\n"))
check(
    "MultiEdit con comentario en el segundo edit",
    True,
    run(
        "MultiEdit",
        file_path="/x/a.py",
        edits=[
            {"old_string": "a = 1", "new_string": "a = 2"},
            {"old_string": "b = 1", "new_string": "b = 2  # nota"},
        ],
    ),
)
check(
    "MultiEdit limpio",
    False,
    run(
        "MultiEdit",
        file_path="/x/a.py",
        edits=[{"old_string": "a = 1", "new_string": "a = 2"}],
    ),
)

with tempfile.TemporaryDirectory() as tmp:
    existing = Path(tmp) / "a.py"
    existing.write_text("# nota vieja\nx = 1\n")
    check(
        "Write que conserva un comentario del fichero",
        False,
        run("Write", file_path=str(existing), content="# nota vieja\nx = 2\n"),
    )
    check(
        "Write que añade un comentario al fichero",
        True,
        run("Write", file_path=str(existing), content="# nota vieja\n# nota nueva\nx = 1\n"),
    )

allows("scratchpad en /tmp", "/tmp/a.py", "", "# nota")
allows("scratchpad en /private/tmp", "/private/tmp/x/a.py", "", "# nota")
allows("configuración del agente", "/x/.claude/hooks/h.py", "", "# nota")


def with_config(label, config, path, new, expected):
    with tempfile.TemporaryDirectory() as tmp:
        if config is not None:
            (Path(tmp) / ".no-comments.json").write_text(config)
        actual = run("Edit", cwd=tmp, file_path=path, old_string="x = 1", new_string=new)
    check(label, expected, actual)


with_config("sin config, comportamiento por defecto", None, "db/migrate/1_x.rb", "x = 1  # nota", True)
with_config("ignore exime el directorio", '{"ignore": ["db/migrate/**"]}', "db/migrate/1_x.rb", "x = 1  # nota", False)
with_config("ignore no exime fuera de su glob", '{"ignore": ["db/migrate/**"]}', "app/models/x.rb", "x = 1  # nota", True)
with_config("ignore con ruta absoluta", '{"ignore": ["/srv/legacy/**"]}', "/srv/legacy/x.py", "x = 1  # nota", False)
with_config("ignore relativo casa con la ruta absoluta", '{"ignore": ["db/migrate/**"]}', "/srv/app/db/migrate/1_x.rb", "x = 1  # nota", False)
with_config("allow exime un pragma propio", '{"allow": ["@openapi"]}', "app/api.rb", "x = 1  # @openapi ref", False)
with_config("allow no exime el resto", '{"allow": ["@openapi"]}', "app/api.rb", "x = 1  # nota suelta", True)
with_config("config corrupta cae a los defaults", "{no es json", "app/x.rb", "x = 1  # nota", True)
with_config("config con tipos raros cae a los defaults", '{"ignore": "app/**"}', "app/x.rb", "x = 1  # nota", True)
with_config("config vacía", "{}", "app/x.rb", "x = 1  # nota", True)

def reason(path, new):
    payload = json.dumps(
        {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": "x = 1", "new_string": new}}
    )
    out = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)
    return json.loads(out.stdout)["hookSpecificOutput"]["permissionDecisionReason"]


def marked(label, expected, new, mode="default", path="/x/a.py"):
    check(
        label,
        expected,
        decision("Edit", mode=mode, file_path=path, old_string="x = 1", new_string=new),
    )


MARK = "# no-comments: bucle desenrollado a mano, la versión idiomática cuesta 40ms por request"

marked("comentario justificado pregunta al usuario", "ask", f"{MARK}\nx = 1")
marked("comentario sin marcador deniega", "deny", "# desenrolla el bucle\nx = 1")
marked("marcador sin razón deniega", "deny", "# no-comments:\nx = 1")
marked("marcador con razón en blanco deniega", "deny", "# no-comments:   \nx = 1")
marked("un justificado arrastra al bloque", "ask", f"{MARK}\n# y de paso esto\nx = 1")

BLOQUE = (
    "// no-comments: nombra un comportamiento de @sentry/nextjs que no se ve desde este\n"
    "// fichero: si no le das nombre al release, el SDK inyecta el build id de Next.\n"
    "// @sentry/nextjs defaults the release to the Next.js build id, a random value.\n"
)
marked("bloque multilínea con el marcador en la primera", "ask", BLOQUE + "x = 1", path="/x/next.config.js")
marked("bloque multilínea sin marcador", "deny", BLOQUE.replace("no-comments: ", "") + "x = 1", path="/x/next.config.js")

colado = reason("/x/a.py", f"{MARK}\n# y de paso esto\nx = 1")
check(
    "el prompt enseña también el comentario sin marcador",
    True,
    "y de paso esto" in colado,
)
marked("dos justificados preguntan", "ask", f"{MARK}\n# no-comments: el orden importa, la API los exige así\nx = 1")
for mode in ["default", "plan", "acceptEdits", "auto", "dontAsk", "bypassPermissions"]:
    marked(f"el modo {mode} no cambia la decisión", "ask", f"{MARK}\nx = 1", mode=mode)
marked("marcador en // también pregunta", "ask", "// no-comments: el orden lo exige la API", path="/x/a.ts")
marked("marcador // en fichero python no es comentario", "allow", "// no-comments: el orden lo exige la API")

justified = reason("/x/a.py", f"{MARK}\nx = 1")
for fragment in ["40ms por request", "Apruébalo si"]:
    check(f"el prompt de aprobación menciona «{fragment}»", True, fragment in justified)
check(
    "el prompt de aprobación no repite el sermón del deny",
    False,
    "el objetivo es cero" in justified,
)


message = reason("/x/servicio.py", "# uno\n# dos\n# tres\n# cuatro\nx = 1")
for fragment in ["servicio.py", "4 comentarios", "(+1 más)", "problema de naming", "commit", "no-comments: <razón>", ".no-comments.json"]:
    check(f"el mensaje de deny menciona «{fragment}»", True, fragment in message)

check("herramienta ajena", False, run("Bash", command="echo # hola"))
check("payload incompleto", False, run("Edit", file_path="/x/a.py"))
check("payload sin file_path", False, run("Edit", old_string="a", new_string="b  # n"))

if failures:
    print(f"{len(failures)} fallo(s):")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("ok")
