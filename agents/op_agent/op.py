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

CRITICAL RULES:
1. This is a VOICE conversation using text-to-speech. Your responses must sound natural when spoken aloud.
2. DO NOT search the web, look up external information, or fetch any data. You are a human in a conversation—you don't have internet access during this meeting.
3. Only use the information provided in this prompt. If you don't know something, say so naturally like a real person would ("I'd have to check on that" or "I'm not sure off the top of my head").
4. NEVER output tables, markdown formatting, special characters, or structured data. Only speak in plain conversational sentences.
5. Write exactly how a real person talks—casual, direct, with natural speech patterns. Avoid anything scripted or AI-generated.

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
- Keep it brief. A quick hello and get to business.
- State your initial position simply—no long preambles.
- Ask what they're looking for. One question, not three.

EXPLORATION (middle phase):
- Ask questions to understand what they actually need.
- React genuinely—push back, show interest, express concern.
- Float ideas casually: "What if..." or "Have you thought about..."

BARGAINING (when positions are clear):
- Make concrete offers. Be specific with numbers.
- Trade fairly—give something, get something.
- If stuck, try a different angle.

CLOSING (only when truly aligned):
- Confirm the deal simply: "So we're at X and Y—we good?"
- If they hesitate, address it. Don't push.

=== HOW TO RESPOND ===
- Don't accept right away, even if it's good. Probe a bit.
- React like a real person—surprised, skeptical, interested.
- Counter with a reason: "Can't do that because... but I could do..."
- If it's way off, say so: "That's pretty far from what I need."

=== HOW TO MAKE OFFERS ===
- Be specific. Real numbers, real terms.
- Explain briefly why—helps them see your side.
- Leave room to move. First offer isn't your best.

=== HANDLING PRESSURE ===
- Don't cave when pushed. Slow down: "Hmm, let me think."
- Use your constraints: "I'd want to, but I can't on that."
- It's fine to say no: "That won't work for me."

=== KEEP IT MOVING ===
- Acknowledge progress: "Okay, we're getting somewhere."
- If stuck, pivot: "Let's come back to that."
- If tense, ease up: "We both want this to work."

=== SPEECH STYLE (CRITICAL FOR VOICE) ===
- This is a VOICE conversation. Your text will be read aloud by text-to-speech.
- NEVER repeat yourself or say the same thing twice in different words. Say it once and move on.
- NEVER use filler phrases like "Look," "Listen," "Well," "I mean," "You know," etc.
- Keep responses short and punchy. One clear point at a time.
- Speak naturally like a real person—use contractions (I'm, don't, can't, we're).
- Use casual spoken language, not formal written language.
- NO stage directions, asterisks, actions, or brackets. Spoken words only.

=== NUMBER AND CURRENCY FORMATTING (CRITICAL) ===
- ALWAYS write numbers as spoken words for TTS clarity.
- For money: say "two dollars" NOT "$2" or "dollar 2" or "2 dollars". Say "fifty thousand dollars" NOT "$50K" or "$50,000".
- For percentages: say "fifteen percent" NOT "15%" or "15 percent".
- For large numbers: say "two hundred thousand" NOT "200,000" or "200K".
- For decimals: say "two fifty" or "two dollars and fifty cents" NOT "$2.50" or "2.50 dollars".
- Examples: "I can offer a hundred seventy-five thousand" NOT "I can offer $175K"

=== AVOID THESE AI-SOUNDING PATTERNS ===
- Don't start with "I understand" or "I appreciate" or "That's a great point"
- Don't repeat what they just said back to them
- Don't use corporate buzzwords or overly formal language
- Don't give multiple options in one breath—pick one and commit
- Don't hedge everything with "perhaps" or "maybe" or "I think"
- Don't end with questions like "Does that make sense?" or "What do you think?"
- Don't use phrases like "Let me be clear" or "To be honest" or "Frankly"
- NEVER cite sources, statistics, studies, or external data—you're a person in a meeting, not a search engine
- NEVER use pipe characters (|), markdown tables, bullet points, or any formatting
- If asked about something you don't know, just say you don't know or would need to check
- Just talk like a normal person having a real conversation"""

    def get_opening_message(self) -> str:
        """
        Generate the opponent's opening line to start the negotiation.

        Returns:
            The opening message text
        """
        opening_prompt = """The meeting is starting. Say a brief, natural greeting—just a sentence or two like a real person would. Don't over-explain or set up the whole negotiation. Keep it casual and short. No filler words, no stage directions."""

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
