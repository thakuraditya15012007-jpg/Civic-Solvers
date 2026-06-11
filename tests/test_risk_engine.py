"""
test_risk_engine.py — Pytest suite validating deterministic arithmetic property
bounds, multipliers, and bounds safety checks of the Risk evaluation module.
"""
import sys
import os
import pytest

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import ai_engine

def test_risk_score_determinism():
    """Verify that identical inputs produce identical scores for regulatory compliance audits."""
    args = ("Pothole", [], 5, False)
    score1 = ai_engine.calculate_risk_score(*args)
    score2 = ai_engine.calculate_risk_score(*args)
    assert score1 == score2
    assert isinstance(score1, int)

def test_monsoon_multiplier_impact():
    """Verify that monsoon vulnerability flags correctly escalate threat index values."""
    score_monsoon = ai_engine.calculate_risk_score("Blocked Drain", ["monsoon_vulnerability"], 7, False)
    score_dry = ai_engine.calculate_risk_score("Blocked Drain", [], 7, False)
    assert score_monsoon > score_dry
    assert score_monsoon == score_dry + 25  # Monsoon Context Multiplier is +25

def test_score_boundary_safety():
    """Verify that risk scores never exceed 100 or fall below 0 under extreme scenarios."""
    # Test floor bounds
    floor_score = ai_engine.calculate_risk_score("Other", [], 0, False)
    assert floor_score >= 0
    
    # Test ceiling bounds
    ceiling_score = ai_engine.calculate_risk_score(
        "Blocked Drain", ["near_school", "monsoon_vulnerability", "immediate_danger"], 10, True
    )
    assert ceiling_score == 100
