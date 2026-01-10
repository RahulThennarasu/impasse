from groq import Groq
import os
import json
import re
from typing import Dict

from agents.scenario_agent.scenario_prompt import create_prompt

# generates negotiation scenario and returns outputs for user, opponent, and coach
def generate_scenario(context: str) -> Dict:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_SCENARIO_MODEL", "llama-3.3-70b-versatile")
    prompt = create_prompt(context)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON that matches the requested schema. No extra text."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=int(os.getenv("GROQ_SCENARIO_TOKENS", "900")),
    )

    scenario_text = response.choices[0].message.content or ""
    scenario = _parse_json_response(scenario_text)

    # Transform opponent data into format OpponentAgent expects
    opponent_agent_config = _build_opponent_config(
        scenario["shared_context"],
        scenario["opponent_briefing"]
    )

    # Transform user data into format CoachAgent expects
    coach_agent_config = _build_coach_config(
        scenario["shared_context"],
        scenario["user_briefing"],
        scenario["opponent_briefing"]
    )

    user_briefing = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["user_briefing"]
    }

    # Build a nicely formatted description for frontend display
    description = _build_display_description(
        scenario.get("user_narrative", ""),
        scenario.get("user_briefing", {}),
        scenario.get("scenario_metadata", {})
    )

    return {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_title": scenario.get("scenario_title"),
        "user_narrative": scenario.get("user_narrative"),
        "description": description,
        "title": scenario.get("scenario_title"),
        "role": scenario.get("user_briefing", {}).get("role_name", "Negotiator"),
        "user_briefing": user_briefing,
        "opponent_agent_config": opponent_agent_config,
        "coach_agent_config": coach_agent_config,
        "scenario_metadata": scenario.get("scenario_metadata")
    }

# transforms scenario data into flat format for OpponentAgent
def _build_opponent_config(shared_context: Dict, opponent_briefing: Dict) -> Dict:
    # Build context string from shared_context
    context = f"""{shared_context.get('situation', '')}
        Relationship History: {shared_context.get('relationship_history', '')}

        Setting: {shared_context.get('setting', '')}

        Stakes: {shared_context.get('stakes', '')}
    """

    objectives = opponent_briefing.get("objectives", {})
    objectives_str = f"""Primary: {objectives.get('primary', '')}
        Secondary Goals:
        {_format_list(objectives.get('secondary', []))}
    """

    interests_str = _format_list(objectives.get("underlying_interests", []))

    batna = opponent_briefing.get("batna", {})
    batna_str = f"""{batna.get('description', '')}
        Strength: {batna.get('strength', 'unknown')}
        Downsides of walking away:
        {_format_list(batna.get('downsides', []))}
    """

    # Build constraints list (combine constraints + non_negotiables)
    constraints = opponent_briefing.get("constraints", [])
    non_negotiables = opponent_briefing.get("non_negotiables", [])
    all_constraints = constraints + [f"Non-negotiable: {n}" for n in non_negotiables]

    # Build information asymmetries string
    private_info = opponent_briefing.get("private_information", [])
    info_asymmetries = _format_list(private_info)

    # Build disposition string from tactics and concession patterns
    tactics = opponent_briefing.get("tactics_to_use", [])
    concession = opponent_briefing.get("concession_pattern", {})
    emotional_triggers = opponent_briefing.get("emotional_triggers", [])

    disposition_str = f"""Tactics to Use:
        {_format_list(tactics)}

        Concession Pattern:
        - Initial stance: {concession.get('initial_stance', '')}
        - Resistance points: {', '.join(concession.get('resistance_points', []))}
        - Flexibility points: {', '.join(concession.get('flexibility_points', []))}
        - Final fallback: {concession.get('final_fallback', '')}

        Emotional Triggers:
        {_format_list(emotional_triggers)}

        Success Criteria:
        - Good outcome: {opponent_briefing.get('success_criteria', {}).get('good_outcome', '')}
        - Great outcome: {opponent_briefing.get('success_criteria', {}).get('great_outcome', '')}
    """

    # Build personality string from traits
    personality_traits = opponent_briefing.get("personality_traits", [])
    personality_str = ", ".join(personality_traits) if personality_traits else "neutral"

    # Build name from role and character name
    character_name = opponent_briefing.get("character_name", "")
    role_name = opponent_briefing.get("role_name", "Counterparty")
    name = f"{character_name} ({role_name})" if character_name else role_name

    return {
        "context": context,
        "counterparty_name": name,
        "counterparty_objectives": objectives_str,
        "counterparty_interests": interests_str,
        "batna": batna_str,
        "constraints": all_constraints,
        "information_asymmetries": info_asymmetries,
        "disposition": disposition_str,
        "personality": personality_str,
        # Also include raw data for flexibility
        "negotiables": opponent_briefing.get("negotiables", []),
        "role_description": opponent_briefing.get("role_description", ""),
    }

# transforms scenario data into flat format for CoachAgent
def _build_coach_config(shared_context: Dict, user_briefing: Dict, opponent_briefing: Dict) -> Dict:
    """
    CoachAgent expects:
    - user_objectives: What you're trying to achieve
    - user_batna: Your walkaway alternative
    - points_of_tension: Known conflicts
    - negotiable_items: What's on the table
    - success_criteria: What defines a good outcome
    - info_asymmetries: What you know vs. what they know
    """
    # Build user objectives string
    user_objectives = user_briefing.get("objectives", {})
    objectives_str = f"""Primary: {user_objectives.get('primary', '')}

Secondary Goals:
{_format_list(user_objectives.get('secondary', []))}

Underlying Interests:
{_format_list(user_objectives.get('underlying_interests', []))}"""

    # Build user BATNA string
    user_batna = user_briefing.get("batna", {})
    batna_str = f"""{user_batna.get('description', '')}
Strength: {user_batna.get('strength', 'unknown')}
Downsides of walking away:
{_format_list(user_batna.get('downsides', []))}"""

    # Build points of tension from both perspectives
    # Combine user constraints, non-negotiables, and general stakes
    user_constraints = user_briefing.get("constraints", [])
    user_non_negotiables = user_briefing.get("non_negotiables", [])
    opponent_non_negotiables = opponent_briefing.get("non_negotiables", [])

    tensions = []
    tensions.append(f"Stakes: {shared_context.get('stakes', '')}")
    tensions.append(f"\nUser's constraints:\n{_format_list(user_constraints)}")
    tensions.append(f"\nUser's non-negotiables:\n{_format_list(user_non_negotiables)}")
    tensions.append(f"\nOpponent's likely non-negotiables:\n{_format_list(opponent_non_negotiables)}")
    tensions_str = "\n".join(tensions)

    # Build negotiable items (user's perspective)
    negotiables = user_briefing.get("negotiables", [])
    negotiables_str = _format_list(negotiables)

    # Build success criteria
    success = user_briefing.get("success_criteria", {})
    success_str = f"""Good outcome: {success.get('good_outcome', '')}
Great outcome: {success.get('great_outcome', '')}"""

    # Build information asymmetries from user's perspective
    # What user knows privately + what user doesn't know about opponent
    user_private = user_briefing.get("private_information", [])
    opponent_private = opponent_briefing.get("private_information", [])

    asymmetries_str = f"""What YOU know that they don't:
{_format_list(user_private)}

What THEY likely know that you don't:
{_format_list(opponent_private)}"""

    return {
        "user_objectives": objectives_str,
        "user_batna": batna_str,
        "points_of_tension": tensions_str,
        "negotiable_items": negotiables_str,
        "success_criteria": success_str,
        "info_asymmetries": asymmetries_str,
    }


# formats a list as bullet points
def _format_list(items: list) -> str:
    if not items:
        return "None specified"
    return "\n".join(f"- {item}" for item in items)


def _build_display_description(narrative: str, user_briefing: Dict, metadata: Dict) -> str:
    """
    Build a nicely formatted description paragraph for frontend display.
    Combines the immersive narrative with key context for a polished user experience.
    """
    # Start with the narrative if available (this is the immersive 3-4 paragraph briefing)
    if narrative:
        return narrative

    # Fallback: build a description from available data
    role = user_briefing.get("role_name", "Negotiator")
    role_desc = user_briefing.get("role_description", "")
    objectives = user_briefing.get("objectives", {})
    primary_goal = objectives.get("primary", "")
    difficulty = metadata.get("difficulty", "intermediate")
    domain = metadata.get("domain", "business")
    skills = metadata.get("key_skills_tested", [])

    parts = []

    if role_desc:
        parts.append(role_desc)

    if primary_goal:
        parts.append(f"Your primary objective is to {primary_goal.lower()}.")

    if skills:
        skills_text = ", ".join(skills[:3])
        parts.append(f"This {difficulty} {domain} scenario will test your skills in {skills_text}.")

    if parts:
        return " ".join(parts)

    # Ultimate fallback
    return f"A {difficulty} negotiation scenario where you play the role of {role}."

# parses json from LLM responses
def _parse_json_response(response_text: str) -> Dict:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {response_text[:500]}...")
