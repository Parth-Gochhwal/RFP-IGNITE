from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import print
from rich.table import Table

from html_rfp_scraper import scan_mock_rfp_sites, HtmlRfpRecord
from audit_logger import log_event


# ---------- Data model ----------

@dataclass
class RFPMetadata:
    id: str
    title: str
    buyer: str
    submission_due_date: date
    file: str
    currency: str = "INR"

    @classmethod
    def from_html(cls, rec: HtmlRfpRecord) -> "RFPMetadata":
        return cls(
            id=rec.id,
            title=rec.title,
            buyer=rec.buyer,
            submission_due_date=rec.due_date,
            file=rec.file,
            currency="INR",
        )
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RFPMetadata":
        """
        Used by MainAgent to load metadata from rfp_index.json.
        """
        due_str = d.get("submission_due_date")
        due = datetime.strptime(due_str, "%Y-%m-%d").date()
        return cls(
            id=d["id"],
            title=d.get("title", ""),
            buyer=d.get("buyer", ""),
            submission_due_date=due,
            file=d["file"],
            currency=d.get("currency", "INR"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "buyer": self.buyer,
            "submission_due_date": self.submission_due_date.isoformat(),
            "file": self.file,
            "currency": self.currency,
        }


# ---------- Sales Agent ----------

class SalesAgent:
    """
    Phase-4 Sales Agent:
    - Scans mock HTML tender portals under mock_sites/
    - Builds an in-memory list of RFPMetadata
    - Filters RFPs due within horizon_days
    - Selects 1 RFP (earliest due date)
    """

    def __init__(self, horizon_days: int = 90):
        self.horizon_days = horizon_days
        self.project_root = Path(__file__).resolve().parent

    def _load_rfps_from_html(self) -> List[RFPMetadata]:
        html_records = scan_mock_rfp_sites(self.project_root)
        rfps = [RFPMetadata.from_html(r) for r in html_records]
        return rfps

    def _filter_upcoming(self, rfps: List[RFPMetadata]) -> List[RFPMetadata]:
        today = date.today()
        cutoff = today + timedelta(days=self.horizon_days)
        return [r for r in rfps if today <= r.submission_due_date <= cutoff]

    def _select_rfp(self, rfps: List[RFPMetadata]) -> Optional[RFPMetadata]:
        if not rfps:
            return None
        return sorted(rfps, key=lambda r: r.submission_due_date)[0]

    def run(self) -> Dict[str, Any]:
        print("[bold cyan]Sales Agent:[/bold cyan] scanning mock HTML tender portals...")

        all_rfps = self._load_rfps_from_html()
        print(f"[green]Found {len(all_rfps)} RFP(s) across mock sites.[/green]")

        upcoming = self._filter_upcoming(all_rfps)
        print(f"[yellow]{len(upcoming)} RFP(s)[/yellow] due within next {self.horizon_days} days.\n")

        if upcoming:
            self._print_rfp_table(upcoming)

        selected = self._select_rfp(upcoming)

        if not selected:
            print("[bold red]No RFPs found within the selected horizon.[/bold red]")
            # Audit: no RFP selected
            try:
                log_event("sales_no_rfp", {"horizon_days": self.horizon_days, "found": len(upcoming)})
            except Exception:
                pass
            return {
                "selected_rfp": None,
                "all_upcoming_rfps": [r.to_dict() for r in upcoming],
            }

        print("\n[bold magenta]Selected RFP for response:[/bold magenta]")
        self._print_rfp_table([selected])

        # Audit: selected RFP
        try:
            log_event("sales_selected_rfp", {"selected_rfp": selected.id, "upcoming_count": len(upcoming)})
        except Exception:
            pass

        return {
            "selected_rfp": selected.to_dict(),
            "all_upcoming_rfps": [r.to_dict() for r in upcoming],
        }

    @staticmethod
    def _print_rfp_table(rfps: List[RFPMetadata]) -> None:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Buyer")
        table.add_column("Title")
        table.add_column("Due Date")
        table.add_column("PDF Path", overflow="fold")

        for r in rfps:
            table.add_row(
                r.id,
                r.buyer,
                r.title,
                r.submission_due_date.isoformat(),
                r.file,
            )

        print(table)


if __name__ == "__main__":
    agent = SalesAgent(horizon_days=90)
    result = agent.run()

    print("\n[bold green]Sales Agent output payload:[/bold green]")
    print(result)
