"""One onboarding page: what it shows and the colors it overrides."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

from pyxpo import Element


@dataclass(frozen=True)
class OnboardingPage:
    """A page. `image` is an Element (an Svg, a Lottie view, your own View) or an Image source: a path, an
    http(s) URL, `asset:name` or `{"uri": ...}`. `content` replaces the whole page body when set.

    `background`, `title_color`, `subtitle_color` and `accent` override the theme for this page; the screen
    background and the accent fade between pages while the user swipes.
    """
    title: Any = None
    subtitle: Any = None
    image: Any = None
    background: Optional[str] = None
    title_color: Optional[str] = None
    subtitle_color: Optional[str] = None
    accent: Optional[str] = None
    on_accent: Optional[str] = None
    backdrop: Optional[str] = None
    content: Optional[Element] = None
    key: Any = None


PageLike = Union[OnboardingPage, Mapping[str, Any]]


def as_page(p: PageLike) -> OnboardingPage:
    if isinstance(p, OnboardingPage):
        return p
    if isinstance(p, Mapping):
        return OnboardingPage(**dict(p))
    raise TypeError("pages must be OnboardingPage or dict items, got %r" % (p,))
