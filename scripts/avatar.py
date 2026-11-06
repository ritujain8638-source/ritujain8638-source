"""Renders your GitHub profile picture into a circular SVG with an animated ring.
Needs Pillow (the workflow installs it). Output: assets/avatar.svg"""
import base64
import io
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from theme import *          # noqa: E402,F401
import ghapi                 # noqa: E402

ROOT = Path(__file__).parent.parent
N = 48          # dots per side (for halftone mode)
CELL = 4.5      # px per dot cell


def fetch_avatar():
    local_path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("AVATAR_FILE")
    if local_path and os.path.exists(local_path):
        return Image.open(local_path).convert("RGB")
    url = ghapi.rest(f"/users/{ghapi.USER}")["avatar_url"]
    url += ("&" if "?" in url else "?") + "s=240"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-gen"})
    with urllib.request.urlopen(req, timeout=30, context=ghapi.SSL_CTX) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def build_photo(img):
    size = int(N * CELL)
    pad = 16
    W = int(size + 2 * pad)
    c, R = W / 2, size / 2
    fitted = ImageOps.fit(img, (size * 2, size * 2), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    fitted.save(buf, format="JPEG", quality=90, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    css = (".ring{transform-box:fill-box;transform-origin:center;animation:spin 28s linear infinite}"
           "@keyframes spin{to{transform:rotate(360deg)}}"
           "@media (prefers-reduced-motion:reduce){.ring{animation:none}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}" '
            f'role="img" aria-label="avatar"><style>{css}</style>'
            f'<defs><clipPath id="c"><circle cx="{c}" cy="{c}" r="{R}"/></clipPath></defs>'
            f'<circle class="ring" cx="{c}" cy="{c}" r="{R + 8}" fill="none" stroke="{ACCENT}" '
            f'stroke-width="1.5" stroke-dasharray="2 8" stroke-linecap="round"/>'
            f'<circle cx="{c}" cy="{c}" r="{R + 2}" fill="none" stroke="{BORDER}" stroke-width="1.5"/>'
            f'<circle cx="{c}" cy="{c}" r="{R}" fill="{BG}"/>'
            f'<image href="data:image/jpeg;base64,{b64}" x="{pad}" y="{pad}" '
            f'width="{size}" height="{size}" preserveAspectRatio="xMidYMid slice" clip-path="url(#c)"/>'
            f'</svg>')


def build_halftone(img):
    gray = ImageOps.autocontrast(ImageOps.grayscale(ImageOps.fit(img, (N, N))))
    size = N * CELL
    pad = 16
    W = int(size + 2 * pad)
    c, R = W / 2, size / 2
    groups = [[] for _ in RAMP]
    for y in range(N):
        for x in range(N):
            v = gray.getpixel((x, y)) / 255
            if v < 0.12:
                continue
            r = CELL * 0.52 * v ** 0.9
            groups[min(len(RAMP) - 1, int(v * len(RAMP)))].append(
                f'<circle cx="{pad + (x + .5) * CELL:.1f}" cy="{pad + (y + .5) * CELL:.1f}" r="{r:.2f}"/>')
    body = "".join(f'<g fill="{RAMP[i]}">{"".join(g)}</g>' for i, g in enumerate(groups) if g)
    css = (".ring{transform-box:fill-box;transform-origin:center;animation:spin 28s linear infinite}"
           "@keyframes spin{to{transform:rotate(360deg)}}"
           "@media (prefers-reduced-motion:reduce){.ring{animation:none}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}" '
            f'role="img" aria-label="avatar"><style>{css}</style>'
            f'<defs><clipPath id="c"><circle cx="{c}" cy="{c}" r="{R}"/></clipPath></defs>'
            f'<circle class="ring" cx="{c}" cy="{c}" r="{R + 8}" fill="none" stroke="{ACCENT}" '
            f'stroke-width="1.5" stroke-dasharray="2 8" stroke-linecap="round"/>'
            f'<circle cx="{c}" cy="{c}" r="{R}" fill="{BG}"/>'
            f'<g clip-path="url(#c)">{body}</g></svg>')


def main():
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    img = fetch_avatar()
    svg = build_halftone(img) if os.environ.get("HALFTONE") == "1" else build_photo(img)
    (out / "avatar.svg").write_text(svg)
    print("wrote assets/avatar.svg")


if __name__ == "__main__":
    main()
