# Image entrances

The sprite sheet can come from any GPT Image entry. The prompt is the same everywhere
([prompt-template.md](prompt-template.md)); entrances without GIF output swap in the
*sprite sheet only* block. After that,
every entrance ends the same way: one sprite sheet PNG → `sprite2gif.py` (or the
[web tool](../docs/index.html)) → GIF.

## Which one to use (agents: check in this order)

| # | Entrance | Use it when | Cost | Transparent bg |
|---|---|---|---|---|
| a | Codex built-in `imagegen` | `codex` CLI is installed and signed in | included in a ChatGPT plan | yes |
| b | ChatGPT (web / app) | the user has no terminal, or prefers clicking; outputs the GIF directly | included in a ChatGPT plan | white bg (use the web tool for transparent) |
| c | OpenAI API | `OPENAI_API_KEY` is set in the environment | pay per image (OpenAI pricing) | depends on model; default white |
| d | Renoise MCP | a Renoise MCP server is connected in Claude Code / Codex | Renoise credits (about 14 per 1K sheet at time of writing) | ask for white bg |

Agent detection:
- a: `command -v codex` succeeds → use it (default).
- c: `[ -n "$OPENAI_API_KEY" ]` → use it if a is missing or the user asks for the API.
- d: a Renoise MCP tool list (e.g. `list_models`, `create_tasks`) is available → use it if the user asks for Renoise or neither a nor c is available.
- b: always possible; give the user the filled prompt and the manual steps below.

Never pick a paid entrance (c, d) silently: tell the user the expected cost first.

---

## a. Codex built-in imagegen (default)

Inside Codex, call the built-in image tool directly. It accepts only four arguments:

| Argument | Value |
|---|---|
| `prompt` | the filled template |
| `referenced_image_paths` | **absolute** path(s) to the reference image (relative paths fail) |
| `num_last_images_to_include` | leave default |
| `transparent_background` | `true` |

From Claude Code or any shell:

```bash
scripts/codex_imagegen.sh my_character.png prompt.txt out/
python3 scripts/sprite2gif.py out/sheet.png -o out/mychar_dance --fps 10 --anchor-x mass
```

Agent-only instruction (put it in the request to Codex, **not** in the image prompt):
*draw ONE still sprite-sheet image with the built-in imagegen tool; do not call any video
model, animation plugin or other generation skill.* Some setups have video skills that
grab the word "animation" otherwise. Run `codex exec` with stdin closed (`< /dev/null`) or
it waits for input forever.

## b. ChatGPT web / app (no command line, GIF straight out)

ChatGPT generates animated GIFs natively.

1. Open ChatGPT, attach your character image, paste the **universal prompt**
   ([prompt-template.md](prompt-template.md)); add a move on the last line or leave it empty.
2. Download the GIF. Done.
3. Optional polish: if the character jitters, you want a transparent GIF, or you want
   snappier timing, also download the 4×4 sheet ChatGPT gives you and drop it into the
   [Sprite → GIF web tool](../docs/index.html) with the matching action preset.

## c. OpenAI API (your own key)

```bash
export OPENAI_API_KEY=sk-...                  # in your shell only, never in a file in this repo
python3 scripts/openai_imagegen.py --ref my_character.png --prompt-file prompt.txt \
  -o out/sheet.png --model gpt-image-2         # any GPT Image model name your key can use
python3 scripts/sprite2gif.py out/sheet.png -o out/mychar_walk --fps 12 --anchor-x mass
```

- `--dry-run` prints the exact request (endpoint, fields, files) without sending it.
- Model: `--model` or `$OPENAI_IMAGE_MODEL` (default `gpt-image-2`).
- Background: some API models reject `background=transparent`, so the script defaults to a
  white background and `sprite2gif.py` removes it. Use `--background transparent` if your
  model supports it.

## d. Renoise MCP (GPT Image 2.6 inside Claude Code / Codex)

[Renoise](https://renoise.ai/plugin?utm_medium=github&utm_source=kiki-pixel-gif) is the
tool I use to run GPT Image 2.6 from my coding agent. Setup instructions are on that page;
once the MCP server is connected:

1. Upload the reference image (`upload_files` / `request_upload`) and note its material id.
2. Estimate first (`estimate_cost`), tell the user the credit cost, wait for a yes.
3. Create one image task:
   ```json
   {
     "model": "gpt-image-2.6-sunburst",
     "kind": "image",
     "ratio": "1:1",
     "resolution": "1k",
     "prompt": "<filled template, with 'Use a plain flat white background.' instead of transparent> Character reference: @material:<id>",
     "references": [{ "ref": "material:<id>", "role": "reference_image" }]
   }
   ```
4. Wait for the task, download the PNG, run `sprite2gif.py` on it.

GPT Image 2.6 on Renoise can also return an animated GIF directly (`outputFormat: "gif"`,
up to 16 frames). The sprite-sheet route stays the default here because it gives you the
sheet, transparent output, baseline locking and timing control.
