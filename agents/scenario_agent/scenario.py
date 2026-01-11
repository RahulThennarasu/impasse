import os
from google import genai
from groq import Groq
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
    fallback_model = os.getenv("GEMINI_SCENARIO_FALLBACK_MODEL", "gemini-2.5-flash")
    groq_fallback_model = os.getenv("GROQ_SCENARIO_FALLBACK_MODEL", "groq/compound")
    logger.info(f"Scenario generation model: {model}")
    prompt = create_prompt(context)

    def _request(model_name: str, max_tokens: int, compact: bool):
        contents = prompt
        if compact:
            contents += (
                "\n\nCRITICAL: Keep all fields concise. Limit any list to 3 items. "
                "Keep user_narrative to 2 short paragraphs."
            )
        return client.models.generate_content(
            model=model_name,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            ),
        )

    max_tokens = int(os.getenv("GEMINI_SCENARIO_TOKENS", "8000"))
    response = None
    try:
        response = _request(model, max_tokens, compact=False)
        scenario = _extract_scenario_from_response(response)
    except Exception as e:
        texts = _collect_response_texts(response) if response is not None else []
        sample = texts[0] if texts else ""
        error_text = str(e).lower()
        try:
            if "503" in error_text or "unavailable" in error_text or "overloaded" in error_text:
                logger.warning("Scenario model overloaded; retrying with fallback model.")
                response = _request(fallback_model, max_tokens, compact=False)
                scenario = _extract_scenario_from_response(response)
            elif _is_truncated(sample):
                retry_tokens = int(os.getenv("GEMINI_SCENARIO_TOKENS_RETRY", "8000"))
                logger.warning(f"Response truncated (sample length: {len(sample)}), retrying with {retry_tokens} tokens and compact prompt")
                response = _request(model, retry_tokens, compact=True)
                scenario = _extract_scenario_from_response(response)
            else:
                raise
        except Exception:
            logger.warning("Gemini scenario parsing failed; falling back to Groq.")
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            groq_response = groq_client.chat.completions.create(
                model=groq_fallback_model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON that matches the requested schema. No extra text."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=int(os.getenv("GROQ_SCENARIO_TOKENS", "900")),
            )
            scenario_text = groq_response.choices[0].message.content or ""
            scenario = _parse_json_response(scenario_text)
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
    # First check if response has parsed attribute
    if hasattr(response, "parsed") and response.parsed is not None:
        logger.debug(f"Found parsed attribute, type: {type(response.parsed)}")
        if isinstance(response.parsed, dict):
            return response.parsed
        if isinstance(response.parsed, str):
            try:
                return _parse_json_response(response.parsed)
            except Exception as e:
                logger.debug(f"Failed to parse response.parsed as JSON: {e}")

    # Collect all possible text candidates
    candidates = _collect_response_texts(response)
    logger.info(
        "Scenario response candidates: text=%s, candidates=%s",
        bool(getattr(response, "text", None)),
        len(getattr(response, "candidates", []) or []),
    )

    # Log first 200 chars of each candidate for debugging
    for i, candidate in enumerate(candidates):
        logger.debug(f"Candidate {i} preview: {candidate[:200] if candidate else '<empty>'}...")

    # Try parsing each candidate
    for i, candidate in enumerate(candidates):
        try:
            logger.info(f"Attempting to parse candidate {i}, length: {len(candidate)}, starts with: {candidate[:50]}, ends with: {candidate[-50:]}")
            result = _parse_json_response(candidate)
            logger.info(f"Successfully parsed candidate {i}")
            return result
        except Exception as e:
            logger.error(f"Failed to parse candidate {i}: {str(e)}")
            logger.error(f"Candidate {i} first 1000 chars: {candidate[:1000]}")
            logger.error(f"Candidate {i} last 500 chars: {candidate[-500:]}")
            continue

    # If all failed, log detailed error info
    logger.error(f"Response type: {type(response)}")
    logger.error(f"Response attributes: {dir(response)}")
    if hasattr(response, "text"):
        logger.error(f"Response.text type: {type(response.text)}, value: {str(response.text)[:500]}")
    if hasattr(response, "candidates") and response.candidates:
        logger.error(f"Number of candidates: {len(response.candidates)}")
        for i, cand in enumerate(response.candidates[:2]):  # Log first 2 candidates
            logger.error(f"Candidate {i} structure: {dir(cand)}")
            if hasattr(cand, "content"):
                logger.error(f"Candidate {i} content: {cand.content}")

    raise ValueError("Could not parse JSON from response: <empty>")


def _collect_response_texts(response) -> list[str]:
    candidates: list[str] = []

    # Check response.text
    has_text_attr = hasattr(response, "text")
    text_value = getattr(response, "text", None) if has_text_attr else None
    logger.debug(f"Response has 'text' attribute: {has_text_attr}, value type: {type(text_value)}, is truthy: {bool(text_value)}")

    if has_text_attr and text_value:
        logger.debug(f"Adding response.text to candidates (length: {len(text_value)})")
        candidates.append(text_value)

    # Check response.candidates
    if hasattr(response, "candidates"):
        logger.debug(f"Response has candidates: {len(response.candidates or [])}")
        for i, cand in enumerate(response.candidates or []):
            logger.debug(f"Processing candidate {i}, type: {type(cand)}")
            content = getattr(cand, "content", None)
            logger.debug(f"Candidate {i} has content: {content is not None}")
            if content:
                parts = getattr(content, "parts", None)
                logger.debug(f"Candidate {i} content has parts: {parts is not None}, count: {len(parts) if parts else 0}")
                if parts:
                    for j, part in enumerate(parts):
                        text = getattr(part, "text", None)
                        logger.debug(f"Candidate {i} part {j} has text: {text is not None}, length: {len(text) if text else 0}")
                        if text:
                            candidates.append(text)

    logger.debug(f"Total candidates collected: {len(candidates)}")
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
    all_constraints = constraints + \
        [f"Non-negotiable: {n}" for n in non_negotiables]

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
    personality_str = ", ".join(
        personality_traits) if personality_traits else "neutral"

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
    tensions.append(
        f"\nUser's non-negotiables:\n{_format_list(user_non_negotiables)}")
    tensions.append(
        f"\nOpponent's likely non-negotiables:\n{_format_list(opponent_non_negotiables)}")
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
        parts.append(
            f"This {difficulty} {domain} scenario will test your skills in {skills_text}.")

    if parts:
        return " ".join(parts)

    # Ultimate fallback
    return f"A {difficulty} negotiation scenario where you play the role of {role}."

# parses json from LLM responses


def _parse_json_response(response_text: str) -> Dict:
    def _sanitize_json(text: str) -> str:
        text = text.strip()
        # Remove triple quotes if present (Gemini sometimes wraps JSON in """)
        if text.startswith('"""') and text.endswith('"""'):
            text = text[3:-3].strip()
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
                out.append({"\\n": "\\n", "\\r": "\\r",
                           "\\t": "\\t"}.get(ch, ch))
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

    # First sanitize the input
    cleaned = _sanitize_json(_strip_invalid_controls(response_text))
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
            escaped_sanitized = _escape_control_chars(
                _sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(
                escaped_sanitized)
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
            escaped_sanitized = _escape_control_chars(
                _sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(
                escaped_sanitized)
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
            escaped_sanitized = _escape_control_chars(
                _sanitize_json(candidate))
            parsed = _try_load(escaped_sanitized) or _raw_decode(
                escaped_sanitized)
        if parsed is not None:
            return parsed

    sanitized = _sanitize_json(_strip_invalid_controls(response_text))
    parsed = _try_load(sanitized) or _raw_decode(sanitized)
    if parsed is None:
        escaped = _escape_control_chars(response_text)
        parsed = _try_load(escaped) or _raw_decode(escaped)
    if parsed is not None:
        return parsed

    raise ValueError(
        f"Could not parse JSON from response: {response_text[:500]}...")
