from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_supabase_returns_singleton() -> None:
    """get_supabase() should return the same instance on repeated calls."""
    mock_client = AsyncMock()

    with patch(
        "app.db.supabase.acreate_client", return_value=mock_client
    ) as mock_create:
        import app.db.supabase as db_module
        from app.db.supabase import get_supabase

        # Reset singleton for test isolation
        db_module._client = None

        client1 = await get_supabase()
        client2 = await get_supabase()

        assert client1 is client2
        mock_create.assert_called_once()  # Only created once — singleton verified
