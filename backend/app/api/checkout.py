"""Stripe Checkout endpoint.

PS-14: Creates a Stripe Checkout session for purchasing a paint guide PDF.
"""

from __future__ import annotations

from typing import Any, cast

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.db.supabase import get_supabase

router = APIRouter(tags=["checkout"])

_PRICE_CENTS = 299  # $2.99
_CURRENCY = "usd"
_PRODUCT_NAME = "2Draw Paint Guide"


class CheckoutRequest(BaseModel):
    job_id: str


class CheckoutResponse(BaseModel):
    session_url: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest) -> CheckoutResponse:
    """Create a Stripe Checkout session for the given job."""
    client = await get_supabase()

    # Verify job exists and is complete
    job_result = await (
        client.table("jobs")
        .select("id, status, settings")
        .eq("id", req.job_id)
        .execute()
    )
    rows = cast(list[dict[str, Any]], job_result.data)
    if not rows:
        raise HTTPException(status_code=404, detail="Job not found")

    job = rows[0]
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail="Job is not complete yet")

    job_settings: dict[str, Any] = job.get("settings") or {}
    pdf_url = job_settings.get("pdf_url")

    # Create exports row
    export_result = await (
        client.table("exports")
        .insert(
            {
                "status": "pending",
                "pdf_url": pdf_url,
                "job_id": req.job_id,
            }
        )
        .execute()
    )
    export_rows = cast(list[dict[str, Any]], export_result.data)
    export_id = str(export_rows[0]["id"])

    # Create Stripe Checkout session
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "unit_amount": _PRICE_CENTS,
                    "currency": _CURRENCY,
                    "product_data": {"name": _PRODUCT_NAME},
                },
                "quantity": 1,
            }
        ],
        success_url=(
            f"{settings.frontend_url}/preview/{req.job_id}"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=f"{settings.frontend_url}/preview/{req.job_id}",
        metadata={"export_id": export_id, "job_id": req.job_id},
    )

    # Store stripe session ID on export
    await (
        client.table("exports")
        .update({"stripe_session_id": session.id})
        .eq("id", export_id)
        .execute()
    )

    return CheckoutResponse(session_url=session.url or "")
