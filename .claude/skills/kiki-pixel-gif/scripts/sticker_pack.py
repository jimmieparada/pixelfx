#!/usr/bin/env python3
"""sticker_pack — turn a pixel sticker sheet into ready-to-upload sticker files.

Sticker sheet layout: each ROW is one sticker (one emotion), each column one frame.
Default 4x4 = 4 stickers x 4 frames. Every sticker is aligned on its own, cropped to a
square and exported in the sizes each platform accepts (see references/sticker-mode.md):

  <out>/<name>/wechat_240.gif          WeChat sticker, 240x240 GIF, <= 500 KB
  <out>/<name>/discord_sticker_320.png Discord sticker, 320x320 APNG, <= 512 KB
  <out>/<name>/discord_emoji_128.gif   Discord emoji, 128x128 GIF, <= 256 KB
  <out>/<name>/slack_128.gif           Slack emoji, 128x128 GIF, <= 128 KB
  <out>/<name>/telegram_512.webm       Telegram video sticker, 512x512 VP9 + alpha, <= 256 KB, <= 3 s
  <out>/preview.gif                    all stickers in one grid on white (for posting)

All animated files are transparent except preview.gif. No text unless you pass --captions.

  python3 scripts/sticker_pack.py stickers_a.png -o out/momo --names shy,angry,cry,heart
  python3 scripts/sticker_pack.py stickers_a.png stickers_b.png -o out/momo --names shy,angry,cry,heart,smug,sleepy,hello,shocked
  python3 scripts/sticker_pack.py stickers_a.png -o out/momo --names shy,angry,cry,heart \
      --captions "so shy,grr,waaah,love u"
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprite2gif import to_rgba_clean, slice_sheet, despeckle, anchors  # noqa: E402

PLATFORMS = [
    # name, file, size, kind, max_bytes
    ("wechat", "wechat_240.gif", 240, "gif", 500 * 1024),
    ("discord_sticker", "discord_sticker_320.png", 320, "apng", 512 * 1024),
    ("discord_emoji", "discord_emoji_128.gif", 128, "gif", 256 * 1024),
    ("slack", "slack_128.gif", 128, "gif", 128 * 1024),
    ("telegram", "telegram_512.webm", 512, "webm", 256 * 1024),
]


def find_font(size: int) -> ImageFont.FreeTypeFont:
    for path, idx in (("/System/Library/Fonts/Menlo.ttc", 1), ("/System/Library/Fonts/PingFang.ttc", 0),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 0), ("C:/Windows/Fonts/consolab.ttf", 0)):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=idx)
            except OSError:
                continue
    return ImageFont.load_default()


def pixel_caption(text: str, width: int) -> Image.Image:
    """Render text small, then upscale with nearest neighbour so it looks like pixel type."""
    small_w = max(32, width // 4)
    font = find_font(12)
    tmp = Image.new("RGBA", (small_w * 3, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for dx in (-1, 0, 1):  # 1px dark outline
        for dy in (-1, 0, 1):
            d.text((2 - bbox[0] + dx, 2 - bbox[1] + dy), text, font=font, fill=(30, 20, 30, 255))
    d.text((2 - bbox[0], 2 - bbox[1]), text, font=font, fill=(255, 255, 255, 255))
    # binarise alpha -> crisp
    a = np.array(img); a[..., 3] = np.where(a[..., 3] > 110, 255, 0); img = Image.fromarray(a)
    scale = max(1, int((width * 0.9) // img.width))
    scale = min(scale, max(1, width // 60))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def build_sticker(cells: list[np.ndarray], pad: int) -> list[Image.Image]:
    anc = [anchors(c, "mass") for c in cells]
    valid = [v for v in anc if v]
    rx = float(np.median([v[0] for v in valid])); ry = float(np.median([v[1] for v in valid]))
    ch = max(c.shape[0] for c in cells); cw = max(c.shape[1] for c in cells)
    CW, CH = cw * 2, ch * 2; ox, oy = cw // 2, ch // 2
    placed = []
    for c, v in zip(cells, anc):
        dx = int(round(rx - v[0])) if v else 0
        dy = int(round(ry - v[1])) if v else 0
        canvas = np.zeros((CH, CW, 4), np.uint8)
        h, w = c.shape[:2]
        canvas[oy + dy:oy + dy + h, ox + dx:ox + dx + w] = c
        placed.append(canvas)
    union = np.zeros((CH, CW), bool)
    for f in placed:
        union |= f[..., 3] > 0
    ys, xs = np.nonzero(union)
    x0, x1, y0, y1 = xs.min() - pad, xs.max() + 1 + pad, ys.min() - pad, ys.max() + 1 + pad
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    x0, y0 = cx - side // 2, cy - side // 2
    out = []
    for f in placed:
        im = Image.fromarray(f)
        out.append(im.crop((x0, y0, x0 + side, y0 + side)))  # crop pads with transparency
    return out


def frames_at(frames: list[Image.Image], size: int, caption: Image.Image | None) -> list[Image.Image]:
    res = []
    for f in frames:
        g = f.resize((size, size), Image.NEAREST)
        if caption is not None:
            cap = caption
            if cap.width > size:
                s = size / cap.width
                cap = cap.resize((max(1, int(cap.width * s)), max(1, int(cap.height * s))), Image.NEAREST)
            g.alpha_composite(cap, ((size - cap.width) // 2, size - cap.height - max(2, size // 40)))
        res.append(g)
    return res


def save_gif(frames: list[Image.Image], path: str, dur: int, colors: int, transparent: bool = True) -> None:
    w, h = frames[0].size
    strip = Image.new("RGB", (w, h * len(frames)), (255, 255, 255))
    for i, f in enumerate(frames):
        bg = Image.new("RGBA", f.size, (255, 255, 255, 255)); bg.alpha_composite(f)
        strip.paste(bg.convert("RGB"), (0, i * h))
    pal = strip.quantize(colors=min(255, colors), method=Image.MEDIANCUT, dither=Image.NONE)
    out = []
    for f in frames:
        bg = Image.new("RGBA", f.size, (255, 255, 255, 255)); bg.alpha_composite(f)
        q = np.asarray(bg.convert("RGB").quantize(palette=pal, dither=Image.NONE)).astype(np.int16)
        if transparent:
            q = q + 1
            q[np.asarray(f)[..., 3] == 0] = 0
            pl = [0, 0, 0] + pal.getpalette()[:255 * 3]
        else:
            pl = pal.getpalette()
        a8 = q.astype(np.uint8)
        im = Image.frombytes("P", (w, h), a8.tobytes()); im.putpalette(pl)
        out.append(im)
    kw = dict(save_all=True, append_images=out[1:], duration=dur, loop=0, optimize=False)
    if transparent:
        kw.update(transparency=0, disposal=2)
    out[0].save(path, **kw)


def save_platform(frames, kind, path, dur, max_bytes) -> int:
    if kind == "gif":
        for colors in (128, 64, 32, 16):
            save_gif(frames, path, dur, colors)
            if os.path.getsize(path) <= max_bytes:
                break
    elif kind == "apng":
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=dur, loop=0,
                       disposal=1, blend=0, optimize=True)
        if os.path.getsize(path) > max_bytes:  # fall back to a reduced palette
            q = [f.quantize(colors=64, method=Image.FASTOCTREE).convert("RGBA") for f in frames]
            for f, src in zip(q, frames):
                f.putalpha(src.getchannel("A"))
            q[0].save(path, save_all=True, append_images=q[1:], duration=dur, loop=0, disposal=1, blend=0, optimize=True)
    elif kind == "webm":
        if not shutil.which("ffmpeg"):
            print("  skip telegram: ffmpeg not found", file=sys.stderr); return 0
        tmp = tempfile.mkdtemp()
        # repeat the loop so the clip is ~1.5-3 s (Telegram plays it looped anyway)
        reps = max(1, min(int(2400 // (dur * len(frames))), 8))
        seq = frames * reps
        for i, f in enumerate(seq):
            f.save(os.path.join(tmp, f"f{i:03d}.png"))
        fps = 1000 / dur
        for br in ("400k", "250k", "150k", "90k"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"{fps:.3f}", "-i", os.path.join(tmp, "f%03d.png"),
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", br, "-an", "-r", "30",
                            "-t", "2.99", path], check=True)
            if os.path.getsize(path) <= max_bytes:
                break
        shutil.rmtree(tmp, ignore_errors=True)
    return os.path.getsize(path) if os.path.exists(path) else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sheets", nargs="+", help="one or more sticker sheets (rows are concatenated)")
    p.add_argument("-o", "--out", required=True, help="output folder")
    p.add_argument("--cols", type=int, default=4, help="frames per sticker")
    p.add_argument("--rows", type=int, default=4, help="stickers per sheet")
    p.add_argument("--names", help="comma-separated sticker names, one per row")
    p.add_argument("--captions", help="optional comma-separated captions, one per row (empty = no text)")
    p.add_argument("--ms", type=int, default=180, help="ms per frame")
    p.add_argument("--pad", type=int, default=10)
    p.add_argument("--platforms", default="wechat,discord_sticker,discord_emoji,slack,telegram")
    a = p.parse_args()

    total = a.rows * len(a.sheets)
    names = (a.names.split(",") if a.names else [f"sticker_{i + 1}" for i in range(total)])
    caps = (a.captions.split(",") if a.captions else [""] * total)
    want = set(a.platforms.split(","))
    os.makedirs(a.out, exist_ok=True)

    cells = []
    for sh in a.sheets:
        cells += slice_sheet(to_rgba_clean(Image.open(sh), 28), a.cols, a.rows)
    for c in cells:
        c[:3, :, 3] = 0; c[-3:, :, 3] = 0; c[:, :3, 3] = 0; c[:, -3:, 3] = 0
        c[..., 3] = despeckle(c[..., 3], 12)

    previews = []
    for r in range(total):
        name = names[r].strip() if r < len(names) else f"sticker_{r + 1}"
        cap_text = caps[r].strip() if r < len(caps) else ""
        frames = build_sticker(cells[r * a.cols:(r + 1) * a.cols], a.pad)
        d = os.path.join(a.out, name); os.makedirs(d, exist_ok=True)
        line = [name]
        for pname, fname, size, kind, maxb in PLATFORMS:
            if pname not in want:
                continue
            cap = pixel_caption(cap_text, size) if cap_text else None
            fr = frames_at(frames, size, cap)
            nbytes = save_platform(fr, kind, os.path.join(d, fname), a.ms, maxb)
            ok = "ok" if 0 < nbytes <= maxb else "OVER"
            line.append(f"{pname} {nbytes // 1024}KB {ok}")
        previews.append(frames_at(frames, 240, pixel_caption(cap_text, 240) if cap_text else None))
        print(" | ".join(line))

    # preview grid on white, for posting
    n = len(previews); cols = min(4, n); rows = (n + cols - 1) // cols
    grid = []
    for i in range(a.cols):
        g = Image.new("RGBA", (cols * 240, rows * 240), (255, 255, 255, 255))
        for k, fr in enumerate(previews):
            g.alpha_composite(fr[i], ((k % cols) * 240, (k // cols) * 240))
        grid.append(g)
    save_gif(grid, os.path.join(a.out, "preview.gif"), a.ms, 128, transparent=False)
    print("preview:", os.path.join(a.out, "preview.gif"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
