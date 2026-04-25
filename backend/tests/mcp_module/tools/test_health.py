"""Tests for mcp_module.tools.health module."""

from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from mcp_module.tools.health import (
    get_weight_data,
    get_steps_data,
    get_sleep_data,
    log_weight,
    log_steps,
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


def _make_weight_record(
    record_date=None,
    weight=75.5,
):
    """
    Create a mock weight record.

    Args:
        record_date: Date for the record.
        weight: Weight value.

    Returns:
        MagicMock: A mock weight SQLAlchemy model.
    """
    if record_date is None:
        record_date = date(2026, 4, 20)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.weight = weight
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


def _make_steps_record(
    record_date=None,
    steps=10000,
):
    """
    Create a mock steps record.

    Args:
        record_date: Date for the record.
        steps: Step count value.

    Returns:
        MagicMock: A mock steps SQLAlchemy model.
    """
    if record_date is None:
        record_date = date(2026, 4, 20)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.steps = steps
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
        record_date = date(2026, 4, 20)
    record = MagicMock()
    record.id = 1
    record.user_id = 42
    record.date = record_date
    record.sleep_start_time_gmt = None
    record.sleep_end_time_gmt = None
    record.sleep_start_time_local = None
    record.sleep_end_time_local = None
    record.total_sleep_seconds = 28800
    record.nap_time_seconds = None
    record.unmeasurable_sleep_seconds = None
    record.deep_sleep_seconds = 7200
    record.light_sleep_seconds = 14400
    record.rem_sleep_seconds = 5400
    record.awake_sleep_seconds = 1800
    record.avg_heart_rate = None
    record.min_heart_rate = None
    record.max_heart_rate = None
    record.avg_spo2 = None
    record.lowest_spo2 = None
    record.highest_spo2 = None
    record.avg_respiration = None
    record.lowest_respiration = None
    record.highest_respiration = None
    record.avg_stress_level = None
    record.awake_count = None
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


MODULE = "mcp_module.tools.health"


class TestGetWeightData:
    """Tests for get_weight_data tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_returns_results(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_weight_data returns serialized
        weight records.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_weight_record()
        mock_crud.return_value = [record]

        result = get_weight_data(mock_ctx)

        assert len(result) == 1
        assert result[0]["weight"] == 75.5
        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_returns_empty_when_no_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_weight_data returns empty list
        when no records exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_weight_data(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_filters_by_date_range(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that date range filters exclude records
        outside the range.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        r1 = _make_weight_record(
            record_date=date(2026, 4, 10),
        )
        r2 = _make_weight_record(
            record_date=date(2026, 4, 20),
        )
        r3 = _make_weight_record(
            record_date=date(2026, 4, 30),
        )
        mock_crud.return_value = [r1, r2, r3]

        result = get_weight_data(
            mock_ctx,
            start_date="2026-04-15",
            end_date="2026-04-25",
        )

        assert len(result) == 1
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
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
            get_weight_data(mock_ctx)

        mock_db.close.assert_called_once()


class TestGetStepsData:
    """Tests for get_steps_data tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    def test_returns_results(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_steps_data returns serialized
        step records.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_steps_record()
        mock_crud.return_value = [record]

        result = get_steps_data(mock_ctx)

        assert len(result) == 1
        assert result[0]["steps"] == 10000
        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    def test_returns_empty_when_no_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_steps_data returns empty list
        when no records exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_steps_data(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    def test_filters_by_date_range(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that date range filters exclude records
        outside the range.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        r1 = _make_steps_record(
            record_date=date(2026, 4, 10),
        )
        r2 = _make_steps_record(
            record_date=date(2026, 4, 20),
        )
        mock_crud.return_value = [r1, r2]

        result = get_steps_data(
            mock_ctx,
            start_date="2026-04-15",
            end_date="2026-04-25",
        )

        assert len(result) == 1
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
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
            get_steps_data(mock_ctx)

        mock_db.close.assert_called_once()


class TestGetSleepData:
    """Tests for get_sleep_data tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    def test_returns_results(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_sleep_data returns serialized
        sleep records.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_sleep_record()
        mock_crud.return_value = [record]

        result = get_sleep_data(mock_ctx)

        assert len(result) == 1
        assert result[0]["total_sleep_seconds"] == 28800
        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    def test_returns_empty_when_no_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_sleep_data returns empty list
        when no records exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_sleep_data(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    def test_filters_by_date_range(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that date range filters exclude records
        outside the range.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        r1 = _make_sleep_record(
            record_date=date(2026, 4, 10),
        )
        r2 = _make_sleep_record(
            record_date=date(2026, 4, 20),
        )
        mock_crud.return_value = [r1, r2]

        result = get_sleep_data(
            mock_ctx,
            start_date="2026-04-15",
            end_date="2026-04-25",
        )

        assert len(result) == 1
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
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
            get_sleep_data(mock_ctx)

        mock_db.close.assert_called_once()


class TestLogWeight:
    """Tests for log_weight tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud.create_health_weight"
    )
    def test_creates_weight_entry(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that log_weight creates a weight entry
        via CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_weight_record(
            record_date=date(2026, 4, 25),
            weight=75.5,
        )
        mock_crud.return_value = record

        result = log_weight(
            mock_ctx,
            weight=75.5,
            date_str="2026-04-25",
        )

        assert result["weight"] == 75.5
        mock_crud.assert_called_once()
        args = mock_crud.call_args
        assert args[0][0] == 42
        assert args[0][2] is mock_db
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud.create_health_weight"
    )
    def test_creates_weight_entry_default_date(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that log_weight uses today when no date
        is provided.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_weight_record()
        mock_crud.return_value = record

        result = log_weight(
            mock_ctx,
            weight=80.0,
        )

        assert result is not None
        args = mock_crud.call_args
        create_schema = args[0][1]
        assert create_schema.date is not None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud.create_health_weight"
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
            log_weight(
                mock_ctx,
                weight=75.5,
                date_str="2026-04-25",
            )

        mock_db.close.assert_called_once()


class TestLogSteps:
    """Tests for log_steps tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud.create_health_steps"
    )
    def test_creates_steps_entry(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that log_steps creates a steps entry
        via CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_steps_record(
            record_date=date(2026, 4, 25),
            steps=12000,
        )
        mock_crud.return_value = record

        result = log_steps(
            mock_ctx,
            step_count=12000,
            date_str="2026-04-25",
        )

        assert result["steps"] == 12000
        mock_crud.assert_called_once()
        args = mock_crud.call_args
        assert args[0][0] == 42
        assert args[0][2] is mock_db
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud.create_health_steps"
    )
    def test_creates_steps_entry_default_date(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that log_steps uses today when no date
        is provided.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        record = _make_steps_record()
        mock_crud.return_value = record

        result = log_steps(
            mock_ctx,
            step_count=8000,
        )

        assert result is not None
        args = mock_crud.call_args
        create_schema = args[0][1]
        assert create_schema.date is not None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud.create_health_steps"
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
            log_steps(
                mock_ctx,
                step_count=10000,
                date_str="2026-04-25",
            )

        mock_db.close.assert_called_once()


class TestUserIsolation:
    """Test that health tools respect user isolation."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.weight_crud"
        ".get_all_health_weight_by_user_id"
    )
    def test_weight_uses_correct_user_id(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_weight_data passes the
        authenticated user_id to CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        get_weight_data(mock_ctx)

        mock_crud.assert_called_once_with(42, mock_db)

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.steps_crud"
        ".get_all_health_steps_by_user_id"
    )
    def test_steps_uses_correct_user_id(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_steps_data passes the
        authenticated user_id to CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        get_steps_data(mock_ctx)

        mock_crud.assert_called_once_with(42, mock_db)

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.sleep_crud"
        ".get_all_health_sleep_by_user_id"
    )
    def test_sleep_uses_correct_user_id(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_sleep_data passes the
        authenticated user_id to CRUD.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        get_sleep_data(mock_ctx)

        mock_crud.assert_called_once_with(42, mock_db)
