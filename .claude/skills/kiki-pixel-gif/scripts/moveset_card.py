#!/usr/bin/env python3
"""moveset_card — lay out a character's moves as a retro game-manual "MOVE LIST" card.

Input: the output prefixes written by sprite2gif.py (each has <prefix>_frames/ and
<prefix>_report.json). Output: an animated card GIF + MP4 and a still PNG, sized for X
(1600x900 by default).

  python3 scripts/moveset_card.py -o out/malfoid_moveset \
      --title "MOVE LIST" --name "MALFOID" \
      --move "out/mv_idle|IDLE|Unbothered|—|Twirls her wand, waiting for you to blink first." \
      --move "out/mv_basic|BASIC|Emerald Spark|A|Quick flick, small green bolt." \
      --move "out/mv_ultimate|ULTIMATE|Serpent Surge|↓↘→ + A+B|Summons an emerald serpent. Full screen hit."

--move format:  prefix|TAG|Move name|Input command|One-line description
Optional --stars "1,2,5" sets a power rating per move.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    "paper": (246, 236, 214), "paper2": (236, 222, 192), "ink": (40, 30, 38),
    "accent": (232, 72, 54), "gold": (240, 178, 40), "panel": (255, 250, 238), "muted": (120, 100, 92),
}
TAG_COLORS = [(76, 140, 220), (64, 168, 104), (232, 72, 54), (150, 90, 200)]


def font(size: int, bold: bool = True):
    for path, idx in (("/System/Library/Fonts/Menlo.ttc", 1 if bold else 0),
                      ("/System/Library/Fonts/PingFang.ttc", 0),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 0),
                      ("C:/Windows/Fonts/consolab.ttf", 0)):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=idx)
            except OSError:
                pass
    return ImageFont.load_default()


def pixel_text(text: str, px: int, color, scale: int, shadow=None) -> Image.Image:
    """Draw text at a small size and upscale with nearest neighbour: chunky pixel type."""
    f = font(px)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    b = d0.textbbox((0, 0), text, font=f)
    w, h = b[2] - b[0] + 2, b[3] - b[1] + 2
    im = Image.new("RGBA", (w + 1, h + 1), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((1 - b[0] + 1, 1 - b[1] + 1), text, font=f, fill=shadow)
    d.text((1 - b[0], 1 - b[1]), text, font=f, fill=color)
    a = np.array(im); a[..., 3] = np.where(a[..., 3] > 100, 255, 0); im = Image.fromarray(a)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def wrap(text: str, px: int, scale: int, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if pixel_text(t, px, (0, 0, 0), scale).width <= max_w:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


STAR = ["..#..", "..#..", "#####", ".###.", ".#.#.", "#...#"]


def pixel_star(color, cell: int) -> Image.Image:
    im = Image.new("RGBA", (5 * cell, len(STAR) * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(STAR):
        for x, ch in enumerate(row):
            if ch == "#":
                d.rectangle((x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1), fill=color)
    return im


def pixel_rect(d: ImageDraw.ImageDraw, box, fill, border, bw: int):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=border)
    d.rectangle((x0 + bw, y0 + bw, x1 - bw, y1 - bw), fill=fill)
    # notched corners for a pixel-game look
    for cx, cy in ((x0, y0), (x1 - bw + 1, y0), (x0, y1 - bw + 1), (x1 - bw + 1, y1 - bw + 1)):
        d.rectangle((cx, cy, cx + bw - 1, cy + bw - 1), fill=PALETTE["paper"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--title", default="MOVE LIST")
    p.add_argument("--name", required=True, help="character name shown on the card")
    p.add_argument("--move", action="append", required=True)
    p.add_argument("--stars", help="comma-separated power rating 1-5 per move")
    p.add_argument("--footer", default="PRESS START")
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--logo", help="optional watermark PNG, placed bottom-right at 60%% opacity")
    a = p.parse_args()

    moves = []
    for m in a.move:
        parts = [x.strip() for x in m.split("|")]
        parts += [""] * (5 - len(parts))
        prefix, tag, name, cmd, desc = parts[:5]
        frames = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(prefix + "_frames/frame_*.png"))]
        if not frames:
            sys.exit(f"no frames found for {prefix}_frames/")
        durs = json.load(open(prefix + "_report.json"))["durations_ms"]
        moves.append(dict(tag=tag, name=name, cmd=cmd, desc=desc, frames=frames, durs=durs))
    stars = [int(x) for x in a.stars.split(",")] if a.stars else [1 + 2 * i for i in range(len(moves))]

    W, H = a.width, a.height
    base = Image.new("RGB", (W, H), PALETTE["paper"])
    d = ImageDraw.Draw(base)
    # paper texture: faint scanlines
    for y in range(0, H, 6):
        d.line([(0, y), (W, y)], fill=PALETTE["paper2"], width=1)
    # outer double border
    d.rectangle((14, 14, W - 15, H - 15), outline=PALETTE["ink"], width=6)
    d.rectangle((28, 28, W - 29, H - 29), outline=PALETTE["ink"], width=2)
    # header
    title = pixel_text(a.title, 16, PALETTE["ink"], 4, shadow=PALETTE["gold"])
    base.paste(title, (60, 52), title)
    nm = pixel_text(a.name, 18, (255, 255, 255), 2)
    bx = W - 60 - nm.width - 36
    d.rectangle((bx, 58, W - 60, 58 + nm.height + 22), fill=PALETTE["accent"])
    base.paste(nm, (bx + 18, 69), nm)
    d.rectangle((60, 60 + title.height + 14, W - 60, 60 + title.height + 20), fill=PALETTE["ink"])

    n = len(moves)
    top = 60 + title.height + 44
    gap = 28
    pw = (W - 120 - gap * (n - 1)) // n
    ph = H - top - 92
    sprite = min(pw - 40, int(ph * 0.56))
    slots = []
    for i, m in enumerate(moves):
        x0 = 60 + i * (pw + gap)
        pixel_rect(d, (x0, top, x0 + pw, top + ph), PALETTE["panel"], PALETTE["ink"], 6)
        tc = TAG_COLORS[i % len(TAG_COLORS)]
        tag = pixel_text(m["tag"], 13, (255, 255, 255), 2)
        d.rectangle((x0 + 18, top + 18, x0 + 18 + tag.width + 20, top + 18 + tag.height + 12), fill=tc)
        base.paste(tag, (x0 + 28, top + 24), tag)
        # power stars
        sx = x0 + pw - 18
        for k in reversed(range(5)):
            on = k < stars[i]
            s = pixel_star(PALETTE["gold"] if on else (214, 200, 172), 4)
            sx -= s.width + 2
            base.paste(s, (sx, top + 22), s)
        sy = top + 18 + tag.height + 24
        # sprite stage
        d.rectangle((x0 + 20, sy, x0 + pw - 20, sy + sprite), fill=(255, 255, 255))
        d.line([(x0 + 40, sy + sprite - 14), (x0 + pw - 40, sy + sprite - 14)], fill=PALETTE["paper2"], width=4)
        slots.append((x0 + pw // 2, sy, sprite))
        ty = sy + sprite + 16
        nm_im = pixel_text(m["name"].upper(), 11, PALETTE["ink"], 3)
        if nm_im.width > pw - 40:
            nm_im = pixel_text(m["name"].upper(), 11, PALETTE["ink"], 2)
        base.paste(nm_im, (x0 + 22, ty), nm_im)
        ty += nm_im.height + 10
        if m["cmd"]:
            lab = pixel_text("INPUT", 11, PALETTE["muted"], 2)
            base.paste(lab, (x0 + 22, ty + 4), lab)
            cmd = pixel_text(m["cmd"], 15, PALETTE["accent"], 2)
            base.paste(cmd, (x0 + 30 + lab.width, ty), cmd)
            ty += cmd.height + 10
        for line in wrap(m["desc"], 9, 2, pw - 44)[:3]:
            li = pixel_text(line, 9, PALETTE["ink"], 2)
            base.paste(li, (x0 + 22, ty), li)
            ty += li.height + 4
    foot = pixel_text(a.footer, 9, PALETTE["ink"], 3)
    base.paste(foot, ((W - foot.width) // 2, H - 66), foot)

    if a.logo:
        lg = Image.open(a.logo).convert("RGBA"); lw = 58
        lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
        la = np.array(lg); la[..., 3] = (la[..., 3] * 0.6).astype(np.uint8); lg = Image.fromarray(la)
        base.paste(lg, (W - lw - 44, H - lg.height - 34), lg)

    # timeline: give every move an integer number of loops inside one card loop
    loops = [sum(m["durs"]) for m in moves]
    T = max(loops) * 2
    STEP = 40
    tracks = []
    for m, L in zip(moves, loops):
        reps = max(1, round(T / L))
        scale = (T / reps) / L
        tracks.append((m["frames"], [x * scale for x in m["durs"]]))
    out = []
    for t in range(0, int(T), STEP):
        c = base.copy()
        for (frames, durs), (cx, sy, sz) in zip(tracks, slots):
            tm = t % sum(durs); k = 0; acc = 0
            while k < len(durs) - 1 and acc + durs[k] <= tm:
                acc += durs[k]; k += 1
            f = frames[k].resize((sz, sz), Image.NEAREST)
            c.paste(f, (cx - sz // 2, sy), f)
        out.append(c)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    # still = each move at its peak-ish frame (frame 9)
    still = base.copy()
    for (frames, _), (cx, sy, sz) in zip(tracks, slots):
        f = frames[min(8, len(frames) - 1)].resize((sz, sz), Image.NEAREST)
        still.paste(f, (cx - sz // 2, sy), f)
    still.save(a.out + ".png")
    strip = Image.new("RGB", (W, H * 4))
    for j in range(4):
        strip.paste(out[j * len(out) // 4], (0, j * H))
    pal = strip.quantize(colors=200, method=Image.MEDIANCUT, dither=Image.NONE)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in out]
    q[0].save(a.out + ".gif", save_all=True, append_images=q[1:], duration=STEP, loop=0, optimize=True)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "1", "-i", a.out + ".gif",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=neighbor,format=yuv420p",
                        "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", a.out + ".mp4"], check=False)
    print(json.dumps({"gif": a.out + ".gif", "png": a.out + ".png", "frames": len(out),
                      "loop_ms": int(T), "gif_mb": round(os.path.getsize(a.out + ".gif") / 1048576, 2)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
