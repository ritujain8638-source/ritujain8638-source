"""Isometric 3D contribution calendar -> assets/isocal.svg (stdlib only)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from theme import *          # noqa: E402,F401
import ghapi                 # noqa: E402

ROOT = Path(__file__).parent.parent
CELL = 14
A, B = CELL * 0.866, CELL * 0.5
MAXH = 46


def shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def poly(pts, fill, opacity=1):
    p = " ".join("%.1f,%.1f" % q for q in pts)
    return f'<polygon points="{p}" fill="{fill}" fill-opacity="{opacity}"/>'


def build(total, weeks, stats):
    W = len(weeks)
    pad = 24
    top = 78
    width = int(2 * pad + (W + 7) * A)
    ox, oy = pad + 7 * A, top + MAXH

    def P(w, d):
        return ox + (w - d) * A, oy + (w + d) * B

    height = int(P(W, 7)[1] + 70)
    peak = max((d["contributionCount"] for wk in weeks for d in wk["contributionDays"]), default=0) or 1

    cur, longest, busiest = stats
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" role="img" aria-label="contribution calendar">',
           f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
           f'<g font-family="{FONT}">',
           f'<text x="{pad}" y="34" font-size="16" font-weight="700" fill="{TEXT}">'
           f'{esc(ghapi.USER)} — contributions, last year</text>',
           f'<text x="{pad}" y="62" font-size="26" font-weight="700" fill="{ACCENT}">{total}</text>',
           f'<text x="{pad+70}" y="62" font-size="11" fill="{MUTED}">commits, PRs, issues &amp; reviews</text>',
           f'<text x="{width-pad}" y="34" text-anchor="end" font-size="11" fill="{MUTED}">'
           f'current streak {cur}d · longest {longest}d · busiest day {busiest}</text>']

    # base slab
    svg.append(poly([P(0, 0), P(W, 0), P(W, 7), P(0, 7)], RAMP[0], .55))

    # bars, back to front
    cells = []
    for w, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            if d["contributionCount"] > 0:
                cells.append((w, d["weekday"], d["contributionCount"]))
    cells.sort(key=lambda c: (c[0] + c[1], c[0]))
    inset = 0.08
    for w, d, c in cells:
        level = min(4, max(1, math.ceil(4 * c / peak)))
        color = RAMP[level]
        h = 4 + (c / peak) * (MAXH - 4)
        w0, w1, d0, d1 = w + inset, w + 1 - inset, d + inset, d + 1 - inset

        def up(p):
            return p[0], p[1] - h

        top_f = [up(P(w0, d0)), up(P(w1, d0)), up(P(w1, d1)), up(P(w0, d1))]
        left = [up(P(w0, d1)), up(P(w1, d1)), P(w1, d1), P(w0, d1)]
        right = [up(P(w1, d0)), up(P(w1, d1)), P(w1, d1), P(w1, d0)]
        svg += [poly(left, shade(color, .55)), poly(right, shade(color, .75)), poly(top_f, color)]

    # month labels under the front edge (never collide with bars)
    last = None
    for w, wk in enumerate(weeks):
        month = wk["contributionDays"][0]["date"][5:7]
        if month != last:
            name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(month) - 1]
            x, y = P(w, 7)
            svg.append(f'<text x="{x:.1f}" y="{y+18:.1f}" font-size="11" fill="{MUTED}">{name}</text>')
            last = month

    # legend
    lx, ly = width - pad - 190, height - 24
    svg.append(f'<text x="{lx}" y="{ly+9}" font-size="11" fill="{MUTED}" text-anchor="end">less</text>')
    for i, c in enumerate(RAMP):
        svg.append(f'<rect x="{lx+8+i*20}" y="{ly}" width="12" height="12" rx="2" fill="{c}"/>')
    svg.append(f'<text x="{lx+118}" y="{ly+9}" font-size="11" fill="{MUTED}">more</text>')
    svg.append("</g></svg>")
    return "\n".join(svg)


def main():
    total, weeks = ghapi.calendar()
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    (out / "isocal.svg").write_text(build(total, weeks, ghapi.streaks(weeks)))
    print("wrote assets/isocal.svg")


if __name__ == "__main__":
    main()
