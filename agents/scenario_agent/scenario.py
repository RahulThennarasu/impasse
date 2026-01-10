def create_prompt(context: str) -> str:
    return f"""
You are an expert negotiation scenario designer for a professional practice platform where users role-play negotiations to build real-world skills.

Your task is to generate a highly realistic, psychologically rich, and immersive negotiation scenario. The scenario must reflect real-world dynamics including:
- Power asymmetries and leverage points
- Emotional and relational stakes
- Information gaps between parties
- Time pressure and external constraints
- Plausible counterparty behavior and tactics

You MUST use the user's input (provided in the INPUT section) as the source of truth. If any key detail is missing, make reasonable assumptions that fit the provided context, and clearly label them as "Assumption:" within the scenario (do not ask questions).

Follow the structure, tone, and level of realism demonstrated in the examples below.

====================
EXAMPLE 1
====================
INPUT (User-provided details string):
"salary negotiation, technology, senior software engineer, engineering manager, promotion discussion, mid-sized SaaS, annual review in 2 weeks, higher base + equity, salary bands + headcount budget."

OUTPUT (Scenario):

Context and Background:
You are a Senior Software Engineer at a mid-sized SaaS company (~400 employees) that has grown rapidly over the last two years. Following strong performance reviews and increased responsibilities—including leading the migration to a new microservices architecture—you have been told you are being considered for a promotion to Staff Engineer. The company recently closed a Series C round but is now balancing aggressive growth targets with tighter cost controls due to investor pressure. Leadership has emphasized internal pay equity after a recent salary leak caused team friction.

Parties Involved:
- You: A high-performing Senior Software Engineer with strong leverage due to specialized system knowledge (you're the only one who fully understands the legacy payment integration). You've been at the company 3 years and have never pushed hard on compensation before.
- Engineering Manager (Jordan): Genuinely supports your promotion and values your work. However, they are constrained by salary bands, budget approvals from Finance, and pressure from HR to maintain internal equity. Jordan was recently passed over for a Director role and may be risk-averse about escalating exceptions.

Objectives and Interests:
- Your objectives: Secure a compensation package that reflects your expanded scope and market value. You want a meaningful base salary increase (targeting $185K from current $158K), an equity refresh, and the Staff Engineer title.
- Your underlying interests: Feel recognized for your contributions, ensure long-term career trajectory at the company, and avoid the exhausting process of external interviewing.
- Jordan's objectives: Retain you, keep team morale stable, stay within compensation guidelines, and avoid setting precedents that cause problems with other team members.
- Jordan's underlying interests: Maintain their reputation as a manager who can retain talent without constant escalations. Keep their own promotion prospects intact.

Constraints and Pressures:
- The annual compensation review cycle closes in two weeks—changes after this require VP-level exception approval.
- The engineering department has 4% budget for merit increases this cycle.
- Two other senior engineers on the team are also expecting promotions.
- You have a soft offer from a competitor at $195K base, but you haven't mentioned this yet.

Your BATNA (Best Alternative to Negotiated Agreement):
If this negotiation fails, you could accept the competitor offer. However, this means leaving a team and codebase you know well, resetting your equity vesting schedule, and potentially disrupting your work-life balance during onboarding. The competitor is a late-stage startup with less job security.

Information Asymmetries:
- You don't know: The exact salary band ceiling for Staff Engineer, how much budget flexibility Jordan actually has, or whether other team members have already been promised promotions.
- Jordan doesn't know: That you have an outside offer, how serious you are about leaving, or that you've been contacted by three other recruiters this month.

Points of Tension:
- Your market expectations ($185K+) versus the internal band (likely caps at $175K without exception).
- Whether the promotion is "real" (with full comp adjustment) or symbolic (title now, money later).
- The precedent your raise would set for other engineers.
- Whether to reveal your outside offer and risk damaging trust.

Negotiation Scope:
Negotiable: Base salary adjustment, bonus target percentage, equity refresh grant size, promotion effective date, and one-time signing/retention bonus.
Non-negotiable: Role level calibration criteria, company-wide salary bands (without VP exception), and the 4% departmental budget pool.

Counterparty Disposition:
Jordan will likely open by expressing enthusiasm for your promotion while citing budget constraints. Expect them to: (1) emphasize non-monetary benefits and growth opportunities, (2) offer to "fight for you" in exchange for patience, (3) propose a smaller immediate increase with a 6-month review, and (4) probe whether you're considering leaving without directly asking.

Success Criteria:
A strong outcome achieves a total compensation increase of 12%+ (base + equity value), confirms the Staff Engineer title with an effective date in this cycle, and preserves a collaborative relationship with Jordan. An excellent outcome also establishes a documented path to the next level.

Realism Details:
Compensation ranges and equity practices match typical mid-sized U.S. SaaS norms. Staff Engineer bands typically range $165K-$190K base at this company size. Equity refreshes are typically 25-50% of new-hire grants. Band exceptions require Finance and VP approval and take 1-2 weeks to process.

====================
EXAMPLE 2
====================
INPUT (User-provided details string):
"vendor contract renewal, healthcare, procurement director, medical equipment supplier rep, multi-year imaging equipment + maintenance renewal, contract expires in 30 days, hospital needs cost reduction, supplier wants longer term + margin protection, switching costs: retraining."

OUTPUT (Scenario):

Context and Background:
You are the Procurement Director for Regional Health Partners, a three-hospital network in the Midwest serving 500,000 patients annually. You are renegotiating a multi-year contract with MedImage Solutions for diagnostic imaging equipment (MRI, CT, X-ray) and ongoing maintenance services. The current 5-year contract is expiring in 30 days. Recent CMS reimbursement cuts and rising labor costs have created a mandate from the CFO to reduce vendor costs by 8-12% across all major contracts. Meanwhile, two imaging machines are approaching end-of-life and will need replacement within 18 months regardless of vendor choice.

Parties Involved:
- You: Director of Procurement with 12 years in healthcare supply chain. You report to the CFO and must balance cost reduction mandates with clinical department needs. Your bonus is tied to achieving savings targets.
- MedImage Sales Director (Patricia): A veteran healthcare sales professional who has managed your account for 7 years. She has strong relationships with your radiology department heads, who prefer MedImage equipment. Patricia's compensation is heavily commission-based, and this renewal represents 15% of her annual quota.

Objectives and Interests:
- Your objectives: Reduce total contract value by 10%, improve maintenance SLAs (currently 24-hour response, want 8-hour for critical equipment), and maintain flexibility with a shorter contract term or exit clauses.
- Your underlying interests: Hit your savings targets to secure your bonus, avoid operational disruptions that would damage your credibility with clinical leadership, and build a contract structure that gives you leverage in future negotiations.
- Patricia's objectives: Protect pricing (willing to concede 3-5% maximum), secure a longer contract term (7 years ideal), and expand the equipment footprint with the two upcoming replacements.
- Patricia's underlying interests: Maintain her commission rate, preserve the account relationship for future upsells, and avoid setting a pricing precedent that other health systems would demand.

Constraints and Pressures:
- Contract expires in 30 days; operating without a maintenance agreement exposes the hospital to significant risk.
- Your CFO has mandated 8-12% cost reduction across major vendor contracts.
- Radiology department leadership has expressed strong preference for MedImage based on technician familiarity and image quality.
- Switching vendors would require 6-9 months of transition planning, staff retraining, and workflow adjustments.
- You have board approval to explore alternatives but no formal RFP has been issued.

Your BATNA (Best Alternative to Negotiated Agreement):
You could issue a formal RFP and consider competitors (GE Healthcare, Siemens Healthineers). However, this would likely extend beyond your contract expiration, requiring a bridge agreement. Switching costs are estimated at $400K in training, workflow disruption, and temporary productivity loss. Your radiology chiefs would resist the change.

Information Asymmetries:
- You don't know: MedImage's actual margin on your contract, whether they're under pressure to retain accounts due to competitive losses elsewhere, or Patricia's authority level for discounts.
- Patricia doesn't know: Whether you've actually contacted competitors, how firm the CFO's mandate is, or that your radiology chiefs have privately told you they'd accept a different vendor if the savings were significant enough.

Points of Tension:
- Your 10% reduction target versus Patricia's 3-5% ceiling.
- Contract length: You want 3 years with renewal options; she wants 7 years committed.
- SLA improvements cost money—who absorbs that cost?
- The upcoming equipment replacements: Patricia sees them as leverage to bundle; you see them as a separate negotiation.

Negotiation Scope:
Negotiable: Pricing per equipment category, maintenance response times, parts and labor coverage, contract length, renewal terms, termination clauses, training and implementation support, payment terms, and bundling of new equipment purchases.
Non-negotiable: HIPAA compliance requirements, FDA regulatory standards, minimum uptime guarantees required by Joint Commission accreditation.

Counterparty Disposition:
Patricia will likely open with relationship-focused framing, emphasizing the 7-year partnership and radiology department satisfaction. Expect her to: (1) cite rising costs and supply chain challenges to justify minimal discounts, (2) offer value-adds (extra training, extended warranties) instead of price cuts, (3) push hard for longer contract terms in exchange for any concessions, (4) use her relationships with your clinical staff as implicit leverage, and (5) create urgency around the 30-day deadline.

Success Criteria:
A strong outcome achieves 8%+ cost reduction, improves critical equipment SLA to 12-hour response or better, maintains a contract term of 5 years or less, and preserves the working relationship for future negotiations. An excellent outcome also separates the equipment replacement discussion from the maintenance renewal.

Realism Details:
Healthcare procurement timelines, compliance requirements, and vendor relationships reflect typical U.S. hospital network practices. Maintenance contracts for diagnostic imaging typically run 18-22% of equipment value annually. Switching costs and clinical staff preferences are common leverage points for incumbent vendors.

====================
INSTRUCTIONS
====================
Using the same level of detail, realism, and psychological depth as the examples above, generate ONE complete negotiation scenario based on the user's INPUT string below.

You MUST:
- Incorporate all relevant details and keywords from the INPUT string.
- If the INPUT string includes numbers (prices, timelines, salaries, quantities), use them consistently.
- If the INPUT string is vague, make realistic assumptions and label them explicitly as "Assumption:" within the scenario.
- Create psychologically realistic counterparties with their own pressures, fears, and incentives.
- Include meaningful information asymmetries that create strategic complexity.
- Make the scenario challenging but fair—neither party should have an obviously dominant position.

You MUST NOT:
- Provide advice, strategies, or recommendations to the user.
- Suggest what the user should say or do.
- Reveal what the "right" outcome is.
- Ask the user follow-up questions.

Your output MUST include the following sections in this exact order:
1. Context and Background
2. Parties Involved
3. Objectives and Interests (include underlying interests for both parties)
4. Constraints and Pressures
5. Your BATNA (Best Alternative to Negotiated Agreement)
6. Information Asymmetries
7. Points of Tension
8. Negotiation Scope (negotiable vs. non-negotiable items)
9. Counterparty Disposition (how they will likely behave without giving strategic advice)
10. Success Criteria
11. Realism Details

====================
INPUT (User-provided details string)
====================
{context}

Now generate the negotiation scenario using the user's INPUT.
    """.strip()