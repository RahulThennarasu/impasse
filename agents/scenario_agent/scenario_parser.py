"""
Parser to extract structured data from scenario text for use by opponent and coach agents.
"""

import re
from typing import Dict

def parse_scenario_text(scenario_text: str) -> Dict:
    """
    Parses the rich scenario text into structured data for agents.

    Returns a dict with keys for both opponent agent and coach agent.
    """

    def extract_section(text: str, section_name: str) -> str:
        """Extracts content between section headers"""
        pattern = f"{section_name}:(.*?)(?=\n[A-Z][a-z]+ [A-Z][a-z]+:|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    # Extract all sections
    context = extract_section(scenario_text, "Context and Background")
    parties = extract_section(scenario_text, "Parties Involved")
    objectives = extract_section(scenario_text, "Objectives and Interests")
    constraints = extract_section(scenario_text, "Constraints and Pressures")
    batna = extract_section(scenario_text, "Your BATNA")
    info_asymm = extract_section(scenario_text, "Information Asymmetries")
    tensions = extract_section(scenario_text, "Points of Tension")
    scope = extract_section(scenario_text, "Negotiation Scope")
    disposition = extract_section(scenario_text, "Counterparty Disposition")
    success = extract_section(scenario_text, "Success Criteria")

    # Parse objectives to separate user vs counterparty
    user_obj_match = re.search(r"- Your objectives:(.*?)(?=\n- |$)", objectives, re.DOTALL)
    user_interests_match = re.search(r"- Your underlying interests:(.*?)(?=\n- |$)", objectives, re.DOTALL)
    counterparty_obj_match = re.search(r"- [A-Za-z']+s objectives:(.*?)(?=\n- |$)", objectives, re.DOTALL)
    counterparty_int_match = re.search(r"- [A-Za-z']+s underlying interests:(.*?)(?=\n- |$)", objectives, re.DOTALL)

    user_objectives = user_obj_match.group(1).strip() if user_obj_match else ""
    user_interests = user_interests_match.group(1).strip() if user_interests_match else ""
    counterparty_objectives = counterparty_obj_match.group(1).strip() if counterparty_obj_match else ""
    counterparty_interests = counterparty_int_match.group(1).strip() if counterparty_int_match else ""

    # Extract counterparty name from parties section
    counterparty_name_match = re.search(r"- ([A-Za-z ]+) \([A-Za-z ]+\):", parties)
    counterparty_name = counterparty_name_match.group(1).strip() if counterparty_name_match else "Counterparty"

    # Parse info asymmetries
    you_dont_know = ""
    they_dont_know = ""
    if "You don't know:" in info_asymm:
        you_dont_know_match = re.search(r"- You don't know:(.*?)(?=\n- |$)", info_asymm, re.DOTALL)
        you_dont_know = you_dont_know_match.group(1).strip() if you_dont_know_match else ""
    if "doesn't know:" in info_asymm:
        they_dont_know_match = re.search(r"- .+ doesn't know:(.*?)(?=\n|$)", info_asymm, re.DOTALL)
        they_dont_know = they_dont_know_match.group(1).strip() if they_dont_know_match else ""

    # Parse negotiable vs non-negotiable
    negotiable = ""
    if "Negotiable:" in scope:
        negotiable_match = re.search(r"Negotiable:(.*?)(?=Non-negotiable:|$)", scope, re.DOTALL)
        negotiable = negotiable_match.group(1).strip() if negotiable_match else ""

    return {
        # For OpponentAgentV2
        "opponent": {
            "context": context,
            "counterparty_name": counterparty_name,
            "counterparty_objectives": counterparty_objectives,
            "counterparty_interests": counterparty_interests,
            "batna": you_dont_know,  # What you DON'T know becomes their hidden info
            "constraints": constraints,
            "information_asymmetries": they_dont_know,  # What THEY don't know
            "disposition": disposition,
            "personality": "professional"  # Can be extracted if specified in scenario
        },

        # For CoachAgentV2
        "coach": {
            "user_objectives": user_objectives,
            "user_batna": batna,
            "points_of_tension": tensions,
            "negotiable_items": negotiable,
            "success_criteria": success,
            "info_asymmetries": info_asymm
        },

        # Full scenario for reference
        "full_scenario": scenario_text
    }


# Example usage
if __name__ == "__main__":
    # Test with a sample scenario
    sample = """
Context and Background:
You are negotiating a salary...

Parties Involved:
- You: A software engineer
- Jordan (Engineering Manager): Your manager

Objectives and Interests:
- Your objectives: Get $185K
- Your underlying interests: Feel valued
- Jordan's objectives: Retain you within budget
- Jordan's underlying interests: Keep team morale high

Constraints and Pressures:
- 2 week deadline

Your BATNA (Best Alternative to Negotiated Agreement):
You have an offer at $195K

Information Asymmetries:
- You don't know: The salary band ceiling
- Jordan doesn't know: That you have an outside offer

Points of Tension:
- Your ask vs their budget

Negotiation Scope:
Negotiable: Base salary, equity
Non-negotiable: Job level

Counterparty Disposition:
Jordan will emphasize budget constraints

Success Criteria:
12%+ increase

Realism Details:
Typical SaaS ranges
"""

    result = parse_scenario_text(sample)
    print("Opponent config:", result['opponent'])
    print("\nCoach config:", result['coach'])
