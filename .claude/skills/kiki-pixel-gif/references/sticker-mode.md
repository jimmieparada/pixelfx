# Sticker mode

One character → a set of small, transparent, looping pixel stickers you can upload to
WeChat, Discord, Telegram or Slack. Default: no text. Captions are optional.

## How it works

One image generation = **4 stickers**: the sheet is 4×4, every **row** is one emotion and
its 4 frames loop. Two generations give a set of 8. The second sheet takes the first one
as a reference so the character stays identical.

```bash
# 1. generate stickers_a.png (and stickers_b.png with stickers_a.png as an extra reference)
# 2. export every platform format
python3 scripts/sticker_pack.py stickers_a.png stickers_b.png -o out/momo \
  --names shy,angry,cry,heart,smug,sleepy,hello,shocked
# optional captions, one per sticker (leave empty for none):
#   --captions "so shy,grr,waaah,love u,,zzz,hi!,!?"
```

Output per sticker (`out/momo/<name>/`) and one `preview.gif` grid on white for posting.

## Platform specs

| Platform | File | Size | Limit | Format notes | Source |
|---|---|---|---|---|---|
| WeChat sticker (表情开放平台) | `wechat_240.gif` | 240×240 | ≤ 500 KB | GIF, transparent | third-party guides; check the official spec on sticker.weixin.qq.com before submitting |
| Discord sticker | `discord_sticker_320.png` | 320×320 | ≤ 512 KB | **APNG** (Discord's help page lists APNG/PNG, not GIF) | [Discord support](https://support.discord.com/hc/articles/4402687377815) |
| Discord emoji | `discord_emoji_128.gif` | 128×128 | ≤ 256 KB | GIF | third-party guides |
| Slack emoji | `slack_128.gif` | 128×128 | ≤ 128 KB | GIF | third-party guides |
| Telegram video sticker | `telegram_512.webm` | 512×512 | ≤ 256 KB, ≤ 3 s, ≤ 30 fps | WEBM, VP9 with alpha, no audio | [Telegram docs](https://core.telegram.org/stickers) |

Checked 2026-11-06. `sticker_pack.py` prints each file's size and `ok` / `OVER`; it lowers
the palette or bitrate automatically until the file fits.

For personal use (adding a GIF to "favourites" in WeChat, sending in a chat) any of the
GIFs work; the specs above are for publishing a sticker pack.

## Prompt (sticker sheet)

```text
Pixel-art STICKER sheet of the character in the reference image.
Keep its identity: {key features}. Front view.
Each ROW is one separate looping emotion sticker made of 4 frames (left to right, frame 4 loops back to frame 1). Exaggerated, instantly readable at small size: big face, bold outline, clear silhouette.
Row 1 {EMOTION}: {what the body and face do across 4 frames}.
Row 2 {EMOTION}: …
Row 3 {EMOTION}: …
Row 4 {EMOTION}: …

PIXEL STYLE
Crisp 16-bit game pixel art with clearly visible square pixels, 1px dark outline, restrained palette, gentle cel shading. No blur, no anti-aliasing, no gradients.

SHEET LAYOUT
Exactly 4 columns x 4 rows = 16 equal square cells in a square image. Same character size and position in every cell, feet on the same baseline, everything inside its cell with padding. No grid lines, borders, text, frame numbers, floor or shadow. Transparent background.
```

Second sheet: same prompt, four new emotions, and add the first sheet as a reference with
"match the character design, pixel size, palette and outline of the second reference exactly".

## Emotion ideas (4 frames each)

| Emotion | Frames |
|---|---|
| shy | blush, cover face with hands, peek out, hide again |
| angry | puffed cheeks, red face, steam puffs, stomp left / right |
| cry | streams of tears, wailing mouth, wobble left / right |
| heart | arms make a heart, small hearts float up and pop |
| smug | half-closed eyes, smirk, chin up, sparkle blinks |
| sleepy | eyes closed, head nods, a "z" bubble grows and floats |
| hello | big smile, wave left / right |
| shocked | small hop, wide eyes, open mouth, "!" pops above |
| thumbs up · facepalm · dance · eating · love-struck · dizzy | … |

Tips: upper-body or chibi full-body both work; keep motion inside the cell (stickers are
cropped tight); avoid tiny details that vanish at 128 px.
