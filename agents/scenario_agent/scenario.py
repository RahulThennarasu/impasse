import os
from google import genai
import json
import logging
import re
from typing import Dict

from agents.scenario_agent.scenario_prompt import create_prompt

logger = logging.getLogger(__name__)

# generates negotiation scenario and returns outputs for user, opponent, and coach
def generate_scenario(context: str) -> Dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = os.getenv("GEMINI_SCENARIO_MODEL", "gemini-2.5-flash-lite")
    logger.info(f"Scenario generation model: {model}")
    prompt = create_prompt(context)

    def _request(max_tokens: int, compact: bool):
        contents = prompt
        if compact:
            contents += (
                "\n\nCRITICAL: Keep all fields concise. Limit any list to 3 items. "
                "Keep user_narrative to 2 short paragraphs."
            )
        return client.models.generate_content(
            model=model,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            ),
        )

    max_tokens = int(os.getenv("GEMINI_SCENARIO_TOKENS", "2000"))
    response = _request(max_tokens, compact=False)
    try:
        scenario = _extract_scenario_from_response(response)
    except Exception:
        texts = _collect_response_texts(response)
        sample = texts[0] if texts else ""
        if _is_truncated(sample):
            retry_tokens = int(os.getenv("GEMINI_SCENARIO_TOKENS_RETRY", "2400"))
            response = _request(retry_tokens, compact=True)
            scenario = _extract_scenario_from_response(response)
        else:
            raise
    # scenario is parsed above

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


def _extract_scenario_from_response(response) -> Dict:
    if hasattr(response, "parsed") and response.parsed is not None:
        if isinstance(response.parsed, dict):
            return response.parsed
        if isinstance(response.parsed, str):
            try:
                return _parse_json_response(response.parsed)
            except Exception:
                pass

    candidates = _collect_response_texts(response)
    logger.info(
        "Scenario response candidates: text=%s, candidates=%s",
        bool(getattr(response, "text", None)),
        len(getattr(response, "candidates", []) or []),
    )

    for candidate in candidates:
        try:
            return _parse_json_response(candidate)
        except Exception:
            continue

    raise ValueError("Could not parse JSON from response: <empty>")


def _collect_response_texts(response) -> list[str]:
    candidates: list[str] = []
    if hasattr(response, "text") and response.text:
        candidates.append(response.text)

    if hasattr(response, "candidates"):
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content and getattr(content, "parts", None):
                for part in content.parts:
                    text = getattr(part, "text", None)
                    if text:
                        candidates.append(text)
    return candidates


def _is_truncated(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip()
    if not stripped.endswith("}"):
        return True
    return stripped.count("{") > stripped.count("}")

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
    def _sanitize_json(text: str) -> str:
        text = text.strip()
        # Remove trailing commas before closing braces/brackets.
        text = re.sub(r",\s*([}\]])", r"\1", text)
        return text

    def _escape_control_chars(text: str) -> str:
        out = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                out.append(ch)
                continue
            if ch == "\\":
                escape = True
                out.append(ch)
                continue
            if ch == "\"":
                in_string = not in_string
                out.append(ch)
                continue
            if in_string and ch in "\n\r\t":
                out.append({"\\n": "\\n", "\\r": "\\r", "\\t": "\\t"}.get(ch, ch))
                continue
            out.append(ch)
        return "".join(out)

    def _strip_invalid_controls(text: str) -> str:
        # Remove non-printable control chars (except whitespace) that break json parsing.
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    def _raw_decode(text: str) -> Dict | None:
        decoder = json.JSONDecoder()
        try:
            obj, _ = decoder.raw_decode(text)
            return obj
        except json.JSONDecodeError:
            return None

    def _try_load(text: str) -> Dict | None:
        if not text:
            return None
        try:
            return json.loads(text, strict=False)
        except json.JSONDecodeError:
            return None

    cleaned = _strip_invalid_controls(response_text)
    direct = _try_load(cleaned) or _raw_decode(cleaned)
    if direct is not None:
        return direct

    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        candidate = json_match.group(1)
        candidate = _strip_invalid_controls(candidate)
        parsed = _try_load(candidate) or _raw_decode(candidate)
        if parsed is None:
            sanitized = _sanitize_json(candidate)
            parsed = _try_load(sanitized) or _raw_decode(sanitized)
        if parsed is None:
            escaped = _escape_control_chars(candidate)
            parsed = _try_load(escaped) or _raw_decode(escaped)
        if parsed is None:
            escaped_sanitized = _escape_control_chars(_sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(escaped_sanitized)
        if parsed is not None:
            return parsed

    brace_index = response_text.find("{")
    if brace_index != -1:
        candidate = response_text[brace_index:]
        candidate = _strip_invalid_controls(candidate)
        parsed = _try_load(candidate) or _raw_decode(candidate)
        if parsed is None:
            sanitized = _sanitize_json(candidate)
            parsed = _try_load(sanitized) or _raw_decode(sanitized)
        if parsed is None:
            escaped = _escape_control_chars(candidate)
            parsed = _try_load(escaped) or _raw_decode(escaped)
        if parsed is None:
            escaped_sanitized = _escape_control_chars(_sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(escaped_sanitized)
        if parsed is not None:
            return parsed

    first = response_text.find("{")
    last = response_text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = response_text[first:last + 1]
        parsed = _try_load(candidate) or _raw_decode(candidate)
        if parsed is None:
            sanitized = _sanitize_json(candidate)
            parsed = _try_load(sanitized) or _raw_decode(sanitized)
        if parsed is None:
            escaped = _escape_control_chars(candidate)
            parsed = _try_load(escaped) or _raw_decode(escaped)
        if parsed is None:
            escaped_sanitized = _escape_control_chars(_sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(escaped_sanitized)
        if parsed is not None:
            return parsed

    sanitized = _sanitize_json(_strip_invalid_controls(response_text))
    parsed = _try_load(sanitized) or _raw_decode(sanitized)
    if parsed is None:
        escaped = _escape_control_chars(response_text)
        parsed = _try_load(escaped) or _raw_decode(escaped)
    if parsed is not None:
        return parsed

    raise ValueError(f"Could not parse JSON from response: {response_text[:500]}...")
