"""Turns your GitHub profile picture into a halftone-dot SVG in the theme colors.
Needs Pillow (the workflow installs it). Output: assets/avatar.svg"""
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from theme import *          # noqa: E402,F401
import ghapi                 # noqa: E402

ROOT = Path(__file__).parent.parent
N = 48          # dots per side
CELL = 4.5      # px per dot cell


def fetch_avatar():
    url = ghapi.rest(f"/users/{ghapi.USER}")["avatar_url"]
    url += ("&" if "?" in url else "?") + "s=240"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-gen"})
    with urllib.request.urlopen(req, timeout=30, context=ghapi.SSL_CTX) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def build(img):
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
            r = CELL * 0.52 * v ** 0.9          # brighter pixel -> bigger dot
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
    (out / "avatar.svg").write_text(build(fetch_avatar()))
    print("wrote assets/avatar.svg")


if __name__ == "__main__":
    main()
