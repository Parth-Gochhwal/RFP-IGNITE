from __future__ import annotations

from datetime import datetime

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import print
from rich.panel import Panel
from rich.table import Table

from sales_agent import SalesAgent, RFPMetadata

from spec_robustness_engine import run_spec_robustness_checks
from audit_logger import log_event


# ---------- Data models for full RFP ----------

@dataclass
class RFPFull:
    meta: RFPMetadata
    scope_of_supply: List[Dict[str, Any]]
    testing_requirements_summary: List[str]

    @classmethod
    def from_index_record(cls, rec: Dict[str, Any]) -> "RFPFull":
        meta = RFPMetadata.from_dict(rec)
        scope = rec.get("scope_of_supply", [])
        tests = rec.get("testing_requirements_summary", [])
        return cls(meta=meta, scope_of_supply=scope, testing_requirements_summary=tests)


# ---------- Main Agent (orchestrator) ----------

class MainAgent:
    """
    Phase-1 Main Agent:
    - Invokes SalesAgent to select an RFP
    - Loads full RFP details (scope + tests) from rfp_index.json
    - Prepares role-specific summaries:
        * technical_input for Technical Agent
        * pricing_input for Pricing Agent
    - Prints everything nicely and returns a structured payload.
    """

    def __init__(self, rfp_index_path: Optional[Path] = None):
        project_root = Path(__file__).resolve().parent
        self.rfp_index_path = rfp_index_path or (project_root / "data" / "rfp_index.json")
        self._spec_robustness = {}

    def _load_index_raw(self) -> Dict[str, Any]:
        if not self.rfp_index_path.exists():
            raise FileNotFoundError(f"RFP index not found at {self.rfp_index_path}")
        with self.rfp_index_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _find_rfp_record(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        raw = self._load_index_raw()
        for rec in raw.get("rfps", []):
            if rec.get("id") == rfp_id:
                return rec
        return None

    def _build_technical_input(self, rfp: RFPFull) -> Dict[str, Any]:
        """
        What Technical Agent cares about:
        - RFP ID, title, buyer, due date
        - RFP file path (for later PDF parsing)
        - Scope of supply: list of line items
        """
        meta = rfp.meta
        return {
            "rfp_id": meta.id,
            "title": meta.title,
            "buyer": meta.buyer,
            "submission_due_date": meta.submission_due_date.isoformat(),
            "file": meta.file,
            "scope_of_supply": rfp.scope_of_supply,
            "spec_robustness": self._spec_robustness,
            "pipeline_run_id": self.pipeline_run_id
        }


    def _build_pricing_input(self, rfp: RFPFull) -> Dict[str, Any]:
        """
        What Pricing Agent cares about:
        - RFP ID, title, buyer, due date
        - RFP file path (for later reference)
        - Testing and acceptance requirements summary
        """
        meta = rfp.meta
        return {
            "rfp_id": meta.id,
            "title": meta.title,
            "buyer": meta.buyer,
            "submission_due_date": meta.submission_due_date.isoformat(),
            "file": meta.file,
            "testing_requirements": rfp.testing_requirements_summary,
            "spec_robustness": self._spec_robustness,
            "pipeline_run_id": self.pipeline_run_id
        }


    def run(self) -> Dict[str, Any]:
        print(Panel.fit("[bold cyan]Main Agent[/bold cyan]: starting RFP orchestration"))
        from datetime import datetime  # add this import at top if missing

        pipeline_run_id = f"run-{datetime.utcnow().isoformat()}Z"
        self.pipeline_run_id = pipeline_run_id
        print(f"[dim]Pipeline Run ID: {self.pipeline_run_id}[/dim]")


        # 1. Ask Sales Agent to pick an RFP
        sales_agent = SalesAgent()
        sales_payload = sales_agent.run()
        selected_meta_dict = sales_payload.get("selected_rfp")

        if not selected_meta_dict:
            print("[bold red]Main Agent:[/bold red] No RFP selected by Sales Agent. Aborting.")
            try:
                log_event("main_no_selection", {"horizon_days": sales_agent.horizon_days})
            except Exception:
                pass
            return {
                "sales_payload": sales_payload,
                "technical_input": None,
                "pricing_input": None,
            }

        selected_id = selected_meta_dict["id"]
        print(f"\n[bold cyan]Main Agent:[/bold cyan] Fetching full details for selected RFP [bold]{selected_id}[/bold]")
        try:
            log_event(
                "sales_selected_rfp",
                {
                    "selected_rfp": selected_id,
                    "upcoming_count": sales_payload.get("upcoming_count")
                },
            pipeline_run_id=self.pipeline_run_id
        )
        except Exception:
            pass


        # 2. Load full record (includes scope_of_supply & testing_requirements_summary)
        rec = self._find_rfp_record(selected_id)
        if rec is None:
            print(f"[bold red]Main Agent:[/bold red] Selected RFP {selected_id} not found in index!")
            return {
                "sales_payload": sales_payload,
                "technical_input": None,
                "pricing_input": None,
            }

        rfp_full = RFPFull.from_index_record(rec)
        # 2.5 Run Specification Robustness Engine
        robustness_report = run_spec_robustness_checks(
            rfp_id=rfp_full.meta.id,
            parsed_rfp_data={
                "scope_of_supply": rfp_full.scope_of_supply,
                "raw_record": rec
            }
        )
        self._spec_robustness = robustness_report
        try:
            log_event(
                "spec_robustness_run", 
                {
                    "rfp_id": rfp_full.meta.id, 
                    "status": robustness_report.get('robustness_status')
                },
                pipeline_run_id=self.pipeline_run_id
            )
        except Exception:
            pass



        # 3. Build role-specific views
        technical_input = self._build_technical_input(rfp_full)
        pricing_input = self._build_pricing_input(rfp_full)

        try:
            log_event(
                "main_inputs_prepared", 
                {
                    "rfp_id": rfp_full.meta.id, 
                    "technical_input_present": bool(technical_input), 
                    "pricing_input_present": bool(pricing_input)
                },
                pipeline_run_id=self.pipeline_run_id
            )
        except Exception:
            pass

        # 4. Pretty-print for debug / demo
        self._print_overall_summary(rfp_full)
        self._print_scope_table(rfp_full.scope_of_supply)
        self._print_testing_summary(rfp_full.testing_requirements_summary)

        print("\n[bold green]Main Agent:[/bold green] Prepared inputs for Technical and Pricing agents.")

        return {
            "sales_payload": sales_payload,
            "technical_input": technical_input,
            "pricing_input": pricing_input,
        }

    @staticmethod
    def _print_overall_summary(rfp: RFPFull) -> None:
        meta = rfp.meta
        text = (
            f"[bold]RFP ID:[/bold] {meta.id}\n"
            f"[bold]Buyer:[/bold] {meta.buyer}\n"
            f"[bold]Title:[/bold] {meta.title}\n"
            f"[bold]Due Date:[/bold] {meta.submission_due_date.isoformat()}\n"
            f"[bold]File:[/bold] {meta.file}"
        )
        print(Panel.fit(text, title="Selected RFP Summary"))

    @staticmethod
    def _print_scope_table(scope: List[Dict[str, Any]]) -> None:
        table = Table(show_header=True, header_style="bold blue", title="Scope of Supply")
        table.add_column("Line ID", style="cyan", no_wrap=True)
        table.add_column("Description")
        table.add_column("Quantity")
        table.add_column("Unit")
        table.add_column("Category")

        for item in scope:
            table.add_row(
                item.get("line_id", ""),
                item.get("description", ""),
                str(item.get("quantity") or item.get("quantity_m") or ""),
                item.get("unit", ""),
                item.get("category", ""),
            )

        print(table)

    @staticmethod
    def _print_testing_summary(tests: List[str]) -> None:
        if not tests:
            print(Panel.fit("[italic]No testing requirements summary found in index.[/italic]",
                            title="Testing & Acceptance Requirements"))
            return

        text = "\n".join(f"- {t}" for t in tests)
        print(Panel.fit(text, title="Testing & Acceptance Requirements"))


# ---------- Script entrypoint ----------

if __name__ == "__main__":
    agent = MainAgent()
    payload = agent.run()

    print("\n[bold green]Main Agent output payload (for downstream agents):[/bold green]")
    print(payload)
