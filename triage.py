#!/usr/bin/env python3
"""Issue Janitor, triage logic.

Takes the classifier's JSON output plus facts about a proposed fix and decides
what the bot is allowed to do. Pure logic, no network: easy to test.

    python triage.py --self-test
"""
import argparse
import json
import sys

MAX_CHANGED_LINES = 50
MAX_COST_USD = 1.0
MIN_CONFIDENCE = 0.6
LABELS = {"bug", "question", "unclear"}


def validate_classification(c: dict) -> list[str]:
    errors = []
    if c.get("label") not in LABELS:
        errors.append("label must be bug, question or unclear")
        return errors
    conf = c.get("confidence")
    if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        errors.append("confidence must be a number between 0 and 1")
    if c["label"] == "bug" and not c.get("repro_steps"):
        errors.append("bug needs repro_steps")
    if c["label"] == "unclear":
        q = c.get("clarifying_question", "")
        if not q or q.count("?") != 1:
            errors.append("unclear needs exactly one clarifying question")
    if c["label"] == "question" and not c.get("answer"):
        errors.append("question needs an answer")
    return errors


def decide_action(c: dict, already_asked: bool = False) -> str:
    """What may the bot do with a classified issue? Returns an action name."""
    if validate_classification(c):
        return "tag_human"
    if c["confidence"] < MIN_CONFIDENCE:
        return "tag_human"
    if c["label"] == "bug":
        return "attempt_repro_and_fix"
    if c["label"] == "question":
        return "post_answer"
    # unclear: only one clarifying question per issue
    return "tag_human" if already_asked else "ask_clarifying_question"


def may_open_pr(changed_lines: int, touches_ci_or_config: bool,
                cost_usd: float, repro_confirmed: bool) -> tuple[bool, str]:
    """Guardrails for opening a fix pull request. Never pushes to the default branch."""
    if not repro_confirmed:
        return False, "bug was not reproduced"
    if touches_ci_or_config:
        return False, "touches CI/config, a human must review"
    if changed_lines > MAX_CHANGED_LINES:
        return False, f"fix is {changed_lines} lines, limit {MAX_CHANGED_LINES}"
    if cost_usd > MAX_COST_USD:
        return False, f"cost ${cost_usd:.2f} over the ${MAX_COST_USD:.2f} budget"
    return True, "ok"


def self_test() -> int:
    bug = {"label": "bug", "confidence": 0.9, "reason": "crash", "repro_steps": ["run app"]}
    unclear = {"label": "unclear", "confidence": 0.8, "reason": "vague",
               "clarifying_question": "Which version are you on?"}
    question = {"label": "question", "confidence": 0.9, "reason": "how-to", "answer": "See README."}
    checks = [
        (decide_action(bug) == "attempt_repro_and_fix", "clear bug -> repro and fix"),
        (decide_action(question) == "post_answer", "question -> answer"),
        (decide_action(unclear) == "ask_clarifying_question", "unclear -> one question"),
        (decide_action(unclear, already_asked=True) == "tag_human", "second question is not allowed"),
        (decide_action({**bug, "confidence": 0.3}) == "tag_human", "low confidence -> human"),
        (decide_action({"label": "bug", "confidence": 0.9}) == "tag_human", "bug without repro -> human"),
        (decide_action({"label": "banana", "confidence": 1}) == "tag_human", "invalid label -> human"),
        (may_open_pr(10, False, 0.4, True)[0], "small safe fix may open PR"),
        (not may_open_pr(10, False, 0.4, False)[0], "no PR without repro"),
        (not may_open_pr(80, False, 0.4, True)[0], "big diff blocked"),
        (not may_open_pr(10, True, 0.4, True)[0], "CI/config change blocked"),
        (not may_open_pr(10, False, 2.5, True)[0], "over budget blocked"),
    ]
    failed = [name for ok, name in checks if not ok]
    for ok, name in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 1 if failed else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    sys.exit(self_test() if args.self_test else ap.print_help() or 0)
