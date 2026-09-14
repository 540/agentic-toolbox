#!/usr/bin/env python3
import fnmatch
import json
import os
import re
import sys
from collections import Counter

CONFIG_NAME = ".no-comments.json"
SKIP_PATHS = ("/tmp/", "/private/tmp/")

SKIP_EXT = {".md", ".mdx", ".markdown", ".json", ".jsonc", ".txt", ".lock", ".csv", ".tsv", ".log", ".svg", ".snap"}
SKIP_DIRS = {"docs", "doc", "node_modules", "vendor", ".git"}

HASH = {".py", ".rb", ".rake", ".sh", ".bash", ".zsh", ".fish", ".yml", ".yaml", ".toml", ".pl", ".pm", ".r", ".tf", ".tfvars", ".hcl", ".ex", ".exs", ".nix", ".ps1", ".conf", ".cfg", ".ini", ".properties", ".gemspec", ".envrc", ".cmake"}
HASH_NAMES = {"Makefile", "Dockerfile", "Gemfile", "Rakefile", "Vagrantfile", "Justfile", "Procfile", ".gitignore", ".dockerignore", ".bashrc", ".zshrc", ".bash_profile", ".zprofile"}
SLASH = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".java", ".kt", ".kts", ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".swift", ".php", ".scala", ".dart", ".groovy", ".m", ".mm", ".proto", ".gradle", ".scss", ".less", ".sass", ".zig", ".v"}
BLOCK_ONLY = {".css"}
DASH = {".sql", ".lua", ".hs", ".elm", ".adb"}
ANGLE = {".html", ".htm", ".vue", ".svelte", ".xml", ".xhtml", ".astro"}

EXEMPT = re.compile(
    r"^!|eslint|@ts-|noqa|type:\s*ignore|shellcheck|prettier-ignore|pragma|ponytail:|rubocop|fmt:\s*(on|off|skip)|"
    r"frozen_string_literal|coding[:=]|nolint|nosec|istanbul ignore|biome-ignore|@formatter|@flow|@jsx|@vitest|@jest|"
    r"language-server|syntax=|copyright|licen[sc]e|spdx|sourceMappingURL|\bnoinspection\b|@generated|@ts-check|\btype-check\b|"
    r"^\s*(region|endregion)\b|^\s*-\*-|serial(izable)?\s*:|^\s*(if|else|elif|endif|include|define|pragma)\b",
    re.IGNORECASE,
)

MARKER = re.compile(r"\bno-comments:\s*(\S.*)", re.IGNORECASE)
ASKABLE_MODES = {"default", "plan", "acceptEdits"}

STRINGS = re.compile(r"""("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)""")


def syntax_for(path):
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    if name.startswith(".env") or ext in SKIP_EXT:
        return None
    if any(part in SKIP_DIRS for part in path.split(os.sep)[:-1]):
        return None
    if name in HASH_NAMES or ext in HASH or name.startswith("Dockerfile"):
        return ("#", None)
    if ext in SLASH:
        return ("//", ("/*", "*/"))
    if ext in BLOCK_ONLY:
        return (None, ("/*", "*/"))
    if ext in DASH:
        return ("--", None)
    if ext in ANGLE:
        return (None, ("<!--", "-->"))
    return None


def as_list(value):
    return value if isinstance(value, list) else []


def load_config():
    try:
        with open(CONFIG_NAME, encoding="utf-8") as fh:
            data = json.load(fh)
        ignore = [p for p in as_list(data.get("ignore")) if isinstance(p, str)]
        allow = [p for p in as_list(data.get("allow")) if isinstance(p, str)]
        return ignore, re.compile("|".join(allow), re.IGNORECASE) if allow else None
    except Exception:
        return [], None


def out_of_scope(path, ignore):
    if path.startswith(SKIP_PATHS) or ".claude/" in path:
        return True
    return any(
        fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"*/{pattern}")
        for pattern in ignore
    )


def strip_strings(line):
    return STRINGS.sub('""', line)


def hash_positions(code):
    for m in re.finditer(r"#", code):
        i = m.start()
        prev = code[i - 1] if i > 0 else ""
        if prev and prev in "${\\#":
            continue
        return i
    return -1


def comments_in(text, syntax):
    line_marker, block = syntax
    found = []
    in_block = False
    for raw in text.splitlines():
        line = raw.strip()
        if in_block:
            end = line.find(block[1])
            found.append(line[:end].strip() if end >= 0 else line)
            if end >= 0:
                in_block = False
            continue
        code = strip_strings(line)
        cut = -1
        if line_marker == "#":
            cut = hash_positions(code)
        elif line_marker:
            cut = code.find(line_marker)
            if line_marker == "//" and cut > 0 and code[cut - 1] == ":":
                cut = -1
        bstart = code.find(block[0]) if block else -1
        if bstart >= 0 and (cut < 0 or bstart < cut):
            rest = code[bstart + len(block[0]):]
            end = rest.find(block[1])
            if end >= 0:
                found.append(rest[:end].strip())
            else:
                found.append(rest.strip())
                in_block = True
            continue
        if cut >= 0:
            found.append(code[cut + len(line_marker):].strip())
    return found


def added_comments(old, new, syntax, allow):
    before = Counter(comments_in(old, syntax))
    after = Counter(comments_in(new, syntax))
    return [
        c
        for c in (after - before).elements()
        if not EXEMPT.search(c) and not (allow and allow.search(c))
    ]


def edits_from(payload):
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input", {})
    path = inp.get("file_path", "")
    if tool == "Write":
        old = ""
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as fh:
                old = fh.read()
        return path, [(old, inp.get("content", ""))]
    if tool == "Edit":
        return path, [(inp.get("old_string", ""), inp.get("new_string", ""))]
    if tool == "MultiEdit":
        return path, [(e.get("old_string", ""), e.get("new_string", "")) for e in inp.get("edits", [])]
    return path, []


NOISE = "Este código no lleva comentarios explicativos: el objetivo es cero. El código dice lo que hace, y un comentario que lo repite caduca en cuanto uno de los dos cambia. Reemite el edit sin ellos. Cuando un bloque parece pedir un comentario que lo narre, es un problema de naming: extráelo a una función o método con buen nombre y deja que el nombre cargue el significado. Las referencias a tickets van en el mensaje de commit y en la PR. Si la excepción se repite en este proyecto, su sitio es el .no-comments.json de la raíz, no el código. Y si crees que un comentario concreto es imprescindible porque nombra una restricción que el código de verdad no puede expresar (un quirk de un sistema externo, una optimización que obliga a escribirlo de forma poco idiomática), reemítelo con el marcador «no-comments: <razón>» y será el usuario quien decida si entra. La razón tiene que nombrar la restricción, no repetir lo que hace el código."

UNASKABLE = "Los comentarios llevan marcador de justificación, pero esta sesión corre en modo %s, donde el marcador no llega al usuario. Un marcador no se aprueba solo. Reemite el edit sin ellos, o pide al usuario que escriba él esa línea."

APPROVAL = "Apruébalo si la razón nombra una restricción que el código no puede expresar por sí solo. Recházalo si solo describe lo que el código ya dice."


def respond(decision, reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def listing(items):
    shown = "\n".join(f"  {item}" for item in items[:3])
    more = f"\n  (+{len(items) - 3} más)" if len(items) > 3 else ""
    return shown + more


def decide(path, comments, mode):
    name = os.path.basename(path)
    plural = "s" if len(comments) > 1 else ""
    justifications = [MARKER.search(c) for c in comments]
    if all(justifications):
        reasons = [m.group(1).strip() for m in justifications]
        attribution = "cada uno con su justificación" if plural else "con esta justificación"
        header = (
            f"el agente quiere añadir {len(comments)} comentario{plural} a {name}, "
            f"{attribution}:\n{listing(reasons)}\n"
        )
        if mode in ASKABLE_MODES:
            return respond("ask", header[0].upper() + header[1:] + APPROVAL)
        return respond("deny", f"COMMENT_UNAPPROVED: {header}" + UNASKABLE % mode)
    return respond(
        "deny",
        f"COMMENT_NOISE: este cambio añade {len(comments)} comentario{plural} "
        f"a {name}:\n{listing(comments)}\n" + NOISE,
    )


def main():
    payload = json.load(sys.stdin)
    path, edits = edits_from(payload)
    if not path or not edits:
        return
    ignore, allow = load_config()
    if out_of_scope(path, ignore):
        return
    syntax = syntax_for(path)
    if not syntax:
        return
    comments = []
    for old, new in edits:
        comments.extend(added_comments(old, new, syntax, allow))
    if comments:
        decide(path, comments, payload.get("permission_mode", "default"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
