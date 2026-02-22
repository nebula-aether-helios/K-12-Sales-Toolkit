"""
science_of_reading_adoption_tracker.py
Tracks Science of Reading adoption signals across CA school districts
using public news, board minutes, and CDE data.
"""
import os, time, json, requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class SORAdoptionTracker:
    """
    Tracks which California districts have adopted, are exploring,
    or are resistant to the Science of Reading framework.

    Data Sources:
        - Google News API (NEWSAPI_KEY in .env)
        - CDE Policy Tracker: https://www.cde.ca.gov/ci/rl/im/
        - EdWeek SOR Coverage: https://www.edweek.org
        - District Board Meeting Minutes (Google Search)

    TODO (Jules):
        - Implement live Google News scraper
        - Add CDE policy document parser
        - Schedule to run weekly (cron job or GitHub Action)
    """

    SOR_KEYWORDS = [
        "science of reading", "SOR", "phonics instruction",
        "structured literacy", "phonemic awareness",
        "decodable readers", "science-based reading",
        "AB 2222",  # California SOR legislation
    ]

    RESISTANCE_KEYWORDS = [
        "balanced literacy", "whole language", "three-cueing",
        "MSV", "leveled readers only",
    ]

    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY")
        self.results = []

    def search_district_news(self, district_name: str, days_back: int = 90) -> list:
        """
        Search NewsAPI for recent SOR mentions for a district.
        
        TODO (Jules): Uncomment API call when NEWSAPI_KEY is available.
        API Docs: https://newsapi.org/docs/endpoints/everything
        """
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        query = f'"{district_name}" AND ("{" OR ".join(self.SOR_KEYWORDS)}")'

        # TODO: Uncomment for live data
        # url = "https://newsapi.org/v2/everything"
        # params = {
        #     "q": query,
        #     "from": from_date,
        #     "sortBy": "relevancy",
        #     "apiKey": self.api_key,
        #     "language": "en",
        #     "pageSize": 10,
        # }
        # resp = requests.get(url, params=params)
        # return resp.json().get("articles", [])

        # Placeholder response
        return [{"title": f"SOR news for {district_name}", "publishedAt": from_date,
                 "description": "Sample article — replace with real NewsAPI call"}]

    def classify_adoption_stage(self, district_name: str) -> dict:
        """
        Classify a district's SOR adoption stage based on news signals.
        
        Returns:
            dict with keys: stage, confidence, evidence, last_updated
        """
        articles = self.search_district_news(district_name)

        # Simple keyword scoring (replace with NLP model — see TODO)
        sor_score = 0
        resistance_score = 0

        for article in articles:
            text = f"{article.get('title','')} {article.get('description','')}".lower()
            sor_score += sum(kw.lower() in text for kw in self.SOR_KEYWORDS)
            resistance_score += sum(kw.lower() in text for kw in self.RESISTANCE_KEYWORDS)

        # TODO (Jules/Gemini): Replace rule-based classifier with
        # fine-tuned BERT model trained on district SOR adoption signals
        if sor_score >= 3:
            stage = "Implementing"
            confidence = min(0.9, sor_score * 0.15)
        elif sor_score >= 1:
            stage = "Committed"
            confidence = 0.6
        elif resistance_score >= 2:
            stage = "Resistant"
            confidence = 0.7
        else:
            stage = "Exploring"
            confidence = 0.4

        return {
            "district": district_name,
            "stage": stage,
            "confidence": round(confidence, 2),
            "sor_signal_count": sor_score,
            "resistance_signal_count": resistance_score,
            "articles_analyzed": len(articles),
            "last_updated": datetime.now().isoformat(),
        }

    def track_district_list(self, districts: list) -> pd.DataFrame:
        """Run adoption tracking for a list of districts."""
        results = []
        for d in districts:
            print(f"  Tracking: {d}...")
            result = self.classify_adoption_stage(d)
            results.append(result)
            time.sleep(0.2)  # Rate limiting

        df = pd.DataFrame(results)
        df.to_csv("sor_adoption_tracker_output.csv", index=False)
        print(f"\nTracking complete: {len(df)} districts")
        print(f"Saved to sor_adoption_tracker_output.csv")
        return df


if __name__ == "__main__":
    tracker = SORAdoptionTracker()

    # Sample district list — replace with full list from district prioritization model
    sample_districts = [
        "Los Angeles Unified School District",
        "Long Beach Unified School District",
        "Pasadena Unified School District",
        "Compton Unified School District",
        "Inglewood Unified School District",
    ]

    print("Science of Reading Adoption Tracker")
    print("=" * 50)
    df = tracker.track_district_list(sample_districts)
    print(df[["district", "stage", "confidence"]].to_string(index=False))
