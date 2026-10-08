from __future__ import annotations

from docmorph_schema import DesignConfig

FONT_STACKS = {
    "serif": 'Charter, "Bitstream Charter", "Sitka Text", Cambria, Georgia, serif',
    "sans": 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    "humanist": 'Seravek, "Gill Sans Nova", Ubuntu, Calibri, "DejaVu Sans", source-sans-pro, sans-serif',
    "slab": 'Rockwell, "Rockwell Nova", "Roboto Slab", "DejaVu Serif", "Sitka Small", serif',
    "mono": 'ui-monospace, "Cascadia Code", "Source Code Pro", Menlo, Consolas, monospace',
}

SPACING = {"compact": 0.75, "normal": 1.0, "relaxed": 1.35}


def _fmt(n: float) -> str:
    return f"{n:.4f}".rstrip("0").rstrip(".")


def build_css(design: DesignConfig) -> str:
    t, c, layout = design.typography, design.colors, design.layout
    space = SPACING[layout.spacing]
    sizes = {f"--dm-h{lvl}": _fmt(t.scale ** (6 - lvl) * 0.8) + "em" for lvl in range(1, 7)}
    vars_ = {
        "--dm-bg": c.background,
        "--dm-text": c.text,
        "--dm-accent": c.accent,
        "--dm-muted": c.muted,
        "--dm-surface": c.surface,
        "--dm-body-font": FONT_STACKS[t.body_font],
        "--dm-heading-font": FONT_STACKS[t.heading_font],
        "--dm-base": _fmt(t.base_size_px) + "px",
        "--dm-leading": _fmt(t.line_height),
        "--dm-heading-weight": str(t.heading_weight),
        "--dm-space": _fmt(space) + "rem",
        "--dm-max": f"{layout.max_width_px}px",
        **sizes,
    }
    root = "".join(f"{k}:{v};" for k, v in vars_.items())
    columns = (
        "@media (min-width: 960px){.dm-section__body{column-count:2;column-gap:3rem}"
        ".dm-section__body>table,.dm-section__body>figure,.dm-section__body>pre{column-span:all}}"
        if layout.columns == 2
        else ""
    )
    return (
        f":root{{{root}}}"
        "*,*::before,*::after{box-sizing:border-box}"
        "html{-webkit-text-size-adjust:100%}"
        "body{margin:0;background:var(--dm-bg);color:var(--dm-text);font-family:var(--dm-body-font);"
        "font-size:var(--dm-base);line-height:var(--dm-leading);text-rendering:optimizeLegibility}"
        ".dm-doc{max-width:var(--dm-max);margin:0 auto;padding:calc(var(--dm-space)*2) 1.25rem 4rem}"
        f".dm-doc p,.dm-doc li{{text-align:{layout.align}}}"
        "h1,h2,h3,h4,h5,h6{font-family:var(--dm-heading-font);font-weight:var(--dm-heading-weight);"
        "line-height:1.2;margin:calc(var(--dm-space)*1.6) 0 calc(var(--dm-space)*0.6)}"
        "h1{font-size:var(--dm-h1)}h2{font-size:var(--dm-h2)}h3{font-size:var(--dm-h3)}"
        "h4{font-size:var(--dm-h4)}h5{font-size:var(--dm-h5)}h6{font-size:var(--dm-h6)}"
        "p,ul,ol,blockquote,pre,figure,.dm-table{margin:0 0 var(--dm-space)}"
        "a{color:var(--dm-accent)}"
        "blockquote{border-left:4px solid var(--dm-accent);padding:.25rem 0 .25rem 1rem;color:var(--dm-muted);"
        "font-style:italic}"
        "pre{background:var(--dm-surface);padding:1rem;border-radius:8px;overflow-x:auto;"
        "font-family:" + FONT_STACKS["mono"] + ";font-size:.875em}"
        "code{font-family:" + FONT_STACKS["mono"] + ";font-size:.9em}"
        "hr{border:0;border-top:1px solid var(--dm-muted);opacity:.4;margin:calc(var(--dm-space)*2) 0}"
        "img{max-width:100%;height:auto;border-radius:6px}"
        "figure{text-align:center}figcaption{color:var(--dm-muted);font-size:.875em;margin-top:.4rem}"
        ".dm-table{overflow-x:auto}"
        "table{border-collapse:collapse;width:100%;font-size:.9375em}"
        "th,td{border:1px solid color-mix(in srgb,var(--dm-muted) 35%,transparent);padding:.5rem .75rem;"
        "text-align:left;vertical-align:top}"
        "th{background:var(--dm-surface);font-weight:600}"
        ".dm-cover{padding:calc(var(--dm-space)*3) 0 calc(var(--dm-space)*2);margin-bottom:var(--dm-space);"
        "border-bottom:3px solid var(--dm-accent)}"
        ".dm-cover h1{margin-top:0}.dm-cover p{color:var(--dm-muted);margin:0}"
        ".dm-toc{background:var(--dm-surface);border-radius:10px;padding:1rem 1.25rem;margin-bottom:"
        "calc(var(--dm-space)*1.5)}"
        ".dm-toc h2{font-size:.8em;text-transform:uppercase;letter-spacing:.08em;margin:0 0 .5rem;"
        "color:var(--dm-muted)}"
        ".dm-toc ol{margin:0;padding-left:1.1rem}.dm-toc a{text-decoration:none}"
        ".dm-toc .dm-toc--l3{margin-left:1rem;font-size:.92em}"
        ".dm-progress{position:fixed;top:0;left:0;right:0;height:3px;background:var(--dm-accent);"
        "transform-origin:0 50%;transform:scaleX(0);z-index:10}"
        ".dm-pager{position:sticky;bottom:0;display:flex;justify-content:space-between;align-items:center;"
        "gap:1rem;padding:.75rem 0;background:var(--dm-bg);border-top:1px solid var(--dm-surface)}"
        ".dm-pager button{font:inherit;font-size:.875em;padding:.45rem .9rem;border-radius:999px;"
        "border:1px solid var(--dm-accent);background:transparent;color:var(--dm-accent);cursor:pointer}"
        ".dm-pager button:disabled{opacity:.35;cursor:default}"
        ".dm-reader--swipe .dm-section--active,.dm-reader--paginate .dm-section--active{"
        "animation:dm-in .25s ease-out;min-height:60vh}"
        "@keyframes dm-in{from{opacity:0;transform:translateX(12px)}to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        "@media (max-width:640px){body{font-size:calc(var(--dm-base)*.94)}.dm-doc{padding-top:1.25rem}}"
        "@media print{.dm-pager,.dm-progress{display:none}.dm-section{display:block!important}}" + columns
    )
