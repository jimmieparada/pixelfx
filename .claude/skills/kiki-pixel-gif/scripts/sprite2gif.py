#!/usr/bin/env python3
"""sprite2gif — turn a pixel-art sprite sheet into a clean looping GIF.

Slices a grid sprite sheet (default 4x4), removes the background, locks every
frame to one shared baseline + horizontal anchor so the character doesn't
jitter, checks the loop seam, and exports X-ready files:

  <name>_white.gif         white background GIF
  <name>_transparent.gif   transparent GIF (1-bit alpha, correct disposal)
  <name>_white.mp4         optional MP4 preview (--mp4), 3 loops
  <name>_sheet_transparent.png / <name>_sheet_white.png   cleaned sheets
  <name>_frames/frame_01.png ...                          aligned RGBA frames
  <name>_contact.png       contact sheet for a quick visual check
  <name>_report.json       QA numbers (seam score, jitter, sizes)

Requires: Python 3.9+, Pillow, numpy. ffmpeg only for --mp4.

Examples
  python3 sprite2gif.py sheet.png -o out/hero --fps 12
  python3 sprite2gif.py sheet.png -o out/hero --durations 220,110,110,90,...
  python3 sprite2gif.py sheet.png -o out/momo --anchor-y none   # jumps: keep drawn vertical motion
  python3 sprite2gif.py sheet.png -o out/momo --lift 0,0,0,0,.03,.12,.22,.28,.3,.26,.14   # add a jump arc
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

X_GIF_LIMIT = 15 * 1024 * 1024  # X accepts animated GIFs up to 15 MB


# ---------------------------------------------------------------- background
def to_rgba_clean(img: Image.Image, bg_tol: int) -> np.ndarray:
    """Return an RGBA array with a real alpha channel.

    If the sheet already has meaningful alpha (imagegen transparent_background),
    keep it and just hard-threshold soft edges. Otherwise remove the background
    by flood-filling near-background colour from the image border, so white
    details *inside* the character are preserved.
    """
    a = np.array(img.convert("RGBA")).astype(np.int16)
    alpha = a[..., 3]
    if (alpha < 250).mean() > 0.05:  # already transparent
        a[..., 3] = np.where(alpha >= 128, 255, 0)
        return a.astype(np.uint8)

    rgb = a[..., :3]
    # background colour = median of the border pixels
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    near = (np.abs(rgb - bg).max(axis=2) <= bg_tol)
    # flood fill from border through "near background" pixels
    from collections import deque
    H, W = near.shape
    seen = np.zeros_like(near)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if near[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if near[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and near[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    a[..., 3] = np.where(seen, 0, 255)
    return a.astype(np.uint8)


def despeckle(alpha: np.ndarray, min_px: int) -> np.ndarray:
    """Drop tiny opaque islands (stray pixels / bleed from neighbouring cells)."""
    if min_px <= 0:
        return alpha
    try:
        from scipy import ndimage  # optional
        lab, n = ndimage.label(alpha > 0)
        if n == 0:
            return alpha
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        keep = np.isin(lab, np.nonzero(sizes >= min_px)[0] + 1)
        return np.where(keep, alpha, 0).astype(alpha.dtype)
    except ImportError:
        return alpha


# ---------------------------------------------------------------- slicing
def find_cuts(alpha: np.ndarray, n: int, axis: int) -> list[int]:
    """Split positions along an axis. Starts from the even split and nudges
    each cut to the emptiest line nearby, which fixes sheets where the model
    drew slightly uneven cells."""
    size = alpha.shape[1 - axis] if axis == 0 else alpha.shape[0]
    occ = (alpha > 0).sum(axis=axis)  # axis=0 -> per column, axis=1 -> per row
    step = size / n
    cuts = [0]
    win = int(step * 0.12)
    for i in range(1, n):
        c = int(round(i * step))
        lo, hi = max(1, c - win), min(size - 1, c + win)
        seg = occ[lo:hi]
        # prefer the emptiest line, tie-break by distance to the even split
        best = min(range(len(seg)), key=lambda k: (seg[k], abs(lo + k - c)))
        cuts.append(lo + best)
    cuts.append(size)
    return cuts


def slice_sheet(rgba: np.ndarray, cols: int, rows: int) -> list[np.ndarray]:
    xs = find_cuts(rgba[..., 3], cols, axis=0)
    ys = find_cuts(rgba[..., 3], rows, axis=1)
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append(rgba[ys[r]:ys[r + 1], xs[c]:xs[c + 1]].copy())
    return cells


def keep_main_blob(cell: np.ndarray, margin: int) -> np.ndarray:
    """Clear a thin margin at the cell border to kill bleed from neighbours."""
    if margin > 0:
        cell[:margin, :, 3] = 0; cell[-margin:, :, 3] = 0
        cell[:, :margin, 3] = 0; cell[:, -margin:, 3] = 0
    return cell


# ---------------------------------------------------------------- anchors
def anchors(cell: np.ndarray, x_mode: str) -> tuple[float, float] | None:
    m = cell[..., 3] > 0
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    # baseline = lowest row that has a meaningful amount of pixels (ignores 1px specks)
    row_counts = m.sum(axis=1)
    thresh = max(2, int(row_counts.max() * 0.04))
    solid = np.nonzero(row_counts >= thresh)[0]
    base = float(solid.max()) if len(solid) else float(ys.max())
    if x_mode == "feet":
        top = base - (base - ys.min()) * 0.30  # lowest 30% of the body
        sel = ys >= top
        cx = float(np.median(xs[sel]))
    elif x_mode == "mass":
        cx = float(np.median(xs))
    elif x_mode == "bbox":
        cx = (xs.min() + xs.max()) / 2.0
    else:
        cx = cell.shape[1] / 2.0
    return cx, base


# ---------------------------------------------------------------- main
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sheet")
    p.add_argument("-o", "--out", required=True, help="output path prefix, e.g. out/hero")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--rows", type=int, default=4)
    p.add_argument("--fps", type=float, default=12, help="uniform frame rate (ignored if --durations)")
    p.add_argument("--durations", help="comma-separated per-frame ms, e.g. 200,100,80,...")
    p.add_argument("--anchor-x", choices=["feet", "mass", "bbox", "none"], default="feet",
                   help="horizontal lock: feet (default) | mass | bbox | none")
    p.add_argument("--anchor-y", choices=["baseline", "none"], default="baseline",
                   help="baseline (default) locks feet to one ground line; none keeps vertical motion (jumps)")
    p.add_argument("--lift", help="comma-separated per-frame height above the baseline, as a fraction of "
                   "cell height (e.g. jump arc 0,0,0,0,.03,.12,.22,.28,.3,.26,.14,0,...). Applied after alignment")
    p.add_argument("--max-jitter", type=int, default=0,
                   help="only correct offsets up to N px (0 = always correct). Use for jumps/attacks with big lunges")
    p.add_argument("--size", type=int, default=480, help="output canvas long edge in px (nearest-neighbour upscale)")
    p.add_argument("--pad", type=int, default=16, help="padding around the union bbox before scaling")
    p.add_argument("--bg", default="#FFFFFF", help="background colour for the white version")
    p.add_argument("--bg-tol", type=int, default=28, help="tolerance for background removal on opaque sheets")
    p.add_argument("--edge-margin", type=int, default=3, help="px cleared at each cell border (anti-bleed)")
    p.add_argument("--min-blob", type=int, default=12, help="drop opaque islands smaller than this (needs scipy)")
    p.add_argument("--colors", type=int, default=128, help="GIF palette size (lower = smaller file)")
    p.add_argument("--max-mb", type=float, default=5.0, help="shrink until the GIF is under this size")
    p.add_argument("--mp4", action="store_true", help="also write a 3-loop MP4 preview (needs ffmpeg)")
    p.add_argument("--trim-last", action="store_true",
                   help="drop the last frame if it duplicates the first (avoids a stutter at the loop point)")
    a = p.parse_args()

    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.basename(a.out)

    sheet = Image.open(a.sheet)
    rgba = to_rgba_clean(sheet, a.bg_tol)
    cells = slice_sheet(rgba, a.cols, a.rows)
    for c in cells:
        keep_main_blob(c, a.edge_margin)
        c[..., 3] = despeckle(c[..., 3], a.min_blob)

    n = len(cells)
    anc = [anchors(c, a.anchor_x) for c in cells]
    empty = [i + 1 for i, v in enumerate(anc) if v is None]
    if empty:
        print(f"WARNING: empty frames {empty} — check the sheet grid", file=sys.stderr)
    valid = [v for v in anc if v is not None]
    ref_x = float(np.median([v[0] for v in valid]))
    ref_y = float(np.median([v[1] for v in valid]))

    # place every cell on a shared big canvas so its anchor lands on (ref_x, ref_y)
    ch = max(c.shape[0] for c in cells); cw = max(c.shape[1] for c in cells)
    CW, CH = cw * 2, ch * 2
    ox, oy = cw // 2, ch // 2
    placed, offsets = [], []
    lifts = [float(x) for x in a.lift.split(",")] if a.lift else []
    lifts += [0.0] * (len(cells) - len(lifts))
    for c, v in zip(cells, anc):
        dx = dy = 0.0
        if v is not None:
            if a.anchor_x != "none":
                dx = ref_x - v[0]
            if a.anchor_y == "baseline":
                dy = ref_y - v[1]
            if a.max_jitter > 0:
                dx = dx if abs(dx) <= a.max_jitter else 0.0
                dy = dy if abs(dy) <= a.max_jitter else 0.0
        if lifts:
            dy -= lifts[len(offsets)] * ch
        dx, dy = int(round(dx)), int(round(dy))
        offsets.append((dx, dy))
        canvas = np.zeros((CH, CW, 4), np.uint8)
        h, w = c.shape[:2]
        canvas[oy + dy:oy + dy + h, ox + dx:ox + dx + w] = c
        placed.append(canvas)

    # crop all frames to the union bbox (+pad) so framing is identical
    union = np.zeros((CH, CW), bool)
    for f in placed:
        union |= f[..., 3] > 0
    ys, xs = np.nonzero(union)
    x0, x1 = max(0, xs.min() - a.pad), min(CW, xs.max() + 1 + a.pad)
    y0, y1 = max(0, ys.min() - a.pad), min(CH, ys.max() + 1 + a.pad)
    # square-ish canvas looks best on X; widen the short side
    w, h = x1 - x0, y1 - y0
    if w < h:
        extra = h - w; x0 = max(0, x0 - extra // 2); x1 = min(CW, x0 + h)
    else:
        extra = w - h; y0 = max(0, y0 - extra); y1 = min(CH, y0 + w)  # add room on top
    frames = [Image.fromarray(f[y0:y1, x0:x1]) for f in placed]

    if a.trim_last and n > 2:
        d = np.abs(np.asarray(frames[-1], np.int16) - np.asarray(frames[0], np.int16)).mean()
        if d < 1.0:
            frames = frames[:-1]

    # durations
    if a.durations:
        durs = [int(x) for x in a.durations.split(",")]
        if len(durs) < len(frames):
            durs += [durs[-1]] * (len(frames) - len(durs))
        durs = durs[:len(frames)]
    else:
        durs = [int(round(1000 / a.fps))] * len(frames)
    durs = [max(20, int(round(d / 10)) * 10) for d in durs]  # GIF timing is in 10 ms units

    # loop-seam check: last->first difference vs. typical neighbour difference
    def diff(i, j):
        A = np.asarray(frames[i]).astype(np.int16); B = np.asarray(frames[j]).astype(np.int16)
        ma = (A[..., 3] > 0) | (B[..., 3] > 0)
        return float((np.abs(A - B)[ma].mean()) if ma.any() else 0.0)
    neigh = [diff(i, i + 1) for i in range(len(frames) - 1)]
    seam = diff(len(frames) - 1, 0)
    med = float(np.median(neigh)) if neigh else 0.0
    seam_ratio = seam / med if med else 0.0

    def render(size: int, colors: int):
        s = size / max(frames[0].size)
        tw, th = int(frames[0].width * s), int(frames[0].height * s)
        big = [f.resize((tw, th), Image.NEAREST) for f in frames]
        white = []
        for f in big:
            bg = Image.new("RGBA", f.size, a.bg); bg.alpha_composite(f)
            white.append(bg.convert("RGB"))
        # shared palette keeps colours stable between frames (no flicker)
        strip = Image.new("RGB", (tw, th * len(white)))
        for i, f in enumerate(white):
            strip.paste(f, (0, i * th))
        pal = strip.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
        wq = [f.quantize(palette=pal, dither=Image.NONE) for f in white]
        # transparent: reserve index 0 for transparency
        tpal = strip.quantize(colors=min(255, colors), method=Image.MEDIANCUT, dither=Image.NONE)
        tq = []
        for f, src in zip(white, big):
            q = f.quantize(palette=tpal, dither=Image.NONE)
            arr = np.asarray(q).astype(np.int16) + 1
            arr[np.asarray(src)[..., 3] == 0] = 0
            a8 = arr.astype(np.uint8); im = Image.frombytes("P", (a8.shape[1], a8.shape[0]), a8.tobytes())
            pl = [0, 0, 0] + tpal.getpalette()[: 255 * 3]
            im.putpalette(pl)
            im.info["transparency"] = 0
            tq.append(im)
        return big, wq, tq

    size, colors = a.size, a.colors
    while True:
        big, wq, tq = render(size, colors)
        wpath = f"{a.out}_white.gif"; tpath = f"{a.out}_transparent.gif"
        wq[0].save(wpath, save_all=True, append_images=wq[1:], duration=durs, loop=0, disposal=1, optimize=False)
        tq[0].save(tpath, save_all=True, append_images=tq[1:], duration=durs, loop=0, disposal=2,
                   transparency=0, optimize=False)
        mb = max(os.path.getsize(wpath), os.path.getsize(tpath)) / 1024 / 1024
        if mb <= a.max_mb or size <= 240:
            break
        if colors > 64:
            colors = 64
        else:
            size = int(size * 0.85)

    # frames + sheets + contact
    fdir = f"{a.out}_frames"; os.makedirs(fdir, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(fdir, f"frame_{i + 1:02d}.png"))
    fw, fh = frames[0].size
    cols = a.cols
    rows_out = (len(frames) + cols - 1) // cols
    sheet_t = Image.new("RGBA", (fw * cols, fh * rows_out), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet_t.paste(f, ((i % cols) * fw, (i // cols) * fh))
    sheet_t.save(f"{a.out}_sheet_transparent.png")
    sw = Image.new("RGBA", sheet_t.size, a.bg); sw.alpha_composite(sheet_t)
    sw.convert("RGB").save(f"{a.out}_sheet_white.png")
    contact = sw.convert("RGB").resize((sw.width * 2, sw.height * 2), Image.NEAREST)
    contact.save(f"{a.out}_contact.png")

    if a.mp4 and shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "2", "-i", wpath,
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=neighbor,format=yuv420p",
                        "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", f"{a.out}_white.mp4"],
                       check=False)

    report = {
        "frames": len(frames),
        "grid": f"{a.cols}x{a.rows}",
        "loop_ms": sum(durs),
        "durations_ms": durs,
        "output_px": list(wq[0].size),
        "palette_colors": colors,
        "white_gif_mb": round(os.path.getsize(wpath) / 1048576, 2),
        "transparent_gif_mb": round(os.path.getsize(tpath) / 1048576, 2),
        "x_ready": max(os.path.getsize(wpath), os.path.getsize(tpath)) < X_GIF_LIMIT,
        "empty_frames": empty,
        "alignment_offsets_px": offsets,
        "seam_diff": round(seam, 2),
        "median_neighbor_diff": round(med, 2),
        "seam_ratio": round(seam_ratio, 2),
        "seam_ok": seam_ratio <= 1.8,
    }
    with open(f"{a.out}_report.json", "w") as fh_:
        json.dump(report, fh_, indent=2)
    print(json.dumps({k: report[k] for k in ("frames", "loop_ms", "output_px", "white_gif_mb",
                                              "transparent_gif_mb", "seam_ratio", "seam_ok", "empty_frames")}))
    if not report["seam_ok"]:
        print("WARNING: last frame -> first frame jump is larger than normal. "
              "Regenerate, or try --trim-last / a ping-pong edit.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
