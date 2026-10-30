"""The `Onboarding` screen: swipeable pages, an indicator, skip / back / next / done buttons."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence

from pyxpo import (Animated, BackHandler, Element, Image, Platform, Pressable, ScrollView, Text, View, component,
                   use_animated_value, use_color_scheme, use_effect, use_imperative_handle, use_memo, use_ref,
                   use_safe_area_insets, use_state, use_window_dimensions)

from .indicators import KINDS, Indicator
from .page import OnboardingPage, PageLike, as_page
from .theme import OnboardingTheme, resolve_theme

LAYOUTS = ("center", "card")
NEXT_STYLES = ("pill", "circle", "text")


@dataclass(frozen=True)
class OnboardingState:
    """What the `render_*` overrides get: where the user is and the actions the built-in buttons use."""
    index: int
    count: int
    page: OnboardingPage
    pages: tuple
    theme: OnboardingTheme
    progress: Any          # animated scroll offset in pages, for your own animations
    accent: str
    on_accent: str
    next: Callable[[], None]
    back: Callable[[], None]
    skip: Callable[[], None]
    done: Callable[[], None]
    go_to: Callable[..., None]

    @property
    def is_first(self) -> bool:
        return self.index == 0

    @property
    def is_last(self) -> bool:
        return self.index == self.count - 1


class OnboardingHandle:
    """`ref.current` of an `Onboarding`."""

    def __init__(self, state: Callable[[], OnboardingState]) -> None:
        self._state = state

    @property
    def index(self) -> int:
        return self._state().index

    def next(self) -> None:
        self._state().next()

    def back(self) -> None:
        self._state().back()

    def go_to(self, index: int, animated: bool = True) -> None:
        self._state().go_to(index, animated)

    def skip(self) -> None:
        self._state().skip()

    def done(self) -> None:
        self._state().done()


def _color_track(progress: Any, colors: List[str]) -> Any:
    """A color that blends from page to page while swiping, or the plain color when every page agrees."""
    if len(set(colors)) == 1:
        return colors[0]
    return progress.interpolate(list(range(len(colors))), colors, extrapolate="clamp")


def _check(name: str, value: Any, allowed: Sequence[str]) -> None:
    if value not in allowed:
        raise ValueError("%s must be one of %s, got %r" % (name, ", ".join(allowed), value))


@component
def Onboarding(pages: Sequence[PageLike] = (), on_done: Optional[Callable[[], Any]] = None,
               on_skip: Optional[Callable[[], Any]] = None, on_change: Optional[Callable[[int], Any]] = None,
               initial_index: int = 0, indicator: str = "expanding", layout: str = "center",
               show_skip: bool = True, show_back: bool = False, show_next: bool = True, skip_to_end: bool = False,
               skip_label: str = "Skip", next_label: str = "Next", back_label: str = "Back",
               done_label: str = "Get started", next_style: str = "pill", full_width_done: bool = True,
               parallax: float = 0.35, animate_text: bool = True, swipe_enabled: bool = True, theme: Any = None,
               style: Any = None, title_style: Any = None, subtitle_style: Any = None, button_style: Any = None,
               button_text_style: Any = None, render_page: Optional[Callable[..., Any]] = None,
               render_indicator: Optional[Callable[[OnboardingState], Any]] = None,
               render_skip: Optional[Callable[[OnboardingState], Any]] = None,
               render_next: Optional[Callable[[OnboardingState], Any]] = None,
               render_done: Optional[Callable[[OnboardingState], Any]] = None,
               render_back: Optional[Callable[[OnboardingState], Any]] = None,
               render_footer: Optional[Callable[[OnboardingState], Any]] = None, header: Any = None,
               safe_area: bool = True, handle_back_button: bool = True, width: Optional[float] = None,
               ref: Any = None) -> Element:
    """A full-screen intro. `pages` are `OnboardingPage`s or dicts with the same keys. Swipe or tap Next to move;
    Done (or Skip) calls `on_done` / `on_skip`. Every colour and size comes from `theme`, every part can be
    replaced with a `render_*` function, and `ref.current` has `next()`, `back()`, `go_to(i)`, `skip()`, `done()`.
    """
    _check("indicator", indicator, KINDS)
    _check("layout", layout, LAYOUTS)
    _check("next_style", next_style, NEXT_STYLES)
    items = [as_page(p) for p in pages]
    if not items:
        raise ValueError("Onboarding needs at least one page")
    count = len(items)
    th = resolve_theme(theme, use_color_scheme() or "light")
    win = use_window_dimensions()
    w = float(width or win.get("width") or 360)
    h = float(win.get("height") or 640)
    insets = use_safe_area_insets() if safe_area else {}
    start = max(0, min(count - 1, int(initial_index)))

    index, set_index = use_state(start)
    scroll_x = use_animated_value(start * w)
    scroller = use_ref(None)
    latest = use_ref(None)

    backgrounds = [p.background or th.background for p in items]
    accents = [p.accent or th.accent for p in items]
    on_accents = [p.on_accent or th.on_accent for p in items]
    nodes = use_memo(lambda: _nodes(scroll_x, w, count, backgrounds, accents, parallax, animate_text),
                     [scroll_x, w, count, tuple(backgrounds), tuple(accents), parallax, animate_text])

    def settle(i: int) -> None:
        i = max(0, min(count - 1, i))
        if i != latest.current.index:
            set_index(i)
            if on_change is not None:
                on_change(i)

    def go_to(i: int, animated: bool = True) -> None:
        i = max(0, min(count - 1, int(i)))
        if scroller.current is not None:
            scroller.current.scrollTo({"x": i * w, "y": 0, "animated": animated})
        settle(i)

    def finish() -> None:
        if on_done is not None:
            on_done()

    def skip() -> None:
        if skip_to_end:
            go_to(count - 1)
        elif on_skip is not None:
            on_skip()
        else:
            finish()

    state = OnboardingState(index=index, count=count, page=items[index], pages=tuple(items), theme=th, progress=nodes["progress"],
                            accent=accents[index], on_accent=on_accents[index],
                            next=lambda: go_to(latest.current.index + 1) if not latest.current.is_last else finish(),
                            back=lambda: go_to(latest.current.index - 1), skip=skip, done=finish, go_to=go_to)
    latest.current = state

    use_imperative_handle(ref, lambda: OnboardingHandle(lambda: latest.current), [])

    def on_back() -> bool:
        if latest.current.index > 0:
            latest.current.back()
            return True
        return False

    def back_listener():
        if not handle_back_button:
            return None
        sub = BackHandler.addEventListener("hardwareBackPress", on_back)
        return sub.remove
    use_effect(back_listener, [handle_back_button])

    def keep_page_on_resize():
        if scroller.current is not None:
            scroller.current.scrollTo({"x": latest.current.index * w, "y": 0, "animated": False})
    use_effect(keep_page_on_resize, [w])

    def on_settled(e: Any) -> None:
        if isinstance(e, dict) and e.get("x") is not None:
            settle(int(round(float(e["x"]) / w)))

    # native shells report the resting page; the web build has no momentum event, so it reads every scroll
    listener = on_settled if Platform.OS == "web" else None
    scroller_el = ScrollView(
        *[View(_page_body(p, i, state, th, nodes, w, h, layout, title_style, subtitle_style, render_page),
               key=p.key if p.key is not None else i, style={"width": w, "overflow": "hidden"}) for i, p in enumerate(items)],
        ref=scroller, horizontal=True, paging_enabled=True, scroll_enabled=swipe_enabled and count > 1,
        shows_horizontal_scroll_indicator=False, bounces=False, content_offset={"x": start * w, "y": 0},
        on_scroll=Animated.event({"x": scroll_x}, listener=listener), scroll_event_throttle=16,
        on_momentum_scroll_end=on_settled, style={"flex": 1})

    top = _top_bar(state, th, header, show_skip, skip_label, render_skip, button_text_style)
    footer = (render_footer(state) if render_footer is not None else
              _footer(state, th, nodes, indicator, render_indicator, show_back, show_next, back_label, next_label,
                      done_label, next_style, full_width_done, button_style, button_text_style, render_back,
                      render_next, render_done))
    return Animated.View(
        View(top, style={"padding_top": insets.get("top", 0)}),
        scroller_el,
        View(footer, style={"padding_bottom": max(insets.get("bottom", 0), 16), "padding_horizontal":
                            th.horizontal_padding, "padding_top": 8}),
        style=[{"flex": 1, "background_color": nodes["background"]}, style])


def _nodes(scroll_x: Any, w: float, count: int, backgrounds: List[str], accents: List[str], parallax: float,
           animate_text: bool) -> dict:
    """Every animated node the screen binds, built once per width and page set."""
    progress = scroll_x * (1.0 / max(w, 1.0))
    shift = w * parallax
    pages = []
    for i in range(count):
        near = [i - 1, i, i + 1]
        pages.append({
            "image_x": progress.interpolate(near, [shift, 0, -shift], extrapolate="clamp") if parallax else None,
            "text_opacity": (progress.interpolate([i - 0.6, i, i + 0.6], [0, 1, 0], extrapolate="clamp")
                             if animate_text else None),
            "text_x": progress.interpolate(near, [w * 0.12, 0, -w * 0.12], extrapolate="clamp") if animate_text else None,
        })
    return {"progress": progress, "background": _color_track(progress, backgrounds),
            "accent": _color_track(progress, accents), "pages": pages}


def _image(image: Any, size: float) -> Any:
    if image is None or isinstance(image, Element):
        return image
    return Image(source=image, resize_mode="contain", style={"width": size, "height": size})


def _page_body(p: OnboardingPage, i: int, state: OnboardingState, th: OnboardingTheme, nodes: dict, w: float,
               h: float, layout: str, title_style: Any, subtitle_style: Any,
               render_page: Optional[Callable[..., Any]]) -> Any:
    if render_page is not None:
        return render_page(p, i, state)
    if p.content is not None:
        return p.content
    n = nodes["pages"][i]
    pad = th.horizontal_padding
    art_h = h * th.illustration_ratio
    art = _image(p.image, min(w - pad * 2, art_h * 0.8))
    # the art takes the room the text leaves, so short screens shrink the art instead of clipping it
    art_style: dict = {"align_items": "center", "justify_content": "center", "height": art_h, "flex_shrink": 1,
                       "min_height": 120}
    if n["image_x"] is not None:
        art_style["translate_x"] = n["image_x"]
    if layout == "card":
        art_style.update({"margin_horizontal": pad * 0.6, "margin_top": 8, "border_radius": 32,
                          "background_color": p.backdrop or th.backdrop, "overflow": "hidden"})
    font = {"font_family": th.font_family} if th.font_family else {}
    title = (Text(p.title, style=[{"color": p.title_color or th.title_color, "font_size": th.title_size,
                                   "font_weight": th.title_weight, "line_height": th.title_line_height,
                                   "text_align": "center" if layout == "center" else "left"}, font, title_style],
                  accessibility_role="header")
             if isinstance(p.title, str) else p.title)
    subtitle = (Text(p.subtitle, style=[{"color": p.subtitle_color or th.subtitle_color, "font_size": th.subtitle_size,
                                         "line_height": th.subtitle_line_height, "margin_top": 12,
                                         "text_align": "center" if layout == "center" else "left"}, font,
                                        subtitle_style])
                if isinstance(p.subtitle, str) else p.subtitle)
    text_style: dict = {"padding_horizontal": pad, "padding_top": 28, "padding_bottom": 16,
                        "align_items": "center" if layout == "center" else "flex-start"}
    if n["text_opacity"] is not None:
        text_style.update({"opacity": n["text_opacity"], "translate_x": n["text_x"]})
    return View(Animated.View(art, style=art_style), Animated.View(title, subtitle, style=text_style),
                style={"flex": 1, "justify_content": "center" if layout == "center" else "flex-start"})


def _text_button(label: str, color: Any, on_press: Callable[[], None], text_style: Any, a11y: str) -> Any:
    return Pressable(Text(label, style=[{"color": color, "font_size": 16, "font_weight": "600"}, text_style]),
                     on_press=on_press, hit_slop=12, accessibility_role="button", accessibility_label=a11y,
                     style=lambda s: {"padding_vertical": 10, "padding_horizontal": 4,
                                      "opacity": 0.5 if s.pressed else 1})


def _top_bar(state: OnboardingState, th: OnboardingTheme, header: Any, show_skip: bool, skip_label: str,
             render_skip: Optional[Callable[[OnboardingState], Any]], text_style: Any) -> Any:
    skip = None
    if show_skip and not state.is_last:
        skip = (render_skip(state) if render_skip is not None else
                _text_button(skip_label, th.skip_color, state.skip, text_style, skip_label))
    return View(View(header, style={"flex": 1}), skip,
                style={"flex_direction": "row", "align_items": "center", "min_height": 52,
                       "padding_horizontal": th.horizontal_padding - 4})


def _filled_button(state: OnboardingState, th: OnboardingTheme, nodes: dict, label: Any, on_press: Callable[[], None],
                   shape: str, button_style: Any, text_style: Any, a11y: str) -> Any:
    size = th.button_height
    box: dict = {"height": size, "border_radius": th.button_radius if shape != "circle" else size / 2,
                 "background_color": nodes["accent"], "align_items": "center", "justify_content": "center"}
    if shape == "circle":
        box["width"] = size
    elif shape == "wide":
        box["align_self"] = "stretch"
    else:
        box["padding_horizontal"] = 28
    font = {"font_family": th.font_family} if th.font_family else {}
    inner = Text(label, style=[{"color": state.on_accent, "font_size": 22 if shape == "circle" else 16,
                                "font_weight": "600"}, font, text_style])
    return Pressable(Animated.View(inner, style=[box, button_style]), on_press=on_press,
                     accessibility_role="button", accessibility_label=a11y,
                     style=lambda s: {"opacity": 0.85 if s.pressed else 1,
                                      "scale": 0.97 if s.pressed else 1,
                                      "align_self": "stretch" if shape == "wide" else "auto"})


def _footer(state: OnboardingState, th: OnboardingTheme, nodes: dict, indicator: str,
            render_indicator: Optional[Callable[[OnboardingState], Any]], show_back: bool, show_next: bool,
            back_label: str, next_label: str, done_label: str, next_style: str, full_width_done: bool,
            button_style: Any, text_style: Any, render_back: Any, render_next: Any, render_done: Any) -> Any:
    accents = [p.accent or th.accent for p in state.pages]
    dots = (render_indicator(state) if render_indicator is not None else
            Indicator(indicator, state.count, state.index, state.progress, th, accents, th.muted,
                      on_press=state.go_to))
    back = None
    if show_back and not state.is_first:
        back = (render_back(state) if render_back is not None else
                _text_button(back_label, th.skip_color, state.back, text_style, back_label))

    if state.is_last:
        if render_done is not None:
            action = render_done(state)
        elif full_width_done:
            return View(View(dots, style={"align_items": "center", "margin_bottom": 20}),
                        _filled_button(state, th, nodes, done_label, state.done, "wide", button_style, text_style,
                                       done_label),
                        View(back, style={"align_items": "center", "margin_top": 8}) if back is not None else None)
        elif next_style == "text":
            action = _text_button(done_label, state.accent, state.done, text_style, done_label)
        else:
            action = _filled_button(state, th, nodes, done_label, state.done, "pill", button_style, text_style,
                                    done_label)
    elif not show_next:
        action = None
    elif render_next is not None:
        action = render_next(state)
    elif next_style == "text":
        action = _text_button(next_label, state.accent, state.next, text_style, next_label)
    elif next_style == "circle":
        action = _filled_button(state, th, nodes, "→", state.next, "circle", button_style, text_style, next_label)
    else:
        action = _filled_button(state, th, nodes, next_label, state.next, "pill", button_style, text_style, next_label)

    row = {"flex_direction": "row", "align_items": "center", "min_height": th.button_height}
    if show_back:
        # Back | indicator | action: the side columns share the width so the indicator stays centred.
        side = {"flex": 1, "flex_direction": "row", "align_items": "center"}
        return View(View(back, style=side), dots,
                    View(action, style=[side, {"justify_content": "flex-end"}]), style=row)
    return View(View(dots, style={"flex": 1}), action, style=row)

