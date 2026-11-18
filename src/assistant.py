"""
VibeFinder command line assistant.

Run it from the project root:
    python -m src.assistant "calm songs for studying"     # one request
    python -m src.assistant                                # interactive, with feedback
    python -m src.assistant --offline "songs for a road trip"
    python -m src.assistant --show-trace "sad songs after a breakup"
"""

import argparse

from tabulate import tabulate

from src.agent import LOW_CONFIDENCE, AgentResult, MusicAgent, setup_logging
from src.llm_client import get_client


def show_result(result: AgentResult, show_trace: bool = False) -> None:
    if show_trace:
        print("--- agent trace ---")
        for line in result.trace:
            print(" ", line)
        print("-------------------\n")

    if result.blocked:
        print(f"Request blocked: {result.block_reason}\n")
        return

    print(f"Profile used: {result.profile}")
    if result.profile_fixes:
        print(f"Profile fixes: {'; '.join(result.profile_fixes)}")
    print(f"Guide notes used: {', '.join(result.notes) or 'none'}")
    print(f"Planner: {result.planner} | Writer: {result.writer} | Confidence: {result.confidence:.2f}\n")
    print(result.summary + "\n")

    rows = [[i, p["title"], p["artist"], p["genre"], f"{p['score']:.2f}", p["reason"]]
            for i, p in enumerate(result.picks, start=1)]
    print(tabulate(rows, headers=["#", "Title", "Artist", "Genre", "Score", "Why"],
                   tablefmt="grid", disable_numparse=True,
                   maxcolwidths=[None, 20, 16, 10, None, 60]))
    print()

    if result.confidence < LOW_CONFIDENCE:
        print("Warning: low confidence. The catalog may not have a good match for this, "
              "so please double-check these picks or rephrase the request.\n")


def interactive(agent: MusicAgent, show_trace: bool) -> None:
    print("VibeFinder - describe the music you want (q to quit).")
    request = input("\nYou: ").strip()
    while request.lower() not in ("q", "quit", "exit"):
        result = agent.run(request)
        show_result(result, show_trace)

        # Human-in-the-loop: the listener accepts the picks or steers the next run.
        feedback = input("Good? (y = yes / type a tweak like 'more upbeat' / q = quit): ").strip()
        if feedback.lower() in ("q", "quit", "exit"):
            break
        if feedback.lower() in ("y", "yes", ""):
            request = input("\nYou: ").strip()
        else:
            request = f"{request}, but {feedback}"
            print(f"\nRe-running with: \"{request}\"")


def main() -> None:
    parser = argparse.ArgumentParser(description="VibeFinder music assistant")
    parser.add_argument("request", nargs="?", help="what you want to listen to")
    parser.add_argument("--offline", action="store_true", help="skip Gemini and use the rule-based fallback")
    parser.add_argument("--show-trace", action="store_true", help="print every agent step")
    parser.add_argument("--no-guide", action="store_true",
                        help="turn off the genre guide (to compare results with and without retrieval)")
    args = parser.parse_args()

    setup_logging()
    client = get_client(offline=args.offline)
    agent = MusicAgent(client=client, notes=[] if args.no_guide else None)
    print(f"Running in {'Gemini' if client else 'offline'} mode.\n")

    if args.request is None:
        interactive(agent, args.show_trace)
    else:
        show_result(agent.run(args.request), args.show_trace)


if __name__ == "__main__":
    main()
