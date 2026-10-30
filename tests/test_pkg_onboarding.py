"""pyxpo-onboarding: paging, buttons, indicators, colour tracks, overrides, the ref handle and the seen flag."""
import pytest
from pyxpo import LocalChannel, Text, View, component, use_ref
from pyxpo.apis.back_handler import _Back
from pyxpo.app import create_app
from pyxpo.renderers.mock import MockRenderer

from pyxpo_onboarding import (DARK, LIGHT, Indicator, Onboarding, OnboardingPage, OnboardingTheme, resolve_theme,
                              use_onboarding_seen)
from pyxpo_onboarding.page import as_page

W = 300
PAGES = [
    OnboardingPage(title="Write", subtitle="Draft posts anywhere.", background="#ffffff", accent="#111111"),
    {"title": "Schedule", "subtitle": "Publish on time.", "background": "#000000", "accent": "#ff0000"},
    OnboardingPage(title="Grow", subtitle="Watch your readers.", background="#ffffff", accent="#0000ff"),
]


def mount(**props):
    box = {"done": 0, "skip": 0, "changes": []}

    @component
    def Root():
        ref = use_ref(None)
        box["ref"] = ref
        kw = dict(pages=PAGES, width=W, on_done=lambda: box.__setitem__("done", box["done"] + 1),
                  on_change=box["changes"].append, ref=ref)
        kw.update(props)
        return Onboarding(**kw)

    ch = LocalChannel()
    r = MockRenderer(ch)
    create_app(Root, ch)
    return r, box


def scroller(r):
    return r.find_all("ScrollView")[0]


def scroll_calls(r):
    return [c.args for c in r.calls if c.module == "Scroll" and c.method == "to"]


def test_first_page_shows_its_text_and_the_skip_and_next_buttons():
    r, _ = mount()
    texts = r.texts(buttons=True)
    for t in ("Write", "Draft posts anywhere.", "Schedule", "Skip", "Next"):
        assert t in texts
    assert "Get started" not in texts
    sv = scroller(r)
    assert sv.props["horizontal"] and sv.props["paging_enabled"]


def test_next_scrolls_one_page_and_reports_the_change():
    r, box = mount()
    r.press(r.find_text("Next"))
    assert scroll_calls(r)[-1][1:] == [W, 0, True]
    assert box["changes"] == [1]


def test_last_page_has_done_and_no_skip():
    r, box = mount(initial_index=2)
    texts = r.texts(buttons=True)
    assert "Get started" in texts and "Skip" not in texts and "Next" not in texts
    r.press(r.find_text("Get started"))
    assert box["done"] == 1


def test_swipe_settles_on_the_page_the_scroll_view_rests_on():
    r, box = mount()
    r.emit("momentum_scroll_end", scroller(r), {"value": {"x": 2 * W, "y": 0}})
    assert box["changes"] == [2]
    assert "Get started" in r.texts(buttons=True)


def test_skip_calls_on_skip_then_falls_back_to_on_done():
    hit = []
    r, box = mount(on_skip=lambda: hit.append(1))
    r.press(r.find_text("Skip"))
    assert hit == [1] and box["done"] == 0
    r, box = mount()
    r.press(r.find_text("Skip"))
    assert box["done"] == 1


def test_skip_to_end_jumps_to_the_last_page():
    r, box = mount(skip_to_end=True)
    r.press(r.find_text("Skip"))
    assert box["changes"] == [2] and box["done"] == 0
    assert scroll_calls(r)[-1][1] == 2 * W


def test_expanding_dots_and_background_follow_the_finger():
    r, _ = mount()
    root = r.root.children[0]
    assert r.resolved(root, "background_color") == 0xFFFFFFFF  # ARGB
    dots = [n for n in r.find_all("View") if r.resolved(n, "height") == LIGHT.dot_size and n.parent and
            n.parent.type != "ScrollView" and "width" in (n.props.get("style") or {})]
    widths = lambda: [r.resolved(d, "width") for d in dots]
    assert widths() == [LIGHT.dot_active_width, LIGHT.dot_size, LIGHT.dot_size]
    r.scroll(scroller(r), x=W)
    assert widths() == [LIGHT.dot_size, LIGHT.dot_active_width, LIGHT.dot_size]
    assert r.resolved(root, "background_color") == 0xFF000000
    r.scroll(scroller(r), x=W / 2)
    assert LIGHT.dot_size < widths()[0] < LIGHT.dot_active_width


def test_back_button_goes_to_the_previous_page_first():
    r, box = mount(initial_index=1)
    assert _Back.handlers
    assert _Back.handlers[-1]() is True
    assert box["changes"] == [0]
    assert _Back.handlers[-1]() is False


def test_ref_handle_moves_between_pages():
    r, box = mount()
    h = box["ref"].current
    assert h.index == 0
    h.go_to(2, animated=False)
    assert h.index == 2 and scroll_calls(r)[-1][1:] == [2 * W, 0, False]
    h.back()
    assert h.index == 1
    h.next()
    h.next()
    assert box["done"] == 1


def test_number_indicator_and_circle_next():
    r, _ = mount(indicator="number", next_style="circle", initial_index=1)
    texts = r.texts(buttons=True)
    assert "2 / 3" in texts and "→" in texts


def test_show_back_and_custom_labels():
    r, _ = mount(show_back=True, initial_index=1, back_label="Prev", next_label="Continue")
    texts = r.texts(buttons=True)
    assert "Prev" in texts and "Continue" in texts
    r.press(r.find_text("Prev"))
    assert scroll_calls(r)[-1][1] == 0


def test_render_overrides_replace_the_parts():
    seen = {}

    def page(p, i, state):
        return Text("custom %d" % i)

    def footer(state):
        seen["state"] = state
        return Text("footer %d/%d" % (state.index, state.count))

    r, _ = mount(render_page=page, render_footer=footer, header=Text("Logo"))
    texts = r.texts()
    assert "custom 0" in texts and "custom 2" in texts and "footer 0/3" in texts and "Logo" in texts
    assert seen["state"].is_first and not seen["state"].is_last


def test_card_layout_and_page_content():
    r, _ = mount(layout="card", pages=[OnboardingPage(content=View(Text("own"))), OnboardingPage(title="B")])
    assert "own" in r.texts() and "B" in r.texts()


def test_bad_options_raise():
    with pytest.raises(ValueError):
        mount(indicator="stars")
    with pytest.raises(ValueError):
        mount(pages=[])
    with pytest.raises(TypeError):
        as_page(3)
    with pytest.raises(ValueError):
        Indicator("stars", 3, 0, None, LIGHT, "#000", "#ccc")


def test_single_page_has_no_indicator_and_no_swipe():
    r, _ = mount(pages=[OnboardingPage(title="Only")])
    assert scroller(r).props["scroll_enabled"] is False
    assert "Get started" in r.texts(buttons=True)


def test_theme_resolution():
    assert resolve_theme(None, "dark") is DARK
    assert resolve_theme("light", "dark") is LIGHT
    assert resolve_theme({"accent": "#123456"}, "light").accent == "#123456"
    t = OnboardingTheme(accent="#abcdef")
    assert resolve_theme({"light": t, "dark": "dark"}, "light") is t
    assert resolve_theme({"light": t, "dark": "dark"}, "dark") is DARK
    assert LIGHT.merge(dot_size=10).dot_size == 10
    with pytest.raises(TypeError):
        resolve_theme(5, "light")


def test_seen_flag_persists_per_version(tmp_path):
    from pyxpo_storage import Storage
    store = Storage(id="onb", path=str(tmp_path))
    box = {}

    @component
    def Root():
        box["v1"] = use_onboarding_seen(storage=store)
        box["v2"] = use_onboarding_seen(version=2, storage=store)
        return Text("x")

    ch = LocalChannel()
    MockRenderer(ch)
    create_app(Root, ch)
    assert box["v1"].seen is False
    box["v1"].mark_seen()
    assert box["v1"].seen is True and box["v2"].seen is False
    assert store.get_boolean("pyxpo.onboarding.seen") is True
    box["v1"].reset()
    assert box["v1"].seen is False
