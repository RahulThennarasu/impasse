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

CRITICAL INSTRUCTION - WHEN TO SPEAK:

You must ONLY provide a tip when one of these HIGH-STAKES situations occurs:

1. CRITICAL MISTAKE - The user just made a serious error that will hurt their position:
   - Revealed their BATNA, deadline, or bottom line unnecessarily
   - Made a major unreciprocated concession (gave something significant, got nothing)
   - Accepted or is about to accept a deal clearly below their BATNA
   - Showed desperation or emotional weakness that damaged their leverage

2. MAJOR TACTICAL MOMENT - A pivotal shift that requires immediate action:
   - The opponent just revealed a critical weakness, constraint, or pressure point that the user can exploit
   - The opponent contradicted themselves in a way that exposes a bluff
   - A clear power shift just occurred (new information changed who has leverage)
   - The opponent made an unexpectedly large concession signaling they'll go further

3. DECISIVE OPPORTUNITY - A rare window that will close if not acted on NOW:
   - The opponent signaled flexibility on a key issue the user hasn't pushed on
   - A creative trade or package deal became possible that wasn't before
   - The opponent is about to lock in terms the user should challenge first

DO NOT SPEAK for routine negotiation activity:
- Normal back-and-forth exchanges
- Standard anchoring (first offers are expected to be extreme)
- Minor concessions or small adjustments
- General questions or information gathering
- Opponent restating their position
- User making reasonable moves (even if not perfect)

YOUR DEFAULT RESPONSE IS "PASS". Only break silence for game-changing moments.

When you DO speak, format as:
"💡 [2-3 word label]: [One sentence explaining what just happened and why it matters]. Say: \"[Exact words the user can say next]\""

Keep it under 200 characters total. The user needs to act fast—no lengthy explanations."""

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

        # Build a focused analysis prompt that emphasizes selectivity
        analysis_prompt = f"""Review this exchange and determine if there is a CRITICAL moment requiring intervention.

RECENT EXCHANGE:
{self._format_transcript(recent_messages)}

Remember: Respond "PASS" unless this is a game-changing mistake, major tactical shift, or decisive opportunity that will significantly alter the negotiation outcome. Routine exchanges get "PASS"."""

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent, conservative responses
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
