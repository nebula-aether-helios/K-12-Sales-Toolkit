import sys
import os
import pytest
import pandas as pd

# Add source directories to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'K-12-Sales-Toolkit')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'K-12-Sales-Toolkit', 'src')))

try:
    from src.data_fetchers import fetch_caaspp_data, fetch_esser_grants
    from src.researcher import SuperintendentResearcher
except ImportError:
    # Adjust for running from different context
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    from data_fetchers import fetch_caaspp_data, fetch_esser_grants
    from researcher import SuperintendentResearcher

def test_fetch_caaspp_data_mock():
    """Test CAASPP fetching (mock mode)."""
    # Create a temp dir for output to avoid overwriting real data if running in parallel
    df = fetch_caaspp_data(year=2024, output_dir="/tmp")
    assert not df.empty
    assert "district_name" in df.columns
    assert "Los Angeles Unified" in df["district_name"].values

def test_fetch_esser_grants_mock():
    """Test ESSER fetching (mock mode)."""
    df = fetch_esser_grants(output_dir="/tmp")
    assert not df.empty
    assert "Recipient Name" in df.columns
    assert "Los Angeles Unified" in df["Recipient Name"].values

def test_researcher_initialization():
    """Test SuperintendentResearcher init."""
    researcher = SuperintendentResearcher()
    assert researcher is not None

def test_generate_ai_brief_mock():
    """Test AI brief generation (mock mode)."""
    researcher = SuperintendentResearcher()
    profile = {
        "name": "Dr. Test",
        "district": "Test District",
        "district_data": "Data",
        "news_mentions": [],
        "linkedin": "Bio"
    }
    # Force mock by ensuring no keys
    researcher.openai_key = None
    researcher.google_key = None

    brief = researcher.generate_ai_brief(profile)
    assert "pain_points" in brief
    assert "best_angle" in brief
    assert "talking_points" in brief
