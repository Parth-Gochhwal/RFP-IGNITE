from __future__ import annotations

import json
from rich import print

from main_agent import MainAgent
from technical_agent import TechnicalAgent
from pricing_agent import PricingAgent


def run_full_pipeline() -> dict:
    """
    Runs the complete Phase-1 pipeline:
        Sales Agent → Main Agent → Technical Agent → Pricing Agent
    Returns a consolidated JSON-serializable dict.
    """

    # 1. Main Agent invokes Sales Agent internally
    main_payload = MainAgent().run()

    technical_input = main_payload["technical_input"]
    pricing_input = main_payload["pricing_input"]

    if technical_input is None or pricing_input is None:
        print("[bold red]Pipeline aborted: No RFP selected by Sales Agent.[/bold red]")
        return {"success": False, "message": "No RFP selected"}

    # 2. Technical Agent: SKU matching
    tech_output = TechnicalAgent().run(technical_input)

    # 3. Pricing Agent: compute totals
    scope_of_supply = technical_input["scope_of_supply"]
    pricing_output = PricingAgent().run(
        technical_output=tech_output,
        pricing_input=pricing_input,
        scope_of_supply=scope_of_supply,
    )

    # 4. Build final JSON result
    final_result = {
        "success": True,
        "rfp_id": technical_input["rfp_id"],
        "buyer": technical_input["buyer"],
        "title": technical_input["title"],
        "submission_due_date": technical_input["submission_due_date"],
        "currency": pricing_input.get("currency", "INR"),
        "technical_recommendations": tech_output,
        "pricing": pricing_output,
    }

    return final_result


if __name__ == "__main__":
    print("[bold cyan]Running full Phase-1 RFP pipeline...[/bold cyan]\n")
    result = run_full_pipeline()

    print("\n[bold green]=== FINAL CONSOLIDATED JSON OUTPUT ===[/bold green]")
    print(json.dumps(result, indent=4))
