"""
Pricing recalculation with overrides support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pricing_agent import PricingAgent
from review.models import GlobalOverrides, LineOverride


def recalculate_pricing_with_overrides(
    technical_output: Dict[str, Any],
    pricing_input: Dict[str, Any],
    scope_of_supply: List[Dict[str, Any]],
    overrides: List[LineOverride],
    global_overrides: GlobalOverrides,
) -> Dict[str, Any]:
    """
    Recalculate pricing with line-level and global overrides.
    
    Args:
        technical_output: Original technical recommendations
        pricing_input: Original pricing input
        scope_of_supply: Scope of supply list
        overrides: List of line overrides
        global_overrides: Global pricing overrides
        
    Returns:
        Pricing output dict with warnings array
    """
    # Build override maps for quick lookup
    override_map: Dict[str, LineOverride] = {o.line_id: o for o in overrides}
    
    # Create modified technical output with overridden SKUs
    modified_technical = {
        "rfp_id": technical_output["rfp_id"],
        "recommendations": [],
    }
    
    warnings: List[str] = []
    
    # Load product prices for validation
    project_root = Path(__file__).resolve().parent.parent
    product_prices_path = project_root / "data" / "pricing" / "product_prices.json"
    with product_prices_path.open("r", encoding="utf-8") as f:
        product_prices_data = json.load(f)
    product_prices = {p["sku"]: float(p["unit_price"]) for p in product_prices_data.get("products", [])}
    
    # Apply line overrides to technical recommendations
    for rec in technical_output["recommendations"]:
        line_id = rec["line_id"]
        override = override_map.get(line_id)
        
        if override and override.approved_sku:
            # Override SKU
            modified_rec = rec.copy()
            modified_rec["best_sku"] = override.approved_sku
            
            # Validate SKU exists in product prices
            if override.approved_sku not in product_prices:
                warnings.append(f"Line {line_id}: SKU {override.approved_sku} not found in product_prices.json")
            
            modified_technical["recommendations"].append(modified_rec)
        else:
            # Keep original
            modified_technical["recommendations"].append(rec)
    
    # Create pricing agent
    agent = PricingAgent()
    
    # Temporarily override product prices for manual unit price overrides
    original_prices = agent.product_prices.copy()
    for override in overrides:
        if override.manual_unit_price is not None and override.approved_sku:
            # Override the price for this SKU
            agent.product_prices[override.approved_sku] = override.manual_unit_price
    
    try:
        # Run pricing agent with modified technical output
        pricing_output = agent.run(
            technical_output=modified_technical,
            pricing_input=pricing_input,
            scope_of_supply=scope_of_supply,
        )
    finally:
        # Restore original prices
        agent.product_prices = original_prices
    
    # Apply global overrides (margin, tax)
    if global_overrides.margin_fraction is not None:
        margin_mult = 1.0 + global_overrides.margin_fraction
        for item in pricing_output["line_items"]:
            item["unit_price"] *= margin_mult
            item["material_total"] = item["unit_price"] * item["quantity"]
        # Recalculate totals
        pricing_output["totals"]["material_total"] = sum(
            item["material_total"] for item in pricing_output["line_items"]
        )
        pricing_output["totals"]["overall_total"] = (
            pricing_output["totals"]["material_total"] + pricing_output["totals"]["tests_total"]
        )
    
    if global_overrides.tax_fraction is not None:
        tax_mult = 1.0 + global_overrides.tax_fraction
        for item in pricing_output["line_items"]:
            item["material_total"] *= tax_mult
        # Recalculate totals
        pricing_output["totals"]["material_total"] = sum(
            item["material_total"] for item in pricing_output["line_items"]
        )
        pricing_output["totals"]["overall_total"] = (
            pricing_output["totals"]["material_total"] + pricing_output["totals"]["tests_total"]
        )
    
    # Apply test exclusions
    if global_overrides.test_exclusions:
        excluded_codes = set(global_overrides.test_exclusions)
        for item in pricing_output["line_items"]:
            # Remove excluded tests from line-level tests
            if "line_level_tests" in item:
                item["line_level_tests"] = [
                    t for t in item["line_level_tests"] if t["code"] not in excluded_codes
                ]
                item["line_level_tests_total"] = sum(t["cost"] for t in item["line_level_tests"])
        
        # Remove excluded tests from global tests
        if "global_tests" in pricing_output:
            pricing_output["global_tests"] = [
                t for t in pricing_output["global_tests"] if t["code"] not in excluded_codes
            ]
        
        # Recalculate test totals
        line_tests_total = sum(
            item.get("line_level_tests_total", 0) for item in pricing_output["line_items"]
        )
        global_tests_total = sum(
            t["cost"] for t in pricing_output.get("global_tests", [])
        )
        pricing_output["totals"]["tests_total"] = line_tests_total + global_tests_total
        pricing_output["totals"]["overall_total"] = (
            pricing_output["totals"]["material_total"] + pricing_output["totals"]["tests_total"]
        )
    
    # Add warnings to output
    pricing_output["warnings"] = warnings
    
    return pricing_output

