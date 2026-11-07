# Moveset mode

One character → three moves (**idle**, **basic attack**, **ultimate**), each a 4×4 sprite
sheet and a looping GIF, plus a retro game-manual **MOVE LIST** card that animates all
three side by side. Made for saving and posting on X.

## Consistency rule

Generate **idle first**. Pass the idle sheet as an extra reference image for the basic and
ultimate sheets, and say "same character and sprite as the idle sheet (same sprite size,
palette, outline, proportions)". Without it the three sheets drift apart.

## Steps

```bash
# 1. three sheets: idle.png → basic.png, ultimate.png (both with idle.png as reference)
# 2. GIFs
python3 scripts/sprite2gif.py idle.png     -o out/mv_idle     --fps 6.67 --anchor-x mass
python3 scripts/sprite2gif.py basic.png    -o out/mv_basic    --durations 260,180,120,110,80,80,90,240,100,100,100,110,120,130,160,260
python3 scripts/sprite2gif.py ultimate.png -o out/mv_ultimate --durations 240,140,140,180,200,110,90,100,320,120,120,130,130,140,160,240
# 3. the card
python3 scripts/moveset_card.py -o out/moveset --name "HERO" --stars 1,2,5 \
  --move "out/mv_idle|IDLE|Unbothered|—|Twirls her wand and waits." \
  --move "out/mv_basic|BASIC|Emerald Spark|A|Quick flick, small green bolt." \
  --move "out/mv_ultimate|ULTIMATE|Serpent Surge|↓↘→ + A+B|Summons an emerald serpent."
```

`--move` is `prefix|TAG|Move name|Input command|Description`. The card is 1600×900
(fits X's 16:9 preview), written as `.gif`, `.mp4` and a still `.png`. `--logo` adds an
optional watermark bottom-right.

Every move gets a whole number of loops inside one card loop, so nothing jumps when the
GIF restarts.

## Prompts

Shared header for all three (fill in the features):

```text
CHARACTER: the character in the reference image: {key features}. Chibi game-sprite proportions (about 3 heads tall), facing RIGHT in side 3/4 view, like a 2D fighting-game sprite.
```

**Idle** — calm, characterful:
```text
Pixel-art animation sprite sheet: IDLE stance, 16 frames. Weight shifts gently, chest rises and falls, hair and clothes sway, one small personality gesture in frames 7-11 (twirl a weapon, adjust glasses, flick hair), frame 16 identical to frame 1. Feet planted.
```

**Basic attack** — quick, light, small effect:
```text
Pixel-art animation sprite sheet: BASIC ATTACK, 16 frames, quick and light. 1-2 ready; 3-4 small step, wind-up; 5 strike; 6-7 a small {effect} with a short trail; 8 small hit spark; 9-11 effect fades; 12-15 return; 16 identical to frame 1. Effects stay small and inside each cell.
```

**Ultimate** — dramatic charge and a big signature effect:
```text
Pixel-art animation sprite sheet: ULTIMATE / special move, 16 frames, dramatic. 1 ready; 2-3 power-up starts, aura flickers, hair and clothes lift; 4-5 full power-up; 6 aim; 7-8 the {signature effect} bursts out; 9 PEAK, biggest frame; 10-12 effect breaks into sparkles; 13-15 aura fades, everything settles; 16 identical to frame 1. Keep the character a bit smaller so the effect stays inside each cell.
```

Append the PIXEL STYLE and SHEET LAYOUT blocks from [prompt-template.md](prompt-template.md)
to each. Pick the effect from the character: weapon → slash arcs, magic → bolts / summons,
martial artist → shockwaves, cute mascot → hearts / stars.

## Naming the moves

Short, punchy, in-character: two words, an adjective plus a noun works ("Emerald Spark",
"Serpent Surge"). Inputs read like a fighting-game manual: `A`, `B`, `→ + A`,
`↓↘→ + A+B`. Power stars: idle 1, basic 2, ultimate 5.
