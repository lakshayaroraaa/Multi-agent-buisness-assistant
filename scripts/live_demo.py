"""Live end-to-end demo: real Azure AI Foundry orchestration and tool execution.

Requires a filled-in .env (see .env.example) with an Azure AI Foundry project,
model deployment, and Cosmos DB. Run `python scripts/ingest_knowledge_base.py`
once first if you want the Knowledge agent to answer from real Azure AI Search
data; otherwise it falls back automatically to local sample-document search.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from agents.orchestrator_agent import handle_message  # noqa: E402 - import after load_dotenv() on purpose


def main() -> None:
    session_id = "live-demo-session"
    print("Type a question for the assistant (Ctrl+C to quit).\n")
    while True:
        try:
            message = input("> ")
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not message.strip():
            continue
        response = handle_message(session_id, message)
        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
