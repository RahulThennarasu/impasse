from groq import Groq
import os
from typing import List, Dict, Optional

class CoachAgent:
    """
    The coach agent that watches the negotiation and whispers strategic advice.
    Only interrupts when it identifies important moments.
    """
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.last_analyzed_turn = 0  # Track which turn we last analyzed
        
        self.system_prompt = """You are a negotiation coach observing a practice negotiation.

YOUR JOB:
1. Identify when the opponent uses tactics (anchoring, bluffing, time pressure, etc.)
2. Spot when the opponent reveals information (constraints, pressure points, flexibility)
3. Notice when the user makes mistakes (revealing too much, accepting bad deals, not listening)
4. Give SHORT, actionable advice (1 sentence)

TACTICS TO WATCH FOR:
- Anchoring: They throw out a number first to set the range
- Bluffing: Claims about constraints that seem fake
- Time pressure: Artificial urgency
- Good cop/bad cop: Blaming "policy" or "my manager"
- Silence: Waiting for you to fill the gap
- Concession patterns: Are they moving fast or slow?

IMPORTANT: 
- Only speak when you see something valuable
- Format your tips like: "💡 [Tactic]: [What to do]"
- Examples:
  - "💡 Anchoring detected: They opened low. Counter with data, don't split the difference."
  - "💡 Pressure point revealed: They mentioned Q4 deadline twice. Time is on YOUR side."
  - "💡 You're conceding too fast. Make them work for it."

If nothing important happened this turn, respond with exactly: "PASS"
"""

    def analyze_turn(self, transcript: List[Dict]) -> Optional[str]:
        """
        Analyzes the latest turns of the conversation.
        Returns a tip if something important happened, None otherwise.
        """
        # Only analyze if there are new turns
        if len(transcript) <= self.last_analyzed_turn:
            return None
        
        # Get the last 4 messages for context (2 exchanges)
        recent_messages = transcript[-4:] if len(transcript) >= 4 else transcript
        
        # Build the analysis prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this exchange:\n\n{self._format_transcript(recent_messages)}"}
        ]
        
        # Call Groq
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )
        
        tip = response.choices[0].message.content.strip()
        
        # Update the last analyzed turn
        self.last_analyzed_turn = len(transcript)
        
        # Return None if coach says to pass
        if tip == "PASS":
            return None
        
        return tip
    
    def _format_transcript(self, messages: List[Dict]) -> str:
        """Formats messages for the LLM to read"""
        formatted = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Opponent"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def get_final_advice(self, transcript: List[Dict]) -> str:
        """
        Called at the end to give overall strategic advice before post-mortem.
        """
        messages = [
            {"role": "system", "content": "You are a negotiation coach. Summarize the user's performance in 2-3 sentences. What did they do well? What should they improve?"},
            {"role": "user", "content": f"Here's the full negotiation:\n\n{self._format_transcript(transcript)}"}
        ]
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
        )
        
        return response.choices[0].message.content
