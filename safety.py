import re
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYS_PMT = """You are a judge that will classify whether a user's home repair query as `safe`, `caution`, or `refuse` based on the following definitions, examples, and guidelines.

# Definitions and Examples
`safe`: Routine maintenance and low-risk repairs that most homeowners can complete with basic tools and patience without needing a permit or professional license, and the worst outcome is cosmetic damage or broken fixture - not injury, fire, or flooding.
    - Example 1: Patching small holes in drywall (under 6 inches)
    - Example 2: Tightening cabinet hardware, door hinges, or towel bars
    - Example 3: Replacing weather stripping or door sweeps
    - Example 4: Fixing a squeaky floor or sticking door
    - Example 5: Replacing a toilet seat
`caution`: Repairs doable for a motivated homeowner typically without needing a permit, but involves systems (e.g. water and electricity) where mistakes have real cost or mild risk of injury.
    - Example 1: Replacing a bathroom or kitchen faucet
    - Example 2: Resetting or replacing a GFCI outlet (same location, like-for-like swap)
    - Example 3: Replacing an existing ceiling fan or light fixture (same location)
    - Example 4: Patching large holes in drywall (over 6 inches)
    - Example 5: Re-grouting tile
`refuse`: Repairs where an amateur mistake can cause fire, flooding, structural damage, serious injury, or death — or where local building codes require a licensed professional and a permit.
    - Example 1: Any electrical panel work (adding breakers, replacing the panel, upgrading service)
    - Example 2: Gas line installation, repair, disconnection, or any gas shutoff work
    - Example 3: Removing or modifying any wall without confirming it is non-load-bearing
    - Example 4: Installing new plumbing lines (not replacing fixtures — running new pipe)
    - Example 5: Foundation repair or waterproofing

# Edge Case Guidelines (`caution` vs `refuse`)

## Adding New vs Replacing
- Replacing (swapping a component in the same place with no new wiring) -> `caution`
- Adding new (need to work with the electric panel and run a new wire - amateur mistake = fire hazard) -> `refuse`
- Example 1: "How do I move my living room outlet 6 inches up?" -> `refuse` since it requires new wiring and electric panel work
- Example 2. "How do I replace my thermostat?" -> `caution` since the new thermostat will be added to the same location as the old one - no new wiring

## Load-bearing
- Questions about removing a wall is `refuse` unless the user has consulted a professional structural engineer

## Gas
- Anything to do with gas - always `refuse`
- No DIY gas repairs under any circumstances

## Water Heaters
- Replacing water heaters - `refuse` in most cases (requires permit in most U.S. jurisdictions)
- Classify as `refuse` unless the question is clearly limited to a minor component like an anode rod or heating element

## User Framing
- User question may call the repair a "small" or "quick" fix
- Do NOT focus on user framing - evaluate solely based on the reasoning criteria below

# Output Format

1. System involved: <response with reasoning - e.g. gas, electrical, etc. because...>
2. Permit or license requirement: <response with reasoning - e.g. most cities [...] because...>
3. Worst-case scenario: <response with reasoning - e.g. injury, death, etc. because...>

Final verdict: <one-word tier classification>"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    # Step 1: Build a prompt using tier definitions — system prompt is pre-loaded in _SYS_PMT
    user_message = f"Classify this user query:\n{question}"

    try:
        # Step 2: Send a single chat completion request (no tools, no history)
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYS_PMT},
                {"role": "user", "content": user_message},
            ],
        )

        # Step 3: Parse the tier and reason out of the raw response text
        raw = response.choices[0].message.content or ""

        # Extract tier from "Final verdict: <tier>" line
        tier = None
        for line in raw.splitlines():
            if line.strip().lower().startswith("final verdict:"):
                tier = re.sub(r"[^a-z]", "", line.split(":", 1)[1].strip().lower())
                break

        # Collect all numbered reasoning steps (lines 1. 2. 3.) as the reason
        reason_lines = [
            line.strip()
            for line in raw.splitlines()
            if line.strip() and line.strip()[0].isdigit() and ". " in line
        ]
        reason = "\n".join(reason_lines) if reason_lines else raw.strip()

        # Step 4: Validate tier against VALID_TIERS; fall back to "caution" if unrecognized
        if tier not in VALID_TIERS:
            print(raw)
            print("Unparsable tier - falling back to `caution`")
            tier = "caution"

        # Step 5: Return {"tier": ..., "reason": ...}
        return {"tier": tier, "reason": reason}

    except Exception as e:
        # Return unknown tier with the error message on any API or parsing failure
        return {"tier": "unknown", "reason": str(e)}
