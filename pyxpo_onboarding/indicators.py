"""Page indicators driven by the scroll position, so they move with the finger on the native thread."""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from pyxpo import Animated, Pressable, Text, View, use_memo

from .theme import OnboardingTheme

KINDS = ("expanding", "dot", "scale", "line", "number", "none")


def _around(progress: Any, i: int, low: Any, high: Any) -> Any:
    """`high` while page `i` is current, `low` one page away, blended in between."""
    return progress.interpolate([i - 1, i, i + 1], [low, high, low], extrapolate="clamp")


def Indicator(kind: str, count: int, index: int, progress: Any, theme: OnboardingTheme, active: Any,
              inactive: str, on_press: Optional[Callable[[int], None]] = None, style: Any = None) -> Any:
    """The built-in indicator `kind` for `count` pages. `progress` is the scroll offset in pages (0 .. count-1).
    `active` is one color or a list with one color per page (dot `i` lights up in page `i`'s accent)."""
    colors = list(active) if isinstance(active, (list, tuple)) else [active] * count
    if kind not in KINDS:
        raise ValueError("indicator must be one of %s, got %r" % (", ".join(KINDS), kind))
    if kind == "none" or count < 2:
        return None
    if kind == "number":
        return Text("%d / %d" % (index + 1, count),
                    style=[{"color": colors[index], "font_size": 14, "font_weight": "600"}, style])
    if kind == "line":
        fill = colors[0] if len(set(colors)) == 1 else progress.interpolate(list(range(count)), colors,
                                                                              extrapolate="clamp")
        return _Line(count, progress, theme, fill, inactive, style)
    return _Dots(kind, count, progress, theme, colors, inactive, on_press, style)


def _Dots(kind: str, count: int, progress: Any, theme: OnboardingTheme, colors: List[str], inactive: str,
          on_press: Optional[Callable[[int], None]], style: Any) -> Any:
    d = theme.dot_size
    dots: List[Any] = []
    for i in range(count):
        active = colors[i]
        if kind == "expanding":
            st = {"width": _around(progress, i, d, theme.dot_active_width), "height": d, "border_radius": d / 2,
                  "background_color": _around(progress, i, inactive, active)}
        elif kind == "scale":
            st = {"width": d, "height": d, "border_radius": d / 2, "scale": _around(progress, i, 1.0, 1.5),
                  "background_color": _around(progress, i, inactive, active)}
        else:
            st = {"width": d, "height": d, "border_radius": d / 2, "background_color": active,
                  "opacity": _around(progress, i, 0.3, 1.0)}
        dot = Animated.View(style=st)
        if on_press is not None:
            dot = Pressable(dot, on_press=(lambda i=i: on_press(i)), hit_slop=8,
                            accessibility_label="Page %d of %d" % (i + 1, count), accessibility_role="button")
        dots.append(View(dot, key=i, style={"margin_horizontal": theme.dot_gap / 2}))
    return View(*dots, style=[{"flex_direction": "row", "align_items": "center", "height": d * 2}, style],
                accessibility_role="adjustable")


def _Line(count: int, progress: Any, theme: OnboardingTheme, active: Any, inactive: str, style: Any) -> Any:
    w, h = theme.line_width, theme.line_height
    seg = w / count
    fill = progress.interpolate([0, count - 1], [seg, w], extrapolate="clamp")
    return View(Animated.View(style={"width": fill, "height": h, "border_radius": h / 2, "background_color": active}),
                style=[{"width": w, "height": h, "border_radius": h / 2, "background_color": inactive,
                        "overflow": "hidden"}, style])


def use_progress(scroll_x: Any, width: float) -> Any:
    """Scroll offset in pages, as an animated node."""
    return use_memo(lambda: scroll_x * (1.0 / max(width, 1.0)), [scroll_x, width])
