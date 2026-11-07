#!/usr/bin/env python3
"""openai_imagegen — generate one sprite sheet with your own OpenAI API key.

Standard library only (no `openai` package needed).

  export OPENAI_API_KEY=sk-...           # never put the key in a file inside this repo
  python3 scripts/openai_imagegen.py --ref my_cat.jpg --prompt-file prompt.txt -o sheet.png
  python3 scripts/openai_imagegen.py --ref my_cat.jpg --prompt-file prompt.txt -o sheet.png --dry-run

With --ref the request goes to /v1/images/edits (reference image as input);
without it, to /v1/images/generations.

Background: some GPT Image API models reject `background=transparent`. The
default here is `--background auto` plus one line appended to the prompt asking
for a plain flat white background; sprite2gif.py removes white backgrounds
cleanly. Pass `--background transparent` if your model supports it.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

API = "https://api.openai.com/v1"
WHITE_BG_LINE = ("\n\nBACKGROUND OVERRIDE: use a plain flat pure white (#FFFFFF) background "
                 "in every cell instead of transparency.")


def multipart(fields: dict, files: list[tuple[str, str]]) -> tuple[bytes, str]:
    boundary = "----sprite" + uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        if v is None:
            continue
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for name, path in files:
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as fh:
            data = fh.read()
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: {mime}\r\n\r\n").encode()
        out += data + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt-file", required=True, help="filled prompt template (text file)")
    p.add_argument("--ref", action="append", default=[], help="reference image (repeatable)")
    p.add_argument("-o", "--out", default="sheet.png")
    p.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"),
                   help="GPT Image model name (default: $OPENAI_IMAGE_MODEL or gpt-image-2)")
    p.add_argument("--size", default="1024x1024", help="square works best for a 4x4 sheet")
    p.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    p.add_argument("--background", default="auto", choices=["auto", "opaque", "transparent"])
    p.add_argument("--dry-run", action="store_true", help="print the request instead of sending it")
    a = p.parse_args()

    with open(a.prompt_file, encoding="utf-8") as fh:
        prompt = fh.read().strip()
    if a.background != "transparent":
        prompt += WHITE_BG_LINE
    for r in a.ref:
        if not os.path.isfile(r):
            sys.exit(f"reference not found: {r}")

    fields = {"model": a.model, "prompt": prompt, "size": a.size, "quality": a.quality, "n": "1"}
    if a.background != "auto":
        fields["background"] = a.background
    if a.background == "transparent":
        fields["output_format"] = "png"

    if a.ref:
        url = f"{API}/images/edits"
        files = [("image[]", r) for r in a.ref]
    else:
        url = f"{API}/images/generations"
        files = []

    if a.dry_run:
        shown = dict(fields)
        shown["prompt"] = prompt[:160] + (f"... [{len(prompt)} chars]" if len(prompt) > 160 else "")
        print(json.dumps({"POST": url,
                          "headers": {"Authorization": "Bearer $OPENAI_API_KEY"},
                          "content_type": "multipart/form-data" if files else "application/json",
                          "fields": shown,
                          "files": [{"field": n, "path": f, "bytes": os.path.getsize(f)} for n, f in files],
                          "writes": os.path.abspath(a.out)}, indent=2))
        return 0

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Export it in your shell; never save it in this repo.")

    if files:
        body, ctype = multipart(fields, files)
    else:
        body, ctype = json.dumps({k: (int(v) if k == "n" else v) for k, v in fields.items()}).encode(), "application/json"
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        if "background" in msg and a.background == "transparent":
            msg += "\nHint: this model may not support transparent backgrounds; rerun without --background transparent."
        sys.exit(f"OpenAI API error {e.code}: {msg}")

    b64 = data["data"][0].get("b64_json")
    if not b64:
        sys.exit(f"no image in response: {json.dumps(data)[:400]}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as fh:
        fh.write(base64.b64decode(b64))
    print(os.path.abspath(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
