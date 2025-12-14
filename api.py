from __future__ import annotations

import json
from pathlib import Path
from fastapi.responses import FileResponse

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from main import run_full_pipeline
from review import router as review_router

# Create FastAPI app
app = FastAPI(
    title="RFP Ignite API",
    description="Phase 2 API for RFP processing pipeline",
    version="2.0.0",
)

# CORS settings for frontend (localhost dev)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # allow POST, OPTIONS, etc.
    allow_headers=["*"],
)

# Include review router
app.include_router(review_router.router)

@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    Returns a simple status message.
    """
    return {"status": "ok"}


@app.post("/run-rfp-pipeline")
def run_rfp_pipeline() -> Dict[str, Any]:
    """
    Runs the full Phase-1 RFP pipeline:
        Sales Agent → Main Agent → Technical Agent → Pricing Agent
    
    Returns the complete pipeline result as JSON.
    On failure, returns a 400 error with a helpful message.
    """
    try:
        result = run_full_pipeline()
        
        # Check if pipeline failed
        if not result.get("success", False):
            error_message = result.get("message", "Pipeline execution failed")
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
        
        # Return successful result
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like our 400 above)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/rfp/{rfp_id}/details")
def get_rfp_details(rfp_id: str):
    """
    Return canonical RFP details read from data/rfp_index.json.
    This does not depend on MainAgent internals to avoid fragile coupling.
    Response:
      {
        "rfp_id": "...",
        "scope_of_supply": [...],
        "pricing_input": {...},            # minimal structure used by recalc
        "testing_requirements": [...],
        "currency": "INR",
        "metadata": {...}                  # other rfp fields for convenience
      }
    """
    try:
        base = Path(__file__).resolve().parent
        index_path = base / "data" / "rfp_index.json"
        if not index_path.exists():
            raise HTTPException(status_code=500, detail=f"rfp_index.json not found at {index_path}")

        with index_path.open("r", encoding="utf-8") as f:
            idx = json.load(f)

        # idx expected shape: {"rfps": [ {...}, {...} ]}
        rfps = idx.get("rfps", [])
        match = None
        for r in rfps:
            if r.get("id") == rfp_id:
                match = r
                break

        if match is None:
            raise HTTPException(status_code=404, detail="RFP not found")

        # Create a minimal pricing_input structure used by recalc endpoint
        pricing_input = {
            "rfp_id": match.get("id"),
            "currency": match.get("currency", "INR"),
            # include any additional small metadata that pricing might want
            "testing_requirements_summary": match.get("testing_requirements_summary", []),
        }

        response = {
            "rfp_id": match.get("id"),
            "scope_of_supply": match.get("scope_of_supply", []),
            "pricing_input": pricing_input,
            "testing_requirements": match.get("testing_requirements_summary", []),
            "currency": match.get("currency", "INR"),
            "metadata": {
                "title": match.get("title"),
                "buyer": match.get("buyer"),
                "submission_due_date": match.get("submission_due_date"),
                "file": match.get("file"),
            }
        }
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run development server
    uvicorn.run(app, host="0.0.0.0", port=8000)