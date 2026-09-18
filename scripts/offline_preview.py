"""Local preview of the assistant's business logic — no Azure credentials needed.

This script does NOT call Azure OpenAI or Azure AI Foundry. It exercises the
same tool functions, Pydantic schemas, and keyword-based routing logic the real
system uses, so you can see and demo real, validated data flowing through the
project before any Azure resources are provisioned. Once your .env is filled
in (see .env.example), run scripts/live_demo.py instead for the real
LLM-orchestrated experience.
"""

from __future__ import annotations

from agents.orchestrator_agent import OfflineRoutingRuntime
from tools.finance_tools import get_budget_summary, get_invoice_status
from tools.hr_tools import get_time_off_balance
from tools.knowledge_tools import search_knowledge_base
from tools.sales_tools import draft_quote, get_lead_status

EXAMPLES: dict[str, tuple[str, object]] = {
    "1": ("Finance — invoice status (INV-1001)", lambda: get_invoice_status("INV-1001")),
    "2": ("Finance — budget summary (Engineering, Q3-2026)", lambda: get_budget_summary("Engineering", "Q3-2026")),
    "3": ("Sales — lead status (LEAD-1001)", lambda: get_lead_status("LEAD-1001")),
    "4": ("Sales — draft quote (CUST-3001, 10% discount)", lambda: draft_quote("CUST-3001", ["PROD-STARTER", "PROD-ANALYTICS"], 10)),
    "5": ("HR — time-off balance (EMP-1001)", lambda: get_time_off_balance("EMP-1001")),
    "6": ("Knowledge — policy search ('remote work policy')", lambda: search_knowledge_base("What is our remote work policy?")),
}


def print_menu() -> None:
    print("\nOffline preview — real tool functions, mock backend data, zero Azure calls.\n")
    for key, (label, _) in EXAMPLES.items():
        print(f"  {key}. {label}")
    print("  r. Try the keyword-based agent router on a free-text question")
    print("  q. Quit")


def main() -> None:
    while True:
        print_menu()
        choice = input("\n> ").strip().lower()
        if choice == "q":
            break
        if choice == "r":
            message = input("Type a question (e.g. 'What is the status of invoice INV-1001?'): ")
            selected = OfflineRoutingRuntime.select_agents(message)
            if not selected:
                print("No agent matched — the real orchestrator would ask a clarifying question here.")
            else:
                for name, reason in selected:
                    print(f"  -> routed to {name} ({reason})")
            continue
        example = EXAMPLES.get(choice)
        if not example:
            print("Unrecognized option.")
            continue
        label, call = example
        try:
            result = call()
            print(f"\n{label}\n{result.model_dump_json(indent=2)}")
        except Exception as error:  # noqa: BLE001 - shown to the person running the demo, not re-raised
            print(f"\n{label} failed: {error}")


if __name__ == "__main__":
    main()
