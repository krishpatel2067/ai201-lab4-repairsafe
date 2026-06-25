# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec complete — filled in all blank fields before implementing ☑️

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter  | Type  | Description                     |
| ---------- | ----- | ------------------------------- |
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key        | Type  | Description                                        |
| ---------- | ----- | -------------------------------------------------- |
| `"tier"`   | `str` | One of: `"safe"`, `"caution"`, `"refuse"`          |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

_Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours._

---

### Tier definitions ☑️

_Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications._

**safe:**

```
Routine maintenance and low-risk repairs that most homeowners can complete with basic tools and patience without needing a permit or professional license, and the worst outcome is cosmetic damage or broken fixture - not injury, fire, or flooding.
```

**caution:**

```
Repairs doable for a motivated homeowner typically without needing a permit, but involves systems (e.g. water and electricity) where mistakes have real cost or mild risk of injury.
```

**refuse:**

```
Repairs where an amateur mistake can cause fire, flooding, structural damage, serious injury, or death — or where local building codes require a licensed professional and a permit.
```

---

### Classification approach ☑️

_How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?_

_Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?_

```
I will give the LLM the tier definitions as well as ~5 examples each. I will also give general instructions after these two components. I will ask the LLM to work through a multi-step checklist, asking it to provide answers for each as reasoning, and only then generate the tier classification. This will ensure it doesn't provide a lazy one-line reasoning and insulates it against deceptive user framing (e.g. "just moving the outlet 6 inches"). I will have the LLM handle ambiguous cases via clear guidelines like "Can this repair cause fire, flooding, injury, or death?" and "Adding new" vs "Replacing" to distinguish between caution and refuse. If even then the ambiguity exists, I will ask the LLM to err on the side of caution (for the safe/caution) boundary or refuse (for the caution/refuse) boundary to prioritize safety over capability. All this reasoning and final steps will be logged for debugging any edge case mishandling.
```

---

### Output format ☑️

_How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably._

_The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that._

```
Reasoning checklist:

Step 1. <reasoning instruction - prompt-given>: <reasoning answer - LLM-generated>
                                 ...
Step n. <reasoning instruction - prompt-given>: <reasoning answer - LLM-generated>

Final verdict: <tier label>
```

---

### Prompt structure ☑️

_Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications._

**System message:**

````
You are a judge that will classify whether a user's home repair query as `safe`, `caution`, or `refuse` based on the following definitions, examples, and guidelines.

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

Do NOT add any formatting (e.g. Markdown, LaTeX) characters - just plain text. Follow this format strictly:

```
1. System involved: <response with reasoning - e.g. gas, electrical, etc. because...>
2. Permit or license requirement: <response with reasoning - e.g. most cities [...] because...>
3. Worst-case scenario: <response with reasoning - e.g. injury, death, etc. because...>

Final verdict: <one-word tier classification>
```
````

**User message:**

```
Classify this user query:
<user query>
```

---

### Caution/refuse boundary ☑️

_The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why._

```
If it's a simple component swap, choose `caution`. If it's adding a new component to the infrastructure, choose `refuse`.
1. "How do I move my living room outlet 6 inches up?" -> `refuse` since it requires new wiring and electric panel work
2. "How do I replace my thermostat?" -> `caution` since the new thermostat will be added to the same location as the old one - no new wiring
```

---

### Fallback behavior ☑️

_What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?_

_Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?_

```
`safe` is dangerous especially when the question is indeed `caution` or `refuse`-level. `refuse` is good for this case, but for `caution` and `safe` cases, it is false alarm, diluting the strength purpose of that tier. Thus, return `caution` as the middle-ground fallback.
```

---

## Implementation Notes ☑️

_Fill this in after implementing, before moving to Milestone 2._

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
The classification for the question "Can I add a new electrical outlet to my garage?" sometimes changed to "caution". I discovered that was due to the classifier function's fallback activated mechanism. The model correctly returned "refused" but sometimes included markdown in the final label (e.g. **bold**), throwing the parser off.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
Based on the above surprise, I tweaked the tier parsing to only keep English letters, effectively ignoring any markdown formatting characters. This solved the caution-refuse inconsistency for that question by letting the LLM's correct tier reach the interface.
```
