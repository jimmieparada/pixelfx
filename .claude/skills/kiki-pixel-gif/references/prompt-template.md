# Prompt template

One universal prompt with three ways to choose the move, all on the last line:

| Move line | What happens |
|---|---|
| empty | the model reads the reference and picks a move that fits the character |
| `idle` · `walk` · `jump` · `dance` · `attack` · `cast` | a tested preset with fixed frame design and timing ([presets.md](presets.md)) |
| anything else, e.g. `summons a glowing fox spirit` | the model animates exactly what you describe |

Style, 16 frames, timing and background are locked in every case.

## Universal prompt (copy-paste)

```text
Turn the character in my uploaded image into a looping pixel-art animation.

CHARACTER FIDELITY
Study the reference and keep every key feature: hairstyle and hair color, face and eye color, outfit pieces, colors and patterns, markings, accessories, and any weapon or prop. For animals keep the species anatomy (correct number of legs, no human body). Chibi game-sprite proportions. Same design, palette, outline and size in every frame.

CHOOSE THE MOVE (read the "Move" line at the end)
- Empty → read the reference and pick ONE short signature move that fits this character: weapon or prop → a move built around it; clear powers or theme → matching pixel effects; idol or stage outfit → a short dance; pet or animal → a species-appropriate idle, walk or tail wag; round mascot → a bouncy jump. Do not invent unrelated powers.
- A preset keyword → use that preset:
  idle: gentle breathing (tiny rise and fall of the upper body), slight sway of hair, clothes or tail, one brief blink if the character has eyelids; feet anchored; no walking, turning or big gestures. 150 ms per frame.
  walk: one walk cycle on the spot, no forward travel, side view; frames 1-8 first stride, 9-16 mirrored; body bobs 1-2 pixels, hair and accessories bounce. 120 ms per frame.
  jump: idle → squash into a crouch → stretch and launch → rise to about 30% of the frame height → apex with the biggest expression → fall → landing squash with dust puffs → rebound → idle. Hold crouch, apex and landing longer.
  dance: two short bars facing front: ready → hit a pose to one side → mirror to the other side → one signature pose that fits the character (heart hands, point up, peace sign) → small bounce → ready. No spins. Hold each hit pose a little longer.
  attack: design an attack that suits the character (weapon → built around it; clear powers → matching effects; otherwise a plausible physical attack). Ready stance → anticipation → attack → impact peak → effects dissipate → recovery. Hold the ready stance and the impact, keep the strike frames fast.
  cast: ready → charge-up (aura, floating hair, gathering particles) → release a bolt, beam or summon matching the character's theme → peak → effect breaks into sparkles → recover. Draw the character a bit smaller so big effects stay in frame.
- Anything else → animate exactly what I describe.
Facing: side 3/4 view for attack, cast, walk and runs; front view for dance, idle and jump.

ANIMATION
16 frames forming one readable loop: ready pose → anticipation → main motion → peak pose → follow-through → back to ready.
Give the ready pose and the peak pose more screen time, keep the in-between frames quick.
Real pose changes with body mechanics, not just moving or rotating a static image. Hair, clothes and effects react to the motion. The last frame flows smoothly back into the first.

PIXEL STYLE
Crisp 16-bit game pixel art with clearly visible square pixels, 1px dark outline, restrained palette, gentle cel shading. No blur, no anti-aliasing, no gradients, no photorealism.

OUTPUT
Deliver an actual animated GIF, not a still image: 16 frames, looping forever.
Timing: use the preset timing if there is one; otherwise about 180 ms per frame and about 300 ms on the ready and peak poses (one loop about 2.5–3 seconds). Never faster than 80 ms per frame.
Square canvas, plain flat white background, fixed camera, character centered with margin. Same character size in every frame; feet stay on the same ground line except during jumps.
Also give me the 16 frames as a 4×4 sprite sheet PNG.
No text, frame numbers, floor, cast shadow or scenery.
Briefly tell me which move you chose.

Move (optional): 
```

Example last lines: `Move (optional): attack` · `Move (optional): idle` ·
`Move (optional): summons a glowing fox spirit` · `Move (optional): sneezes and gets startled` ·
or leave it empty to let the model choose.

## Sprite sheet only (for `sprite2gif.py` / the web tool)

Entrances without GIF output (Codex imagegen, OpenAI API, Renoise still images), or when
you want the cleanest result: replace the **OUTPUT** block with this one. The script then
does the slicing, baseline locking, timing and transparency.

```text
SHEET LAYOUT
Deliver ONE still image: exactly 4 columns x 4 rows = 16 equal square cells in a square image.
Frames read left to right, then top to bottom. Fixed camera, identical character size, palette and design in every cell; consecutive frames of the SAME character, not variations.
Ground contact points sit on the same baseline at about 85% of each cell height, body centered horizontally in its cell.
Keep the whole character and all effects inside each cell with clear padding; nothing touches or crosses cell borders. One character per cell.
No grid lines, borders, frame numbers, text, watermark, floor, cast shadow or scenery.
Transparent background.
```

If the entrance can't do transparency, end with `Plain flat white background.` instead;
the script removes white backgrounds and keeps white details inside the character.

## Making it more specific (optional)

The universal prompt works as is. For more control:

- **Name the features.** Replace the generic fidelity line with 5–10 concrete nouns and
  colours from the reference ("platinum-blonde hair, green-and-silver striped tie" beats
  "stylish outfit"). Helps most with busy designs: long hair, capes, many accessories.
- **Script the beats.** Beyond the six presets, paste a full 16-frame breakdown from
  [actions.md](actions.md) (idle, walk, run, attack, cast, jump, dance, wave) under
  ANIMATION. Use this when the model keeps drawing near-identical frames: give heights,
  sizes or angles per frame.
- **Change the speed.** Edit the ms numbers in OUTPUT, or keep the sheet and set
  `--fps` / `--durations` in the script or web tool.

## Why the layout lines matter

- **4×4, square, equal cells**: the slicer assumes an even grid (it nudges cuts to the
  emptiest line, but cannot recover a 5×3 sheet you asked as 4×4).
- **Same baseline + centered**: frames that start close to aligned need smaller
  corrections and don't "swim".
- **Padding, nothing crosses borders**: a sword tip or spell that crosses into the
  next cell gets cut off or bleeds into the neighbour frame.
- **No floor / shadow**: a drawn shadow ellipse breaks background removal and the
  baseline detector.
- **Explicit timing**: without ms numbers models tend to play 16 frames in about a
  second, which reads as frantic.

## Where to run it

The prompt is model-agnostic: paste it into any GPT Image entrance that accepts a
reference image. How to call each one (and the agent-only instructions) is in
[image-entrances.md](image-entrances.md).
