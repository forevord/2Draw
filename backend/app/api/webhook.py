"""Stripe webhook endpoint.

PS-14: Handles checkout.session.completed events to mark exports as paid.
Idempotent via the unique stripe_session_id constraint on the exports table.
"""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.db.supabase import get_supabase

router = APIRouter(tags=["webhook"])
logger = logging.getLogger(__name__)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request) -> dict[str, str]:
    """Verify and handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        logger.warning("Stripe webhook verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id: str = session["id"]
        customer_email: str = session.get("customer_details", {}).get(
            "email", ""
        )

        client = await get_supabase()
        await (
            client.table("exports")
            .update({"status": "paid", "user_email": customer_email})
            .eq("stripe_session_id", session_id)
            .execute()
        )
        logger.info("Export marked as paid for session %s", session_id)

    return {"status": "ok"}
