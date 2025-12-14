from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup


@dataclass
class HtmlRfpRecord:
    id: str
    title: str
    buyer: str
    due_date: date
    file: str  # relative link to PDF


def parse_html_file(path: Path) -> List[HtmlRfpRecord]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    records: List[HtmlRfpRecord] = []

    for row in soup.select("table#rfp-list tbody tr"):
        id_cell = row.select_one(".rfp-id")
        title_cell = row.select_one(".rfp-title")
        buyer_cell = row.select_one(".rfp-buyer")
        due_cell = row.select_one(".rfp-due")
        link_cell = row.select_one(".rfp-link a")

        if not (id_cell and title_cell and buyer_cell and due_cell and link_cell):
            continue

        rfp_id = id_cell.get_text(strip=True)
        title = title_cell.get_text(strip=True)
        buyer = buyer_cell.get_text(strip=True)
        due_str = due_cell.get_text(strip=True)
        href = link_cell.get("href", "").strip()
        while href.startswith("../"):
            href = href[3:]

        # Parse ISO date yyyy-mm-dd
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()

        records.append(
            HtmlRfpRecord(
                id=rfp_id,
                title=title,
                buyer=buyer,
                due_date=due_date,
                file=href,
            )
        )

    return records


def scan_mock_rfp_sites(project_root: Path | None = None) -> List[HtmlRfpRecord]:
    """
    Scan all mock HTML tender portals under mock_sites/ and return a flat list
    of HtmlRfpRecord objects.
    """
    root = project_root or Path(__file__).resolve().parent
    mock_dir = root / "mock_sites"

    html_files = [
        p for p in mock_dir.glob("*.html") if p.is_file()
    ]

    all_records: List[HtmlRfpRecord] = []
    for f in html_files:
        all_records.extend(parse_html_file(f))

    return all_records
