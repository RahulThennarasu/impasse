"""
Test script demonstrating the negotiation practice flow with NegotiationSession.

This shows how the Session Manager coordinates between:
- OpponentAgent (generates responses)
- CoachAgent (provides real-time tips)
- PostMortemAgent (analyzes after negotiation ends)
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from op_agent.op import OpponentAgent
from coach_agent.coach import CoachAgent
from post_mortem.mortem import PostMortemAgent
from app.core.session import NegotiationSession

# Flag to choose between generated scenario or manual test data
USE_GENERATED_SCENARIO = False

if USE_GENERATED_SCENARIO:
    from scenario_agent.scenario import generate_scenario

    context = "salary negotiation, technology, senior software engineer, engineering manager, promotion discussion, mid-sized SaaS, annual review in 2 weeks, higher base + equity, salary bands + headcount budget."

    print("Generating scenario...")
    scenario_result = generate_scenario(context)

    print(f"\nScenario: {scenario_result['scenario_title']}")
    print(f"\n{scenario_result['user_narrative']}\n")

    opponent_config = scenario_result["opponent_agent_config"]
    coach_config = scenario_result["coach_agent_config"]
    user_briefing = scenario_result["user_briefing"]
else:
    # Manual test data
    opponent_config = {
        "context": "Engineering manager at a mid-sized SaaS company under cost pressure",
        "counterparty_name": "Jordan (Engineering Manager)",
        "counterparty_objectives": "Retain you, stay within compensation guidelines, maintain team morale",
        "counterparty_interests": "Keep reputation as manager who retains talent without escalations. Protect own promotion prospects.",
        "batna": "The salary band ceiling for Staff Engineer is $175K. Going above requires VP exception approval which takes 1-2 weeks and may fail.",
        "constraints": "Annual review cycle closes in 2 weeks. Engineering department has 4% budget for merit increases. Two other engineers expecting promotions.",
        "information_asymmetries": "You don't know about the outside offer at $195K, how serious you are about leaving, or that you've been contacted by other recruiters.",
        "disposition": "Will open by expressing enthusiasm while citing budget constraints. Will offer to 'fight for you' in exchange for patience. Will propose smaller immediate increase with 6-month review. Will probe about leaving without directly asking.",
        "personality": "friendly but firm, supportive yet constrained"
    }

    coach_config = {
        "user_objectives": "Secure compensation reflecting expanded scope and market value. Target $185K from current $158K, equity refresh, and Staff Engineer title.",
        "user_batna": "You have a soft offer from competitor at $195K base, but this means leaving a team and codebase you know well, resetting equity vesting, and potential work-life balance disruption. The competitor is late-stage startup with less job security.",
        "points_of_tension": "Market expectations ($185K+) vs internal band (caps at $175K without exception). Whether promotion is real (with comp) or symbolic (title now, money later). Precedent for other engineers. Whether to reveal outside offer and risk damaging trust.",
        "negotiable_items": "Base salary adjustment, bonus target percentage, equity refresh grant size, promotion effective date, one-time signing/retention bonus.",
        "success_criteria": "Strong outcome: 12%+ total comp increase (base + equity), Staff Engineer title effective this cycle, preserve collaborative relationship. Excellent: Also establish documented path to next level.",
        "info_asymmetries": "You don't know: Exact salary band ceiling, Jordan's budget flexibility, whether others already promised promotions. Jordan doesn't know: Your outside offer, how serious you are about leaving, that you've been contacted by multiple recruiters."
    }

    user_briefing = {
        "objectives": {
            "primary": "Secure Staff Engineer promotion with compensation reflecting market value",
            "secondary": ["Get $185K base", "Equity refresh", "Clear path to next level"]
        },
        "batna": {
            "description": "Accept competitor offer at $195K",
            "strength": "moderate",
            "downsides": ["Reset equity vesting", "Leave known team", "Less job security"]
        },
        "success_criteria": {
            "good_outcome": "12%+ total comp increase, Staff title this cycle",
            "great_outcome": "Base at $180K+, equity refresh, documented path to Principal"
        },
        "negotiables": ["Base salary", "Equity refresh", "Retention bonus", "Start date"]
    }

# =============================================================================
# CREATE SESSION AND AGENTS
# =============================================================================

print("=" * 70)
print("NEGOTIATION SIMULATION: Session-Based Architecture")
print("=" * 70)

# Create the session - this owns the transcript
session = NegotiationSession(
    scenario_id="salary-negotiation-test",
    user_briefing=user_briefing,
    opponent_config=opponent_config,
    coach_config=coach_config
)

# Create agents
opponent = OpponentAgent(opponent_config)
coach = CoachAgent(coach_config)

print(f"\nSession ID: {session.session_id}")
print(f"Opponent: {session.opponent_name}")

print("\nYOUR OBJECTIVES:")
print("   - Get $185K base (from current $158K)")
print("   - Equity refresh")
print("   - Staff Engineer title")
print("\nHIDDEN INFO (opponent doesn't know):")
print("   - You have outside offer at $195K")
print("   - You've been contacted by multiple recruiters")
print("\n" + "=" * 70 + "\n")

# =============================================================================
# START NEGOTIATION
# =============================================================================

session.start()

# Opponent opens
print("OPPONENT OPENING:")
opening = opponent.get_opening_message()
session.add_opening_message(opening, audio_duration_ms=2500)
print(f"JORDAN: {opening}\n")

# Simulated user messages (in real app, these come from STT)
user_messages = [
    "Thanks for meeting with me. I wanted to discuss the Staff Engineer promotion and compensation adjustment.",
    "I appreciate that, but I've done my research and the market rate for Staff Engineers with my experience is around $185K. Can we discuss getting closer to that number?",
    "Actually, I do have some time sensitivity. I've received interest from other companies and need to make a decision soon. What if we explored a retention bonus to bridge the gap?",
    "I can accept $175K base with a $15K retention bonus and an equity refresh of 50% of new hire grant. Does that work for you?"
]

# Run the negotiation
for user_msg in user_messages:
    print(f"{'─' * 70}")
    print(f"TURN {session.current_turn + 1}")
    print(f"{'─' * 70}\n")

    # User speaks (in real app: STT transcribes audio)
    session.add_user_message(user_msg, audio_duration_ms=3000)
    print(f"YOU: {user_msg}\n")

    # Opponent responds (Session provides transcript to agent)
    import time
    start = time.time()
    opp_response = opponent.get_response(session.get_llm_transcript())
    latency = int((time.time() - start) * 1000)

    session.add_opponent_message(opp_response, latency_ms=latency, audio_duration_ms=2000)
    print(f"JORDAN: {opp_response}\n")

    # Coach analyzes (Session provides transcript to coach)
    tip = coach.analyze_turn(session.get_transcript())
    if tip:
        print(f"COACH: {tip}")
    else:
        print(f"COACH: (watching silently...)")

    print()

# =============================================================================
# END NEGOTIATION
# =============================================================================

session.end()

print("\n" + "=" * 70)
print("NEGOTIATION COMPLETE")
print("=" * 70)

# Session metrics
print(f"\nSession Metrics:")
print(f"  Duration: {session.get_duration_seconds():.1f} seconds")
print(f"  Turns: {session.get_turn_count()}")
print(f"  Messages: {session.get_message_count()}")
print(f"  Avg Response Latency: {session.get_average_response_latency():.0f}ms")

# Coach final advice
print(f"\nCOACH'S FINAL FEEDBACK:")
final_advice = coach.get_final_advice(session.get_transcript())
print(final_advice)

# =============================================================================
# POST-MORTEM ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("POST-MORTEM ANALYSIS")
print("=" * 70)

# Create post-mortem agent with full context
post_mortem = PostMortemAgent(
    user_briefing=user_briefing,
    opponent_hidden_state=opponent.get_hidden_state(),
    coach_config=coach_config
)

# Get opponent reveal
print("\n" + post_mortem.get_opponent_reveal())

# Run full analysis (uncomment to run - makes API call)
# print("\nRunning full post-mortem analysis...")
# analysis = post_mortem.analyze(session.get_transcript())
# print(post_mortem.get_summary(analysis))

# =============================================================================
# SHOW SESSION DATA (for debugging/storage)
# =============================================================================

print("\n" + "=" * 70)
print("SESSION DATA (for storage)")
print("=" * 70)

session_data = session.to_dict()
print(f"\nSession ID: {session_data['session_id']}")
print(f"Status: {session_data['status']}")
print(f"Transcript entries: {len(session_data['transcript'])}")

# Show one transcript entry as example
if session_data['transcript']:
    print(f"\nExample transcript entry:")
    entry = session_data['transcript'][1]  # First user message
    for key, value in entry.items():
        print(f"  {key}: {value}")
