import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.tools import tool  # noqa: E402

from agent.config import build_model  # noqa: E402


@tool
def add_two_numbers(first: int, second: int) -> int:
    """Add two integers."""
    return first + second


def main():
    model = build_model()
    response = model.bind_tools([add_two_numbers]).invoke(
        "Use the add_two_numbers tool to calculate 2 + 3. Do not calculate it yourself."
    )
    tool_calls = [
        {"name": call["name"], "args": call["args"]}
        for call in response.tool_calls
    ]
    print(
        json.dumps(
            {
                "tool_call_detected": bool(tool_calls),
                "tool_calls": tool_calls,
            },
            sort_keys=True,
        )
    )
    if not tool_calls:
        raise SystemExit("The model did not return a tool call.")


if __name__ == "__main__":
    main()