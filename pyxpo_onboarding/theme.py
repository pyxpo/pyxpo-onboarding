"""Colors, type and spacing for the onboarding screens, with a light and a dark default."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OnboardingTheme:
    """Every color and size the built-in parts use. Override any field with `replace` or `theme.merge(...)`.

    Page colors (`OnboardingPage.background`, `title_color`, `accent`, ...) win over these per page.
    """
    background: str = "#ffffff"
    title_color: str = "#111318"
    subtitle_color: str = "#5b6170"
    accent: str = "#111318"
    on_accent: str = "#ffffff"
    muted: str = "#d5d8df"
    skip_color: str = "#5b6170"
    backdrop: str = "#f2f3f6"
    title_size: float = 30
    title_weight: str = "700"
    title_line_height: float = 36
    subtitle_size: float = 16
    subtitle_line_height: float = 24
    font_family: Optional[str] = None
    horizontal_padding: float = 28
    button_height: float = 54
    button_radius: float = 27
    dot_size: float = 8
    dot_active_width: float = 24
    dot_gap: float = 8
    line_width: float = 96
    line_height: float = 4
    illustration_ratio: float = 0.52
    extra: Dict[str, Any] = field(default_factory=dict)

    def merge(self, **changes: Any) -> "OnboardingTheme":
        return replace(self, **changes)


LIGHT = OnboardingTheme()
DARK = OnboardingTheme(
    background="#121316",
    title_color="#f4f5f7",
    subtitle_color="#a3a8b5",
    accent="#f4f5f7",
    on_accent="#121316",
    muted="#3a3d46",
    skip_color="#a3a8b5",
    backdrop="#1c1e23",
)


def resolve_theme(theme: Any, scheme: str) -> OnboardingTheme:
    """`theme` is None (follow the system), "light", "dark", an OnboardingTheme, a dict of overrides, or
    `{"light": ..., "dark": ...}` with either kind of value on each side."""
    base = DARK if scheme == "dark" else LIGHT
    if theme is None:
        return base
    if isinstance(theme, OnboardingTheme):
        return theme
    if theme in ("light", "dark"):
        return DARK if theme == "dark" else LIGHT
    if isinstance(theme, dict):
        if "light" in theme or "dark" in theme:
            return resolve_theme(theme.get(scheme), scheme)
        return replace(base, **theme)
    raise TypeError("theme must be None, 'light', 'dark', an OnboardingTheme or a dict, got %r" % (theme,))
