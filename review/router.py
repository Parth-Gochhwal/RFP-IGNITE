"""
FastAPI router for review endpoints.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from main import run_full_pipeline
from main_agent import MainAgent
from review.export import generate_export_zip
from review.models import ApprovedReview, GlobalOverrides, LineOverride, ReviewDraft, ReviewSaveRequest
from review.recalculate import recalculate_pricing_with_overrides
from review.store import ReviewStore
from audit_logger import log_event

router = APIRouter(prefix="/api", tags=["review"])

# Initialize store
store = ReviewStore()


@router.get("/rfp/{rfp_id}/draft")
def get_rfp_draft(rfp_id: str) -> Dict[str, Any]:
    """
    Get the last pipeline result and any saved draft overrides.
    Returns: { "pipeline": <full pipeline JSON>, "draft": <review draft or null>, "scope_of_supply": <list> }
    """
    # Run pipeline to get latest result
    try:
        pipeline_result = run_full_pipeline()
        
        # Validate RFP ID matches
        if pipeline_result.get("rfp_id") != rfp_id:
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline returned RFP ID {pipeline_result.get('rfp_id')}, expected {rfp_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run pipeline: {str(e)}")
    
    # Get scope_of_supply from MainAgent
    try:
        main_payload = MainAgent().run()
        technical_input = main_payload.get("technical_input")
        scope_of_supply = technical_input.get("scope_of_supply", []) if technical_input else []
        pricing_input = main_payload.get("pricing_input", {})
    except Exception as e:
        # If MainAgent fails, use empty list
        scope_of_supply = []
        pricing_input = {}
    
    # Load draft if exists
    draft = store.load_draft(rfp_id)
    draft_dict = None
    if draft:
        draft_dict = draft.to_dict()
    
    return {
        "pipeline": pipeline_result,
        "draft": draft_dict,
        "scope_of_supply": scope_of_supply,
        "pricing_input": pricing_input,
    }


@router.post("/rfp/{rfp_id}/review/save")
def save_review_draft(rfp_id: str, request: ReviewSaveRequest) -> Dict[str, Any]:
    """
    Save a reviewer draft (not final).
    Stores to data/reviews/{rfp_id}_draft.json
    """
    if request.rfp_id != rfp_id:
        raise HTTPException(
            status_code=400,
            detail=f"RFP ID mismatch: path {rfp_id} vs body {request.rfp_id}"
        )
    
    # Create draft
    draft = ReviewDraft(
        rfp_id=rfp_id,
        saved_at=datetime.now(),
        saved_by=request.reviewer,
        request=request,
    )
    
    # Save to store
    store.save_draft(rfp_id, draft)
    
    return {
        "success": True,
        "draft": draft.to_dict(),
    }


@router.post("/pricing/recalculate")
def recalculate_pricing(
    technical_output: Dict[str, Any],
    scope_of_supply: List[Dict[str, Any]],
    overrides: List[Dict[str, Any]],
    global_overrides: Dict[str, Any],
    pricing_input: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recalculate pricing with overrides.
    
    Accepts:
    - technical_output: from pipeline
    - scope_of_supply: from technical_input
    - overrides: List[LineOverride dicts]
    - global_overrides: GlobalOverrides dict
    - pricing_input: from pipeline
    
    Returns full pricing JSON with warnings.
    """
    # Parse overrides
    line_overrides = [LineOverride(**o) for o in overrides]
    global_overrides_obj = GlobalOverrides(**global_overrides)
    
    # Recalculate
    try:
        pricing_output = recalculate_pricing_with_overrides(
            technical_output=technical_output,
            pricing_input=pricing_input,
            scope_of_supply=scope_of_supply,
            overrides=line_overrides,
            global_overrides=global_overrides_obj,
        )
        return pricing_output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")


@router.post("/rfp/{rfp_id}/review/approve")
def approve_review(rfp_id: str, request: ReviewSaveRequest) -> Dict[str, Any]:
    """
    Accept the draft as final.
    Validates, saves approved review, generates export ZIP, returns final response.
    """
    if request.rfp_id != rfp_id:
        raise HTTPException(
            status_code=400,
            detail=f"RFP ID mismatch: path {rfp_id} vs body {request.rfp_id}"
        )
    
    # Get pipeline result
    try:
        pipeline_result = run_full_pipeline()
        if pipeline_result.get("rfp_id") != rfp_id:
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline RFP ID mismatch: {pipeline_result.get('rfp_id')} vs {rfp_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline result: {str(e)}")
    
    # Get technical output and scope
    technical_output = pipeline_result["technical_recommendations"]
    main_payload = MainAgent().run()
    technical_input = main_payload.get("technical_input")
    if not technical_input:
        raise HTTPException(status_code=500, detail="Failed to get technical input")
    scope_of_supply = technical_input["scope_of_supply"]
    pricing_input = main_payload.get("pricing_input", {})
    
    # Recalculate with overrides
    line_overrides = request.overrides
    global_overrides_obj = request.global_overrides
    
    try:
        recalculated_pricing = recalculate_pricing_with_overrides(
            technical_output=technical_output,
            pricing_input=pricing_input,
            scope_of_supply=scope_of_supply,
            overrides=line_overrides,
            global_overrides=global_overrides_obj,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")
    
    # Build final response
    final_response = {
        "success": True,
        "rfp_id": rfp_id,
        "buyer": pipeline_result["buyer"],
        "title": pipeline_result["title"],
        "submission_due_date": pipeline_result["submission_due_date"],
        "currency": pipeline_result["currency"],
        "technical_recommendations": technical_output,
        "pricing": recalculated_pricing,
        "approved_by": request.reviewer,
        "approved_at": datetime.now().isoformat(),
        "overrides_applied": {
            "line_overrides": [o.model_dump() for o in line_overrides],
            "global_overrides": global_overrides_obj.model_dump(),
        },
    }
    final_response["pipeline_run_id"] = (
    recalculated_pricing.get("pipeline_run_id")
    or technical_output.get("pipeline_run_id")
    )

    
    # Build audit trail
    draft = store.load_draft(rfp_id)
    audit_trail = []
    if draft:
        audit_trail.append({
            "action": "draft_saved",
            "saved_at": draft.saved_at.isoformat(),
            "saved_by": draft.saved_by,
            "notes": draft.request.notes,
        })
    audit_trail.append({
        "action": "approved",
        "approved_at": datetime.now().isoformat(),
        "approved_by": request.reviewer,
        "notes": request.notes,
    })
    
    # Create approved review
    approved = ApprovedReview(
        rfp_id=rfp_id,
        approved_at=datetime.now(),
        approved_by=request.reviewer,
        final_response=final_response,
        audit_trail=audit_trail,
    )
    
    # Save approved review
    store.save_approved(rfp_id, approved)
    
    # Generate export ZIP
    export_path = store.base_path / f"{rfp_id}_export.zip"
    try:
        generate_export_zip(rfp_id, final_response, export_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate export ZIP: {str(e)}")

    # Audit: approved review
    try:
        log_event("review_approved", {"rfp_id": rfp_id, "approved_by": request.reviewer, "approved_at": datetime.now().isoformat()})
    except Exception:
        pass

    return {
        "success": True,
        "final_response": final_response,
        "export_url": f"/api/rfp/{rfp_id}/export",
        "audit_trail": audit_trail,
    }


@router.get("/rfp/{rfp_id}/export")
def get_export_zip(rfp_id: str) -> FileResponse:
    """
    Return the ZIP file generated by approve.
    """
    export_path = store.base_path / f"{rfp_id}_export.zip"
    if not export_path.exists():
        raise HTTPException(status_code=404, detail="Export ZIP not found. Please approve the review first.")
    
    return FileResponse(
        path=export_path,
        media_type="application/zip",
        filename=f"{rfp_id}_export.zip",
    )

