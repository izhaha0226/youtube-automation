"""Smoke tests — no external API calls, only structure/imports."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))


def test_imports():
    from app.main import app  # noqa: F401
    from app.core.config import settings
    from app.schemas import (  # noqa: F401
        NarrationInput,
        ReviewInput,
        ScenarioInput,
        ThumbnailInput,
        TopicInput,
    )

    assert settings.default_model == "gpt-5.4"
    assert settings.channel_name == "리치고"


def test_scoring_rules_present():
    from app.core.config import settings

    rules = settings.scoring_rules
    assert rules["thresholds"]["strong_recommend"] == 24
    assert rules["top_k"] == 3


def test_srt_timestamp():
    from app.modules.subtitle.subtitler import _ts

    assert _ts(0) == "00:00:00,000"
    assert _ts(1_001) == "00:00:01,001"
    assert _ts(3_661_123) == "01:01:01,123"


def test_slugify():
    from app.core.paths import slugify

    assert slugify("금리 집값 영향") == "금리-집값-영향"
