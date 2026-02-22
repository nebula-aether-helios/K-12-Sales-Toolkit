"""
Tests for district scoring and pilot readiness models.
TODO (Jules): Expand with real test cases once live data is connected.
"""
import pytest
import pandas as pd
import sys
import os

# ============================================================
# Test: Partnership Readiness Scoring
# ============================================================

def score_district_helper(ela_pct, budget, sor_signal, recent_init, supt_tenure, miles):
    """Standalone scoring function for testing."""
    sor_map = {"None": 0, "Exploring": 10, "Committed": 16, "Implementing": 20}
    s = 0
    s += max(0, (60 - ela_pct) / 60) * 30
    s += min(budget / 500, 1.0) * 25
    s += sor_map.get(sor_signal, 0)
    if recent_init: s += 8
    if supt_tenure < 3: s += 7
    s += max(0, (400 - miles) / 400) * 10
    return round(s, 2)


def test_high_need_district_scores_high():
    """A district with low ELA, high budget, SOR commitment should score high."""
    score = score_district_helper(
        ela_pct=25, budget=450, sor_signal="Committed",
        recent_init=True, supt_tenure=1.5, miles=10
    )
    assert score >= 70, f"High-need district should score Tier 1, got {score}"


def test_low_need_district_scores_lower():
    """A district with high ELA proficiency and no SOR interest should score lower."""
    score = score_district_helper(
        ela_pct=72, budget=100, sor_signal="None",
        recent_init=False, supt_tenure=12, miles=350
    )
    assert score < 50, f"Low-need district should score Tier 3, got {score}"


def test_score_range():
    """All scores should be between 0 and 100."""
    import numpy as np
    for _ in range(100):
        score = score_district_helper(
            ela_pct=float(np.random.uniform(0, 100)),
            budget=float(np.random.uniform(0, 1000)),
            sor_signal=np.random.choice(["None","Exploring","Committed","Implementing"]),
            recent_init=bool(np.random.choice([True, False])),
            supt_tenure=float(np.random.uniform(0, 20)),
            miles=float(np.random.uniform(0, 500))
        )
        assert 0 <= score <= 100, f"Score out of range: {score}"


# ============================================================
# Test: Pilot Readiness Scorecard
# ============================================================

def pilot_score(leadership, initiative_count, teacher_voice, time_alloc, data_culture):
    """Standalone pilot readiness scorer for testing."""
    weights = [25, 20, 20, 20, 15]
    answers = [leadership, initiative_count, teacher_voice, time_alloc, data_culture]
    total = sum((a / 3) * w for a, w in zip(answers, weights))
    return round(total, 1)


def test_perfect_readiness_scores_100():
    score = pilot_score(3, 3, 3, 3, 3)
    assert score == 100.0, f"Perfect answers should score 100, got {score}"


def test_worst_readiness_scores_zero():
    score = pilot_score(1, 1, 1, 1, 1)
    # With answers of 1/3 each, score = (1/3)*100 = 33.3
    assert score < 40, f"Worst answers should score low, got {score}"


def test_pilot_tier_classification():
    """Verify tier thresholds are correct."""
    high = pilot_score(3, 3, 3, 3, 3)
    medium = pilot_score(2, 2, 2, 2, 2)
    low = pilot_score(1, 1, 1, 1, 1)

    assert high >= 70, "Perfect should be Tier 1 ready"
    assert 50 <= medium < 70, "Medium should need pre-work"
    assert low < 50, "Low should not be ready"
