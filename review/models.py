"""
Pydantic models for review payloads and saved review documents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LineOverride(BaseModel):
    """Override for a single line item."""
    line_id: str
    approved_sku: Optional[str] = None
    manual_unit_price: Optional[float] = Field(None, ge=0)
    override_reason: Optional[str] = None


class GlobalOverrides(BaseModel):
    """Global pricing overrides (margin, tax, test exclusions)."""
    margin_fraction: Optional[float] = Field(None, ge=0, le=1, description="Margin as fraction (0.1 = 10%)")
    tax_fraction: Optional[float] = Field(None, ge=0, le=1, description="Tax as fraction (0.18 = 18%)")
    test_exclusions: Optional[List[str]] = Field(None, description="List of test codes to exclude")


class ReviewSaveRequest(BaseModel):
    """Request body for saving a review draft."""
    rfp_id: str
    overrides: List[LineOverride]
    global_overrides: GlobalOverrides
    reviewer: str = Field(..., min_length=1, description="Reviewer name (required)")
    notes: Optional[str] = None


class ReviewDraft(BaseModel):
    """Saved review draft document."""
    rfp_id: str
    saved_at: datetime
    saved_by: str
    request: ReviewSaveRequest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "rfp_id": self.rfp_id,
            "saved_at": self.saved_at.isoformat(),
            "saved_by": self.saved_by,
            "request": self.request.model_dump(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReviewDraft":
        """Create from dict."""
        saved_at = d["saved_at"]
        if isinstance(saved_at, str):
            saved_at = datetime.fromisoformat(saved_at)
        return cls(
            rfp_id=d["rfp_id"],
            saved_at=saved_at,
            saved_by=d["saved_by"],
            request=ReviewSaveRequest(**d["request"]),
        )


class ApprovedReview(BaseModel):
    """Final approved review document with audit trail."""
    rfp_id: str
    approved_at: datetime
    approved_by: str
    final_response: Dict[str, Any]  # Full pipeline result with overrides applied
    audit_trail: List[Dict[str, Any]]  # History of drafts leading to approval

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "rfp_id": self.rfp_id,
            "approved_at": self.approved_at.isoformat(),
            "approved_by": self.approved_by,
            "final_response": self.final_response,
            "audit_trail": self.audit_trail,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ApprovedReview":
        """Create from dict."""
        approved_at = d["approved_at"]
        if isinstance(approved_at, str):
            approved_at = datetime.fromisoformat(approved_at)
        return cls(
            rfp_id=d["rfp_id"],
            approved_at=approved_at,
            approved_by=d["approved_by"],
            final_response=d["final_response"],
            audit_trail=d["audit_trail"],
        )

