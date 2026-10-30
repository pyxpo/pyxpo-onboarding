"""Customizable onboarding and intro slides for pyxpo apps."""
from __future__ import annotations

from .indicators import KINDS as INDICATORS, Indicator
from .onboarding import LAYOUTS, NEXT_STYLES, Onboarding, OnboardingHandle, OnboardingState
from .page import OnboardingPage
from .seen import SeenFlag, use_onboarding_seen
from .theme import DARK, LIGHT, OnboardingTheme, resolve_theme

__version__ = "0.1.0a1"

__all__ = [
    "Onboarding", "OnboardingPage", "OnboardingTheme", "OnboardingState", "OnboardingHandle", "Indicator",
    "use_onboarding_seen", "SeenFlag", "LIGHT", "DARK", "resolve_theme", "INDICATORS", "LAYOUTS", "NEXT_STYLES",
]
