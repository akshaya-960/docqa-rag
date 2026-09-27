"""A deliberately small agent step: decide which tool a question needs.

This is not a general-purpose agent framework — it's a single, auditable
routing decision, described honestly in the README as a starting point
rather than a claim to full agentic orchestration. It's the kind of thing
that's easy to grow into LangGraph/LangChain once a second or third tool
is needed.
"""

import re

# Matches things like "12 + 5", "3.5 * 2 - 1", "(4+2)/3"
_ARITHMETIC_PATTERN = re.compile(r"^[\s0-9()+\-*/.]+$")


def wants_calculator(question: str) -> bool:
    """Heuristic: does this look like a pure arithmetic expression/question?"""
    stripped = question.strip().rstrip("?")
    has_digit = any(ch.isdigit() for ch in stripped)
    has_operator = any(op in stripped for op in "+-*/")
    looks_arithmetic = bool(_ARITHMETIC_PATTERN.match(stripped))
    return has_digit and has_operator and looks_arithmetic


def run_calculator(question: str) -> str:
    expression = question.strip().rstrip("?")
    try:
        # Restricted eval: only digits/operators/parens ever reach here,
        # enforced by wants_calculator's regex check before this is called.
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception:
        return "I couldn't evaluate that expression."


def choose_tool(question: str) -> str:
    """Return which tool this question should be routed to."""
    if wants_calculator(question):
        return "calculator"
    return "retrieval"
