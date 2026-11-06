"""One place for the look. Change ACCENT / RAMP to re-theme everything."""

BG = "#0b0709"        # near-black with a warm tint
BORDER = "#3a1a22"
TEXT = "#e9dfe1"
MUTED = "#9a8589"
ACCENT = "#d63d58"    # red wine, lifted a bit so it stays readable on dark
WINE = "#722f37"      # classic burgundy, used for badges / fills
# contribution levels, darkest -> brightest
RAMP = ["#2a1318", "#5a1a28", "#8c2438", "#c2324b", "#ef7a8c"]
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
