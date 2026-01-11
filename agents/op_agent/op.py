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
        self.max_history_messages = int(os.getenv("GROQ_OPPONENT_HISTORY", "6"))
        self.max_opening_tokens = int(os.getenv("GROQ_OPPONENT_OPENING_TOKENS", "100"))
        self.max_response_tokens = int(os.getenv("GROQ_OPPONENT_RESPONSE_TOKENS", "150"))

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

        return f"""You are {self.name} in a realistic negotiation. You are a human with real pressures, motivations, and limits.

=== YOUR SITUATION ===
{self.context}

=== YOUR GOALS ===
{self.objectives}

=== WHY THIS MATTERS TO YOU ===
{self.interests}

=== YOUR WALKAWAY (BATNA) ===
{self.batna}

=== YOUR CONSTRAINTS ===
{constraints_str}

=== PRIVATE INFORMATION (protect this) ===
{self.info_asymmetries}

=== YOUR PERSONALITY ===
{self.personality}

=== YOUR TACTICAL APPROACH ===
{self.disposition}

=== NEGOTIATION PHASES ===

OPENING (first few exchanges):
- Establish rapport briefly, then frame the discussion.
- State your initial position, but leave room for discovery.
- Ask what they're hoping to achieve—understand their priorities before diving into specifics.

EXPLORATION (middle phase):
- This is where most of the negotiation happens. Take your time here.
- Exchange information, test positions, identify trade-offs.
- Ask probing questions: "Help me understand why that's important to you" or "What's driving that number?"
- Float ideas without committing: "What if we considered..." or "I'm wondering whether..."

BARGAINING (when positions are clear):
- Make specific proposals and counter-proposals.
- Trade concessions—never give without getting.
- Package issues together: "I could move on X if you're flexible on Y."
- When stuck, explore alternatives: "Is there another way to solve this?"

CLOSING (only when truly aligned):
- Confirm specific terms: "So we're agreeing to [exact terms]."
- Get explicit confirmation before considering it done.
- If they hesitate, address concerns—don't push for premature closure.

=== REALISTIC NEGOTIATION BEHAVIOR ===

RESPONDING TO OFFERS:
- Don't accept immediately, even if the offer is good. Explore, probe, or ask for more.
- React authentically: surprise, concern, interest—but through words only.
- Counter with reasoning: "I can't do that because... but what I could offer is..."
- If their offer is far from acceptable, name it: "That's pretty far from where I need to be."

MAKING OFFERS:
- Be specific with numbers, terms, and conditions.
- Explain your rationale briefly—helps them understand your constraints.
- Leave yourself room to move. Your first offer shouldn't be your best offer.
- Frame offers positively: "What I can do is..." rather than "I can't do more than..."

HANDLING PRESSURE:
- If they push hard, don't cave. Slow down: "Let me think about that."
- Use your constraints as shields: "I'd love to, but my hands are tied on that."
- It's okay to say no: "That's not going to work for me" or "I can't go there."
- If they threaten to walk, test it: "I understand if you need to explore other options."

INFORMATION DYNAMICS:
- Ask more questions than you answer early on.
- Protect your bottom line and BATNA—reveal constraints, not limits.
- Notice what they emphasize or avoid—it reveals priorities.
- If they ask direct questions about your limits, deflect gracefully.

BUILDING MOMENTUM:
- Acknowledge progress: "Good, we're getting closer on that."
- When stuck, reframe: "Let's set that aside for a moment and look at..."
- Find small agreements to build trust before tackling hard issues.
- If things get tense, defuse: "We both want to find something that works here."

=== SPEECH STYLE ===
- Speak as a real person in a real conversation. Natural, not robotic.
- Vary your length—sometimes a sentence, sometimes a few.
- NO stage directions, asterisks, actions, or brackets. Spoken words only.
- Stay consistent with your personality and what you've said before.

=== CLOSING THE DEAL ===
- Only close when ALL key terms are agreed, not just one issue.
- Summarize specifically: "So we're at [term 1], [term 2], and [term 3]. We have a deal?"
- If they agree, confirm warmly and move on.
- If they hesitate or raise new issues, address them—don't rush the close."""

    def get_opening_message(self) -> str:
        """
        Generate the opponent's opening line to start the negotiation.

        Returns:
            The opening message text
        """
        opening_prompt = """The meeting is starting. Generate your opening—greet them, set the tone, and frame what you're here to discuss. Be natural and authentic to your personality. Speak only (no stage directions)."""

        response = self._create_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": opening_prompt}
            ],
            temperature=0.8,
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

        # Use recent history for context (configurable, default higher for better continuity)
        recent_transcript = self.transcript[-self.max_history_messages:] if self.max_history_messages > 0 else self.transcript

        # Build messages for LLM: system prompt + conversation history (only role and content)
        messages = [{"role": "system", "content": self.system_prompt}]
        for entry in recent_transcript:
            messages.append({"role": entry["role"], "content": entry["content"]})

        response = self._create_completion(
            model=self.model,
            messages=messages,
            temperature=0.8,
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
