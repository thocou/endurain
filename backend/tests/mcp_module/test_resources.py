"""Tests for mcp_module.resources module."""

import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from mcp_module.resources import (
    recent_activities,
    health_summary,
    user_profile,
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


def _make_columns(*names):
    """
    Create mock column objects for __table__.columns.

    Args:
        names: Column name strings.

    Returns:
        List of mock column objects.
    """
    cols = []
    for name in names:
        col = MagicMock()
        col.name = name
        cols.append(col)
    return cols


WEIGHT_COLS = _make_columns(
    "id", "user_id", "date", "weight",
    "bmi", "body_fat", "body_water", "bone_mass",
    "muscle_mass", "physique_rating", "visceral_fat",
    "metabolic_age", "source",
)

STEPS_COLS = _make_columns(
    "id", "user_id", "date", "steps", "source",
)

SLEEP_COLS = _make_columns(
    "id", "user_id", "date",
    "sleep_start_time_gmt", "sleep_end_time_gmt",
    "sleep_start_time_local", "sleep_end_time_local",
    "total_sleep_seconds", "nap_time_seconds",
    "unmeasurable_sleep_seconds",
    "deep_sleep_seconds", "light_sleep_seconds",
    "rem_sleep_seconds", "awake_sleep_seconds",
    "avg_heart_rate", "min_heart_rate",
    "max_heart_rate", "avg_spo2", "lowest_spo2",
    "highest_spo2", "avg_respiration",
    "lowest_respiration", "highest_respiration",
    "avg_stress_level", "awake_count",
    "restless_moments_count",
    "sleep_score_overall", "sleep_score_duration",
    "sleep_score_quality",
    "garminconnect_sleep_id", "sleep_stages",
    "source", "hrv_status", "resting_heart_rate",
    "avg_skin_temp_deviation", "awake_count_score",
    "rem_percentage_score", "deep_percentage_score",
    "light_percentage_score", "avg_sleep_stress",
    "sleep_stress_score",
)


MODULE = "mcp_module.resources"


def _make_weight_record(record_date=None):
    """
    Create a mock weight record.

    Args:
        record_date: Date for the record.

    Returns:
        MagicMock: A mock weight SQLAlchemy model.
    """
    if record_date is None:
        record_date = date.today() - timedelta(days=5)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.weight = 75.5
    record.bmi = None
    record.body_fat = None
    record.body_water = None
    record.bone_mass = None
    record.muscle_mass = None
    record.physique_rating = None
    record.visceral_fat = None
    record.metabolic_age = None
    record.source = None
    table = MagicMock()
    type(table).columns = PropertyMock(
        return_value=WEIGHT_COLS
    )
    type(record).__table__ = PropertyMock(
        return_value=table
    )
    return record


def _make_steps_record(record_date=None):
    """
    Create a mock steps record.

    Args:
        record_date: Date for the record.

    Returns:
        MagicMock: A mock steps SQLAlchemy model.
    """
    if record_date is None:
        record_date = date.today() - timedelta(days=5)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.steps = 10000
    record.source = None
    table = MagicMock()
    type(table).columns = PropertyMock(
        return_value=STEPS_COLS
    )
    type(record).__table__ = PropertyMock(
        return_value=table
    )
    return record


def _make_sleep_record(record_date=None):
    """
    Create a mock sleep record.

    Args:
        record_date: Date for the record.

    Returns:
        MagicMock: A mock sleep SQLAlchemy model.
    """
    if record_date is None:
        record_date = date.today() - timedelta(days=5)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.sleep_start_time_gmt = None
    record.sleep_end_time_gmt = None
    record.sleep_start_time_local = None
    record.sleep_end_time_local = None
    record.total_sleep_seconds = 28800
    record.nap_time_seconds = 0
    record.unmeasurable_sleep_seconds = 0
    record.deep_sleep_seconds = 7200
    record.light_sleep_seconds = 14400
    record.rem_sleep_seconds = 7200
    record.awake_sleep_seconds = 0
    record.avg_heart_rate = 55
    record.min_heart_rate = 48
    record.max_heart_rate = 65
    record.avg_spo2 = None
    record.lowest_spo2 = None
    record.highest_spo2 = None
    record.avg_respiration = None
    record.lowest_respiration = None
    record.highest_respiration = None
    record.avg_stress_level = None
    record.awake_count = 2
    record.restless_moments_count = None
    record.sleep_score_overall = None
    record.sleep_score_duration = None
    record.sleep_score_quality = None
    record.garminconnect_sleep_id = None
    record.sleep_stages = None
    record.source = None
    record.hrv_status = None
    record.resting_heart_rate = None
    record.avg_skin_temp_deviation = None
    record.awake_count_score = None
    record.rem_percentage_score = None
    record.deep_percentage_score = None
    record.light_percentage_score = None
    record.avg_sleep_stress = None
    record.sleep_stress_score = None
    table = MagicMock()
    type(table).columns = PropertyMock(
        return_value=SLEEP_COLS
    )
    type(record).__table__ = PropertyMock(
        return_value=table
    )
    return record


class TestRecentActivities:
    """Tests for recent_activities resource."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_returns_recent_activities(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that recent_activities returns last 20
        activities as JSON summary.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        activity = MagicMock()
        activity.model_dump.return_value = {
            "id": 1,
            "name": "Morning Run",
            "activity_type": 1,
            "start_time": "2026-04-20T08:00:00",
            "distance": 5000,
            "elapsed_time": 1800,
        }
        mock_crud.return_value = [activity]

        result = recent_activities(mock_ctx)
        data = json.loads(result)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Morning Run"
        assert data[0]["distance"] == 5000
        mock_crud.assert_called_once_with(
            42, mock_db,
            page_number=1,
            num_records=20,
            user_is_owner=True,
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_returns_empty_when_no_activities(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that recent_activities returns empty
        list when no activities exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = recent_activities(mock_ctx)
        data = json.loads(result)

        assert data == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.activities_crud"
        ".get_user_activities_with_pagination"
    )
    def test_user_isolation(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that recent_activities only fetches
        activities for the authenticated user.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        recent_activities(mock_ctx)

        mock_crud.assert_called_once_with(
            42, mock_db,
            page_number=1,
            num_records=20,
            user_is_owner=True,
        )

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
        an exception occurs.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            recent_activities(mock_ctx)

        mock_db.close.assert_called_once()


class TestHealthSummary:
    """Tests for health_summary resource."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_returns_health_summary(
        self, mock_weight, mock_steps, mock_sleep,
        mock_get_db, mock_ctx,
    ):
        """
        Test that health_summary returns weight,
        steps, and sleep data for last 30 days.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_weight.return_value = [
            _make_weight_record()
        ]
        mock_steps.return_value = [
            _make_steps_record()
        ]
        mock_sleep.return_value = [
            _make_sleep_record()
        ]

        result = health_summary(mock_ctx)
        data = json.loads(result)

        assert "weight" in data
        assert "steps" in data
        assert "sleep" in data
        assert "period" in data
        assert len(data["weight"]) == 1
        assert len(data["steps"]) == 1
        assert len(data["sleep"]) == 1
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_returns_empty_when_no_data(
        self, mock_weight, mock_steps, mock_sleep,
        mock_get_db, mock_ctx,
    ):
        """
        Test that health_summary returns empty lists
        when no health data exists.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_weight.return_value = None
        mock_steps.return_value = None
        mock_sleep.return_value = None

        result = health_summary(mock_ctx)
        data = json.loads(result)

        assert data["weight"] == []
        assert data["steps"] == []
        assert data["sleep"] == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_filters_old_records(
        self, mock_weight, mock_steps, mock_sleep,
        mock_get_db, mock_ctx,
    ):
        """
        Test that records older than 30 days are
        excluded from the summary.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        old_date = date.today() - timedelta(days=60)
        mock_weight.return_value = [
            _make_weight_record(record_date=old_date)
        ]
        mock_steps.return_value = [
            _make_steps_record(record_date=old_date)
        ]
        mock_sleep.return_value = [
            _make_sleep_record(record_date=old_date)
        ]

        result = health_summary(mock_ctx)
        data = json.loads(result)

        assert data["weight"] == []
        assert data["steps"] == []
        assert data["sleep"] == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_user_isolation(
        self, mock_weight, mock_steps, mock_sleep,
        mock_get_db, mock_ctx,
    ):
        """
        Test that health_summary only fetches data
        for the authenticated user.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_weight.return_value = None
        mock_steps.return_value = None
        mock_sleep.return_value = None

        health_summary(mock_ctx)

        mock_weight.assert_called_once_with(42, mock_db)
        mock_steps.assert_called_once_with(42, mock_db)
        mock_sleep.assert_called_once_with(42, mock_db)

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_db_session_closed_on_exception(
        self, mock_weight, mock_steps, mock_sleep,
        mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        an exception occurs.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_weight.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            health_summary(mock_ctx)

        mock_db.close.assert_called_once()


class TestUserProfile:
    """Tests for user_profile resource."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_returns_profile_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that user_profile returns the
        authenticated user's profile as JSON.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        user = MagicMock()
        user.id = 42
        user.name = "Test User"
        user.username = "testuser"
        user.email = "test@example.com"
        user.city = "TestCity"
        user.birthdate = date(1990, 1, 15)
        user.gender = 1
        user.units = "metric"
        user.height = 180
        user.max_heart_rate = 190
        user.preferred_language = "en"
        user.first_day_of_week = 0
        user.currency = "EUR"
        mock_crud.return_value = user

        result = user_profile(mock_ctx)
        data = json.loads(result)

        assert data["id"] == 42
        assert data["name"] == "Test User"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["birthdate"] == "1990-01-15"
        mock_crud.assert_called_once_with(
            42, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_returns_null_when_not_found(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that user_profile returns null JSON
        when user is not found.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = user_profile(mock_ctx)
        data = json.loads(result)

        assert data is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_handles_null_birthdate(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that user_profile handles a null
        birthdate correctly.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        user = MagicMock()
        user.id = 42
        user.name = "Test"
        user.username = "test"
        user.email = "t@t.com"
        user.city = None
        user.birthdate = None
        user.gender = None
        user.units = "metric"
        user.height = None
        user.max_heart_rate = None
        user.preferred_language = "en"
        user.first_day_of_week = 0
        user.currency = None
        mock_crud.return_value = user

        result = user_profile(mock_ctx)
        data = json.loads(result)

        assert data["birthdate"] is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_user_isolation(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that user_profile only fetches profile
        for the authenticated user.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        user_profile(mock_ctx)

        mock_crud.assert_called_once_with(
            42, mock_db
        )

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_db_session_closed_on_exception(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        an exception occurs.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            user_profile(mock_ctx)

        mock_db.close.assert_called_once()
