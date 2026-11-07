# Quality check

Run through this after `sprite2gif.py`. Look at `<name>_contact.png` (all frames at a
glance) and play `<name>_white.gif`. Numbers come from `<name>_report.json`.

## Must pass (otherwise regenerate the sheet)

| Check | How to see it | Fix |
|---|---|---|
| 16 frames, none empty | report `frames: 16`, `empty_frames: []` | regenerate; stress "exactly 4 columns x 4 rows" |
| Same character in every frame | contact sheet: hair, outfit colours, accessories, limb count | add the missing features to `{KEY_FEATURES}` |
| Frames actually differ | contact sheet: poses are clearly different | add sizes/angles per frame (see jump in actions.md) |
| Nothing cut off | weapon tips, ears, tails, effects inside each frame | ask for more padding / smaller character |
| No bleed from neighbours | no stray fragments at frame edges | raise `--edge-margin`, or regenerate |
| Correct order | play the GIF: the action reads ready → peak → back | regenerate (the model occasionally shuffles rows) |

## Should pass (tune with script flags first)

| Check | Target | Flag |
|---|---|---|
| No jitter / swimming | feet stay put in idle/walk/attack | `--anchor-x mass` for walk/run, `feet` for stances |
| Loop seam | `seam_ratio <= 1.8` | `--trim-last` if frame 16 duplicates frame 1 |
| Timing feels punchy | holds on ready/peak, fast in-betweens | `--durations` |
| Jumps keep their height | character leaves the ground | `--anchor-y none` |
| Clean edges | no coloured fringe around the outline | default alpha threshold handles imagegen fringe |

## X / social ready

| Check | Target |
|---|---|
| File size | each GIF < 5 MB (X limit is 15 MB; smaller loads faster in the feed) |
| Canvas | square, 480 px default (`--size`) — X upscales pixel art cleanly |
| Loop | infinite (`loop=0`), set by the script |
| Background | post the white GIF in the feed; keep the transparent GIF for stickers / overlays |
| Preview | `--mp4` writes a 3-loop MP4 if you prefer posting video |
