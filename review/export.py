"""
Export functionality for approved reviews (ZIP generation).
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def generate_export_zip(
    rfp_id: str,
    final_response: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Generate export ZIP file containing:
    - final_response.json
    - pricing.csv (line-wise)
    - technical.csv (line-wise matches)
    - summary.txt (one-page summary)
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. final_response.json
        import json
        json_str = json.dumps(final_response, indent=2, ensure_ascii=False)
        zipf.writestr("final_response.json", json_str.encode("utf-8"))
        
        # 1.5 audit_trail.json (append-only audit log snapshot)
        audit_path = Path(__file__).resolve().parent.parent / "data" / "audit_log.json"
        if audit_path.exists():
            audit_raw = audit_path.read_text(encoding="utf-8")
            zipf.writestr("audit_trail.json", audit_raw.encode("utf-8"))
        else:
            # still include file for determinism
            zipf.writestr(
                "audit_trail.json",
                b"[]"
            )

        
        # 2. pricing.csv
        pricing = final_response.get("pricing", {})
        line_items = pricing.get("line_items", [])
        pricing_csv = io.StringIO()
        writer = csv.writer(pricing_csv)
        writer.writerow([
            "Line ID", "Description", "Category", "Best SKU", "Quantity", "Unit",
            "Unit Price", "Material Total", "Line Tests Total", "Grand Total"
        ])
        for item in line_items:
            writer.writerow([
                item.get("line_id", ""),
                item.get("description", ""),
                item.get("category", ""),
                item.get("best_sku", ""),
                item.get("quantity", 0),
                item.get("unit", ""),
                item.get("unit_price", 0),
                item.get("material_total", 0),
                item.get("line_level_tests_total", 0),
                item.get("material_total", 0) + item.get("line_level_tests_total", 0),
            ])
        totals = pricing.get("totals", {})
        writer.writerow([])
        writer.writerow(["TOTALS", "", "", "", "", "", "", totals.get("material_total", 0), totals.get("tests_total", 0), totals.get("overall_total", 0)])
        zipf.writestr("pricing.csv", pricing_csv.getvalue().encode("utf-8"))
        
        # 3. technical.csv
        technical = final_response.get("technical_recommendations", {})
        recommendations = technical.get("recommendations", [])
        technical_csv = io.StringIO()
        writer = csv.writer(technical_csv)
        writer.writerow([
            "Line ID", "Description", "Category", "Best SKU", "Top Match 1", "Score 1",
            "Top Match 2", "Score 2", "Top Match 3", "Score 3"
        ])
        for rec in recommendations:
            matches = rec.get("top_matches", [])
            row = [
                rec.get("line_id", ""),
                rec.get("description", ""),
                rec.get("category", ""),
                rec.get("best_sku", ""),
            ]
            for i in range(3):
                if i < len(matches):
                    row.extend([matches[i].get("sku", ""), matches[i].get("score", 0)])
                else:
                    row.extend(["", ""])
            writer.writerow(row)
        zipf.writestr("technical.csv", technical_csv.getvalue().encode("utf-8"))
        
        # 4. summary.txt (executive-grade plain text)
        def _fmt_money(val: Any) -> str:
            try:
                return f"{float(val):,.2f} {final_response.get('currency', 'N/A')}"
            except Exception:
                return f"{val} {final_response.get('currency', 'N/A')}"

        def _scope_overview(resp: Dict[str, Any]) -> List[str]:
            buyer = resp.get('buyer', 'N/A')
            title = resp.get('title', 'N/A')
            due = resp.get('submission_due_date', 'N/A')
            lines = [
                "Scope Overview:",
                f"  Buyer: {buyer}",
                f"  Title: {title}",
                f"  Submission Due Date: {due}",
            ]
            # include deterministic counts
            pricing_items = resp.get('pricing', {}).get('line_items', [])
            lines.append(f"  Line Items (count): {len(pricing_items)}")
            return lines

        def _spec_quality_assessment(resp: Dict[str, Any]) -> List[str]:
            # Pull spec robustness info if present
            sr = resp.get('spec_robustness') or resp.get('spec_quality') or {}
            status = sr.get('robustness_status', 'UNKNOWN')
            missing = sr.get('missing_fields', {})
            fw = sr.get('fallback_applied', [])
            uw = sr.get('unit_warnings', [])
            lines = [
                "Specification Quality Assessment:",
                f"  Overall Status: {status}",
            ]
            # deterministic presentation of missing fields
            if missing:
                for idx in sorted(missing.keys(), key=lambda x: int(x) if isinstance(x, int) or (isinstance(x, str) and x.isdigit()) else str(x)):
                    lines.append(f"  Line {idx}: missing -> {', '.join(sorted(missing[idx]))}")
            else:
                lines.append("  Missing Fields: None")
            if fw:
                lines.append(f"  Fallbacks Applied: {len(fw)} (see logs)")
            else:
                lines.append("  Fallbacks Applied: 0")
            if uw:
                lines.append(f"  Unit Warnings: {len(uw)}")
            else:
                lines.append("  Unit Warnings: 0")
            return lines

        def _key_assumptions(resp: Dict[str, Any]) -> List[str]:
            assumptions = resp.get('assumptions') or resp.get('key_assumptions') or []
            lines = ["Key Assumptions:"]
            if assumptions:
                for a in assumptions:
                    lines.append(f"  - {a}")
            else:
                # deterministic defaults from pricing/technical
                currency = resp.get('currency', 'N/A')
                lines.append(f"  - Prices quoted in {currency}")
                lines.append("  - Delivery and testing per buyer spec unless noted")
            return lines

        def _technical_recommendation_summary(resp: Dict[str, Any]) -> List[str]:
            tech_in = resp.get('technical_input') or resp.get('technical_recommendations') or {}
            recs = []
            # if structure matches earlier export usage
            if isinstance(tech_in, dict):
                recs = tech_in.get('recommendations') or tech_in.get('top_recommendations') or []
            elif isinstance(tech_in, list):
                recs = tech_in
            lines = ["Technical Recommendation Summary:"]
            if recs:
                for r in recs[:5]:
                    lid = r.get('line_id', r.get('line_item_id', 'N/A'))
                    desc = r.get('description', '')
                    best = r.get('best_sku', r.get('sku', 'N/A'))
                    lines.append(f"  Line {lid}: {desc[:80]}")
                    lines.append(f"    Recommendation: {best}")
            else:
                lines.append("  No technical recommendations available")
            return lines

        def _risk_and_clarifications(resp: Dict[str, Any]) -> List[str]:
            risks = resp.get('risks') or []
            clar = resp.get('clarifications') or resp.get('clarification_questions') or []
            lines = ["Risk & Clarifications:"]
            if risks:
                for r in risks:
                    lines.append(f"  - {r}")
            else:
                lines.append("  - No explicit risks flagged")
            if clar:
                for c in clar:
                    lines.append(f"  Clarification: {c}")
            else:
                lines.append("  Clarifications: None")
            return lines

        def _audit_reference(rfp_id: str, resp: Dict[str, Any]) -> List[str]:
            # include deterministic audit references: counts and keys
            totals = resp.get('pricing', {}).get('totals', {})
            technical = resp.get('technical_recommendations', {})
            sr = resp.get('spec_robustness') or {}
            lines = ["Audit Reference:", f"  RFP ID: {rfp_id}", f"  Generated: {datetime.utcnow().isoformat()}Z"]
            lines.append(f"  Pricing Totals: material={totals.get('material_total',0)}, tests={totals.get('tests_total',0)}, overall={totals.get('overall_total',0)}")
            lines.append(f"  Technical Recommendations: {len(technical.get('recommendations', []) if isinstance(technical, dict) else (len(technical) if isinstance(technical, list) else 0))}")
            lines.append(f"  Spec Robustness Status: {sr.get('robustness_status', 'N/A')}")
            return lines

        def _audit_processing_history(rfp_id: str) -> List[str]:
            """Produce a concise, deterministic timeline of key audit events for this RFP.

            Does not dump the full log; references `data/audit_log.json` for traceability.
            """
            audit_lines = ["Audit & Processing History:"]
            audit_path = Path(__file__).resolve().parent.parent / 'data' / 'audit_log.json'
            try:
                if not audit_path.exists():
                    audit_lines.append(f"  No audit log found. Full log path: {audit_path}")
                    return audit_lines

                raw = audit_path.read_text(encoding='utf-8')
                entries = json.loads(raw or '[]')
                current_run_id = final_response.get("pipeline_run_id")
                # filter relevant events for this rfp_id
                relevant = []
                for e in entries:
                    try:
                        payload = e.get('payload', {}) if isinstance(e, dict) else {}
                        # match if payload contains rfp_id in any known keys
                        if not isinstance(payload, dict):
                            continue
                        if (
                            current_run_id
                            and e.get("pipeline_run_id") == current_run_id
                        ):
                            relevant.append(e)
                        continue
                        # earlier sales event may include selected_rfp
                        if payload.get('selected_rfp') == rfp_id or payload.get('selected_rfp') == str(rfp_id):
                            relevant.append(e)
                            continue
                        # review_approved may have rfp_id top-level in payload
                        if payload.get('approved_rfp') == rfp_id:
                            relevant.append(e)
                            continue
                        # some events embed selected_rfp id under other keys
                        # fallback: stringify payload and check containment
                        try:
                            if isinstance(payload, dict) and any(str(v) == str(rfp_id) for v in payload.values()):
                                relevant.append(e)
                        except Exception:
                            pass
                    except Exception:
                        continue

                # deterministic ordering by timestamp asc
                def _ts_key(ev: dict):
                    t = ev.get('timestamp') if isinstance(ev, dict) else None
                    return t or ''

                relevant_sorted = sorted(relevant, key=_ts_key)

                # Map event_type to concise message
                for ev in relevant_sorted:
                    et = ev.get('event_type', 'unknown')
                    ts = ev.get('timestamp', '')
                    payload = ev.get('payload', {}) or {}
                    if et == 'sales_selected_rfp':
                        audit_lines.append(f"  {ts}: RFP selected by Sales Agent (id={payload.get('selected_rfp')})")
                    elif et == 'spec_robustness_summary':
                        audit_lines.append(f"  {ts}: Spec robustness run (status={payload.get('status')})")
                    elif et == 'main_inputs_prepared':
                        audit_lines.append(f"  {ts}: Main Agent prepared technical/pricing inputs")
                    elif et == 'technical_recommendations':
                        audit_lines.append(f"  {ts}: Technical recommendations generated ({payload.get('recommendation_count', 0)} lines)")
                    elif et == 'pricing_completed':
                        audit_lines.append(f"  {ts}: Pricing completed (overall_total={payload.get('overall_total')})")
                    elif et == 'review_approved':
                        audit_lines.append(f"  {ts}: Review approved by {payload.get('approved_by')}")
                    else:
                        # generic but concise
                        audit_lines.append(f"  {ts}: {et} - {', '.join(f'{k}={v}' for k,v in sorted(payload.items()))}")

                if not relevant_sorted:
                    audit_lines.append(f"  No audit events found for RFP {rfp_id}. Full log path: {audit_path}")
                else:
                    audit_lines.append(f"  Full audit log: {audit_path}")
                return audit_lines
            except Exception:
                audit_lines.append(f"  Failed to read audit log. Full log path: {audit_path}")
                return audit_lines

        # assemble summary deterministically
        summary_sections: List[str] = []
        summary_sections.append(f"RFP Response Summary - {rfp_id}")
        summary_sections.append("=" * 72)
        summary_sections.append("")
        summary_sections.extend(_scope_overview(final_response))
        summary_sections.append("")
        summary_sections.extend(_spec_quality_assessment(final_response))
        summary_sections.append("")
        summary_sections.extend(_key_assumptions(final_response))
        summary_sections.append("")
        summary_sections.extend(_technical_recommendation_summary(final_response))
        summary_sections.append("")
        summary_sections.extend(_risk_and_clarifications(final_response))
        summary_sections.append("")
        summary_sections.extend(_audit_reference(rfp_id, final_response))
        summary_sections.append("")
        # Pricing snapshot (deterministic ordering)
        summary_sections.append("Pricing Snapshot:")
        summary_sections.append(f"  Material Total: {_fmt_money(totals.get('material_total', 0))}")
        summary_sections.append(f"  Tests/Services Total: {_fmt_money(totals.get('tests_total', 0))}")
        summary_sections.append(f"  Overall Total: {_fmt_money(totals.get('overall_total', 0))}")
        summary_sections.append("")
        summary_sections.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        summary_text = "\n".join(summary_sections)
        zipf.writestr("summary.txt", summary_text.encode("utf-8"))

