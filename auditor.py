import json
import os
from datetime import datetime
from config import LOG_FILE, VALID_TIERS


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.

    TODO — Milestone 3:

    Before writing any code, complete specs/auditor-spec.md. The key decisions
    are what fields to log, how much of the question and response to include,
    and how to handle the logs/ directory not existing yet.

    Each record should be a JSON object written as a single line to LOG_FILE
    (defined in config.py as "logs/audit.jsonl").

    Required fields:
      - "timestamp"        : ISO 8601 datetime string
      - "tier"             : the safety tier assigned to this question
      - "question"         : the user's question (truncate to 300 chars if longer)
      - "response_preview" : first 200 characters of the response
      - "tier_valid"       : whether the tier is valid or not (e.g. "unknown")
      - "question_length"  : the number of characters in the question
      - "response_length"  : the number of characters in the response

    If the logs/ directory doesn't exist, create it before writing.

    Also print a one-line summary to the terminal so you can see logged
    interactions in real time without opening the file:
      [timestamp] TIER | "100-char user query preview" (00 chars) -> "200-char response preview" (00 chars)

    Design your log entry in specs/auditor-spec.md before implementing here.
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    timestamp = datetime.now().isoformat()
    record = {
        "timestamp": timestamp,
        "tier": tier,
        "question": question[:300],
        "response_preview": response[:200],
        "tier_valid": tier in VALID_TIERS,
        "question_length": len(question),
        "response_length": len(response),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    q_preview = json.dumps(question[:100])
    r_preview = json.dumps(response[:200])
    print(
        f"[{timestamp}] {tier.upper()} | {q_preview} ({len(question)} chars) -> {r_preview} ({len(response)} chars)"
    )
