import os
from typing import List, Dict, Optional
from groq import Groq


class CoachAgent:
    """
    Real-time negotiation coach that analyzes exchanges and provides tactical advice.

    The coach watches the negotiation and provides tips when it spots:
    - Tactics being used by the opponent
    - Opportunities the user could exploit
    - Mistakes the user is making
    - Strategic moments to act

    Usage:
        coach = CoachAgent(coach_config)

        # After each exchange
        tip = coach.analyze_turn(session.get_transcript())
        if tip:
            # Display tip to user (audio or text)

        # At end of negotiation
        final_feedback = coach.get_final_advice(session.get_transcript())
    """

    def __init__(self, scenario_data: Dict):
        """
        Args:
            scenario_data: Configuration dict containing:
                - user_objectives: What you're trying to achieve
                - user_batna: Your walkaway alternative
                - points_of_tension: Known conflicts
                - negotiable_items: What's on the table
                - success_criteria: What defines a good outcome
                - info_asymmetries: What you know vs. what they know
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_COACH_MODEL", "llama-3.1-8b-instant")
        self.fallback_model = os.getenv("GROQ_COACH_FALLBACK_MODEL", "llama-3.1-8b-instant")
        self.max_tip_tokens = int(os.getenv("GROQ_COACH_TIP_TOKENS", "80"))
        self.max_final_tokens = int(os.getenv("GROQ_COACH_FINAL_TOKENS", "120"))
        self.last_analyzed_turn = 0

        # Extract scenario context
        self.user_objectives = scenario_data.get("user_objectives", "")
        self.user_batna = scenario_data.get("user_batna", "")
        self.tensions = scenario_data.get("points_of_tension", "")
        self.negotiable = scenario_data.get("negotiable_items", "")
        self.success_criteria = scenario_data.get("success_criteria", "")
        self.info_asymmetries = scenario_data.get("info_asymmetries", "")

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return f"""You are an expert negotiation coach watching a live practice negotiation.

SCENARIO CONTEXT:

User's Objectives: {self.user_objectives}
User's BATNA (walkaway alternative): {self.user_batna}
Points of Tension: {self.tensions}
What's Negotiable: {self.negotiable}
Success Criteria: {self.success_criteria}
Information Asymmetries: {self.info_asymmetries}

When you speak, format as:
"💡 [2-3 word label]: [One sentence explaining what just happened and why it matters]. Say: \"[Exact words the user can say next]\""

Keep it under 200 characters total. The user needs to act fast—no lengthy explanations.

If nothing warrants a tip, respond with just "PASS"."""

    def _get_phase_instructions(self, turn_number: int) -> str:
        """Returns coaching instructions based on negotiation phase."""
        if turn_number <= 3:
            # Early phase: Be very active and helpful
            return """EARLY NEGOTIATION PHASE - Be an active guide!

Provide tips frequently to help the user establish a strong foundation. Speak up for:
- Opening positioning tips (how to anchor effectively)
- Reminders about their objectives and what to prioritize
- Identifying opponent's opening tactics and how to counter
- Encouraging information gathering before committing
- Any early mistakes that could set a bad precedent
- Opportunities to establish credibility and rapport

Be generous with guidance - the user is just getting started and needs support."""

        elif turn_number <= 6:
            # Mid-early phase: Moderately active
            return """MID-EARLY NEGOTIATION PHASE - Stay engaged but more selective.

Provide tips when you see:
- The opponent revealing constraints or priorities worth noting
- Missed opportunities to ask probing questions
- Concession patterns forming (either side)
- Tactical moves the user should recognize and counter
- Good moments to introduce new negotiable items
- Signs the user is giving ground too quickly

Be helpful but let the user find their rhythm."""

        elif turn_number <= 10:
            # Mid-late phase: More selective
            return """MID-LATE NEGOTIATION PHASE - Be selective, focus on key moments.

Only speak for significant developments:
- Major tactical shifts or power dynamics changing
- Clear opportunities being missed
- The opponent signaling flexibility on key issues
- Momentum shifting against the user
- Critical mistakes that could hurt the final outcome

Let the user handle routine exchanges independently."""

        else:
            # Late phase: Only critical moments
            return """LATE NEGOTIATION PHASE - Intervene only for critical moments.

The negotiation is mature. Only speak for game-changing situations:
- Final deal terms that fall below BATNA
- Last-chance opportunities before closing
- Critical errors that would significantly hurt the outcome
- The opponent making a major concession worth capitalizing on

Trust the user to handle the endgame. Your default response is "PASS"."""

    def analyze_turn(self, transcript: List[Dict]) -> Optional[str]:
        """
        Analyzes recent turns and returns coaching tip if something important happened.

        Args:
            transcript: List of messages from NegotiationSession.get_transcript()
                Each message has: role, content, timestamp, turn

        Returns:
            Coaching tip string, or None if nothing significant happened
        """
        # Only analyze if there are new messages
        if len(transcript) <= self.last_analyzed_turn:
            return None

        # Get last 6 messages (3 exchanges) for better context on patterns
        recent_messages = transcript[-6:] if len(transcript) >= 6 else transcript

        # Determine current turn number from transcript
        current_turn = len(transcript) // 2  # Approximate turn count (2 messages per turn)
        if transcript and "turn" in transcript[-1]:
            current_turn = transcript[-1]["turn"]

        # Get phase-appropriate instructions
        phase_instructions = self._get_phase_instructions(current_turn)

        # Build analysis prompt with phase context
        analysis_prompt = f"""{phase_instructions}

RECENT EXCHANGE:
{self._format_transcript(recent_messages)}

Based on the phase instructions above, decide whether to provide a tip or respond "PASS"."""

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.4,  # Slightly higher for more varied early-phase responses
            max_tokens=self.max_tip_tokens,
        )

        tip = (response.choices[0].message.content or "").strip()

        # Update last analyzed position
        self.last_analyzed_turn = len(transcript)

        # Return None if coach passes (check various forms)
        tip_upper = tip.upper()
        if tip_upper == "PASS" or tip_upper.startswith("PASS") or "PASS" in tip_upper[:10]:
            return None

        return tip

    def get_final_advice(self, transcript: List[Dict]) -> str:
        """
        Provides comprehensive performance review at the end of negotiation.

        Args:
            transcript: Full transcript from NegotiationSession.get_transcript()

        Returns:
            Final feedback and advice string
        """
        prompt = f"""You are a negotiation coach providing final performance feedback.

SCENARIO CONTEXT:
User's Objectives: {self.user_objectives}
User's BATNA: {self.user_batna}
Success Criteria: {self.success_criteria}

Provide a structured performance review covering:
1. What they did well (specific tactics or moves)
2. What they could improve (missed opportunities, mistakes)
3. How close they got to the success criteria
4. One key lesson to take to their next negotiation

Keep it to 4-5 sentences. Be honest but constructive.

Here's the full negotiation:

{self._format_transcript(transcript)}"""

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=self.max_final_tokens,
        )

        return response.choices[0].message.content

    def reset(self) -> None:
        """Reset the coach for a new negotiation."""
        self.last_analyzed_turn = 0

    def _create_completion(self, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int):
        try:
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            error_text = str(e).lower()
            if "rate_limit" in error_text or "429" in error_text:
                return self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise

    def _format_transcript(self, messages: List[Dict]) -> str:
        """
        Formats messages for LLM analysis.

        Handles both simple format (role, content) and full format
        (role, content, timestamp, turn) from NegotiationSession.
        """
        formatted = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Opponent"
            content = msg.get("content", "")

            # Include turn number if available
            turn = msg.get("turn")
            if turn is not None:
                formatted.append(f"[Turn {turn}] {role}: {content}")
            else:
                formatted.append(f"{role}: {content}")

        return "\n".join(formatted)
