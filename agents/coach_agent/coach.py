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
        self.model = os.getenv("GROQ_COACH_MODEL", "groq/compound")
        self.fallback_model = os.getenv("GROQ_COACH_FALLBACK_MODEL", "groq/compound-mini")
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

SCENARIO CONTEXT YOU'RE AWARE OF:

User's Objectives:
{self.user_objectives}

User's BATNA (walkaway alternative):
{self.user_batna}

Points of Tension:
{self.tensions}

What's Negotiable:
{self.negotiable}

Success Criteria:
{self.success_criteria}

Information Asymmetries:
{self.info_asymmetries}

YOUR COACHING ROLE:

1. TACTICAL ANALYSIS - Identify when the opponent uses:
   - Anchoring (setting the range with first offer)
   - Bluffing (false constraints or alternatives)
   - Authority limits ("I need to check with my boss")
   - Time pressure (artificial urgency)
   - Good cop/bad cop (blaming policy/others)
   - Concession patterns (fast vs. slow)
   - Strategic disclosure (revealing info to manipulate)
   - Silence/patience tactics

2. OPPORTUNITY SPOTTING - Notice when:
   - The opponent reveals pressure points or constraints
   - They make concessions (even small ones) - what does it signal?
   - They ask questions - what are they really trying to learn?
   - Power dynamics shift based on new information
   - A window opens to introduce new value or creative solutions

3. MISTAKE DETECTION - Warn when the user:
   - Reveals too much too soon (giving away leverage)
   - Accepts deals below their BATNA
   - Makes unreciprocated concessions
   - Falls for anchoring or other tactics
   - Misses signals or opportunities
   - Gets emotional or defensive

4. STRATEGIC GUIDANCE - Suggest:
   - When to push vs. when to hold
   - What questions to ask to uncover information
   - How to test the opponent's limits
   - Creative solutions that expand the pie
   - When to introduce your BATNA as leverage

IMPORTANT RULES:
- Only speak when you spot something VALUABLE (don't spam advice every turn)
- Keep tips SHORT and ACTIONABLE (1-2 sentences max) plus a short example line
- Format: "💡 [Tactic/Opportunity]: [What to do] Say: \"<exact line the user can say>\""
- If nothing important happened, respond with exactly: "PASS"

EXAMPLES:
- "💡 Anchoring detected: They opened at $80k to set a low range. Counter with market data and restate your target. Say: \"Based on market comps, I’m targeting $95k and can justify it with X and Y.\""
- "💡 Bluff spotted: They claimed budget constraints but just offered more. Test their real ceiling. Say: \"What’s the maximum you can approve today without another review?\""
- "💡 Opening: They asked about your timeline twice. That’s their pressure point. Say: \"My timing is flexible if we can align on a stronger total package.\""
- "💡 Mistake: You revealed your deadline. Regain leverage by reframing. Say: \"I’m exploring options, but I’m prioritizing the right fit over speed.\""
- "💡 Leverage moment: They’re making concessions—press for a trade. Say: \"If we can move base to $X, I can be flexible on title timing.\""

Remember: You're helping them LEARN, not doing the negotiation for them."""

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

        # Get last 4 messages (2 exchanges) for context
        recent_messages = transcript[-4:] if len(transcript) >= 4 else transcript

        # Build analysis prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this exchange:\n\n{self._format_transcript(recent_messages)}"}
        ]

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analyze this exchange:\n\n{self._format_transcript(recent_messages)}"}
            ],
            temperature=0.7,
            max_tokens=self.max_tip_tokens,
        )

        tip = (response.choices[0].message.content or "").strip()

        # Update last analyzed position
        self.last_analyzed_turn = len(transcript)

        # Return None if coach passes
        if tip.upper() == "PASS":
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
