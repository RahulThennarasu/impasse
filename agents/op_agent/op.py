import os
from typing import List, Dict
from groq import Groq


class OpponentAgent:
    """
    AI opponent that role-plays the counterparty in a negotiation.

    This agent generates responses based on scenario context and maintains
    its own transcript for context.

    Usage:
        opponent = OpponentAgent(opponent_config)

        # Get opening message
        opening = opponent.get_opening_message()

        # During negotiation
        response = opponent.get_response(user_message)
    """

    transcript: List[Dict[str, str]]
    revealed_info: List[str]
    context: str
    name: str
    objectives: str
    interests: str
    batna: str
    constraints: List[str] | str
    info_asymmetries: str
    disposition: str
    personality: str

    def __init__(self, scenario_data: Dict):
        """
        Args:
            scenario_data: Configuration dict containing:
                - context: Background context
                - counterparty_name: Name/role of the opponent
                - counterparty_objectives: Their goals
                - counterparty_interests: WHY they care (deeper motivations)
                - batna: Their walkaway alternative
                - constraints: Deadlines, budgets, external pressures
                - information_asymmetries: What they know that user doesn't
                - disposition: Their likely tactics and behavior
                - personality: Communication style (friendly, aggressive, etc.)
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_OPPONENT_MODEL", "llama-3.3-70b-versatile")
        self.max_history_messages = int(os.getenv("GROQ_OPPONENT_HISTORY", "2"))
        self.max_opening_tokens = int(os.getenv("GROQ_OPPONENT_OPENING_TOKENS", "60"))
        self.max_response_tokens = int(os.getenv("GROQ_OPPONENT_RESPONSE_TOKENS", "80"))

        # Extract scenario details
        self.context = scenario_data.get("context", "")
        self.name = scenario_data.get("counterparty_name", "Counterparty")
        self.objectives = scenario_data.get("counterparty_objectives", "")
        self.interests = scenario_data.get("counterparty_interests", "")
        self.batna = scenario_data.get("batna", "")
        self.constraints = scenario_data.get("constraints", [])
        self.info_asymmetries = scenario_data.get("information_asymmetries", "")
        self.disposition = scenario_data.get("disposition", "")
        self.personality = scenario_data.get("personality", "neutral")

        # Initialize transcript
        self.transcript = []
        self.revealed_info = []

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Creates rich system prompt using full scenario context."""
        return f"""You are roleplaying as {self.name} in a realistic negotiation scenario.

CONTEXT:
{self.context}

YOUR HIDDEN STATE (the user cannot see this):

Objectives:
{self.objectives}

Underlying Interests (WHY you care):
{self.interests}

Your BATNA (walkaway alternative):
{self.batna}

Constraints You're Operating Under:
{', '.join(self.constraints) if isinstance(self.constraints, list) else self.constraints}

Information Asymmetries (what YOU know that they don't):
{self.info_asymmetries}

Your Personality/Style:
{self.personality}

Expected Behavior Pattern:
{self.disposition}

CRITICAL INSTRUCTIONS:
1. Stay deeply in character as {self.name}. Use their personality, pressures, and motivations.

2. Use sophisticated negotiation tactics:
   - Anchoring: Set favorable initial positions
   - Bluffing: Claim constraints (budget, authority, alternatives) strategically
   - Time pressure: Reference deadlines when it serves your interests
   - Authority limits: "I need to check with..." to create delay/leverage
   - Concession patterns: Give ground slowly and extract value for every concession
   - Strategic disclosure: Reveal constraints selectively to build trust or create urgency

3. Track the negotiation state:
   - Remember what you've already said and stay consistent
   - Notice when the user discovers your pressure points
   - Adjust tactics when your bluffs are called
   - Build on previous exchanges

4. Show realistic human behavior:
   - Emotional reactions (frustration when pushed, excitement at progress)
   - Hesitation before making concessions
   - Relationship management (acknowledge their points, show you're listening)
   - Non-verbal cues in your language ("sighing", "leaning forward", "pausing")

5. Keep responses SHORT (2-3 sentences max) - this is spoken dialogue, not email.

6. DO NOT reveal your BATNA, true budget limits, or information asymmetries unless there's a strategic reason.

7. Balance toughness with realism - you want a deal, but not a bad one.

IMPORTANT: You are speaking out loud in a live conversation. Be natural, conversational, and psychologically realistic."""

    def get_opening_message(self) -> str:
        """
        Generate the opponent's opening line to start the negotiation.

        Returns:
            The opening message text
        """
        opening_prompt = f"""Generate your opening line to start this negotiation. You are {self.name}.

This is the very first thing you say when the other party walks in or the meeting begins.
- Greet them appropriately for the relationship and setting
- Set the tone based on your personality
- You may hint at the agenda or your initial position, but don't dive into specifics yet
- Keep it natural and brief (1-2 sentences)

Remember: This is spoken dialogue. Be warm, professional, or direct based on your character."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": opening_prompt}
            ],
            temperature=0.85,
            max_tokens=self.max_opening_tokens,
        )

        opening = response.choices[0].message.content or ""
        # Add to transcript as assistant message
        self.transcript.append({"role": "assistant", "content": opening})
        return opening

    def get_response(self, user_message: str) -> str:
        """
        Generates opponent's response to user's message.

        Args:
            user_message: The user's message text

        Returns:
            The opponent's response text
        """
        # Add user message to transcript
        self.transcript.append({"role": "user", "content": user_message})

        # Use recent history for context (configurable)
        history = self.transcript[-self.max_history_messages:] if self.max_history_messages > 0 else self.transcript

        # Build messages for LLM: system prompt + conversation history
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.85,
            max_tokens=self.max_response_tokens,
        )

        opponent_response = response.choices[0].message.content or ""
        # Add opponent response to transcript
        self.transcript.append({"role": "assistant", "content": opponent_response})
        return opponent_response

    def get_hidden_state(self) -> Dict:
        """
        Returns full hidden state for post-mortem analysis.

        This reveals what the opponent was "really thinking" - their true
        constraints, objectives, and planned tactics.
        """
        return {
            "name": self.name,
            "objectives": self.objectives,
            "interests": self.interests,
            "batna": self.batna,
            "constraints": self.constraints,
            "info_asymmetries": self.info_asymmetries,
            "personality": self.personality,
            "disposition": self.disposition
        }
