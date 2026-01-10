from dotenv import load_dotenv
load_dotenv()

import sys
import os
# Add parent directory to path so we can import the agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from op_agent.op import OpponentAgent
from coach_agent.coach import CoachAgent

# Simulated scenario data (this would come from your friend's scenario generator)
scenario_data = {
    "context": """You are a Senior Software Engineer at a mid-sized SaaS company (~400 employees)
that has grown rapidly. You're being considered for promotion to Staff Engineer after leading
a successful microservices migration. The company recently closed Series C but is now under
pressure to control costs.""",

    "opponent": {
        "context": "Engineering manager at a mid-sized SaaS company under cost pressure",
        "counterparty_name": "Jordan (Engineering Manager)",
        "counterparty_objectives": "Retain you, stay within compensation guidelines, maintain team morale",
        "counterparty_interests": "Keep reputation as manager who retains talent without escalations. Protect own promotion prospects.",
        "batna": "The salary band ceiling for Staff Engineer is $175K. Going above requires VP exception approval which takes 1-2 weeks and may fail.",
        "constraints": "Annual review cycle closes in 2 weeks. Engineering department has 4% budget for merit increases. Two other engineers expecting promotions.",
        "information_asymmetries": "You don't know about the outside offer at $195K, how serious you are about leaving, or that you've been contacted by other recruiters.",
        "disposition": "Will open by expressing enthusiasm while citing budget constraints. Will offer to 'fight for you' in exchange for patience. Will propose smaller immediate increase with 6-month review. Will probe about leaving without directly asking.",
        "personality": "friendly but firm, supportive yet constrained"
    },

    "coach": {
        "user_objectives": "Secure compensation reflecting expanded scope and market value. Target $185K from current $158K, equity refresh, and Staff Engineer title.",
        "user_batna": "You have a soft offer from competitor at $195K base, but this means leaving a team and codebase you know well, resetting equity vesting, and potential work-life balance disruption. The competitor is late-stage startup with less job security.",
        "points_of_tension": "Market expectations ($185K+) vs internal band (caps at $175K without exception). Whether promotion is real (with comp) or symbolic (title now, money later). Precedent for other engineers. Whether to reveal outside offer and risk damaging trust.",
        "negotiable_items": "Base salary adjustment, bonus target percentage, equity refresh grant size, promotion effective date, one-time signing/retention bonus.",
        "success_criteria": "Strong outcome: 12%+ total comp increase (base + equity), Staff Engineer title effective this cycle, preserve collaborative relationship. Excellent: Also establish documented path to next level.",
        "info_asymmetries": "You don't know: Exact salary band ceiling, Jordan's budget flexibility, whether others already promised promotions. Jordan doesn't know: Your outside offer, how serious you are about leaving, that you've been contacted by multiple recruiters."
    }
}

print("=" * 70)
print("NEGOTIATION SIMULATION: Salary Negotiation (V2 Agents)")
print("=" * 70)
print("\n🎯 YOUR OBJECTIVES:")
print("   - Get $185K base (from current $158K)")
print("   - Equity refresh")
print("   - Staff Engineer title")
print("\n🔒 HIDDEN INFO (opponent doesn't know):")
print("   - You have outside offer at $195K")
print("   - You've been contacted by multiple recruiters")
print("\n" + "=" * 70 + "\n")

# Initialize agents
opponent = OpponentAgent(scenario_data["opponent"])
coach = CoachAgent(scenario_data["coach"])

# Simulate negotiation
conversation = [
    "Thanks for meeting with me. I wanted to discuss the Staff Engineer promotion and compensation adjustment.",
    "I appreciate that, but I've done my research and the market rate for Staff Engineers with my experience is around $185K. Can we discuss getting closer to that number?",
    "Actually, I do have some time sensitivity. I've received interest from other companies and need to make a decision soon. What if we explored a retention bonus to bridge the gap?",
    "I can accept $175K base with a $15K retention bonus and an equity refresh of 50% of new hire grant. Does that work for you?"
]

for turn, user_msg in enumerate(conversation, 1):
    print(f"{'─' * 70}")
    print(f"TURN {turn}")
    print(f"{'─' * 70}\n")

    # User speaks
    print(f"💬 YOU: {user_msg}\n")

    # Opponent responds
    opp_response = opponent.get_response(user_msg)
    print(f"💼 JORDAN: {opp_response}\n")

    # Coach analyzes
    tip = coach.analyze_turn(opponent.transcript)
    if tip:
        print(f"🎯 COACH: {tip}")
    else:
        print(f"🎯 COACH: (watching silently...)")

    print()

# Final analysis
print("\n" + "=" * 70)
print("NEGOTIATION COMPLETE")
print("=" * 70)

final_advice = coach.get_final_advice(opponent.transcript)
print(f"\n📊 COACH'S FINAL FEEDBACK:\n{final_advice}\n")

# Post-mortem reveal
print("=" * 70)
print("POST-MORTEM: OPPONENT'S HIDDEN STATE REVEALED")
print("=" * 70)
hidden = opponent.get_hidden_state()
print(f"\nJordan's real constraints:")
print(f"  • {hidden['batna']}")
print(f"  • {hidden['constraints']}")
print(f"\nWhat Jordan didn't know:")
print(f"  • {hidden['info_asymmetries']}")
print(f"\n💡 ANALYSIS:")
print(f"   You negotiated to $175K base + $15K retention + equity.")
print(f"   Their ceiling was $175K without VP exception.")
print(f"   You extracted the maximum from their band AND got extra value via retention bonus!")
print(f"   Strong negotiation - you discovered their constraint and worked around it.")
