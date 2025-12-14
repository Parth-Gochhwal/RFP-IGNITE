from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich import print
from rich.table import Table
from rich.panel import Panel
from audit_logger import log_event


class PricingAgent:
    """
    Pricing Agent (improved):

    - Reads product_prices.json and test_prices.json
    - Computes material totals per line as before.
    - Detects tests but applies them intelligently:
        * per_rfp_tests -> applied once for the whole RFP
        * per_category_tests -> applied once per category present in scope
        * per_line_tests -> applied per line (routine, per drum, etc.)
    - Returns:
        - line_items (each with material and per-line tests)
        - global_tests: list of tests applied once (with code, description, cost, reason)
        - totals: material_total + tests_total + overall_total
    """

    # Map test codes to application frequency:
    # - "per_rfp": apply once for the whole RFP
    # - "per_category": apply once per category present in scope
    # - "per_line": keep as applied per line (legacy behavior)
    TEST_FREQUENCY = {
        "HT_TYPE_TEST_SUITE": "per_category",
        "CC_TYPE_TEST_SUITE": "per_category",
        "HT_ACCEPTANCE_TEST_SUITE": "per_rfp",
        "CC_ACCEPTANCE_TEST_SUITE": "per_rfp",
        "ROUTINE_TEST_PER_DRUM": "per_line",
        "SITE_PRE_DELIVERY_INSPECTION": "per_rfp",
        "CAT6_CERTIFICATION_TEST": "per_category",
        "PTFE_WIRE_QUALIFICATION_TEST": "per_category",
    }

    def __init__(
        self,
        product_prices_path: Optional[Path] = None,
        test_prices_path: Optional[Path] = None,
    ):
        project_root = Path(__file__).resolve().parent
        self.product_prices_path = product_prices_path or (
            project_root / "data" / "pricing" / "product_prices.json"
        )
        self.test_prices_path = test_prices_path or (
            project_root / "data" / "pricing" / "test_prices.json"
        )

        self.product_prices = self._load_product_prices()
        self.test_prices = self._load_test_prices()

    def _load_product_prices(self) -> Dict[str, float]:
        if not self.product_prices_path.exists():
            raise FileNotFoundError(f"product_prices.json not found at {self.product_prices_path}")
        with self.product_prices_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        prices = {}
        for p in raw.get("products", []):
            prices[p["sku"]] = float(p["unit_price"])
        return prices

    def _load_test_prices(self) -> Dict[str, Dict[str, Any]]:
        if not self.test_prices_path.exists():
            raise FileNotFoundError(f"test_prices.json not found at {self.test_prices_path}")
        with self.test_prices_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        tests_by_code = {}
        for t in raw.get("tests", []):
            tests_by_code[t["code"]] = t
        return tests_by_code

    # ---------- Utilities ----------

    def _lookup_quantity_unit_category(
        self,
        line_id: str,
        scope_of_supply: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        for item in scope_of_supply:
            if item.get("line_id") == line_id:
                qty = item.get("quantity")
                if qty is None:
                    qty = item.get("quantity_m")
                return {
                    "quantity": float(qty) if qty is not None else 0.0,
                    "unit": item.get("unit", ""),
                    "category": item.get("category", ""),
                }
        return {"quantity": 0.0, "unit": "", "category": ""}

    def _detect_tests_for_line(
        self,
        category: str,
        testing_requirements: List[str],
    ) -> List[str]:
        """
        Very simple rule-based detection of which tests apply for a given line,
        based on category + text in testing_requirements.
        Returns a list of test codes that might be relevant.
        """
        text = " ".join(testing_requirements).lower()
        codes: List[str] = []

        def add_if_present(code: str):
            if code not in codes and code in self.test_prices:
                codes.append(code)

        # Detect type tests
        if "type test" in text or "type tests" in text:
            if category in ("control_cable", "multi_pair_cable"):
                add_if_present("CC_TYPE_TEST_SUITE")
            elif category == "ht_power_cable":
                add_if_present("HT_TYPE_TEST_SUITE")

        # Acceptance tests
        if "acceptance test" in text or "acceptance tests" in text:
            if category in ("control_cable", "multi_pair_cable"):
                add_if_present("CC_ACCEPTANCE_TEST_SUITE")
            elif category == "ht_power_cable":
                add_if_present("HT_ACCEPTANCE_TEST_SUITE")

        # Routine tests
        if "routine test" in text or "routine tests" in text:
            add_if_present("ROUTINE_TEST_PER_DRUM")

        # Pre-delivery / inspection
        if (
            "pre-delivery inspection" in text
            or "pre delivery inspection" in text
            or "inspection at vendor works" in text
            or "third party inspection" in text
        ):
            add_if_present("SITE_PRE_DELIVERY_INSPECTION")

        # Category-specific tests
        if category == "cat6_stp":
            add_if_present("CAT6_CERTIFICATION_TEST")

        if "ptfe" in text or category == "ptfe_wire":
            add_if_present("PTFE_WIRE_QUALIFICATION_TEST")

        return codes

    def _cost_for_test(self, code: str) -> float:
        test = self.test_prices.get(code)
        if not test:
            return 0.0
        # Preference: price_per_batch, price_per_category, price_per_rfp, price_per_drum, price_per_visit
        for key in ("price_per_rfp", "price_per_category", "price_per_batch", "price_per_drum", "price_per_visit"):
            if key in test:
                return float(test[key])
        return 0.0

    # ---------- Main run ----------

    def run(
        self,
        technical_output: Dict[str, Any],
        pricing_input: Dict[str, Any],
        scope_of_supply: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        print(Panel.fit("[bold cyan]Pricing Agent[/bold cyan]: Calculating prices for recommended SKUs (improved)"))

        rfp_id = pricing_input["rfp_id"]
        testing_requirements = pricing_input.get("testing_requirements", [])

        # Collect categories present and the mapping from line->category
        category_to_lines: Dict[str, List[str]] = {}
        line_category_map: Dict[str, str] = {}
        for item in scope_of_supply:
            lid = item.get("line_id")
            cat = item.get("category", "")
            line_category_map[lid] = cat
            category_to_lines.setdefault(cat, []).append(lid)

        # First pass: compute per-line material totals and gather per-line detected tests
        line_items_priced = []
        total_material = 0.0
        per_line_tests_accum: Dict[str, List[str]] = {}  # line_id -> test codes
        for rec in technical_output["recommendations"]:
            line_id = rec["line_id"]
            best_sku = rec.get("best_sku")
            desc = rec.get("description")
            category = rec.get("category") or line_category_map.get(line_id, "")

            qty_info = self._lookup_quantity_unit_category(line_id, scope_of_supply)
            quantity = qty_info["quantity"]
            unit = qty_info["unit"]

            unit_price = self.product_prices.get(best_sku, 0.0)
            material_total = unit_price * quantity
            total_material += material_total

            # detect line-level tests (this list may include both per_line and higher freq tests;
            # we will aggregate frequencies later)
            detected = self._detect_tests_for_line(category, testing_requirements)
            per_line_tests_accum[line_id] = detected

            # For now, only attach per-line routine tests in the line item (others handled globally)
            routine_tests = []
            routine_total = 0.0
            for code in detected:
                freq = self.TEST_FREQUENCY.get(code, "per_line")
                if freq == "per_line":
                    price = self._cost_for_test(code)
                    routine_tests.append({
                        "code": code,
                        "description": self.test_prices[code]["description"],
                        "cost": price
                    })
                    routine_total += price

            line_items_priced.append({
                "line_id": line_id,
                "description": desc,
                "category": category,
                "best_sku": best_sku,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "material_total": material_total,
                "line_level_tests": routine_tests,
                "line_level_tests_total": routine_total,
                # global tests will be attached later
            })

        # Second pass: compute global tests (per_rfp and per_category)
        global_tests: List[Dict[str, Any]] = []
        applied_tests: Set[str] = set()
        global_tests_total = 0.0

        # Per-RFP tests: detect across full testing_requirements text
        for code, freq in self.TEST_FREQUENCY.items():
            if freq == "per_rfp":
                # If any line detected this code (or text contains it), apply once
                # Use detection heuristics: check if any detected lists contain it
                # Simpler: check if the test code is likely relevant based on testing_requirements text
                if code in ("HT_ACCEPTANCE_TEST_SUITE", "CC_ACCEPTANCE_TEST_SUITE", "SITE_PRE_DELIVERY_INSPECTION"):
                    # Determine presence heuristically
                    if any(code in self._detect_tests_for_line(line_category_map[lid], testing_requirements) for lid in line_category_map):
                        price = self._cost_for_test(code)
                        if code not in applied_tests and price > 0:
                            global_tests.append({
                                "code": code,
                                "description": self.test_prices[code]["description"],
                                "cost": price,
                                "applied_for": "per_rfp"
                            })
                            global_tests_total += price
                            applied_tests.add(code)

        # Per-category tests: apply once per distinct category present
        for category, lines in category_to_lines.items():
            for lid in lines:
                detected = per_line_tests_accum.get(lid, [])
                for code in detected:
                    freq = self.TEST_FREQUENCY.get(code, "per_line")
                    if freq == "per_category":
                        # apply once for this category if not already applied
                        # e.g., HT_TYPE_TEST_SUITE
                        key = f"{code}::category::{category}"
                        if key in applied_tests:
                            continue
                        price = self._cost_for_test(code)
                        if price > 0:
                            global_tests.append({
                                "code": code,
                                "description": self.test_prices[code]["description"],
                                "cost": price,
                                "applied_for": f"per_category:{category}"
                            })
                            global_tests_total += price
                            applied_tests.add(key)

        # Third pass: attach global tests info to output but not duplicate them to every line.
        # Totals aggregation:
        total_tests = global_tests_total
        # Add per-line test totals
        for itm in line_items_priced:
            total_tests += itm["line_level_tests_total"]

        overall = {
            "material_total": total_material,
            "tests_total": total_tests,
            "overall_total": total_material + total_tests,
        }

        self._print_summary(line_items_priced, global_tests, overall)

        result = {
            "rfp_id": rfp_id,
            "line_items": line_items_priced,
            "global_tests": global_tests,
            "totals": overall,
        }
        try:
            log_event("pricing_completed", {"rfp_id": rfp_id, "material_total": overall.get('material_total'), "overall_total": overall.get('overall_total')})
        except Exception:
            pass
        return result

    # ---------- Pretty print ----------

    @staticmethod
    def _print_summary(line_items: List[Dict[str, Any]], global_tests: List[Dict[str, Any]], totals: Dict[str, float]) -> None:
        print("\n[bold magenta]Pricing Summary per Line Item[/bold magenta]")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Line ID", style="cyan", no_wrap=True)
        table.add_column("Best SKU")
        table.add_column("Qty")
        table.add_column("Unit")
        table.add_column("Unit Price")
        table.add_column("Material Total")
        table.add_column("Line Test Cost")
        table.add_column("Grand Total (w/o global tests)")

        for item in line_items:
            grand = item["material_total"] + item["line_level_tests_total"]
            table.add_row(
                item["line_id"],
                item["best_sku"] or "-",
                f"{item['quantity']}",
                item["unit"],
                f"{item['unit_price']:.2f}",
                f"{item['material_total']:.2f}",
                f"{item['line_level_tests_total']:.2f}",
                f"{grand:.2f}",
            )

        print(table)

        if global_tests:
            gtext = "\n".join(f"- {t['code']}: {t['description']} = {t['cost']:.2f} (applied_for={t['applied_for']})" for t in global_tests)
            print(Panel.fit(gtext, title="Global / Category / RFP-level Tests"))

        totals_text = (
            f"[bold]Total Material:[/bold] {totals['material_total']:.2f}\n"
            f"[bold]Total Tests/Services:[/bold] {totals['tests_total']:.2f}\n"
            f"[bold]Overall Total:[/bold] {totals['overall_total']:.2f}"
        )
        print(Panel.fit(totals_text, title="Overall Pricing Totals"))


# -------- Script demo entrypoint: run full chain --------

if __name__ == "__main__":
    from main_agent import MainAgent
    from technical_agent import TechnicalAgent

    # 1. Main Agent: Sales + context
    main_payload = MainAgent().run()

    technical_input = main_payload["technical_input"]
    pricing_input = main_payload["pricing_input"]

    # 2. Technical Agent: SKU recommendations
    tech_output = TechnicalAgent().run(technical_input)

    # 3. Pricing Agent: pricing using technical_output + scope + testing info
    scope_of_supply = technical_input["scope_of_supply"]

    agent = PricingAgent()
    pricing_output = agent.run(
        technical_output=tech_output,
        pricing_input=pricing_input,
        scope_of_supply=scope_of_supply,
    )

    print("\n[bold green]Pricing Agent output payload:[/bold green]")
    print(pricing_output)
