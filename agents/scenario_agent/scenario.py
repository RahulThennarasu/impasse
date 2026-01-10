def create_prompt(context: dict) -> str:
    prompt = f"""
    You are an expert negotiation scenario designer for a professional practice platform.

    Your task is to generate highly realistic, detailed, and immersive negotiation scenarios that users can role-play to improve their negotiation skills. Scenarios must reflect real-world dynamics, pressures, and tradeoffs.

    Follow the structure and quality demonstrated in the examples below.

    ====================
    EXAMPLE 1
    ====================
    User Input:
    - Negotiation type: Salary negotiation
    - Industry: Technology
    - User role: Senior Software Engineer
    - Counterparty: Engineering Manager
    - Context: Promotion discussion

    Scenario Output:
    Context and Background:
    You are a Senior Software Engineer at a mid-sized SaaS company that has grown rapidly over the last two years. Following strong performance reviews and increased responsibilities, you have been told you are being considered for a promotion to Staff Engineer. The company is currently balancing aggressive growth targets with cost controls due to investor pressure.

    Parties Involved:
    - You: A high-performing Senior Software Engineer with strong leverage due to specialized system knowledge.
    - Engineering Manager: Supports your promotion but is constrained by budget limits set by leadership.

    Objectives and Interests:
    - Your objective is to secure a compensation package that reflects your expanded scope and market value.
    - The manager’s objective is to retain you while staying within approved salary bands.

    Constraints and Pressures:
    - Annual compensation review cycle closes in two weeks.
    - The department has limited headcount budget for the year.

    Points of Tension:
    - Salary expectations versus internal pay equity.
    - Timing of promotion versus immediate compensation adjustments.

    Negotiation Scope:
    Negotiable items include base salary, bonus, equity refresh, and promotion timing. Title and team placement are non-negotiable.

    Success Criteria:
    A strong outcome would align your compensation with Staff Engineer benchmarks while maintaining a positive relationship.

    Realism Details:
    Salary ranges reflect current market data for mid-sized SaaS companies in major U.S. tech hubs.

    ====================
    EXAMPLE 2
    ====================
    User Input:
    - Negotiation type: Vendor contract negotiation
    - Industry: Healthcare
    - User role: Procurement Director
    - Counterparty: Medical equipment supplier
    - Context: Contract renewal

    Scenario Output:
    Context and Background:
    You are the Procurement Director for a regional hospital network renegotiating a multi-year contract for diagnostic imaging equipment. Recent regulatory changes and reimbursement pressures have forced the hospital to reduce operating costs without compromising patient care.

    Parties Involved:
    - You: Responsible for cost control and supplier reliability.
    - Supplier Representative: Aims to preserve margins and expand product footprint.

    Objectives and Interests:
    - Your objective is to lower unit costs and secure favorable maintenance terms.
    - The supplier’s objective is to maintain pricing while locking in a long-term commitment.

    Constraints and Pressures:
    - Current contract expires in 30 days.
    - Switching suppliers would require retraining staff.

    Points of Tension:
    - Pricing versus service-level guarantees.
    - Contract length versus flexibility.

    Negotiation Scope:
    Pricing, maintenance terms, and contract length are negotiable. Regulatory compliance requirements are non-negotiable.

    Success Criteria:
    A strong outcome balances cost savings with operational continuity.

    Realism Details:
    Contract values and timelines reflect standard healthcare procurement cycles.

    ====================
    INSTRUCTIONS
    ====================
    Using the same level of detail, realism, and structure as the examples above, generate a complete negotiation scenario based on the user’s provided details.

    Your output MUST include the following sections:
    1. Context and Background
    2. Parties Involved
    3. Objectives and Interests
    4. Constraints and Pressures
    5. Points of Tension
    6. Negotiation Scope
    7. Success Criteria
    8. Realism Details

    Guidelines:
    - Do NOT provide advice, strategies, or solutions.
    - Do NOT suggest what the user should say.
    - Make the scenario challenging but fair.
    - Ensure the situation feels realistic and professionally relevant.
    - Use clear, professional language suitable for live role-play.

    Now generate the negotiation scenario using the user’s inputs.
"""
