---
name: kiki-pixel-gif
description: Turn any character, pet or mascot image into looping pixel-art GIFs with GPT Image 2.6 — a single move, a sticker pack (WeChat / Discord / Telegram / Slack), or a 3-move game-style move list. Use when the user asks for a pixel sprite, sprite sheet, pixel GIF, 8-bit/16-bit animation, idle/walk/run/attack/jump/dance animation of a character, "make my pet/character pixel art and animate it", "pixel sticker pack", "表情包", or "move list / 招式表".
---

# Kiki Pixel GIF

Part of **AI Animation Lab**. One reference image (+ an optional move request) → the
model picks or follows the move → a looping pixel-art GIF ready to post.

## When to use

Trigger phrases: "pixel sprite", "sprite sheet", "pixel art GIF", "8-bit / 16-bit
animation", "make my cat a pixel sprite", "idle / walk / attack animation",
"像素精灵图", "像素 GIF", "精灵图动画", "像素表情包", "sticker pack", "emoji",
"move list", "招式表", "大招".

Not for: game-engine export (Unity/Godot atlases) or smooth non-pixel animation
(smooth dance loops: see the Character Dance GIF skill).

## Modes

Single character only (no versus scenes, no game UI). Style is always locked: pixel art,
4×4 = 16 cells, explicit timing, white or transparent background.

| Mode | User says | Output | Guide |
|---|---|---|---|
| **GIF** (default) | "make a pixel GIF of …", optionally a move | one 16-frame loop | below |
| **Sticker** | "sticker pack", "表情包", "emoji", "Discord / Telegram / WeChat stickers" | 4 stickers per sheet (one per row, 4 frames each), exported per platform | [references/sticker-mode.md](references/sticker-mode.md) + `scripts/sticker_pack.py` |
| **Moveset** | "move list", "招式表", "idle + attack + ultimate" | 3 sheets + 3 GIFs + a game-manual MOVE LIST card | [references/moveset-mode.md](references/moveset-mode.md) + `scripts/moveset_card.py` |

Choosing the move in GIF mode (the `Move` line of the universal prompt):
- **empty** → the model reads the reference and picks a fitting move;
- **preset keyword** `idle` · `walk` · `jump` · `dance` · `attack` · `cast` → tested frame design and timing
  ([references/presets.md](references/presets.md); idle and attack come from prompts with 240K / 237K views on X);
- **free text** → the model animates exactly what the user describes.

Sticker mode: default no text; pass `--captions` only if the user wants words. Ask which
emotions they want, else use shy, angry, cry, heart (+ smug, sleepy, hello, shocked for a set of 8).
Moveset mode: generate idle first, then pass the idle sheet as a reference for basic and ultimate.

## What you need

- A reference image of the character, pet or mascot (or a short text description —
  then generate a clean reference image first).
- Optionally, what the user wants it to do ("summons a fox spirit", "K-pop dance", "sneezes").
  If they don't say, the model chooses a move that fits the character.
- Image generation: **GPT Image 2.6** (or another GPT Image model) through any entrance:
  Codex, ChatGPT, the OpenAI API or Renoise MCP. No terminal? Use ChatGPT + the
  [web tool](docs/index.html).
- Python 3.9+ with `Pillow` and `numpy` (`scipy` optional, `ffmpeg` optional for MP4).

## Steps

1. **Take the universal prompt** from [references/prompt-template.md](references/prompt-template.md).
2. **The move.** If the user asked for one, write it on the `Move (optional):` line, in
   their words. If not, leave it empty: the prompt tells the model to read the reference
   and choose (weapon → attack, powers → matching effects, idol outfit → dance,
   pet → idle/walk, mascot → jump). Don't impose a fixed template move.
3. **Optional precision.** For busy designs, replace the generic fidelity line with
   5–10 concrete features with colours. If a previous attempt gave near-identical
   frames, paste a 16-frame breakdown from [references/actions.md](references/actions.md).
   Keep the PIXEL STYLE block and the timing line word for word.
4. **Generate with any GPT Image entrance.** Entrances with GIF output (ChatGPT) use the
   prompt as is; the others use the *sprite sheet only* OUTPUT block. Pick the first one that
   works in the user's environment (details: [references/image-entrances.md](references/image-entrances.md)):

   | Entrance | Detect | How |
   |---|---|---|
   | a. Codex built-in imagegen (default) | `command -v codex` | inside Codex: call `imagegen` (ref by **absolute** path, `transparent_background: true`); from a shell: `scripts/codex_imagegen.sh <ref> <prompt.txt> <out_dir>` |
   | b. ChatGPT web / app | always available | give the user the universal prompt; ChatGPT returns the GIF itself (plus the sheet for optional polish in the web tool) |
   | c. OpenAI API | `$OPENAI_API_KEY` set | `scripts/openai_imagegen.py --ref <ref> --prompt-file prompt.txt -o sheet.png [--model …]` |
   | d. Renoise MCP | Renoise MCP tools connected | `gpt-image-2.6-sunburst`, 1:1, 1k, ref as `reference_image`; estimate cost and ask first |

   For c and d, tell the user the cost before generating. When calling Codex (a), add the
   agent-only line *"draw ONE still image with the built-in imagegen tool; do not call any
   video model or other generation plugin"* to the request — never into the image prompt.
   Entrances that can't do transparency: append `Use a plain flat white background.`
5. **Look at the sheet before going on.** 16 cells, same character, poses clearly
   different, nothing crossing cell borders. If not, fix the prompt and regenerate
   (see QA). Don't try to rescue a broken sheet in post.
6. **Build the GIF** (no Python? drop the sheet into [docs/index.html](docs/index.html), same steps in the browser):
   ```bash
   python3 scripts/sprite2gif.py sheet.png -o out/<name>_<action> <flags from actions.md> --mp4
   ```
   This slices the grid, removes the background, locks every frame to one baseline,
   checks the loop seam, and writes `_white.gif`, `_transparent.gif`, cleaned sheets,
   16 frame PNGs, a contact sheet and `_report.json`.
7. **QA** with [references/qa-checklist.md](references/qa-checklist.md): open the
   contact sheet, play the GIF, read `seam_ratio` and file sizes. Tune flags
   (anchor, durations) before regenerating.
8. **Deliver**: white GIF (for posting), transparent GIF (stickers/overlays), the
   transparent sprite sheet, and the prompt used.

## Prompt

Use the universal prompt in [references/prompt-template.md](references/prompt-template.md)
verbatim; it ends with an optional `Move:` line and asks for ~180 ms frames
(~300 ms on key poses, ~3 s loop) so the GIF is not frantic.

## Quality bar

A result ships only if: exactly 16 frames · same identity in all frames · poses
clearly change · nothing clipped or bleeding · plays in the right order ·
`seam_ratio ≤ 1.8` · no visible jitter · each GIF < 5 MB.

## Known limits

- The model draws 16 key poses, not mathematically interpolated in-betweens, so very
  fast actions can look a little snappy. Variable `--durations` hides most of it.
- Very detailed references (long flowing hair, capes) drift more between frames; list
  those features explicitly.
- Transparent output can carry a faint coloured fringe; the script's alpha threshold
  removes it. If the background comes back opaque, the script flood-fills it away.
- Copyrighted characters are fine for personal fan posts; use original characters for
  commercial work.
