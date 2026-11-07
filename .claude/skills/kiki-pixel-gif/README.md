# Kiki Pixel GIF · AI Animation Lab

Turn any character, pet or mascot into a **looping pixel-art GIF** with GPT Image 2.6.
Upload one image, say what it should do (or let the AI pick a move that fits the character), get a looping pixel GIF you can post right away.

**Don't want to set anything up?** You can also use it in one click on Renoise, the tool I make my animations with: [Pixel GIF on Renoise](https://renoise.ai/project?id=pixelGif&utm_medium=github&utm_source=kiki-pixel-gif) (upload a character, get the GIF).

![Kiki Pixel GIF showcase](assets/showcase.gif)

| Attack | Dance | Jump |
|:---:|:---:|:---:|
| ![attack](examples/malfoid-attack/white.gif) | ![dance](examples/heartbeat-dance/white.gif) | ![jump](examples/momo-jump/white.gif) |
| anime character · spell attack | anime idol · dance loop | original mascot · squash & stretch jump |

## Three modes

| GIF | Sticker pack | Move list |
|:---:|:---:|:---:|
| one character, one looping move | 4 stickers per generation, ready for WeChat / Discord / Telegram / Slack | idle + basic + ultimate on a game-manual card |
| ![gif](examples/heartbeat-dance/white.gif) | ![stickers](examples/momo-stickers/preview.gif) | ![moves](examples/malfoid-moveset/move_list.gif) |

**Choosing the move (GIF mode):** leave it empty and the AI picks one that fits the character · type a preset (`idle`, `walk`, `jump`, `dance`, `attack`, `cast`) for a tested frame design · or describe anything you want.

- Sticker mode: [references/sticker-mode.md](references/sticker-mode.md) (platform sizes and limits included) → `scripts/sticker_pack.py`
- Move list mode: [references/moveset-mode.md](references/moveset-mode.md) → `scripts/moveset_card.py`

This is the first skill of **AI Animation Lab**: tested prompts packaged as agent skills, so you get the same result every time instead of copy-pasting a prompt and hoping.

## How it works

```
reference image ──► GPT Image 2.6 draws a 4×4 sprite sheet (16 frames, transparent)
                         │
                         ▼
               sprite2gif.py  slice → clean background → lock baseline → check loop
                         │
                         ▼
          white GIF · transparent GIF · sprite sheet · 16 frame PNGs · MP4 preview
```

## No command line? 3 steps

1. **Copy the prompt.** Open [references/prompt-template.md](references/prompt-template.md) and copy the universal prompt. Write the move you want on the last line, or leave it empty and the AI picks one that fits your character.
2. **Generate.** In ChatGPT (web or app), attach your character image, paste the prompt, send. ChatGPT returns the animated GIF directly.
3. **Download and post.** Want it smoother, transparent, or with punchier timing? Drop the 4×4 sheet ChatGPT also gives you into the **[Sprite → GIF web tool](https://mayzmei.github.io/kiki-pixel-gif/)** and pick the action preset. It runs in your browser: nothing to install, nothing uploaded.

## Quick start

### As a skill (Claude Code, Codex, any agent that reads `SKILL.md`)

```bash
git clone https://github.com/Mayzmei/kiki-pixel-gif ~/.claude/skills/kiki-pixel-gif
```

Then just ask:

> make my cat a pixel sprite, walk cycle
> turn this character into a pixel-art attack GIF

The agent follows [SKILL.md](SKILL.md): reads your image, picks an action, fills the prompt, generates the sheet, builds the GIF and checks quality.

### By hand

1. Copy the [universal prompt](references/prompt-template.md), add a move on the last line or leave it empty. For a sheet-only entrance, swap in the *sprite sheet only* block.
2. Generate **one image** with GPT Image 2.6 through any entrance (table below), attaching your reference image.
3. Build the GIF:

```bash
pip install pillow numpy scipy
python3 scripts/sprite2gif.py sheet.png -o out/mychar_walk --fps 12 --anchor-x mass --mp4
```

### Image entrances

Same prompt everywhere; pick whatever you already have. Details: [references/image-entrances.md](references/image-entrances.md).

| Entrance | Command / steps | Cost |
|---|---|---|
| Codex (default) | `scripts/codex_imagegen.sh my_char.png prompt.txt out/` | included in a ChatGPT plan |
| ChatGPT web / app | paste the universal prompt + image, download the GIF | included in a ChatGPT plan |
| OpenAI API | `OPENAI_API_KEY=… scripts/openai_imagegen.py --ref my_char.png --prompt-file prompt.txt -o sheet.png --model <gpt-image model>` | your API usage |
| Renoise MCP | connect [Renoise](https://renoise.ai/plugin?utm_medium=github&utm_source=kiki-pixel-gif) in Claude Code / Codex, ask for `gpt-image-2.6-sunburst` | Renoise credits |

The API script never stores your key: it only reads `OPENAI_API_KEY` from your shell. `--dry-run` prints the request without sending it.

## Actions

| Action | Best for | Script flags |
|---|---|---|
| `idle` | pets, portraits | `--fps 6.7 --anchor-x mass` |
| `walk` | pets, characters | `--fps 12 --anchor-x mass` |
| `run` | characters | `--fps 18 --anchor-x mass` |
| `attack` | characters with a weapon | `--durations …` (snappy timing) |
| `cast` | magic users | `--durations …` |
| `jump` | mascots, blobs | `--lift …` + `--durations …` |
| `dance` | idols, cute characters | `--fps 10 --anchor-x mass` |
| `wave` | mascots, avatars | `--fps 10 --anchor-x mass` |

You don't have to pick one: by default the AI chooses a move from the character's look. The table is for when you want a specific, reliable motion; full 16-frame beats and timings are in [references/actions.md](references/actions.md).

## What `sprite2gif.py` does

- **Slices the grid** (default 4×4) and snaps each cut to the emptiest line, so slightly uneven sheets still slice cleanly.
- **Cleans the background**: keeps real alpha, drops the coloured fringe transparent outputs sometimes carry, or flood-fills a white background away without eating white details inside the character.
- **Kills jitter**: puts every frame on one shared baseline and horizontal anchor (`feet`, `mass` or `bbox`).
- **Checks the loop**: compares the last→first jump with normal frame-to-frame motion (`seam_ratio`, ≤ 1.8 passes).
- **Times it**: uniform `--fps` or per-frame `--durations` to hold key poses and rush the in-betweens; `--lift` adds a jump arc.
- **Ships X-ready files**: square 480 px nearest-neighbour upscale, shared palette (no colour flicker), infinite loop, shrinks itself under `--max-mb` (default 5 MB; X allows 15 MB).

Same steps run in the browser in [`docs/index.html`](docs/index.html) (GitHub Pages ready).

Outputs: `_white.gif`, `_transparent.gif`, `_sheet_white.png`, `_sheet_transparent.png`, `_frames/`, `_contact.png`, `_report.json`, and `_white.mp4` with `--mp4`.

## Examples

Each folder in [`examples/`](examples) has the reference image, the exact prompt, the raw sheet from the model, the command used, and the outputs.

| Example | Reference | Frames | Loop | Seam ratio |
|---|---|---|---|---|
| [malfoid-attack](examples/malfoid-attack) | anime character sheet | 16 | 1.97 s | 0.73 |
| [heartbeat-dance](examples/heartbeat-dance) | anime character (front view) | 16 | 1.96 s | 0.48 |
| [momo-jump](examples/momo-jump) | original mascot | 16 | 1.61 s | 0.38 |
| [heartbeat-auto](examples/heartbeat-auto) | move left empty (AI picked a dance) | 16 | 3.24 s | 0.83 |
| [momo-stickers](examples/momo-stickers) | sticker mode, 8 emotions | 8 × 4 | 0.72 s each | — |
| [malfoid-moveset](examples/malfoid-moveset) | move list mode | 3 × 16 | 2.4 / 2.24 / 2.56 s | 0.53 / 0.53 / 0.36 |

The Momo mascot was generated as a sample input; use your own photo or character.

## Tips

- Leave the move empty first and see what the AI picks; then ask for something specific.
- Name 5–10 concrete features with colours in the prompt. "Platinum-blonde hair, green-and-silver striped tie" keeps identity far better than "stylish outfit".
- If the 16 frames come back nearly identical, write sizes and heights per frame as percentages of the cell (see `jump`).
- Check the sheet before running the script. A broken sheet is cheaper to regenerate than to fix.
- Post the white GIF in the feed; keep the transparent GIF for stickers and overlays.

## Roadmap

- [x] Kiki Pixel GIF
- [ ] kiki-dance-gif: Character Dance GIF (next in AI Animation Lab)

## License

MIT. Made by [Kiki](https://x.com/Mayz1169).
