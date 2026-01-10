from google import genai
import json
import re
from typing import Dict

from agents.scenario_agent.scenario_prompt import create_prompt

# generates a negotiation scneario and returns structured outputs for user and the opponent
def generate_scenario(context: str) -> Dict:
    client = genai.Client()
    prompt = create_prompt(context)

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    scenario = _parse_json_response(response.text)

    opponent_context = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["opponent_briefing"]
    }

    user_briefing = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["user_briefing"]
    }

    return {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_title": scenario.get("scenario_title"),
        "user_narrative": scenario.get("user_narrative"),
        "user_briefing": user_briefing,
        "opponent_context": opponent_context,
        "scenario_metadata": scenario.get("scenario_metadata")
    }

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

