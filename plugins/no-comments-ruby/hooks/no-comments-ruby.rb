#!/usr/bin/ruby
# frozen_string_literal: true

# PreToolUse hook on Write|Edit|MultiEdit. Denies a write when the text being
# ADDED to a .rb/.rake file contains a comment that is not a machine-read
# pragma (shebang, frozen_string_literal, encoding, sorbet sigil, rubocop
# directive). The premise: code states what it does, and a comment restating
# it rots the moment either one changes.
#
# Only ADDED comments count. A comment already present in old_string travels
# with the code it annotates, so refactors and moves never trip the hook.
#
# The line scanner tracks single/double/backtick strings, #{} interpolation,
# % literals and heredoc bodies so a '#' inside data is not read as a comment.
# Ambiguity resolves toward silence: a missed comment is a review finding, a
# false deny is a blocked agent.
#
# Pinned to /usr/bin/ruby (system ruby, no version-manager shim) and
# stdlib-only. Fail-open everywhere: anything unexpected -> exit 0. Workflow
# guardrail, not a security boundary.

require "json"

RUBY_PATH = /\.(?:rb|rake)\z/

PRAGMA = /\A\#\s*(?:
            !                              |  # shebang
            frozen_string_literal\s*:      |
            (?:en)?coding\s*[:=]           |
            -\*-                           |  # emacs modeline
            typed\s*:                      |  # sorbet
            rubocop\s*:                    |
            :\s*no(?:doc|cov)\s*:
          )/x

HEREDOC = /<<([-~])?(["'`]?)([A-Z_][A-Z0-9_]*)\2/

PERCENT_CLOSE = { "[" => "]", "(" => ")", "{" => "}", "<" => ">" }.freeze

# Comment text on a line, or nil. Walks the line so a '#' inside a string,
# an interpolation, or a % literal is not mistaken for a comment start.
def comment_at(line)
  i = 0
  prev = nil
  while i < line.length
    c = line[i]
    case c
    when "'", '"', "`"
      i = skip_string(line, i, c)
      prev = nil
      next
    when "%"
      skipped = skip_percent_literal(line, i, prev)
      if skipped
        i = skipped
        prev = nil
        next
      end
    when "#"
      return line[i..] if prev.nil? || prev.match?(/\s/)
    end
    prev = c
    i += 1
  end
  nil
end

# End of a %w[]/%q()/%r{} literal starting at start, or nil when this '%' is
# modulo. Only a '%' that opens an expression can start a literal, which keeps
# 'total % count' out of it.
def skip_percent_literal(line, start, prev)
  return nil unless prev.nil? || prev.match?(/[\s(\[{,=]/)

  rest = line[start..]
  m = rest.match(/\A%[qQwWiIrs]?([^\sA-Za-z0-9])/)
  return nil unless m

  open = m[1]
  close = PERCENT_CLOSE[open] || open
  depth = 1
  i = start + m[0].length
  while i < line.length
    case line[i]
    when "\\" then i += 1
    when open then depth += 1 if close != open
    when close
      depth -= 1
      return i + 1 if depth.zero?
    end
    i += 1
  end
  i
end

def skip_string(line, start, quote)
  i = start + 1
  while i < line.length
    case line[i]
    when "\\"
      i += 2
      next
    when quote
      return i + 1
    when "#"
      if quote != "'" && line[i + 1] == "{"
        i = skip_interpolation(line, i + 2)
        next
      end
    end
    i += 1
  end
  i
end

def skip_interpolation(line, start)
  depth = 1
  i = start
  while i < line.length && depth.positive?
    case line[i]
    when "{" then depth += 1
    when "}" then depth -= 1
    end
    i += 1
  end
  i
end

# Comment lines in a chunk of source, skipping heredoc bodies and =begin
# blocks' interiors (the =begin/=end pair itself is reported as one comment).
def comments(text)
  found = []
  pending = []
  block = false

  text.to_s.each_line do |raw|
    line = raw.chomp

    if pending.any?
      pending.shift if line.strip == pending.first
      next
    end

    if block
      block = false if line.start_with?("=end")
      next
    end

    if line.start_with?("=begin")
      block = true
      found << line
      next
    end

    comment = comment_at(line)
    found << comment.strip if comment && !comment.match?(PRAGMA)

    line.scan(HEREDOC) { |_, _, id| pending << id }
  end

  found
end

def deny(reason)
  puts JSON.generate(
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: reason
    }
  )
  exit 0
end

begin
  # Only guard real Ruby projects: plugin hooks run user-globally, and this
  # rule must not fire while editing fixtures or examples in other repos.
  exit 0 unless File.exist?("Gemfile")

  input = JSON.parse($stdin.read)

  file = input.dig("tool_input", "file_path").to_s
  exit 0 unless file.match?(RUBY_PATH)
  exit 0 if file.start_with?("/tmp/", "/private/tmp/") || file.include?(".claude/")

  tool_input = input["tool_input"]
  edits = tool_input["edits"] || [tool_input]

  added = edits.flat_map do |edit|
    new_text = (edit["content"] || edit["new_string"]).to_s
    kept = comments(edit["old_string"])
    comments(new_text) - kept
  end
  exit 0 if added.empty?

  shown = added.first(3).map { |c| "  #{c}" }.join("\n")
  more = added.length > 3 ? "\n  (+#{added.length - 3} more)" : ""

  deny "COMMENT_NOISE: this change adds #{added.length} " \
       "comment#{"s" if added.length > 1} to #{File.basename(file)}:\n" \
       "#{shown}#{more}\n" \
       "This codebase carries no explanatory comments: the target is zero. " \
       "Code states what it does, and a comment restating it rots as soon as " \
       "either changes. Re-issue the edit without them. When a block reads " \
       "as though it needs a narration comment, that is a naming problem: " \
       "extract it into a well-named method and let the name carry the " \
       "meaning. Ticket references belong in the commit message and the PR. " \
       "If you believe a specific comment is genuinely required (an external " \
       "quirk or a constraint the code truly cannot express), stop and ask " \
       "the user to approve that one line rather than writing it."
rescue StandardError
  exit 0
end
