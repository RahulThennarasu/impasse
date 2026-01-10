from google import genai
import os

from agents.scenario_agent.scenario_prompt import create_prompt


def generate_response(context: str) -> str:
    client = genai.Client()
    prompt = create_prompt(context)

    scenario = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    opponent_context = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["opponent_briefing"]
    }

    user_content = {
        "shared_context": scenario["shared_context"],
        "briefing": scenario["user_briefing"]
    }

