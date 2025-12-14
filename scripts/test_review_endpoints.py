"""
Test script for review endpoints.
Simple requests-based test that exercises the complete review flow.
"""

import json
import sys
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"


def test_review_flow():
    print("=" * 60)
    print("Testing Review Endpoints")
    print("=" * 60)

    # -------------------------------------------------------------
    # STEP 1 — RUN PIPELINE
    # -------------------------------------------------------------
    print("\n1. Running pipeline...")
    response = requests.post(f"{BASE_URL}/run-rfp-pipeline")
    if response.status_code != 200:
        print("ERROR: Pipeline failed")
        print(response.text)
        return False

    pipeline_result = response.json()
    rfp_id = pipeline_result["rfp_id"]
    print(f"✓ Pipeline completed. RFP ID: {rfp_id}")

    # -------------------------------------------------------------
    # STEP 2 — FETCH DRAFT SNAPSHOT
    # -------------------------------------------------------------
    print(f"\n2. Fetching draft for {rfp_id}...")
    response = requests.get(f"{BASE_URL}/api/rfp/{rfp_id}/draft")
    if response.status_code != 200:
        print("ERROR: Failed to fetch draft")
        print(response.text)
        return False

    draft_data = response.json()
    print(f"✓ Draft fetched. Has draft: {draft_data['draft'] is not None}")

    # -------------------------------------------------------------
    # STEP 3 — FETCH RFP DETAILS (to get scope_of_supply + pricing_input)
    # -------------------------------------------------------------
    print(f"\n3. Fetching RFP details for {rfp_id}...")
    response = requests.get(f"{BASE_URL}/api/rfp/{rfp_id}/details")
    if response.status_code != 200:
        print("ERROR: Failed to fetch RFP details")
        print(response.text)
        return False

    details = response.json()
    scope_of_supply = details["scope_of_supply"]
    pricing_input = details["pricing_input"]
    print("✓ RFP details fetched (scope_of_supply + pricing_input)")

    # -------------------------------------------------------------
    # STEP 4 — CREATE OVERRIDES
    # -------------------------------------------------------------
    print("\n4. Creating sample override...")

    technical = pipeline_result["technical_recommendations"]
    recommendations = technical["recommendations"]

    if not recommendations:
        print("ERROR: No technical recommendations returned")
        return False

    first_line = recommendations[0]
    line_id = first_line["line_id"]

    # Choose a modified SKU (top match)
    if first_line["top_matches"]:
        override_sku = first_line["top_matches"][0]["sku"]
    else:
        override_sku = first_line["best_sku"]

    overrides = [
        {
            "line_id": line_id,
            "approved_sku": override_sku,
            "manual_unit_price": None,
            "override_reason": "Test override – auto selected",
        }
    ]

    global_overrides = {
        "margin_fraction": 0.10,  # 10% margin
        "tax_fraction": None,
        "test_exclusions": None,
    }

    save_request = {
        "rfp_id": rfp_id,
        "overrides": overrides,
        "global_overrides": global_overrides,
        "reviewer": "Test Reviewer",
        "notes": "Draft save test",
    }

    print("✓ Override prepared")

    # -------------------------------------------------------------
    # STEP 5 — SAVE DRAFT
    # -------------------------------------------------------------
    print("\n5. Saving draft...")
    response = requests.post(
        f"{BASE_URL}/api/rfp/{rfp_id}/review/save",
        json=save_request,
    )
    if response.status_code != 200:
        print("ERROR: Failed to save draft")
        print(response.text)
        return False

    print("✓ Draft saved")

    # -------------------------------------------------------------
    # STEP 6 — RECALCULATE PRICING WITH OVERRIDES
    # -------------------------------------------------------------
    print("\n6. Recalculating pricing with overrides...")

    technical_output = pipeline_result["technical_recommendations"]

    recalc_request = {
        "technical_output": technical_output,
        "scope_of_supply": scope_of_supply,
        "overrides": overrides,
        "global_overrides": global_overrides,
        "pricing_input": pricing_input,
    }

    response = requests.post(
        f"{BASE_URL}/api/pricing/recalculate",
        json=recalc_request,
    )
    if response.status_code != 200:
        print("ERROR: Failed to recalc pricing")
        print(response.text)
        return False

    recalc_result = response.json()
    total = recalc_result["totals"]["overall_total"]
    print(f"✓ Recalculated. Total={total:.2f}")

    if recalc_result.get("warnings"):
        print("Warnings:", recalc_result["warnings"])

    # -------------------------------------------------------------
    # STEP 7 — APPROVE FINAL RFP RESPONSE
    # -------------------------------------------------------------
    print("\n7. Approving final RFP response...")

    approve_request = {
        "rfp_id": rfp_id,
        "overrides": overrides,
        "global_overrides": global_overrides,
        "reviewer": "Test Reviewer",
        "notes": "Automated approval",
    }

    response = requests.post(
        f"{BASE_URL}/api/rfp/{rfp_id}/review/approve",
        json=approve_request,
    )
    if response.status_code != 200:
        print("ERROR: Approval failed")
        print(response.text)
        return False

    approve_result = response.json()
    export_url = approve_result["export_url"]
    print(f"✓ Approved. Export URL: {export_url}")

    # -------------------------------------------------------------
    # STEP 8 — DOWNLOAD ZIP EXPORT
    # -------------------------------------------------------------
    print("\n8. Downloading export ZIP...")

    response = requests.get(f"{BASE_URL}{export_url}")
    if response.status_code != 200:
        print("ERROR: Failed to download ZIP")
        print(response.text)
        return False

    zip_path = Path(f"{rfp_id}_test_export.zip")
    with zip_path.open("wb") as f:
        f.write(response.content)

    print(f"✓ ZIP downloaded: {zip_path} ({len(response.content)} bytes)")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_review_flow()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend.")
        sys.exit(1)
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
