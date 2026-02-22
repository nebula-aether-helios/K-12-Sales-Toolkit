"""
personalized_email_generator.py
AI-powered email personalization engine for K-8 education outreach.
Generates highly personalized emails using prospect research data.
"""
import os, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class K8EmailGenerator:
    """
    GPT-powered email generator for K-8 education sales outreach.
    
    Takes prospect research data and generates 3 email variants:
    1. Subject-line-first (short, punchy)
    2. Problem-focused (lead with their pain)
    3. Peer-story (lead with similar district)

    Dependencies:
        - openai >= 1.3.0
        - OPENAI_API_KEY in .env

    TODO (Jules):
        - Add A/B testing tracker (log which variants get responses)
        - Integrate with HubSpot to auto-enroll prospects in sequences
        - Add follow-up email generator (3-touch sequence)
    """

    LP_CONTEXT = """
    Literacy Partners is a boutique K-8 professional development firm founded by
    Dahlia Dallal. They use the Science of Reading to create world-class,
    tailored PD that increases test scores while fostering joy in reading.
    Their model is relationship-driven, ongoing (not drive-by workshops),
    and differentiated by school readiness level.
    """

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.generated_emails = []

    def _build_prompt(self, prospect: dict, variant: str) -> str:
        """Build GPT prompt for a specific email variant."""
        base_context = f"""
        You are a mission-driven K-8 education sales rep writing on behalf of Literacy Partners.
        
        About Literacy Partners:
        {self.LP_CONTEXT}
        
        Prospect Research:
        - Name: {prospect.get('name', '[Name]')}
        - Title: {prospect.get('title', '[Title]')}
        - District: {prospect.get('district', '[District]')}
        - District ELA Proficiency: {prospect.get('ela_proficiency_pct', 'TBD')}%
        - Recent Initiative: {prospect.get('recent_initiative', 'None found')}
        - SOR Adoption Stage: {prospect.get('sor_stage', 'Exploring')}
        - Key Pain Point: {prospect.get('pain_point', 'Teacher retention in literacy coaching')}
        - Funding Available: {prospect.get('funding_note', 'ESSER III expires Sept 2026')}
        """

        variants = {
            "subject_first": (
                "Write a cold email leading with a compelling subject line. "
                "Max 3 sentences in body. Include a soft CTA for a 15-min call. "
                "Tone: warm, educator-to-educator, NOT salesy."
            ),
            "problem_focused": (
                "Write a cold email that opens by naming their specific pain point, "
                "then shows how LP solves it. End with a case study teaser. "
                "Max 4 sentences. Tone: empathetic, specific, credible."
            ),
            "peer_story": (
                "Write a cold email that opens with a brief story from a similar district "
                "that faced the same challenge, then connects it to LP. "
                "Max 4 sentences. Tone: storytelling, relatable, no buzzwords."
            ),
        }

        return base_context + "\n\nEmail Style: " + variants.get(variant, variants["subject_first"])

    def generate(self, prospect: dict) -> dict:
        """
        Generate 3 personalized email variants for a prospect.
        
        Args:
            prospect: dict with keys: name, title, district, ela_proficiency_pct,
                      recent_initiative, sor_stage, pain_point, funding_note
        
        Returns:
            dict with keys: prospect_name, district, variants (list of 3 emails),
                            generated_at, ready_to_send
        """
        variants = {}

        for v in ["subject_first", "problem_focused", "peer_story"]:
            # TODO (Jules): Uncomment when OPENAI_API_KEY is available
            # from openai import OpenAI
            # client = OpenAI(api_key=self.openai_key)
            # prompt = self._build_prompt(prospect, v)
            # response = client.chat.completions.create(
            #     model="gpt-4-turbo-preview",
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=300,
            #     temperature=0.7,
            # )
            # variants[v] = response.choices[0].message.content

            # Placeholder templates — replace with GPT call above
            variants[v] = self._get_template(prospect, v)

        result = {
            "prospect_name": prospect.get("name"),
            "district": prospect.get("district"),
            "generated_at": datetime.now().isoformat(),
            "variants": variants,
            "ready_to_send": False,  # Set to True after human review
            "notes": "Review and personalize before sending. Add 1 specific detail.",
        }

        self.generated_emails.append(result)
        return result

    def _get_template(self, prospect: dict, variant: str) -> str:
        """Placeholder templates — replace with GPT output."""
        name = prospect.get("name", "[Name]")
        district = prospect.get("district", "[District]")
        ela = prospect.get("ela_proficiency_pct", "TBD")
        pain = prospect.get("pain_point", "teacher retention")

        templates = {
            "subject_first": f"""Subject: SOR Implementation Support for {district}

Hi {name},

I saw {district} recently committed to Science of Reading — 
congratulations on that shift. I work with Literacy Partners, and we specialize in 
exactly the coaching infrastructure that makes SOR stick for teachers long-term.

Worth 15 minutes to explore? 

[Your Name]
P.S. — I'm a former K-8 teacher. I promise not to waste your time.""",

            "problem_focused": f"""Subject: The gap between SOR adoption and teacher confidence

Hi {name},

With {ela}% ELA proficiency and SOR adoption underway, {district} is at exactly the
point where implementation quality determines everything — and that's usually a coaching gap.

That's Literacy Partners' specialty: ongoing, tailored coaching (not workshops) that
turns SOR commitment into measurable teacher practice change.

Can I show you a 1-pager from a similar district? 15 minutes?

[Your Name]""",

            "peer_story": f"""Subject: How [Similar District] solved {pain}

Hi {name},

A year ago, a district a lot like {district} was dealing with {pain}.
They tried workshops. They didn't move the needle.

Then they piloted Literacy Partners' ongoing coaching model.
Year 1: Teacher confidence scores up 40%. Year 2: They expanded district-wide.

Would you like to hear how they did it?

[Your Name]""",
        }
        return templates.get(variant, templates["subject_first"])

    def batch_generate(self, prospects: list) -> list:
        """Generate emails for a list of prospects."""
        results = []
        for p in prospects:
            result = self.generate(p)
            results.append(result)
        return results

    def export_to_csv(self, output_path: str = "generated_emails.csv"):
        """Export all generated emails to CSV for HubSpot import."""
        rows = []
        for email in self.generated_emails:
            for variant, content in email["variants"].items():
                rows.append({
                    "prospect_name": email["prospect_name"],
                    "district": email["district"],
                    "variant": variant,
                    "email_content": content,
                    "generated_at": email["generated_at"],
                    "ready_to_send": email["ready_to_send"],
                })
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} email variants to {output_path}")
        return df


if __name__ == "__main__":
    generator = K8EmailGenerator()

    # Sample prospect
    sample_prospect = {
        "name": "Dr. [Assistant Superintendent]",
        "title": "Assistant Superintendent of Curriculum & Instruction",
        "district": "Los Angeles Unified School District",
        "ela_proficiency_pct": 38,
        "recent_initiative": "Science of Reading adoption (Feb 2024)",
        "sor_stage": "Committed",
        "pain_point": "inconsistent SOR implementation across schools",
        "funding_note": "ESSER III funds expire Sept 2026",
    }

    print("K-8 Email Personalization Engine")
    print("=" * 50)
    result = generator.generate(sample_prospect)

    print(f"\nGenerated 3 email variants for: {result['prospect_name']}")
    print(f"District: {result['district']}")
    print(f"\n{'='*50}")

    for variant, content in result["variants"].items():
        print(f"\n--- VARIANT: {variant.upper().replace('_', ' ')} ---")
        print(content)
        print()
