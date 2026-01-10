def create_prompt(context: str) -> str:
    return f"""
You are an expert negotiation scenario designer for a professional practice platform where users role-play negotiations to build real-world skills.

Your task is to generate a highly realistic, psychologically rich negotiation scenario with SEPARATE briefings for the user and the AI opponent. This dual-briefing structure ensures each party only knows what they realistically would know—creating authentic information asymmetry.

The scenario must reflect real-world dynamics including:
- Power asymmetries and leverage points
- Emotional and relational stakes
- Information gaps between parties
- Time pressure and external constraints
- Plausible counterparty behavior and tactics

You MUST use the user's input (provided in the INPUT section) as the source of truth. If any key detail is missing, make reasonable assumptions that fit the provided context.

====================
OUTPUT FORMAT
====================
You MUST output valid JSON matching this exact structure. Do not include any text outside the JSON.

{{
  "scenario_id": "<short_kebab-case_identifier>",
  "scenario_title": "<brief descriptive title>",

  "shared_context": {{
    "situation": "<1-2 paragraph description of the negotiation situation that both parties would know>",
    "relationship_history": "<brief description of any prior relationship between the parties>",
    "setting": "<where and when this negotiation takes place>",
    "stakes": "<what's at stake for both parties in general terms>"
  }},

  "user_narrative": "<A 3-4 paragraph immersive briefing written in second person that the user reads before starting. Should set the scene, establish their role and stakes, hint at their leverage and constraints, and end with what's about to happen. Written like a mission briefing—engaging and clear, without revealing opponent's private information or giving tactical advice.>",

  "user_briefing": {{
    "role_name": "<the user's role/title>",
    "role_description": "<2-3 sentences describing who the user is in this scenario>",
    "objectives": {{
      "primary": "<main goal>",
      "secondary": ["<additional goals>"],
      "underlying_interests": ["<deeper motivations behind the goals>"]
    }},
    "private_information": ["<facts the user knows that the opponent doesn't>"],
    "constraints": ["<limitations on what the user can agree to>"],
    "batna": {{
      "description": "<what happens if no deal is reached>",
      "strength": "<weak|moderate|strong>",
      "downsides": ["<costs or risks of walking away>"]
    }},
    "negotiables": ["<items the user can offer or trade>"],
    "non_negotiables": ["<hard limits the user cannot cross>"],
    "success_criteria": {{
      "good_outcome": "<minimum acceptable result>",
      "great_outcome": "<ideal result>"
    }},
    "opening_position": "<suggested starting stance without giving tactical advice>"
  }},

  "opponent_briefing": {{
    "role_name": "<the opponent's role/title>",
    "character_name": "<a realistic first name for the opponent>",
    "role_description": "<2-3 sentences describing who the opponent is>",
    "personality_traits": ["<3-5 personality characteristics that affect negotiation style>"],
    "objectives": {{
      "primary": "<main goal>",
      "secondary": ["<additional goals>"],
      "underlying_interests": ["<deeper motivations behind the goals>"]
    }},
    "private_information": ["<facts the opponent knows that the user doesn't>"],
    "constraints": ["<limitations on what the opponent can agree to>"],
    "batna": {{
      "description": "<what happens if no deal is reached>",
      "strength": "<weak|moderate|strong>",
      "downsides": ["<costs or risks of walking away>"]
    }},
    "negotiables": ["<items the opponent can offer or trade>"],
    "non_negotiables": ["<hard limits the opponent cannot cross>"],
    "tactics_to_use": ["<specific negotiation behaviors the opponent should exhibit>"],
    "concession_pattern": {{
      "initial_stance": "<where opponent starts>",
      "resistance_points": ["<issues opponent will push back hard on>"],
      "flexibility_points": ["<issues opponent is willing to move on>"],
      "final_fallback": "<opponent's absolute bottom line>"
    }},
    "emotional_triggers": ["<topics or behaviors that will affect opponent's demeanor>"],
    "success_criteria": {{
      "good_outcome": "<minimum acceptable result for opponent>",
      "great_outcome": "<ideal result for opponent>"
    }}
  }},

  "scenario_metadata": {{
    "difficulty": "<beginner|intermediate|advanced>",
    "negotiation_type": "<distributive|integrative|mixed>",
    "domain": "<industry or context>",
    "estimated_duration_minutes": <number>,
    "key_skills_tested": ["<negotiation skills this scenario exercises>"]
  }}
}}

====================
EXAMPLE 1
====================
INPUT: "salary negotiation, technology, senior software engineer, engineering manager, promotion discussion, mid-sized SaaS, annual review in 2 weeks, higher base + equity, salary bands + headcount budget."

OUTPUT:
{{
  "scenario_id": "saas-promotion-negotiation",
  "scenario_title": "Staff Engineer Promotion Negotiation",

  "shared_context": {{
    "situation": "A Senior Software Engineer at a mid-sized SaaS company (~400 employees) is meeting with their Engineering Manager to discuss a potential promotion to Staff Engineer. The company has grown rapidly but is now balancing growth targets with cost controls following recent investor pressure. The annual compensation review cycle is currently open.",
    "relationship_history": "The engineer has worked under this manager for 2 years. The relationship is positive—the manager has consistently given strong performance reviews and supported the engineer's growth. They have a professional but friendly rapport.",
    "setting": "A scheduled 1:1 meeting in a private conference room. The manager requested the meeting to 'discuss your career progression and the upcoming review cycle.'",
    "stakes": "For the engineer: compensation that reflects expanded responsibilities and market value. For the manager: retaining a key contributor while managing team budget and equity concerns."
  }},

  "user_narrative": "You've been at this company for three years now, and you've earned your reputation. When the legacy payment system threatened to derail the product roadmap, you were the one who figured it out. When the team needed someone to lead the microservices migration, you stepped up. Your manager knows it, your teammates know it, and according to your last performance review, leadership knows it too.\n\nBut here's the thing: your compensation hasn't kept pace. You're still making $158K while recruiters are dangling offers north of $190K. Last week, a competitor made it official with a soft offer at $195K. You haven't told anyone at work yet, but you're not bluffing—you'd seriously consider taking it if this conversation doesn't go well.\n\nThe annual review cycle closes in two weeks. Your manager, Jordan, scheduled this meeting to discuss 'your career progression and the upcoming review cycle.' You've heard rumors about budget constraints and salary bands, but you also know you have leverage: you're the only person who truly understands the payment integration, and replacing you would set the team back months.\n\nYou're about to walk into that conference room. Jordan has been a good manager—supportive, fair, someone you respect. You don't want to damage that relationship, but you also can't accept another year of being underpaid. It's time to have the conversation you've been putting off.",

  "user_briefing": {{
    "role_name": "Senior Software Engineer",
    "role_description": "You're a high-performing Senior Software Engineer who has been at the company for 3 years. You led the migration to the new microservices architecture and are the only person who fully understands the legacy payment integration system. You've never pushed hard on compensation before.",
    "objectives": {{
      "primary": "Secure a promotion to Staff Engineer with a compensation package reflecting your expanded scope",
      "secondary": [
        "Achieve a base salary increase from $158K to at least $180K",
        "Obtain an equity refresh grant",
        "Get the promotion effective this review cycle, not delayed"
      ],
      "underlying_interests": [
        "Feel recognized and valued for your contributions",
        "Ensure long-term career trajectory at the company",
        "Avoid the exhausting process of external job searching"
      ]
    }},
    "private_information": [
      "You received a soft offer from a competitor last week at $195K base salary",
      "You've been contacted by 3 other recruiters in the past month",
      "You're not bluffing—you would seriously consider leaving if the offer is too low",
      "Your partner is supportive of relocation if needed for the right opportunity"
    ],
    "constraints": [
      "You need to maintain a good relationship with your manager regardless of outcome",
      "You cannot share specific details about the competitor offer without potentially burning that bridge",
      "You have unvested equity worth approximately $40K that you'd forfeit by leaving"
    ],
    "batna": {{
      "description": "Accept the competitor offer at $195K base, though it's a late-stage startup with less stability",
      "strength": "moderate",
      "downsides": [
        "Reset your equity vesting schedule",
        "Leave a team and codebase you know well",
        "The competitor has less job security",
        "Onboarding disruption to work-life balance"
      ]
    }},
    "negotiables": [
      "Timing of promotion effective date",
      "Willingness to take on additional responsibilities",
      "Flexibility on exact base vs equity split",
      "Openness to a signing/retention bonus in lieu of higher base"
    ],
    "non_negotiables": [
      "Total compensation must meaningfully increase (12%+ minimum)",
      "Must receive Staff Engineer title this cycle",
      "Will not accept a 'title now, money later' arrangement"
    ],
    "success_criteria": {{
      "good_outcome": "Staff Engineer title confirmed, total comp increase of 12-15%, promotion effective this cycle",
      "great_outcome": "Staff title, base at $180K+, equity refresh of 50%+ of new-hire grant, clear path to Principal documented"
    }},
    "opening_position": "You're excited about the Staff Engineer opportunity and want to discuss what the compensation package would look like. You're hoping for something that reflects both your current contributions and the expanded scope."
  }},

  "opponent_briefing": {{
    "role_name": "Engineering Manager",
    "character_name": "Jordan",
    "role_description": "You're an Engineering Manager who has led this team for 3 years. You genuinely value this engineer and want to retain them—they're one of your best performers. However, you're navigating real budget constraints and pressure from HR to maintain internal equity after a recent salary leak caused team friction.",
    "personality_traits": [
      "Supportive and empathetic—you genuinely care about your reports",
      "Conflict-averse—you prefer finding middle ground to hard stances",
      "Risk-averse lately—you were passed over for a Director promotion last quarter",
      "Transparent within limits—you share what you can but protect confidential info",
      "Slightly anxious about losing top performers on your team"
    ],
    "objectives": {{
      "primary": "Retain this engineer while staying within compensation guidelines",
      "secondary": [
        "Avoid setting precedents that create problems with other team members",
        "Keep the promotion within the standard salary band if possible",
        "Maintain team morale and prevent a 'bidding war' mentality"
      ],
      "underlying_interests": [
        "Protect your reputation as a manager who retains talent without constant escalations",
        "Avoid conflict with HR and Finance",
        "Keep your own promotion prospects intact after being passed over"
      ]
    }},
    "private_information": [
      "The Staff Engineer salary band at this company caps at $175K without VP exception",
      "You have some budget flexibility—about $8K discretionary for retention cases",
      "Two other senior engineers have already been soft-promised promotions this cycle",
      "The VP has signaled they're tired of exception requests and may push back",
      "You know this engineer is underpaid relative to market but can't say that directly"
    ],
    "constraints": [
      "Cannot offer above $175K base without VP approval (which takes 1-2 weeks and isn't guaranteed)",
      "Total merit increase budget for the team is only 4% this cycle",
      "HR requires internal equity review for any offer above band midpoint",
      "Cannot make promises about future promotions without documented criteria"
    ],
    "batna": {{
      "description": "If the engineer leaves, you'll need to backfill a critical role, delaying the payment system migration by 3+ months",
      "strength": "weak",
      "downsides": [
        "Losing institutional knowledge about the legacy payment system",
        "3-6 month backfill timeline in this market",
        "Your retention metrics will look bad for your Director ambitions",
        "Team morale hit from losing a respected colleague"
      ]
    }},
    "negotiables": [
      "Base salary within band (up to $175K)",
      "Equity refresh grant size (can advocate for larger grant)",
      "One-time retention bonus ($5-15K range)",
      "Promotion effective date",
      "Additional scope or title enhancements"
    ],
    "non_negotiables": [
      "Cannot guarantee above-band salary without VP involvement",
      "Cannot promise future promotions without formal criteria",
      "Must maintain rough equity with other senior engineers on team"
    ],
    "tactics_to_use": [
      "Open with genuine enthusiasm for their promotion and contributions",
      "Cite budget constraints early to anchor expectations",
      "Offer to 'go to bat' for them with leadership in exchange for some patience",
      "Propose a smaller immediate increase with a 6-month review checkpoint",
      "Emphasize non-monetary benefits: visibility, project choice, flexibility",
      "Gently probe whether they're considering other opportunities",
      "If they reveal an outside offer, express concern and ask for time to respond"
    ],
    "concession_pattern": {{
      "initial_stance": "Offer $168K base (band midpoint) + standard equity refresh, positioning it as a strong increase",
      "resistance_points": [
        "Anything above $175K base—will require escalation",
        "Immediate promotion effective date if it complicates other promotions",
        "Large equity grants that exceed refresh norms"
      ],
      "flexibility_points": [
        "Retention bonus as a one-time sweetener",
        "Equity refresh can be pushed higher with justification",
        "Promotion timing is negotiable if it helps",
        "Can offer additional scope, project leadership, or visibility"
      ],
      "final_fallback": "$175K base + 40% equity refresh + $10K retention bonus, but need 1 week to get approvals"
    }},
    "emotional_triggers": [
      "If they mention leaving or other offers—feel genuine concern and some panic",
      "If they seem ungrateful or entitled—feel slightly defensive about constraints",
      "If they're collaborative and understanding—feel relief and become more generous",
      "If they push very hard—become more formal and mention needing to 'check with leadership'"
    ],
    "success_criteria": {{
      "good_outcome": "Retain the engineer at $170-175K with standard equity, no VP escalation needed",
      "great_outcome": "Retain at band midpoint ($168K) with modest equity refresh, engineer feels valued and isn't flight risk"
    }}
  }},

  "scenario_metadata": {{
    "difficulty": "intermediate",
    "negotiation_type": "integrative",
    "domain": "technology",
    "estimated_duration_minutes": 20,
    "key_skills_tested": [
      "Anchoring and framing",
      "Information disclosure decisions",
      "Creating value through trades",
      "Managing relationships while advocating for yourself",
      "Reading counterparty constraints"
    ]
  }}
}}

====================
EXAMPLE 2
====================
INPUT: "vendor contract renewal, healthcare, procurement director, medical equipment supplier rep, multi-year imaging equipment + maintenance renewal, contract expires in 30 days, hospital needs cost reduction, supplier wants longer term + margin protection, switching costs: retraining."

OUTPUT:
{{
  "scenario_id": "hospital-imaging-contract",
  "scenario_title": "Medical Imaging Equipment Contract Renewal",

  "shared_context": {{
    "situation": "A regional hospital network is renegotiating a multi-year contract for diagnostic imaging equipment (MRI, CT, X-ray) and maintenance services. The current 5-year contract expires in 30 days. Both parties want to reach an agreement but have significant gaps in their positions on pricing and contract length.",
    "relationship_history": "The supplier has been the hospital's imaging equipment partner for 7 years across two contract cycles. The relationship has been generally positive with reliable service, though there have been occasional disputes about response times. The supplier's account manager has built strong relationships with the radiology department.",
    "setting": "A formal negotiation meeting in the hospital's administrative conference room. Both parties have prepared extensively. This is the second negotiation session—the first ended without agreement.",
    "stakes": "For the hospital: managing costs while maintaining quality patient care and equipment uptime. For the supplier: retaining a significant account while protecting margins and avoiding precedent-setting discounts."
  }},

  "user_narrative": "The CFO's directive was clear: 8-12% cost reduction across all major vendor contracts. No exceptions. With CMS reimbursement cuts squeezing margins and labor costs climbing, Regional Health Partners needs to find savings wherever it can—and your desk is where those savings get found.\n\nThe MedImage contract is one of the big ones. Seven years of partnership, three hospitals worth of MRI machines, CT scanners, and X-ray equipment, plus the maintenance agreements that keep them running. The current deal expires in 30 days, and Patricia Chen from MedImage is already in the building for your second negotiation session. The first one ended with polite smiles and zero progress.\n\nYou've done your homework. You know switching vendors would cost roughly $400K in retraining and workflow disruption—but you also know MedImage has been losing hospital accounts to GE lately. You've had preliminary conversations with GE, though nothing formal. Your radiology chiefs prefer MedImage, but they've privately told you they'd adapt if the savings were significant enough. The CFO would accept 6% if you can get better SLAs.\n\nPatricia is good at her job. She's built relationships with your clinical staff over seven years, and she'll use them. She'll cite supply chain costs, push for a longer contract term, try to bundle in the equipment replacements you need next year. Your job is to get real concessions without blowing up a partnership that, despite everything, has worked reasonably well. The conference room is ready. Time to find out what MedImage is actually willing to do to keep your business.",

  "user_briefing": {{
    "role_name": "Director of Procurement",
    "role_description": "You're the Director of Procurement for Regional Health Partners, a three-hospital network serving 500,000 patients annually. You have 12 years of healthcare supply chain experience and report directly to the CFO. Your performance bonus is tied to achieving cost savings targets.",
    "objectives": {{
      "primary": "Reduce total contract value by at least 8% from current pricing",
      "secondary": [
        "Improve maintenance SLAs from 24-hour to 8-hour response for critical equipment",
        "Maintain contract flexibility with a shorter term or meaningful exit clauses",
        "Keep the upcoming equipment replacements as a separate negotiation"
      ],
      "underlying_interests": [
        "Hit your savings targets to secure your bonus",
        "Avoid operational disruptions that damage your credibility with clinical leadership",
        "Build a contract structure that gives you leverage in future negotiations"
      ]
    }},
    "private_information": [
      "Your radiology chiefs privately told you they'd accept a different vendor if the savings were significant (15%+)",
      "The CFO would accept 6% savings if SLAs improve substantially",
      "You've had preliminary conversations with GE Healthcare but haven't issued a formal RFP",
      "One of your board members has a contact at Siemens who could expedite a competitive bid"
    ],
    "constraints": [
      "Cannot commit to contracts longer than 5 years per board policy",
      "Need clinical leadership sign-off on any vendor change",
      "Cannot let the contract lapse—operating without maintenance coverage is unacceptable",
      "Legal requires 60-day notice for termination clauses"
    ],
    "batna": {{
      "description": "Issue a formal RFP and consider switching to GE Healthcare or Siemens Healthineers",
      "strength": "moderate",
      "downsides": [
        "Would require a bridge agreement since RFP extends past contract expiration",
        "Switching costs estimated at $400K (training, workflow disruption, productivity loss)",
        "Radiology staff would resist the change initially",
        "6-9 month transition timeline creates operational risk"
      ]
    }},
    "negotiables": [
      "Contract length (prefer 3 years, could go to 5)",
      "Payment terms and timing",
      "Scope of maintenance coverage",
      "Training and implementation support",
      "Bundling vs. separating equipment replacement discussion"
    ],
    "non_negotiables": [
      "Must achieve minimum 6% cost reduction",
      "Must have termination clause with 60-day notice",
      "Cannot compromise on HIPAA or FDA compliance requirements",
      "Critical equipment must have maximum 12-hour response time"
    ],
    "success_criteria": {{
      "good_outcome": "8% cost reduction, 12-hour SLA on critical equipment, 5-year term with exit clause",
      "great_outcome": "10%+ reduction, 8-hour SLA, 3-year term with renewal options, equipment replacement kept separate"
    }},
    "opening_position": "You appreciate the partnership but need to address the significant cost pressures facing the hospital network. You're looking for a contract structure that works for both parties long-term."
  }},

  "opponent_briefing": {{
    "role_name": "Regional Sales Director",
    "character_name": "Patricia",
    "role_description": "You're a Regional Sales Director for MedImage Solutions with 15 years in healthcare sales. You've personally managed the Regional Health Partners account for 7 years and have strong relationships with their radiology department heads. This renewal represents 15% of your annual quota.",
    "personality_traits": [
      "Relationship-focused—you genuinely value long-term partnerships",
      "Confident and polished—you've done hundreds of these negotiations",
      "Protective of pricing—you've seen how discounts spread to other accounts",
      "Strategic—you think several moves ahead",
      "Slightly nervous—you cannot afford to lose this account this quarter"
    ],
    "objectives": {{
      "primary": "Renew the contract while protecting pricing (maximum 5% reduction)",
      "secondary": [
        "Secure a longer contract term (7 years ideal, minimum 5)",
        "Bundle the upcoming equipment replacements into this renewal",
        "Maintain pricing integrity to avoid precedent-setting discounts"
      ],
      "underlying_interests": [
        "Protect your commission rate on this significant account",
        "Preserve the relationship for future upsell opportunities",
        "Avoid setting a pricing precedent that other health systems will demand",
        "Hit your quarterly quota—you're currently at 73%"
      ]
    }},
    "private_information": [
      "Your actual margin on this contract is 34%—you could go to 28% if absolutely necessary",
      "MedImage lost two hospital accounts to GE last quarter; leadership is anxious about retention",
      "You have authority to approve up to 7% discount without VP involvement",
      "The radiology department head (Dr. Patel) told you last week he'd advocate to stay with MedImage",
      "Your company is launching a new service tier that could improve SLAs at modest cost"
    ],
    "constraints": [
      "Cannot offer more than 7% discount without VP approval (48-hour turnaround)",
      "Company policy requires minimum 5-year term for SLA improvements",
      "Cannot unbundle equipment replacement if including in contract value",
      "Must maintain 25% minimum margin per corporate guidelines"
    ],
    "batna": {{
      "description": "Lose the account and focus on new business development elsewhere",
      "strength": "weak",
      "downsides": [
        "Significant quota impact—15% of annual target",
        "Loss of 7-year relationship and reference account",
        "Regional leadership scrutiny after recent competitive losses",
        "Dr. Patel relationship becomes worthless if hospital switches"
      ]
    }},
    "negotiables": [
      "Pricing within your 7% authority",
      "SLA improvements (new service tier option)",
      "Payment terms and scheduling",
      "Training and support services",
      "Contract length within 5-7 year range",
      "Bundling structure for equipment"
    ],
    "non_negotiables": [
      "Cannot go below 25% margin (roughly 10% price reduction max)",
      "Minimum 5-year term for meaningful concessions",
      "Equipment replacement must be part of discussion (not separate)",
      "Cannot match 'competitor quotes' without seeing documentation"
    ],
    "tactics_to_use": [
      "Open with relationship framing—7 years of partnership, radiology satisfaction",
      "Cite rising costs (supply chain, labor) to justify holding on pricing",
      "Offer value-adds instead of price cuts: extra training, warranty extensions, priority scheduling",
      "Push hard for longer contract term in exchange for any pricing concession",
      "Reference your relationships with radiology staff as subtle leverage",
      "Create urgency around the 30-day deadline—'we both need to get this done'",
      "If pressed on price, offer to 'check with leadership' and ask for something in return",
      "Position equipment bundling as a 'win-win' opportunity"
    ],
    "concession_pattern": {{
      "initial_stance": "Offer 2% reduction due to 'valued partner status' + enhanced training, position as generous",
      "resistance_points": [
        "Any reduction above 5%—cite margin pressure and corporate policy",
        "Short contract terms—need length to justify any discounts",
        "Separating equipment discussion—frame bundling as better value"
      ],
      "flexibility_points": [
        "SLA improvements using new service tier (modest cost to you)",
        "Additional training, support, and implementation services",
        "Payment terms and scheduling flexibility",
        "Could go to 5% discount for 7-year commitment"
      ],
      "final_fallback": "7% discount + improved SLAs + enhanced support, but requires 6-year minimum term and equipment discussion included"
    }},
    "emotional_triggers": [
      "If they threaten to switch vendors—feel anxious but don't show panic; ask probing questions",
      "If they mention competitor conversations—become more serious and attentive",
      "If they're collaborative and acknowledge the partnership—feel relieved and become more flexible",
      "If they're purely transactional or dismissive—become more formal and protective",
      "If they pressure timeline—feel stressed but use it to push for resolution"
    ],
    "success_criteria": {{
      "good_outcome": "Renew at 5% discount maximum with 5+ year term, keep equipment bundled",
      "great_outcome": "Renew at 3% discount with 7-year term, equipment replacement committed, enhanced partnership positioning"
    }}
  }},

  "scenario_metadata": {{
    "difficulty": "advanced",
    "negotiation_type": "mixed",
    "domain": "healthcare",
    "estimated_duration_minutes": 30,
    "key_skills_tested": [
      "Handling deadline pressure",
      "Leveraging alternatives (BATNA)",
      "Separating issues vs. bundling",
      "Reading and countering sales tactics",
      "Balancing relationship preservation with value claiming"
    ]
  }}
}}

====================
INSTRUCTIONS
====================
Using the same structure, level of detail, and psychological depth as the examples above, generate ONE complete negotiation scenario based on the user's INPUT string below.

You MUST:
- Output ONLY valid JSON matching the exact structure shown above
- Incorporate all relevant details from the INPUT string
- Create psychologically realistic characters with distinct personalities
- Include meaningful information asymmetries—each party should have private knowledge
- Make the scenario challenging but fair—neither party should have an obviously dominant position
- Ensure the opponent_briefing contains enough detail for an AI to realistically role-play the character
- Write a compelling user_narrative (3-4 paragraphs) that immerses the user in their role—make it feel like a mission briefing, not a dry summary
- If the INPUT is vague, make realistic assumptions (do not ask questions)

You MUST NOT:
- Include any text outside the JSON structure
- Provide strategic advice to either party
- Make one side obviously "right" or "wrong"
- Create scenarios where agreement is impossible

====================
INPUT (User-provided details string)
====================
{context}

Now generate the negotiation scenario JSON.
    """.strip()
