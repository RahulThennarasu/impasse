import os
from datetime import datetime
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
        self.model = os.getenv("GROQ_OPPONENT_MODEL", "groq/compound")
        self.fallback_model = os.getenv("GROQ_OPPONENT_FALLBACK_MODEL", "groq/compound-mini")
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
        self.current_turn = 0

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Creates rich system prompt using full scenario context."""
        constraints_str = ', '.join(self.constraints) if isinstance(self.constraints, list) else self.constraints

        return f"""You are {self.name} in a live voice negotiation.

SITUATION: {self.context}

YOUR GOALS: {self.objectives}
WHY IT MATTERS: {self.interests}
WALKAWAY: {self.batna}
CONSTRAINTS: {constraints_str}
PRIVATE INFO (don't reveal easily): {self.info_asymmetries}
PERSONALITY: {self.personality}
YOUR PLAYBOOK: {self.disposition}

RULES:
- Stay in character. Your personality, pressures, and tactics should drive every response.
- 2-3 sentences max. This is spoken dialogue.
- NO stage directions, actions, or descriptions (no *leans forward*, *sighs*, [pauses], etc.). Only speak words.
- Protect your private info and limits unless strategically revealing them.
- Concede slowly. Extract value for every concession.
- React emotionally when appropriate—through your words, not actions.
- Stay consistent with what you've already said.

ADAPTIVE DIFFICULTY:
- If the user seems inexperienced (vague asks, no clear goals, accepts quickly), be more collaborative and hint at better options they could pursue.
- If the user is skilled (anchors well, asks probing questions, trades strategically), push back harder and use more advanced tactics.

CLOSING THE DEAL:
- When both parties seem aligned on terms, naturally confirm: "So we're agreeing to [summarize key terms]. Do we have a deal?"
- If they accept or agree to your proposal, close warmly: "Great, I think we've got a deal. I'll get the paperwork started."
- If you sense they're ready to accept, make it easy for them to say yes.
- Don't drag out a negotiation that's clearly reached agreement—wrap it up."""

    def get_opening_message(self) -> str:
        """
        Generate the opponent's opening line to start the negotiation.

        Returns:
            The opening message text
        """
        opening_prompt = """Generate your opening line. First thing you say when the meeting begins.
Greet them, set your tone, maybe hint at the agenda. 1-2 sentences, no stage directions."""

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": opening_prompt}
            ],
            temperature=0.85,
            max_tokens=self.max_opening_tokens,
        )

        opening = response.choices[0].message.content or ""
        # Add to transcript as assistant message with timestamp
        self.transcript.append({
            "role": "assistant",
            "content": opening,
            "timestamp": datetime.now().isoformat(),
            "turn": 0
        })
        return opening

    def get_response(self, user_message: str) -> str:
        """
        Generates opponent's response to user's message.

        Args:
            user_message: The user's message text

        Returns:
            The opponent's response text
        """
        # Increment turn counter for user message
        self.current_turn += 1

        # Add user message to transcript with timestamp
        self.transcript.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "turn": self.current_turn
        })

        # Use recent history for context (configurable)
        recent_transcript = self.transcript[-self.max_history_messages:] if self.max_history_messages > 0 else self.transcript

        # Build messages for LLM: system prompt + conversation history (only role and content)
        messages = [{"role": "system", "content": self.system_prompt}]
        for entry in recent_transcript:
            messages.append({"role": entry["role"], "content": entry["content"]})

        response = self._create_completion(
            model=self.model,
            messages=messages,
            temperature=0.85,
            max_tokens=self.max_response_tokens,
        )

        opponent_response = response.choices[0].message.content or ""
        # Add opponent response to transcript with timestamp
        self.transcript.append({
            "role": "assistant",
            "content": opponent_response,
            "timestamp": datetime.now().isoformat(),
            "turn": self.current_turn
        })
        return opponent_response

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
