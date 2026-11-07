# Action library

**Optional.** The universal prompt lets the model choose a move from the character's look,
or follow a one-line request. Use these breakdowns when you want a specific, repeatable
motion, or when a free-form move came back with near-identical frames.

Each action = 16 frames on a 4×4 sheet + recommended timing + the matching
`sprite2gif.py` flags. Paste the beats under ANIMATION in the
[universal prompt](prompt-template.md) (and put the action sentence on the `Move:` line);
replace words in *italics* with what fits the character.

| Action | Facing | Loop | Timing | Script flags |
|---|---|---|---|---|
| idle | front 3/4 | ~2.4 s | 150 ms/frame | `--fps 6.7 --anchor-x mass` |
| walk | side, right | ~1.3 s | 12 fps | `--fps 12 --anchor-x mass` |
| run | side, right | ~0.9 s | 16–18 fps | `--fps 18 --anchor-x mass` |
| attack (melee / weapon) | side 3/4, right | ~1.8–2 s | variable | `--durations` (below) |
| cast (magic / energy) | side 3/4, right | ~2 s | variable | `--durations` (below) |
| jump | front 3/4 | ~1.6 s | variable | `--anchor-y none --durations` (below) |
| dance | front | ~1.6 s | 10 fps | `--fps 10 --anchor-x mass` |
| happy / wave | front 3/4 | ~1.6 s | 100 ms/frame | `--fps 10 --anchor-x mass` |

Rule of thumb: **hold the poses that read (ready stance, impact, apex), rush the
frames in between.** Uniform timing makes attacks look floaty.

---

## idle
Action sentence: *breathing in a relaxed idle loop*
```
1-4 relaxed stance, body rises slightly with an in-breath; 5-8 body sinks back down;
9 a small secondary motion begins (ear twitch / hair sway / tail swish);
10-12 the secondary motion completes; 13 a quick blink (only if the species has eyelids);
14-16 settle back into the exact pose of frame 1.
Keep the character in the same spot; feet never leave the baseline; no walking or turning.
```

## walk
Action sentence: *doing a walk cycle in place*
```
One full walk cycle on the spot (treadmill style, no forward travel):
frames 1-8 first half of the stride, frames 9-16 the mirrored second half,
legs moving in a natural gait order (for four-legged animals: back-left, front-left,
back-right, front-right). The body bobs up and down by one or two pixels,
ears/hair bounce slightly, *tail wags*. Feet always return to the same baseline.
```

## run
Action sentence: *running in place*
```
One full run cycle on the spot, no forward travel: 1-4 contact → push-off → flight →
landing for the first leg, 5-8 the same for the other leg, 9-16 repeat with clear
variation in arms/hair/cloth so the two halves are not identical copies.
Body leans forward; one frame per half-cycle has both feet off the ground.
```

## attack (weapon / melee)
Action sentence: *performing a signature attack*
```
1-2 ready stance; 3-4 anticipation: crouch and pull the *weapon* back;
5 explosive strike; 6-7 follow-through with a *motion smear / slash arc*;
8 impact peak, *effect* at full size; 9-11 effect breaks apart and fades;
12-14 recovery back toward guard; 15-16 ready stance identical to frame 1.
```
Effect hint: if the character clearly has a power, use it (*water, fire, lightning,
petals*). If not, keep it physical: dust, speed lines, a plain slash arc. Do not invent
unrelated powers.

Durations (ms, 16 values):
`200,200,140,120,70,70,80,160,90,90,90,90,100,110,160,200`

## cast (magic)
Action sentence: *casting an attack spell with their *wand / hands / staff**
```
1-2 ready stance, *wand* low; 3-4 anticipation: lean back, *wand* raised behind the
shoulder, hair and cloth lift; 5 snap forward pointing; 6 a bright spark forms at the tip;
7 a *bolt* shoots forward with sparkles; 8 impact peak: a big *shaped burst* in front;
9-11 the burst breaks into sparkles that fade; 12-14 recovery, cloth and hair settle;
15-16 ready stance identical to frame 1.
```
Durations: `200,200,140,120,80,70,70,160,90,90,90,90,100,110,160,200`

## jump
Action sentence: *doing a big, bouncy, cartoon happy jump with exaggerated squash and stretch*
```
1 idle. 2 idle, slightly lower. 3 squash: body ~75% height, ~125% width.
4 deeper squash ~65% height. 5 launch: stretched tall (~130% height), feet leaving the ground.
6 rising, ~15% of cell height above the ground line. 7 rising ~25%. 8 near apex ~32%.
9 APEX ~35%, biggest expression, a couple of sparkles. 10 falling ~28%. 11 falling ~12%,
stretching down toward the floor. 12 landing squash ~70% height, small dust puffs.
13 rebound stretch ~115%. 14 small squash ~90%. 15 settling. 16 idle identical to frame 1.
The ground line stays at the same height in every cell; airborne frames show empty space under the feet.
```
Spell out the percentages: without them the model draws 16 near-identical poses.
Script: `--anchor-y none` (keep the vertical motion) and
`--durations 160,120,100,140,60,60,70,80,160,70,60,90,80,80,100,160`

## dance
Action sentence: *doing a cute, bouncy idol dance loop*
```
1 ready, hands on hips. 2 bounce down. 3 step right, arms swing up right, hips pop right.
4 point to the upper right, wink. 5 bounce down. 6 step left, arms swing up left, hips pop left.
7 point to the upper left, wink. 8 bounce down, arms crossed. 9 hands make a big heart above the head.
10 lean right with the heart. 11 lean left with the heart. 12 heart down to the chest.
13 small hop, arms wide, hair and skirt flare. 14 land with bent knees. 15 shoulder shimmy,
hands near the face. 16 ready pose identical to frame 1. Stay facing front the whole time (no spins).
Hair, ribbons and clothes react to every move.
```
Spins look broken on a sprite sheet (the back view drifts off-model), so keep dances front-facing.

## happy / wave
Action sentence: *waving hello happily*
```
1-2 idle smile; 3-4 hand rises; 5-8 two big waves left-right with a small body sway;
9 wink; 10-12 two more waves; 13-14 hand lowers; 15-16 idle identical to frame 1.
```

---

### Writing your own action
1. Write it as 5–7 beats first (ready → anticipation → main motion → peak → settle).
2. Spread the beats over 16 frames, giving the peak and the ready pose one or two frames each.
3. Always end with "identical to frame 1".
4. If an action keeps coming back with near-identical frames, add sizes/heights as
   percentages of the cell (see jump).
