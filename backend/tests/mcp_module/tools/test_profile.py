"""Tests for mcp_module.tools.profile module."""

from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from mcp_module.tools.profile import (
    get_profile,
    get_goals,
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


def _make_user(
    user_id=42,
    name="Test User",
    username="testuser",
    email="test@example.com",
    city="Madrid",
    birthdate=None,
    gender="male",
    units="metric",
    height=180,
    max_heart_rate=190,
    preferred_language="us",
    first_day_of_week="monday",
    currency="euro",
):
    """
    Create a mock user object.

    Args:
        user_id: User ID.
        name: User full name.
        username: Username.
        email: Email address.
        city: City.
        birthdate: Birthdate.
        gender: Gender.
        units: Units preference.
        height: Height in cm.
        max_heart_rate: Max heart rate.
        preferred_language: Language code.
        first_day_of_week: First day of week.
        currency: Currency.

    Returns:
        MagicMock: A mock user object.
    """
    user = MagicMock()
    user.id = user_id
    user.name = name
    user.username = username
    user.email = email
    user.city = city
    user.birthdate = birthdate
    user.gender = gender
    user.units = units
    user.height = height
    user.max_heart_rate = max_heart_rate
    user.preferred_language = preferred_language
    user.first_day_of_week = first_day_of_week
    user.currency = currency
    return user


def _make_goal_model(
    goal_id=1,
    user_id=42,
    interval="weekly",
    activity_type="run",
    goal_type="distance",
    goal_distance=50000,
):
    """
    Create a mock goal ORM model.

    Args:
        goal_id: Goal ID.
        user_id: User ID.
        interval: Goal interval.
        activity_type: Activity type.
        goal_type: Goal type.
        goal_distance: Distance target.

    Returns:
        MagicMock: A mock goal model.
    """
    goal = MagicMock()
    goal.id = goal_id
    goal.user_id = user_id
    goal.interval = interval
    goal.activity_type = activity_type
    goal.goal_type = goal_type
    goal.goal_calories = None
    goal.goal_activities_number = None
    goal.goal_distance = goal_distance
    goal.goal_elevation = None
    goal.goal_duration = None
    return goal


MODULE = "mcp_module.tools.profile"


class TestGetProfile:
    """Tests for get_profile tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_returns_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_profile returns user profile
        data.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        user = _make_user()
        mock_crud.return_value = user

        result = get_profile(mock_ctx)

        assert result["id"] == 42
        assert result["name"] == "Test User"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["city"] == "Madrid"
        assert result["gender"] == "male"
        assert result["units"] == "metric"
        assert result["height"] == 180
        assert result["max_heart_rate"] == 190
        assert result["preferred_language"] == "us"
        assert result["first_day_of_week"] == "monday"
        assert result["currency"] == "euro"
        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_returns_none_when_not_found(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_profile returns None when user
        is not found.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_profile(mock_ctx)

        assert result is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_birthdate_serialization(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that birthdate is serialized to ISO
        format string.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        user = _make_user(
            birthdate=date(1990, 5, 15),
        )
        mock_crud.return_value = user

        result = get_profile(mock_ctx)

        assert result["birthdate"] == "1990-05-15"
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_birthdate_none(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that None birthdate is preserved.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        user = _make_user(birthdate=None)
        mock_crud.return_value = user

        result = get_profile(mock_ctx)

        assert result["birthdate"] is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
    def test_user_isolation(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_profile uses the authenticated
        user_id from context.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = _make_user()

        get_profile(mock_ctx)

        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.users_crud.get_user_by_id")
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

        with pytest.raises(
            Exception, match="DB error"
        ):
            get_profile(mock_ctx)

        mock_db.close.assert_called_once()


class TestGetGoals:
    """Tests for get_goals tool."""

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.goals_crud"
        ".get_user_goals_by_user_id"
    )
    @patch(f"{MODULE}.goals_schema.UsersGoalRead")
    def test_returns_data(
        self, mock_schema_cls, mock_crud,
        mock_get_db, mock_ctx,
    ):
        """
        Test that get_goals returns serialized goal
        list.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        goal_obj = _make_goal_model()
        mock_crud.return_value = [goal_obj]
        mock_validated = MagicMock()
        mock_validated.model_dump.return_value = {
            "id": 1,
            "user_id": 42,
            "interval": "weekly",
            "activity_type": "run",
            "goal_type": "distance",
            "goal_distance": 50000,
            "goal_calories": None,
            "goal_activities_number": None,
            "goal_elevation": None,
            "goal_duration": None,
        }
        mock_schema_cls.model_validate.return_value = (
            mock_validated
        )

        result = get_goals(mock_ctx)

        assert len(result) == 1
        assert result[0]["goal_type"] == "distance"
        assert result[0]["goal_distance"] == 50000
        mock_crud.assert_called_once_with(
            42, mock_db,
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.goals_crud"
        ".get_user_goals_by_user_id"
    )
    def test_returns_empty(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_goals returns empty list when
        no goals exist.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_goals(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.goals_crud"
        ".get_user_goals_by_user_id"
    )
    def test_user_isolation(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_goals uses the authenticated
        user_id from context.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = []

        get_goals(mock_ctx)

        mock_crud.assert_called_once_with(
            42, mock_db,
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.goals_crud"
        ".get_user_goals_by_user_id"
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

        with pytest.raises(
            Exception, match="DB error"
        ):
            get_goals(mock_ctx)

        mock_db.close.assert_called_once()
