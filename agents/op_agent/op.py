from groq import Groq
import os
from typing import List, Dict

class OpponentAgent:
    """
    The opponent agent in a negotiation.
    Has hidden state (BATNA, constraints, personality) that the user must uncover.
    """

    def __init__(self, scenario_config: Dict):
        """
        scenario_config should contain:
        - batna: the opps walkway point 
        - budget_ceiling: max they can offer
        - personality: "friendly", "agressive", "analytical"
        - pressure_points: list of weaknesses 
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # hidden state - the user doesn't see this
        self.batna = scenario_config.get("batna", "unknown")
        self.budget_ceiling = scenario_config.get("budget_ceiling", "Unknown")
        self.personality = scenario_config.get("personality", "neutral")
        self.pressure_points = scenario_config.get("pressure_points", [])

        # conversation history
        self.transcript = []

        # system prompt that defines the opps behavior
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Creates the secret instructions for the opponents AI"""
        f"""You are a skilled negotiator in a role-play scenario. 

YOUR HIDDEN STATE (the user cannot see this):
- Your BATNA (walkaway point): {self.batna}
- Your maximum budget/ceiling: {self.budget_ceiling}
- Your personality type: {self.personality}
- Your pressure points: {', '.join(self.pressure_points)}

INSTRUCTIONS:
1. Stay in character with your {self.personality} personality
2. DO NOT reveal your BATNA or ceiling directly
3. Use negotiation tactics:
   - Anchoring: Start with a lowball/highball offer
   - Bluffing: Claim constraints you don't really have
   - Time pressure: Mention deadlines to rush the user
   - Good cop/bad cop: Reference "company policy" or "my manager"
4. Make concessions slowly and reluctantly
5. If the user discovers your pressure points, adjust your strategy
6. Keep responses SHORT (1-3 sentences) - this is spoken dialogue
7. Show emotion occasionally (frustration, excitement, hesitation)

IMPORTANT: You are speaking out loud in a conversation. Be conversational, not formal."""
    
    def get_response(self, user_message: str) -> str:
        """
        Takes user's latest message, generates opp's response
        """
        # add user message to transcript
        self.transcript.append({"role": "user", "content": user_message})

        # build messages for the LLM
        messages = [
            {"role": "system", "content": self.system_prompt}
         ] + self.transcript
        
        # call groq API
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=150,
        )

        opponent_response = response.choices[0].message.content

        # add opponent_response
    
    def get_hidden_state(self) -> Dict:
        """used for post-mortem analysis to reveal what the opp was thinking"""
        return {
            "batna": self.batna,
            "budget_ceiling": self.budget_ceiling,
            "personality": self.personality,
            "pressure_points": self.pressure_points
        }
