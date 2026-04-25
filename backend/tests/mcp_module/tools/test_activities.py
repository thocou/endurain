"""Tests for mcp_module.tools.activities module."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from mcp_module.tools.activities import (
    list_activities,
    get_activity,
    get_activity_laps,
    get_activity_streams,
    delete_activity,
)


@pytest.fixture
def mock_ctx():
    """
    Create a mock MCP context with user_id=42.

    Returns:
        MagicMock: A mock context object.
    """
    ctx = MagicMock()
    ctx.request_context.access_token.client_id = "42"
    return ctx


@pytest.fixture
def mock_activity():
    """
    Create a mock activity with model_dump support.

    Returns:
        MagicMock: A mock activity Pydantic model.
    """
    activity = MagicMock()
    activity.model_dump.return_value = {
        "id": 1,
        "name": "Morning Run",
        "activity_type": 1,
        "distance": 5000,
        "user_id": 42,
    }
    activity.user_id = 42
    return activity


@pytest.fixture
def mock_lap():
    """
    Create a mock activity lap.

    Returns:
        MagicMock: A mock lap Pydantic model.
    """
    lap = MagicMock()
    lap.model_dump.return_value = {
        "id": 1,
        "activity_id": 1,
        "total_distance": 1000.0,
        "total_elapsed_time": 300.0,
    }
    return lap


@pytest.fixture
def mock_stream():
    """
    Create a mock activity stream.

    Returns:
        MagicMock: A mock stream Pydantic model.
    """
    stream = MagicMock()
    stream.model_dump.return_value = {
        "id": 1,
        "activity_id": 1,
        "stream_type": 1,
        "stream_waypoints": [{"lat": 0, "lon": 0}],
    }
    return stream


MODULE = "mcp_module.tools.activities"


class TestListActivities:
    """Tests for list_activities tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_returns_serialized_list(
        self, mock_crud, mock_get_db, mock_ctx,
        mock_activity,
    ):
        """
        Test that list_activities returns a list
        of activity dicts.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = [mock_activity]

        result = list_activities(mock_ctx)

        assert len(result) == 1
        assert result[0]["name"] == "Morning Run"
        mock_crud.assert_called_once_with(
            42,
            mock_db,
            page_number=1,
            num_records=10,
            activity_type=None,
            start_date=None,
            end_date=None,
            user_is_owner=True,
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_returns_empty_list_when_none(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that list_activities returns empty
        list when CRUD returns None.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = list_activities(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_passes_filters_to_crud(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that date and type filters are parsed
        and passed correctly to CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        list_activities(
            mock_ctx,
            start_date="2026-01-01",
            end_date="2026-01-31",
            activity_type=1,
            page_number=2,
            num_records=5,
        )

        mock_crud.assert_called_once_with(
            42,
            mock_db,
            page_number=2,
            num_records=5,
            activity_type=1,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            user_is_owner=True,
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_db_session_closed_on_exception(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        CRUD raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            list_activities(mock_ctx)

        mock_db.close.assert_called_once()


class TestGetActivity:
    """Tests for get_activity tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_returns_activity_dict(
        self, mock_crud, mock_get_db, mock_ctx,
        mock_activity,
    ):
        """
        Test that get_activity returns a serialized
        activity dictionary.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = mock_activity

        result = get_activity(mock_ctx, activity_id=1)

        assert result["id"] == 1
        assert result["name"] == "Morning Run"
        mock_crud.assert_called_once_with(
            1, 42, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_returns_none_when_not_found(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_activity returns None when
        activity is not found.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_activity(mock_ctx, activity_id=999)

        assert result is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_db_session_closed_on_exception(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        CRUD raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            get_activity(mock_ctx, activity_id=1)

        mock_db.close.assert_called_once()


class TestGetActivityLaps:
    """Tests for get_activity_laps tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.laps_crud"
        ".get_activity_laps"
    )
    def test_returns_laps_list(
        self, mock_crud, mock_get_db, mock_ctx,
        mock_lap,
    ):
        """
        Test that get_activity_laps returns a list
        of lap dictionaries.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = [mock_lap]

        result = get_activity_laps(
            mock_ctx, activity_id=1
        )

        assert len(result) == 1
        assert result[0]["total_distance"] == 1000.0
        mock_crud.assert_called_once_with(
            1, 42, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.laps_crud"
        ".get_activity_laps"
    )
    def test_returns_empty_list_when_none(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_activity_laps(
            mock_ctx, activity_id=1
        )

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.laps_crud"
        ".get_activity_laps"
    )
    def test_db_session_closed_on_exception(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        CRUD raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            get_activity_laps(
                mock_ctx, activity_id=1
            )

        mock_db.close.assert_called_once()


class TestGetActivityStreams:
    """Tests for get_activity_streams tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.streams_crud"
        ".get_activity_streams"
    )
    def test_returns_streams_list(
        self, mock_crud, mock_get_db, mock_ctx,
        mock_stream,
    ):
        """
        Test that get_activity_streams returns a list
        of stream dictionaries.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = [mock_stream]

        result = get_activity_streams(
            mock_ctx, activity_id=1
        )

        assert len(result) == 1
        assert result[0]["stream_type"] == 1
        mock_crud.assert_called_once_with(
            1, 42, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.streams_crud"
        ".get_activity_streams"
    )
    def test_returns_empty_list_when_none(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_activity_streams returns empty
        list when no streams exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_activity_streams(
            mock_ctx, activity_id=1
        )

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.streams_crud"
        ".get_activity_streams"
    )
    def test_db_session_closed_on_exception(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        CRUD raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            get_activity_streams(
                mock_ctx, activity_id=1
            )

        mock_db.close.assert_called_once()


class TestDeleteActivity:
    """Tests for delete_activity tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.activities_crud.delete_activity")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_deletes_owned_activity(
        self, mock_get, mock_delete, mock_get_db,
        mock_ctx, mock_activity,
    ):
        """
        Test that delete_activity verifies ownership
        then deletes the activity.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = mock_activity

        result = delete_activity(
            mock_ctx, activity_id=1
        )

        assert "deleted successfully" in result
        mock_get.assert_called_once_with(
            1, 42, mock_db
        )
        mock_delete.assert_called_once_with(
            1, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.activities_crud.delete_activity")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_returns_not_found_for_missing(
        self, mock_get, mock_delete, mock_get_db,
        mock_ctx,
    ):
        """
        Test that delete_activity returns not found
        message when activity doesn't exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = None

        result = delete_activity(
            mock_ctx, activity_id=999
        )

        assert "not found" in result
        mock_delete.assert_not_called()
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.activities_crud.delete_activity")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_db_session_closed_on_exception(
        self, mock_get, mock_delete, mock_get_db,
        mock_ctx, mock_activity,
    ):
        """
        Test that DB session is closed even when
        delete raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = mock_activity
        mock_delete.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            delete_activity(mock_ctx, activity_id=1)

        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_activity_by_id_from_user_id"
    )
    def test_user_isolation(
        self, mock_get, mock_get_db, mock_ctx,
    ):
        """
        Test that delete_activity passes the
        authenticated user_id for ownership check.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = None

        delete_activity(mock_ctx, activity_id=5)

        mock_get.assert_called_once_with(
            5, 42, mock_db
        )
        mock_db.close.assert_called_once()
