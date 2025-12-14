from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from rich import print
from rich.table import Table
from rich.panel import Panel
from audit_logger import log_event


# ---------- Utilities for parsing specs from free-form descriptions ----------

RE_CORE_AREA = re.compile(r"(?P<core>\d+)\s*(?:C|Core|core)?\s*[x×]\s*(?P<area>\d+)\s*(?:sqmm|sqmm|mm2|mm²)?", flags=re.IGNORECASE)
RE_AREA_ONLY = re.compile(r"(?P<area>\d+)\s*(?:sqmm|mm2|mm²)", flags=re.IGNORECASE)
RE_CORE_ONLY = re.compile(r"(?P<core>\d+)\s*(?:C|Core|core)", flags=re.IGNORECASE)


def parse_core_and_area(description: str) -> Tuple[Optional[int], Optional[float]]:
    """
    Try to extract core_count (int) and area_sqmm (float) from natural-language line descriptions.
    Examples:
      - "3 Core x 185 sqmm" -> (3, 185.0)
      - "1 Core x 1000 sqmm" -> (1, 1000.0)
      - "3C x 50 sqmm" -> (3, 50.0)
    Returns (core_count or None, area_sqmm or None)
    """
    if not description:
        return None, None

    m = RE_CORE_AREA.search(description)
    if m:
        core = int(m.group("core"))
        area = float(m.group("area"))
        return core, area

    m2 = RE_AREA_ONLY.search(description)
    area = float(m2.group("area")) if m2 else None

    m3 = RE_CORE_ONLY.search(description)
    core = int(m3.group("core")) if m3 else None

    return core, area


def jaccard_similarity(a: str, b: str) -> float:
    """Simple token-set Jaccard similarity between two strings (0..1)."""
    ta = set(re.findall(r"\w+", a.lower()))
    tb = set(re.findall(r"\w+", b.lower()))
    if not ta or not tb:
        return 0.0
    inter = ta.intersection(tb)
    uni = ta.union(tb)
    return len(inter) / len(uni)


# ---------- Technical Agent (improved matching) ----------

class TechnicalAgent:
    """
    Technical Agent (improved):
      - Reads `data/catalog/catalog.json` where each product may include:
          {
            "sku": "...",
            "oem": "...",
            "category": "ht_power_cable",
            "core_count": 3,
            "area_sqmm": 185,
            "description": "3C x 185 sqmm HT cable..."
          }
      - For each RFP line item, parse `core_count` and `area_sqmm` from the description when present,
        and score catalog SKUs by:
          * category match (required)
          * core_count closeness (if both present)
          * area_sqmm closeness (if both present)
          * description similarity (Jaccard)
      - Produces top-3 matches with scores in 0..100 and a chosen best_sku.
    """

    def __init__(self, catalog_path: Path | None = None):
        project_root = Path(__file__).resolve().parent
        self.catalog_path = catalog_path or (project_root / "data" / "catalog" / "catalog.json")

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"catalog.json not found at {self.catalog_path}")
        with self.catalog_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw.get("products", [])

    @staticmethod
    def _score_candidate(
        line_desc: str,
        line_core: Optional[int],
        line_area: Optional[float],
        product: Dict[str, Any],
    ) -> float:
        """
        Compute a composite score (0..100) for how well `product` matches the RFP line.
        Weights (tunable):
          - core match closeness: 30
          - area closeness: 30
          - description similarity: 20
          - category match (binary): 20 (but we filter on category outside this function)
        Missing fields are ignored and weights are scaled.
        """
        # Base components
        weights = {"core": 30.0, "area": 30.0, "desc": 20.0}
        total_weight = 0.0
        score = 0.0

        # core_count closeness -> normalized 0..1 by exp decay on absolute difference
        prod_core = product.get("core_count")
        if line_core is not None and prod_core is not None:
            total_weight += weights["core"]
            diff = abs(line_core - prod_core)
            # Map diff to similarity: 1.0 if exact, 0.5 if diff==1, 0.2 if diff==2, etc.
            core_sim = math.exp(-0.8 * diff)
            score += core_sim * weights["core"]

        # area_sqmm closeness -> normalized similarity
        prod_area = product.get("area_sqmm")
        if line_area is not None and prod_area is not None and prod_area > 0:
            total_weight += weights["area"]
            # relative difference
            rel_err = abs(line_area - prod_area) / max(line_area, prod_area)
            area_sim = math.exp(-3.0 * rel_err)  # sharper falloff
            score += area_sim * weights["area"]

        # description similarity (Jaccard)
        prod_desc = product.get("description", "") or product.get("title", "")
        if prod_desc:
            total_weight += weights["desc"]
            desc_sim = jaccard_similarity(line_desc or "", prod_desc)
            score += desc_sim * weights["desc"]

        # If no components matched, return 0 (will be handled by caller)
        if total_weight <= 0:
            return 0.0

        # Normalize to 0..100
        normalized = (score / total_weight) * 100.0
        return round(normalized, 2)

    def run(self, technical_input: Dict[str, Any]) -> Dict[str, Any]:
        print(Panel.fit("[bold cyan]Technical Agent[/bold cyan]: Matching RFP scope with OEM catalog (improved)"))

        rfp_id = technical_input["rfp_id"]
        scope = technical_input["scope_of_supply"]

        catalog = self._load_catalog()

        results = []
        # Pre-group catalog by category for efficient filtering
        catalog_by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for p in catalog:
            cat = p.get("category", "unknown")
            catalog_by_cat.setdefault(cat, []).append(p)

        for line in scope:
            line_id = line.get("line_id")
            desc = line.get("description", "") or ""
            category = line.get("category")
            # Parse core and area from description
            line_core, line_area = parse_core_and_area(desc)

            # Candidate list: filter by category first (strict), else fall back to whole catalog
            candidates = catalog_by_cat.get(category, [])
            if not candidates:
                # fallback to all products (low-quality match)
                candidates = catalog

            scored_candidates: List[Tuple[Dict[str, Any], float]] = []
            for prod in candidates:
                # fallback: ensure category matches strongly, otherwise deprioritize (but don't drop)
                prod_cat = prod.get("category")
                if prod_cat != category:
                    # small penalty if category mismatches
                    cat_penalty = 0.5
                else:
                    cat_penalty = 1.0

                raw_score = self._score_candidate(desc, line_core, line_area, prod)
                final_score = raw_score * cat_penalty
                scored_candidates.append((prod, final_score))

            # Sort by score desc, pick top 3
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            top = scored_candidates[:3]

            top_matches = []
            for prod, score in top:
                top_matches.append({
                    "sku": prod.get("sku"),
                    "oem": prod.get("oem"),
                    "score": float(round(score, 2)),
                    "core_count": prod.get("core_count"),
                    "area_sqmm": prod.get("area_sqmm"),
                })

            best_sku = top_matches[0]["sku"] if top_matches else None

            results.append({
                "line_id": line_id,
                "description": desc,
                "category": category,
                "requested_core_count": line_core,
                "requested_area_sqmm": line_area,
                "top_matches": top_matches,
                "best_sku": best_sku
            })

        self._print_results(results)

        result = {
            "rfp_id": rfp_id,
            "recommendations": results
        }
        try:
            log_event("technical_recommendations", {"rfp_id": rfp_id, "recommendation_count": len(results)})
        except Exception:
            pass
        return result
        

    @staticmethod
    def _print_results(results: List[Dict[str, Any]]) -> None:
        print("\n[bold magenta]Technical Agent Recommendations Table[/bold magenta]")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Line ID", style="cyan", no_wrap=True)
        table.add_column("Category")
        table.add_column("Best SKU")
        table.add_column("Match Breakdown (Top 3)")

        for row in results:
            formatted = ", ".join(f"{m['sku']} ({m['score']}%)" for m in row["top_matches"])
            table.add_row(
                row["line_id"],
                row["category"] or "-",
                row["best_sku"] or "-",
                formatted
            )

        print(table)


# Script demo entrypoint — optional for testing
if __name__ == "__main__":
    from main_agent import MainAgent  # import dynamically to test full chain

    main_payload = MainAgent().run()
    tech_input = main_payload["technical_input"]
    agent = TechnicalAgent()
    output = agent.run(tech_input)

    print("\n[bold green]Technical Agent output payload:[/bold green]")
    print(output)
