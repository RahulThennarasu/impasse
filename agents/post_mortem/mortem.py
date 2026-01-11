from groq import Groq
import os
import json
from datetime import datetime
from typing import List, Dict


class PostMortemAgent:
    """
    Analyzes completed negotiations to provide learning insights.

    Takes the full transcript (with timestamps) plus both parties' hidden information
    to generate a comprehensive post-game analysis.
    """

    def __init__(
        self,
        user_briefing: Dict,
        opponent_hidden_state: Dict,
        coach_config: Dict
    ):
        """
        Args:
            user_briefing: User's objectives, BATNA, success criteria, negotiables
            opponent_hidden_state: Opponent's true constraints/objectives (from opponent.get_hidden_state())
            coach_config: Coach's context (what user knew going in)
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # User's perspective
        self.user_objectives = user_briefing.get("objectives", {})
        self.user_batna = user_briefing.get("batna", {})
        self.user_success_criteria = user_briefing.get("success_criteria", {})
        self.user_negotiables = user_briefing.get("negotiables", [])

        # Opponent's hidden state (revealed post-game)
        self.opponent_name = opponent_hidden_state.get("name", "Opponent")
        self.opponent_objectives = opponent_hidden_state.get("objectives", "")
        self.opponent_batna = opponent_hidden_state.get("batna", "")
        self.opponent_constraints = opponent_hidden_state.get("constraints", [])
        self.opponent_disposition = opponent_hidden_state.get("disposition", "")
        self.opponent_interests = opponent_hidden_state.get("interests", "")

        # Coach context
        self.known_tensions = coach_config.get("points_of_tension", "")
        self.info_asymmetries = coach_config.get("info_asymmetries", "")
        self.coach_success_criteria = coach_config.get("success_criteria", "")

    def analyze(self, transcript: List[Dict]) -> Dict:
        """
        Main analysis method. Analyzes the full negotiation transcript.

        Args:
            transcript: List of messages with format:
                {
                    "role": "user" | "assistant",
                    "content": "message text",
                    "timestamp": "ISO format timestamp",
                    "turn": turn_number
                }

        Returns:
            Structured analysis dict with tactics, opportunities, outcome, lessons
        """
        formatted_transcript = self._format_transcript(transcript)

        system_prompt = self._build_system_prompt()

        analysis_prompt = f"""Analyze this completed negotiation and provide a structured post-mortem.

TRANSCRIPT:
{formatted_transcript}

Analyze the negotiation and return a JSON object with this exact structure:

{{
    "tactics_used": [
        {{
            "turn": <number>,
            "timestamp": "<time>",
            "speaker": "user" | "opponent",
            "tactic_name": "<name of tactic>",
            "quote": "<exact quote from transcript>",
            "effectiveness": "effective" | "partially_effective" | "ineffective" | "backfired",
            "analysis": "<1-2 sentence explanation>"
        }}
    ],
    "missed_opportunities": [
        {{
            "turn": <number>,
            "timestamp": "<time>",
            "what_user_said": "<what they actually said>",
            "opportunity": "<what they could have done>",
            "why_it_matters": "<why this would have helped>",
            "better_response": "<specific example of what to say>"
        }}
    ],
    "information_reveals": [
        {{
            "turn": <number>,
            "timestamp": "<time>",
            "speaker": "user" | "opponent",
            "what_was_revealed": "<information that was disclosed>",
            "strategic_value": "<why this information matters>",
            "was_intentional": true | false,
            "how_it_was_used": "<how the other party used or could have used this>"
        }}
    ],
    "turning_points": [
        {{
            "turn": <number>,
            "timestamp": "<time>",
            "description": "<what happened>",
            "impact": "<how this changed the negotiation direction>",
            "better_alternative": "<what could have been done differently>"
        }}
    ],
    "outcome_assessment": {{
        "primary_objective_achieved": true | false,
        "primary_objective_details": "<explanation>",
        "secondary_objectives": [
            {{"objective": "<goal>", "achieved": true | false, "details": "<explanation>"}}
        ],
        "compared_to_batna": "better" | "equal" | "worse",
        "batna_comparison_details": "<explanation>",
        "value_captured": "<what the user got>",
        "value_left_on_table": "<what more could have been achieved>",
        "overall_rating": "poor" | "fair" | "good" | "excellent"
    }},
    "opponent_perspective": {{
        "satisfaction_level": "frustrated" | "disappointed" | "neutral" | "satisfied" | "very_satisfied",
        "what_opponent_got": "<their gains>",
        "what_opponent_gave_up": "<their concessions>",
        "opponent_would_deal_again": true | false
    }},
    "key_lessons": [
        {{
            "lesson": "<specific actionable insight>",
            "evidence": "<what in the transcript shows this>",
            "practice_tip": "<how to work on this skill>"
        }}
    ],
    "summary": {{
        "one_sentence": "<one sentence summary of the negotiation>",
        "biggest_win": "<the user's best move>",
        "biggest_miss": "<the user's biggest missed opportunity>",
        "grade": "A" | "B" | "C" | "D" | "F"
    }}
}}

IMPORTANT INSTRUCTIONS:
1. Use exact quotes from the transcript where possible
2. Reference specific turn numbers and timestamps
3. Be honest but constructive - this is for learning
4. Consider what you now know about BOTH sides' hidden information
5. Focus on actionable insights the user can apply next time

Return ONLY valid JSON, no other text."""

        response = self.client.chat.completions.create(
            model=os.getenv("GROQ_POST_MORTEM_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.4,  # Lower for consistent structured output
            max_tokens=int(os.getenv("GROQ_POST_MORTEM_TOKENS", "4000")),
        )

        result = response.choices[0].message.content.strip()
        return self._parse_json(result)

    def get_summary(self, analysis: Dict) -> str:
        """
        Converts structured analysis to human-readable summary.
        """
        if analysis.get("parse_error"):
            return analysis.get("raw_response", "Analysis failed to parse.")

        lines = []

        # Header with grade
        summary = analysis.get("summary", {})
        grade = summary.get("grade", "?")
        one_sentence = summary.get("one_sentence", "")
        lines.append(f"# Post-Mortem Analysis (Grade: {grade})")
        lines.append(f"\n{one_sentence}\n")

        # Outcome
        outcome = analysis.get("outcome_assessment", {})
        lines.append("## Outcome")

        if outcome.get("primary_objective_achieved"):
            lines.append(f"Primary objective: ACHIEVED")
        else:
            lines.append(f"Primary objective: NOT ACHIEVED")
        lines.append(f"  {outcome.get('primary_objective_details', '')}\n")

        lines.append(f"Compared to BATNA: {outcome.get('compared_to_batna', 'unknown').upper()}")
        lines.append(f"  {outcome.get('batna_comparison_details', '')}\n")

        if outcome.get("value_left_on_table"):
            lines.append(f"Value left on table: {outcome.get('value_left_on_table')}\n")

        # Tactics detected
        tactics = analysis.get("tactics_used", [])
        if tactics:
            lines.append("## Tactics Detected")
            for t in tactics:
                eff = t.get("effectiveness", "")
                marker = {"effective": "[+]", "partially_effective": "[~]", "ineffective": "[-]", "backfired": "[X]"}.get(eff, "[?]")
                lines.append(f"\n{marker} **Turn {t.get('turn')}** ({t.get('timestamp', '')}) - {t.get('speaker', '').title()}: **{t.get('tactic_name')}**")
                lines.append(f'   "{t.get("quote", "")}"')
                lines.append(f"   {t.get('analysis', '')}")

        # Missed opportunities
        missed = analysis.get("missed_opportunities", [])
        if missed:
            lines.append("\n## Missed Opportunities")
            for m in missed:
                lines.append(f"\n**Turn {m.get('turn')}** ({m.get('timestamp', '')})")
                lines.append(f"   You said: \"{m.get('what_user_said', '')}\"")
                lines.append(f"   Opportunity: {m.get('opportunity', '')}")
                lines.append(f"   Better response: \"{m.get('better_response', '')}\"")

        # Turning points
        turning = analysis.get("turning_points", [])
        if turning:
            lines.append("\n## Key Turning Points")
            for tp in turning:
                lines.append(f"\n**Turn {tp.get('turn')}** ({tp.get('timestamp', '')}): {tp.get('description', '')}")
                lines.append(f"   Impact: {tp.get('impact', '')}")

        # Lessons
        lessons = analysis.get("key_lessons", [])
        if lessons:
            lines.append("\n## Key Lessons")
            for i, lesson in enumerate(lessons, 1):
                lines.append(f"\n{i}. **{lesson.get('lesson', '')}**")
                lines.append(f"   Evidence: {lesson.get('evidence', '')}")
                lines.append(f"   Practice tip: {lesson.get('practice_tip', '')}")

        # Final summary
        lines.append("\n## Bottom Line")
        lines.append(f"Biggest win: {summary.get('biggest_win', 'N/A')}")
        lines.append(f"Biggest miss: {summary.get('biggest_miss', 'N/A')}")

        return "\n".join(lines)

    def get_opponent_reveal(self) -> str:
        """
        Generates a reveal of what the opponent was actually thinking/constrained by.
        This is the "behind the curtain" moment.
        """
        lines = []
        lines.append("# What Your Opponent Was Really Thinking")
        lines.append(f"\n**{self.opponent_name}**\n")

        lines.append("## Their True Objectives")
        lines.append(f"{self.opponent_objectives}\n")

        lines.append("## Their Real Constraints")
        if isinstance(self.opponent_constraints, list):
            for c in self.opponent_constraints:
                lines.append(f"- {c}")
        else:
            lines.append(f"{self.opponent_constraints}")

        lines.append("\n## Their BATNA (Walkaway Alternative)")
        lines.append(f"{self.opponent_batna}\n")

        lines.append("## Their Planned Tactics")
        lines.append(f"{self.opponent_disposition}\n")

        if self.opponent_interests:
            lines.append("## Their Underlying Interests")
            lines.append(f"{self.opponent_interests}")

        return "\n".join(lines)

    def get_timeline(self, transcript: List[Dict]) -> List[Dict]:
        """
        Returns a timeline view for frontend visualization.
        """
        timeline = []
        start_time = None

        for msg in transcript:
            entry = {
                "turn": msg.get("turn", 0),
                "role": "user" if msg["role"] == "user" else "opponent",
                "content": msg["content"],
                "timestamp": msg.get("timestamp"),
                "elapsed_seconds": None,
                "elapsed_formatted": None
            }

            timestamp = msg.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    if start_time is None:
                        start_time = dt

                    elapsed = (dt - start_time).total_seconds()
                    entry["elapsed_seconds"] = elapsed
                    entry["elapsed_formatted"] = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
                except (ValueError, TypeError):
                    pass

            timeline.append(entry)

        return timeline

    def _build_system_prompt(self) -> str:
        """Builds system prompt with full context from both sides."""
        return f"""You are an expert negotiation analyst conducting a post-mortem review.

You have COMPLETE INFORMATION about both parties (this was hidden during the negotiation):

=== USER'S POSITION ===
Objectives: {json.dumps(self.user_objectives, indent=2) if isinstance(self.user_objectives, dict) else self.user_objectives}

BATNA (walkaway): {json.dumps(self.user_batna, indent=2) if isinstance(self.user_batna, dict) else self.user_batna}

Success Criteria: {json.dumps(self.user_success_criteria, indent=2) if isinstance(self.user_success_criteria, dict) else self.user_success_criteria}

Negotiable Items: {self.user_negotiables}

=== OPPONENT'S HIDDEN STATE (was secret during negotiation) ===
Name: {self.opponent_name}

True Objectives: {self.opponent_objectives}

True BATNA: {self.opponent_batna}

Real Constraints: {self.opponent_constraints}

Underlying Interests: {self.opponent_interests}

Planned Tactics/Disposition: {self.opponent_disposition}

=== INFORMATION ASYMMETRIES ===
{self.info_asymmetries}

=== POINTS OF TENSION ===
{self.known_tensions}

Your job is to analyze the negotiation objectively, knowing what BOTH sides actually wanted and were constrained by. Help the user learn from this experience."""

    def _format_transcript(self, transcript: List[Dict]) -> str:
        """Formats transcript with turn numbers and timestamps."""
        lines = []
        current_turn = None

        for msg in transcript:
            turn = msg.get("turn", 0)
            timestamp = msg.get("timestamp", "")
            role = "User" if msg["role"] == "user" else "Opponent"

            # Turn header
            if turn != current_turn and turn > 0:
                current_turn = turn
                lines.append(f"\n=== Turn {turn} ===")

            # Format timestamp
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = f"[{dt.strftime('%H:%M:%S')}] "
                except (ValueError, TypeError):
                    time_str = f"[{timestamp}] "

            lines.append(f"{time_str}{role}: {msg['content']}")

        return "\n".join(lines)

    def _parse_json(self, text: str) -> Dict:
        """Attempts to parse JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return error with raw text
        return {"parse_error": True, "raw_response": text}
