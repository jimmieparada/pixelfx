# Move presets

Type one keyword on the `Move:` line of the universal prompt: `idle`, `walk`, `jump`,
`dance`, `attack` or `cast`. The prompt carries a short version of each preset so it works
in ChatGPT without this file; this page is the full design and the reasoning.

The two oldest presets come from prompts that already worked at scale on X:
**idle** (240K views) and **attack** (237K views), both originally written for GPT Image 2.5.

Shared rules for every preset: 16 frames on a 4×4 sheet, pixel style locked, white or
transparent background, the last frame flows back into the first.

| Preset | Facing | Loop | Timing | `sprite2gif.py` flags |
|---|---|---|---|---|
| idle | front 3/4 | ~2.4 s | 150 ms every frame | `--fps 6.7 --anchor-x mass` |
| walk | side, right | ~1.9 s | 120 ms every frame | `--fps 8.3 --anchor-x mass` |
| jump | front 3/4 | ~2.2 s | 100–260 ms, holds on crouch / apex / landing | `--lift … --durations …` |
| dance | front | ~2.6 s | 140–220 ms, holds on poses | `--fps 6 --anchor-x mass` |
| attack | side 3/4, right | ~2.2 s | 260 ms ready, 80–100 ms strike, 240 ms impact | `--durations …` |
| cast | side 3/4, right | ~2.4 s | like attack, longer charge | `--durations …` |

---

## idle — subtle, alive, anchored
From the 240K idle prompt.
```
Gentle breathing: a tiny rise and fall of the upper body over the 16 frames.
Slight secondary movement in hair, clothing or relevant appendages (ears, tail, wings).
One brief natural blink around frames 9-10, only if the character has visible eyelids.
Feet or contact points anchored; no walking, turning, dramatic gestures or scene changes.
```
Timing: 150 ms per frame (2.4 s loop, same as the original).

## walk — in place, readable gait
```
One full walk cycle on the spot (treadmill style, no forward travel): frames 1-8 first half
of the stride, 9-16 the mirrored second half. Body bobs by one or two pixels, arms or
front legs swing opposite to the legs, hair / ears / tail bounce.
Four-legged animals: back-left, front-left, back-right, front-right.
```
Timing: 120 ms per frame.

## jump — squash and stretch
```
1-2 idle; 3-4 squash into a crouch (about 70% height); 5 launch, stretched tall;
6-8 rising (up to about 30% of the cell height); 9 apex, biggest expression;
10-11 falling, stretched toward the floor; 12 landing squash with small dust puffs;
13 rebound stretch; 14-16 settle back into idle.
```
Spell out heights: without numbers models draw 16 near-identical poses.
Timing: holds on crouch, apex and landing (~220–260 ms), 80–100 ms in the air.

## dance — two short bars, front-facing
```
Read the character's vibe (idol, cool, goofy, elegant) and choreograph two bars:
ready → step and hit a pose to one side → mirror to the other side →
one signature pose (heart hands, point up, peace sign, hair flip…) → small bounce → ready.
Stay facing front (no spins: back views drift off-model). Hair and clothes follow every move.
```
Timing: 140 ms between poses, 220 ms on each hit pose.

## attack — from the 237K combat prompt
```
Design an attack that suits the character:
- carries a weapon → build the attack around it;
- clearly identifiable powers → matching effects (water, fire, lightning…);
- otherwise → a plausible physical attack based on their appearance. Don't invent unrelated powers.
Ready stance → anticipation → attack → impact peak → effects dissipate → recovery.
Animate real changes in pose and body mechanics.
```
Timing: hold the ready stance and the impact (~240–260 ms), fast strike frames (80–100 ms),
"emphasise anticipation and fast strikes" as in the original. ~2.2 s loop.

## cast — magic / energy
```
Ready → charge-up (aura, floating hair or cloth, particles gathering) → release
(bolt, beam, summon or burst matching the character's theme) → peak → effect breaks into
sparkles → recover. Keep big effects inside the frame: draw the character a bit smaller.
```
Timing: like attack with a longer charge (~2.4 s).

---

## Original prompts (Sep 2026, GPT Image 2.5)

Kept for reference; the presets above are distilled from them.

<details>
<summary>Idle (240K views)</summary>

```text
Turn the character in my uploaded reference image into an adorable pixel-art sprite with a looping idle animation.

CHARACTER
Use the uploaded image as the character reference. Preserve the character's recognizable features, colors, hairstyle, outfit, accessories, and distinctive silhouette. Adapt its original anatomy into cute chibi proportions without forcing non-human characters into a human body. If the reference is cropped, infer the missing body details to match the visible design.

STYLE
Create crisp pixel art with clearly defined square pixels, clean outlines, and a cohesive limited palette. No blurry edges, smooth vector styling, or realistic rendering.

ANIMATION
Create 16 consecutive frames of one subtle, seamless idle animation:
- Gentle breathing with a tiny rise and fall of the upper body.
- Slight secondary movement in hair, clothing, or relevant appendages.
- One brief natural blink if the character has visible eyes.
- Keep the character in place, with its feet or contact points anchored.
- Keep the design, proportions, camera angle, and scale consistent.
- No walking, turning, dramatic gestures, or scene changes.
- Make the last frame transition smoothly back to the first.

SPRITE SHEET
Arrange the 16 frames in exactly 4 columns × 4 rows, ordered left to right, top to bottom.
Canvas: 1024 × 1024 pixels. Each cell: 256 × 256 pixels.
Use identical alignment and a fixed baseline across all cells.
Keep the entire character inside each cell, with at least 16 pixels of transparent padding on every side, including around moving accessories.
No overlapping cells, grid lines, labels, text, or watermarks.

TRANSPARENCY
Use a genuinely transparent RGBA background with alpha zero outside the character.
Do not draw a checkerboard or add a solid background, floor, or cast shadow.
Preserve white and pale details inside the character.

DELIVERABLES
1. A transparent 4 × 4 PNG sprite sheet.
2. A transparent animated GIF of the single character, using all 16 frames at 256 × 256 pixels, looping forever with an approximately 2.4-second cycle.
3. A ZIP containing all 16 individual transparent PNG frames.
```
</details>

<details>
<summary>Combat (237K views)</summary>

```text
Using the character reference image I upload, create a pixel-art battle animation. Deliver a transparent animated GIF and a 4×4 sprite sheet containing 16 sequential frames.

CHARACTER FIDELITY
Identify the character's hairstyle, outfit, colors, weapon, proportions, and distinctive features. Translate them into a recognizable chibi pixel-art sprite. Keep the character's identity, scale, clothing, and equipment consistent across all frames.

BATTLE DESIGN
Automatically design an attack that suits the character:
- If they carry a weapon, build the animation around it.
- If their abilities are clearly identifiable, use the appropriate effects, such as water, fire, or lightning.
- If their abilities are unclear, create a plausible physical attack based on their appearance. Do not invent unrelated powers.

Proceed without asking preliminary questions. Create one coherent battle loop:
Ready stance → Anticipation → Attack → Impact peak → Effects dissipate → Recovery.
Distribute the sequence naturally across 16 frames. The final frame must transition smoothly into the first. Animate actual changes in pose and body mechanics; do not fake movement by merely translating or rotating a static character image.

PIXEL-ART STYLE
Use crisp 16-bit game-style pixel art with readable silhouettes, sharp pixel edges, and a restrained palette. Maintain a consistent pixel scale for both the character and effects. Avoid blur, photorealistic rendering, and style drift.

SPRITE SHEET REQUIREMENTS
- Exactly 4 columns × 4 rows, totaling 16 frames.
- Frames play left to right, then top to bottom.
- All cells must have identical dimensions.
- Use a fixed camera, consistent character scale, a stable ground baseline, and consistent animation registration.
- Keep the entire body, weapon, and effects inside its cell. Nothing may cross cell boundaries or be cropped.
- No text, frame numbers, grid lines, watermarks, or background scenery.

TRANSPARENCY AND ANIMATION
Slice the sheet into frames and assemble a transparent, infinitely looping GIF. Adjust frame durations to emphasize anticipation and fast strikes. Aim for a total loop duration of approximately 1.5–2 seconds.
```
</details>
