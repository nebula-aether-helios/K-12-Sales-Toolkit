import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SuperintendentResearcher:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")

        # Load data cache if available
        # Try multiple paths
        possible_paths = [
            "../data/processed/caaspp_ela_2024.csv",
            "K-12-Sales-Toolkit/data/processed/caaspp_ela_2024.csv",
            "data/processed/caaspp_ela_2024.csv"
        ]
        self.caaspp_data = pd.DataFrame()
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    self.caaspp_data = pd.read_csv(p)
                    break
                except:
                    continue

    def research(self, name: str, district: str) -> dict:
        print(f"🔬 Researching {name} at {district}...")

        # 1. Get District Data
        district_data = self._get_district_context(district)

        # 2. Get News/Signals (Mocked for now or use tracker)
        news = self._get_recent_news(district)

        # 3. Get LinkedIn/Web Bio (Simulated)
        bio = self._get_simulated_bio(name, district)

        profile = {
            "name": name,
            "district": district,
            "district_data": district_data,
            "news_mentions": news,
            "linkedin": bio,
            "timestamp": datetime.now().isoformat()
        }

        # 4. Generate AI Brief
        brief = self.generate_ai_brief(profile)
        profile["ai_brief"] = brief

        return profile

    def _get_district_context(self, district_name):
        # Filter CAASPP data
        if not self.caaspp_data.empty:
            d_data = self.caaspp_data[self.caaspp_data["district_name"] == district_name]
            if not d_data.empty:
                # Calculate avg proficiency if available
                if "percentage_standard_met_and_above" in d_data.columns:
                    avg_prof = d_data["percentage_standard_met_and_above"].mean()
                    return f"ELA Proficiency: {avg_prof:.1f}% (approx)"
        return "District data not found in cache."

    def _get_recent_news(self, district_name):
        # In a real scenario, call NewsAPI here
        return [
            f"{district_name} adopts new literacy curriculum",
            f"Superintendent emphasizes equity in recent town hall"
        ]

    def _get_simulated_bio(self, name, district):
        return f"{name} has been Superintendent at {district} for 3 years. Previously Asst. Supt at a neighboring district. Focuses on equity and early literacy."

    def generate_ai_brief(self, profile_data: dict) -> dict:
        prompt = f"""
        You are a K-8 education sales strategist for Literacy Partners.

        Based on this research about {profile_data['name']} at {profile_data['district']}:

        District Data: {profile_data.get('district_data')}
        Recent News: {profile_data.get('news_mentions')}
        LinkedIn Activity: {profile_data.get('linkedin')}

        Generate:
        1. Top 3 pain points (inferred from the data)
        2. Best outreach angle for Literacy Partners
        3. Suggested email subject line
        4. 5 key talking points for the first call

        Be specific. Use data from the research to make concrete recommendations.
        Return as valid JSON with keys: pain_points, best_angle, email_subject, talking_points.
        """

        # Try OpenAI
        if self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                import json
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"OpenAI failed: {e}")

        # Try Gemini
        if self.google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                import json
                return json.loads(text)
            except Exception as e:
                print(f"Gemini failed: {e}")

        # Fallback
        return {
            "pain_points": [
                "Stagnant ELA scores despite new curriculum",
                "Teacher burnout from constant initiative shifts",
                "Lack of consistent coaching across schools"
            ],
            "best_angle": "Literacy Partners provides the 'glue' (coaching) that makes their new curriculum actually work.",
            "email_subject": f"Supporting your literacy goals at {profile_data['district']}",
            "talking_points": [
                "We know you've adopted Science of Reading - how is implementation going?",
                "Our model focuses on teacher retention, not just scores.",
                "We can use ESSER funds before they expire.",
                "We customize to each school's readiness.",
                "Dahlia (our founder) would love to share a case study."
            ]
        }
