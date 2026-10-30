# Changelog

## 0.1.0a1

- First release: the `Onboarding` screen with swipeable pages, the `expanding`, `dot`, `scale`, `line` and `number`
  indicators, `center` and `card` layouts, and `pill`, `circle` and `text` next buttons.
- The background, the accent and the indicator follow the finger on the native thread, with parallax on the
  illustration and a text fade.
- `OnboardingTheme` with light and dark defaults. Pages can override their colors. Every part can be replaced with
  a `render_*` function.
- `ref.current` exposes `next()`, `back()`, `go_to()`, `skip()` and `done()`. The Android back button goes to the
  previous page.
- With `show_back=True` the footer has three columns (Back, indicator, Next), so the indicator stays centered.
- `use_onboarding_seen()` stores a per-version "seen" flag with pyxpo-storage.
