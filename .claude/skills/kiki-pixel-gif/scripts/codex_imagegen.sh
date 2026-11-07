#!/usr/bin/env bash
# Generate one sprite sheet with Codex's built-in imagegen tool from Claude Code / any shell.
#
# usage: scripts/codex_imagegen.sh <reference_image> <prompt_file> <out_dir>
#   -> writes <out_dir>/sheet.png
#
# Needs the Codex CLI (`npm i -g @openai/codex`, signed in). Uses your ChatGPT plan's
# image allowance, no API key.
set -euo pipefail
REF="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"   # imagegen needs ABSOLUTE paths
PROMPT_FILE="$2"
OUT="$(mkdir -p "$3" && cd "$3" && pwd)"

TASK="The user has already approved this image generation. Do not ask questions; generate now.
Use your built-in image_gen tool (imagegen) ONLY to draw ONE still image.
Do NOT call any video model, animation plugin, external API, MCP server or other generation skill,
and do NOT draw the image with code.
Call imagegen with:
  referenced_image_paths: [\"$REF\"]
  transparent_background: true
  prompt: the text between the PROMPT markers below.
Then copy the generated PNG from ~/.codex/generated_images/... to $OUT/sheet.png and print the path.

PROMPT>>>
$(cat "$PROMPT_FILE")
<<<PROMPT"

# stdin closed on purpose: codex exec otherwise waits for input forever
codex exec --skip-git-repo-check -s workspace-write \
  --add-dir "$HOME/.codex/generated_images" -C "$OUT" "$TASK" < /dev/null > "$OUT/codex.log" 2>&1

if [ -s "$OUT/sheet.png" ]; then
  echo "$OUT/sheet.png"
else
  echo "imagegen did not produce sheet.png — see $OUT/codex.log" >&2
  exit 1
fi
