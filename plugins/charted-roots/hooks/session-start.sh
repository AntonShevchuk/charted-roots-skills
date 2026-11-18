#!/bin/sh
# Load the Charted Roots vault model into the session, only inside a vault.
# Silent (no output) anywhere else.

vault="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$vault/.obsidian/plugins/charted-roots/data.json" ] || exit 0

model="${CLAUDE_PLUGIN_ROOT}/skills/vault-verify/references/charted-roots-model.md"
[ -f "$model" ] || exit 0

# A vault that imports its own copy of the model already has it in context.
[ -f "$vault/.claude/conventions/charted-roots-model.md" ] && exit 0

# Hook output is capped at 10,000 characters; past that, point to the file.
size=$(wc -c < "$model" | tr -d ' ')
if [ "$size" -le 9800 ]; then
  cat "$model"
else
  printf 'This is a Charted Roots vault. Read %s before working on its notes; the vault'"'"'s CLAUDE.md and .claude/conventions/ override it.\n' "$model"
fi
