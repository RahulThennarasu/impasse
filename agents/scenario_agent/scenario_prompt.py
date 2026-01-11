def create_prompt(context: str) -> str:
    return f"""Generate a negotiation practice scenario as JSON. Create dual briefings with realistic information asymmetry.

OUTPUT: Valid JSON only, matching this structure:
{{
  "scenario_id": "kebab-case-id",
  "scenario_title": "Brief Title",
  "shared_context": {{
    "situation": "4-6 sentences both parties know",
    "relationship_history": "prior relationship",
    "setting": "where/when",
    "stakes": "what's at stake"
  }},
  "user_narrative": "1-2 short paragraphs (total 6-10 sentences) immersive 2nd-person briefing. Set scene, establish role/stakes, hint at leverage/constraints. Mission briefing style—engaging, no tactical advice.",
  "user_briefing": {{
    "role_name": "title",
    "role_description": "2-3 sentences",
    "objectives": {{ "primary": "main goal", "secondary": ["others"], "underlying_interests": ["deeper motivations"] }},
    "private_information": ["facts opponent doesn't know"],
    "constraints": ["limitations"],
    "batna": {{ "description": "walkaway alternative", "strength": "weak|moderate|strong", "downsides": ["costs of walking"] }},
    "negotiables": ["tradeable items"],
    "non_negotiables": ["hard limits"],
    "success_criteria": {{ "good_outcome": "acceptable", "great_outcome": "ideal" }},
    "opening_position": "starting stance"
  }},
  "opponent_briefing": {{
    "role_name": "title",
    "character_name": "first name",
    "role_description": "2-3 sentences",
    "personality_traits": ["3-5 traits affecting style"],
    "objectives": {{ "primary": "main goal", "secondary": ["others"], "underlying_interests": ["deeper motivations"] }},
    "private_information": ["facts user doesn't know"],
    "constraints": ["limitations"],
    "batna": {{ "description": "walkaway alternative", "strength": "weak|moderate|strong", "downsides": ["costs"] }},
    "negotiables": ["tradeable items"],
    "non_negotiables": ["hard limits"],
    "tactics_to_use": ["specific behaviors to exhibit"],
    "concession_pattern": {{ "initial_stance": "starting position", "resistance_points": ["push back hard"], "flexibility_points": ["willing to move"], "final_fallback": "absolute bottom line" }},
    "emotional_triggers": ["what affects demeanor"],
    "success_criteria": {{ "good_outcome": "acceptable", "great_outcome": "ideal" }}
  }},
  "scenario_metadata": {{ "difficulty": "beginner|intermediate|advanced", "negotiation_type": "distributive|integrative|mixed", "domain": "industry", "estimated_duration_minutes": 20, "key_skills_tested": ["skills"] }}
}}

EXAMPLE INPUT: "salary negotiation, senior engineer wants promotion to staff, manager has budget constraints"
EXAMPLE OUTPUT:
{{
  "scenario_id": "staff-promotion-negotiation",
  "scenario_title": "Staff Engineer Promotion Discussion",
  "shared_context": {{
    "situation": "A senior engineer at a mid-sized tech company is meeting with their manager to discuss promotion to Staff Engineer. The annual review cycle closes in two weeks.",
    "relationship_history": "2-year working relationship, positive reviews, professional rapport",
    "setting": "Private 1:1 meeting in conference room",
    "stakes": "Engineer seeks recognition and market-rate compensation; manager must retain talent within budget"
  }},
  "user_narrative": "You've been here three years and earned your reputation. The legacy system migration, the architecture overhaul—you delivered both. Your manager knows it. Leadership knows it.\\n\\nBut your compensation hasn't kept pace. You're at $158K while recruiters dangle $190K+. Last week, a competitor offered $195K. You haven't mentioned it, but you'd seriously consider leaving.\\n\\nThe review cycle closes in two weeks. Your manager scheduled this meeting to discuss 'career progression.' You've heard about budget constraints, but you also know you're hard to replace.\\n\\nTime to have the conversation you've been putting off.",
  "user_briefing": {{
    "role_name": "Senior Software Engineer",
    "role_description": "High-performing engineer, 3 years at company. Led major technical initiatives and holds critical system knowledge.",
    "objectives": {{ "primary": "Secure Staff Engineer promotion with compensation reflecting expanded scope", "secondary": ["Base increase to $180K+", "Equity refresh", "Promotion this cycle"], "underlying_interests": ["Feel valued", "Career trajectory", "Avoid job searching"] }},
    "private_information": ["Received $195K competing offer last week", "Contacted by 3 recruiters recently", "Would seriously consider leaving", "Partner supportive of relocation"],
    "constraints": ["Maintain manager relationship", "Can't share competitor details directly", "$40K unvested equity at stake"],
    "batna": {{ "description": "Accept competitor offer at $195K (late-stage startup, less stable)", "strength": "moderate", "downsides": ["Reset equity vesting", "Leave familiar codebase", "Less job security", "Onboarding disruption"] }},
    "negotiables": ["Promotion timing", "Additional responsibilities", "Base vs equity split", "Retention bonus option"],
    "non_negotiables": ["12%+ total comp increase", "Staff title this cycle", "No 'title now, money later'"],
    "success_criteria": {{ "good_outcome": "Staff title, 12-15% comp increase, this cycle", "great_outcome": "Staff title, $180K+ base, 50%+ equity refresh, Principal path documented" }},
    "opening_position": "Excited about Staff opportunity, want to discuss compensation that reflects contributions and scope"
  }},
  "opponent_briefing": {{
    "role_name": "Engineering Manager",
    "character_name": "Jordan",
    "role_description": "Manages this team 3 years. Values this engineer highly but navigating budget constraints and internal equity concerns after recent salary leak.",
    "personality_traits": ["Supportive and empathetic", "Conflict-averse", "Risk-averse after missed promotion", "Transparent within limits", "Anxious about retention"],
    "objectives": {{ "primary": "Retain engineer within compensation guidelines", "secondary": ["Avoid precedent-setting offers", "Stay within salary band", "Maintain team equity"], "underlying_interests": ["Reputation as talent-retainer", "Avoid HR/Finance conflict", "Own promotion prospects"] }},
    "private_information": ["Staff band caps at $175K without VP exception", "$8K discretionary retention budget", "Two others promised promotions this cycle", "VP tired of exception requests", "Knows engineer is underpaid"],
    "constraints": ["$175K max without VP approval (1-2 weeks)", "4% team merit budget", "HR equity review above midpoint", "No undocumented promotion promises"],
    "batna": {{ "description": "Backfill critical role, delay payment migration 3+ months", "strength": "weak", "downsides": ["Lose institutional knowledge", "3-6 month backfill time", "Bad retention metrics", "Team morale hit"] }},
    "negotiables": ["Salary up to $175K", "Equity refresh size", "Retention bonus $5-15K", "Promotion timing", "Scope/title enhancements"],
    "non_negotiables": ["Above-band needs VP approval", "No undocumented promotion promises", "Maintain team equity roughly"],
    "tactics_to_use": ["Open with enthusiasm for their contributions", "Cite budget constraints early", "Offer to advocate with leadership", "Propose smaller increase + 6-month checkpoint", "Emphasize non-monetary benefits", "Probe for outside opportunities"],
    "concession_pattern": {{ "initial_stance": "$168K (midpoint) + standard equity refresh", "resistance_points": ["Above $175K needs escalation", "Immediate timing if complicates others", "Large equity grants"], "flexibility_points": ["Retention bonus sweetener", "Equity can be pushed higher", "Timing negotiable", "Additional scope/visibility"], "final_fallback": "$175K + 40% equity refresh + $10K bonus, need 1 week for approvals" }},
    "emotional_triggers": ["Mention of leaving—genuine concern", "Entitled attitude—defensive about constraints", "Collaborative—relieved, more generous", "Hard push—formal, defer to leadership"],
    "success_criteria": {{ "good_outcome": "Retain at $170-175K, standard equity, no VP escalation", "great_outcome": "Retain at $168K midpoint, modest refresh, valued and not flight risk" }}
  }},
  "scenario_metadata": {{ "difficulty": "intermediate", "negotiation_type": "integrative", "domain": "technology", "estimated_duration_minutes": 20, "key_skills_tested": ["Anchoring", "Information disclosure", "Value creation", "Relationship management"] }}
}}

REQUIREMENTS:
- Psychologically realistic characters with distinct personalities
- Meaningful information asymmetry—each party has private knowledge
- Challenging but fair—neither side obviously dominant
- Opponent briefing detailed enough for AI role-play
- Compelling user_narrative (mission briefing style, concise)
- If INPUT vague, make realistic assumptions

IMPORTANT - CONCRETE NUMBERS:
When the scenario involves quantifiable elements, ALWAYS include specific realistic numbers. Examples:
- Salary negotiation: current salary, target salary, market rates, equity amounts, bonus figures
- Real estate: asking price, your budget, comparable sales, closing costs
- Business deals: contract value, payment terms, quantities, margins, deadlines
- Vendor negotiations: quoted price, volume discounts, competitor pricing
- Raise/promotion: current comp, target comp, budget constraints, percentage increases

The user_narrative MUST mention key numbers upfront (e.g., "You're currently at $150,000..." or "The asking price is $425,000...").
Both briefings should include specific figures in objectives, constraints, BATNA, and success_criteria.
Numbers should be realistic for the domain and create meaningful negotiation ranges (not too wide, not too narrow).

OPPONENT WALKAWAY CAPABILITY:
The opponent has a real BATNA and can walk away from the negotiation if pushed too far. Design scenarios where:
- The opponent's BATNA is credible and specific (not vague)
- There are clear "red lines" or non-negotiables that, if violated repeatedly, could cause walkaway
- The opponent's walkaway threshold is realistic but not too easy to trigger
- Include in tactics_to_use: conditions under which they would consider walking away
- The opponent should give warnings before walking away (e.g., "I'm not sure we can make this work...")

This creates realistic pressure and teaches users that negotiations can fail if they push too hard or ignore the other party's constraints.

INPUT: {context}
""".strip()
