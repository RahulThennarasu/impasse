from google import genai
import json
import re
from typing import Dict

from agents.scenario_agent.scenario_prompt import create_prompt

# generates negotiation scenario and returns outputs for user and opponent
def generate_scenario(context: str) -> Dict:
    client = genai.Client()
    prompt = create_prompt(context)

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    scenario = _parse_json_response(response.text)

    # Transform opponent data into format OpponentAgent expects
    opponent_agent_config = _build_opponent_config(
        scenario["shared_context"],
        scenario["opponent_briefing"]
    )

    user_briefing = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["user_briefing"]
    }

    return {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_title": scenario.get("scenario_title"),
        "user_narrative": scenario.get("user_narrative"),
        "user_briefing": user_briefing,
        "opponent_agent_config": opponent_agent_config,
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

# formats a list as bullet points
def _format_list(items: list) -> str:
    if not items:
        return "None specified"
    return "\n".join(f"- {item}" for item in items)

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

