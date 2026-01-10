# Test file: agents/test_agents.py
from op_agent.op import OpponentAgent
from coach_agent.coach import CoachAgent

# Scenario config
scenario = {
    "batna": "$90,000 minimum salary",
    "budget_ceiling": "$110,000",
    "personality": "friendly but firm",
    "pressure_points": ["Q4 hiring deadline", "3 other candidates in pipeline"]
}

# Initialize agents
opponent = OpponentAgent(scenario)
coach = CoachAgent()

# Simulate a negotiation turn
user_msg = "I'm looking for $105,000 for this role"
opp_response = opponent.get_response(user_msg)
print(f"Opponent: {opp_response}")

# Coach analyzes
tip = coach.analyze_turn(opponent.transcript)
if tip:
    print(f"Coach: {tip}")
