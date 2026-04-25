"""Tests for mcp_module.tools.gear module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_module.tools.gear import (
    list_gear,
    get_gear,
    create_gear,
    delete_gear,
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


def _make_gear_schema(
    gear_id=1,
    nickname="My Bike",
    gear_type=1,
    brand="Trek",
    model_name="Domane",
):
    """
    Create a mock gear Pydantic schema object.

    Args:
        gear_id: Gear ID.
        nickname: Gear nickname.
        gear_type: Gear type integer.
        brand: Brand name.
        model_name: Model name.

    Returns:
        MagicMock: A mock gear schema with model_dump.
    """
    schema = MagicMock()
    schema.id = gear_id
    schema.nickname = nickname
    schema.gear_type = gear_type
    schema.brand = brand
    schema.model = model_name
    schema.user_id = 42
    schema.created_at = "2026-04-20"
    schema.active = True
    schema.initial_kms = 0.0
    schema.purchase_value = None
    schema.strava_gear_id = None
    schema.garminconnect_gear_id = None
    schema.model_dump = MagicMock(
        return_value={
            "id": gear_id,
            "nickname": nickname,
            "gear_type": gear_type,
            "brand": brand,
            "model": model_name,
            "user_id": 42,
            "created_at": "2026-04-20",
            "active": True,
            "initial_kms": 0.0,
            "purchase_value": None,
            "strava_gear_id": None,
            "garminconnect_gear_id": None,
        }
    )
    return schema


MODULE = "mcp_module.tools.gear"


class TestListGear:
    """Tests for list_gear tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user")
    @patch(f"{MODULE}.gear_schema.Gear")
    def test_returns_results(
        self, mock_schema_cls, mock_crud,
        mock_get_db, mock_ctx,
    ):
        """
        Test that list_gear returns serialized gear
        items.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        gear_obj = MagicMock()
        mock_crud.return_value = [gear_obj]
        mock_validated = _make_gear_schema()
        mock_schema_cls.model_validate.return_value = (
            mock_validated
        )

        result = list_gear(mock_ctx)

        assert len(result) == 1
        assert result[0]["nickname"] == "My Bike"
        mock_crud.assert_called_once_with(42, mock_db)
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(
        f"{MODULE}.gear_crud.get_gear_by_type_and_user"
    )
    @patch(f"{MODULE}.gear_schema.Gear")
    def test_with_type_filter(
        self, mock_schema_cls, mock_crud,
        mock_get_db, mock_ctx,
    ):
        """
        Test that list_gear passes gear_type filter
        to the correct CRUD function.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        gear_obj = MagicMock()
        mock_crud.return_value = [gear_obj]
        mock_validated = _make_gear_schema(
            gear_type=2, nickname="Running Shoes"
        )
        mock_schema_cls.model_validate.return_value = (
            mock_validated
        )

        result = list_gear(mock_ctx, gear_type=2)

        assert len(result) == 1
        mock_crud.assert_called_once_with(
            2, 42, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user")
    def test_returns_empty(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that list_gear returns empty list when
        no gear exists.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = list_gear(mock_ctx)

        assert result == []
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user")
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
            list_gear(mock_ctx)

        mock_db.close.assert_called_once()


class TestGetGear:
    """Tests for get_gear tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_returns_data(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_gear returns a single gear item.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        gear = _make_gear_schema()
        mock_crud.return_value = gear

        result = get_gear(mock_ctx, gear_id=1)

        assert result["nickname"] == "My Bike"
        mock_crud.assert_called_once_with(
            42, 1, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_not_found(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_gear returns None for
        non-existent gear.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        result = get_gear(mock_ctx, gear_id=999)

        assert result is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_user_isolation(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that get_gear passes the authenticated
        user_id to CRUD for ownership filtering.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.return_value = None

        get_gear(mock_ctx, gear_id=1)

        mock_crud.assert_called_once_with(
            42, 1, mock_db
        )
        mock_db.close.assert_called_once()


class TestCreateGear:
    """Tests for create_gear tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.create_gear")
    def test_success(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that create_gear creates gear via CRUD
        with all fields.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        created = _make_gear_schema()
        mock_crud.return_value = created

        result = create_gear(
            mock_ctx,
            nickname="My Bike",
            gear_type=1,
            brand="Trek",
            model="Domane",
        )

        assert result["nickname"] == "My Bike"
        assert result["gear_type"] == 1
        mock_crud.assert_called_once()
        call_args = mock_crud.call_args
        gear_arg = call_args[0][0]
        assert gear_arg.nickname == "My Bike"
        assert gear_arg.gear_type == 1
        assert gear_arg.brand == "Trek"
        assert call_args[0][1] == 42
        assert call_args[0][2] is mock_db
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.create_gear")
    def test_without_optional_fields(
        self, mock_crud, mock_get_db, mock_ctx,
    ):
        """
        Test that create_gear works without optional
        brand and model fields.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        created = _make_gear_schema(
            brand=None, model_name=None,
        )
        mock_crud.return_value = created

        result = create_gear(
            mock_ctx,
            nickname="My Shoes",
            gear_type=2,
        )

        assert result is not None
        call_args = mock_crud.call_args
        gear_arg = call_args[0][0]
        assert gear_arg.brand is None
        assert gear_arg.model is None
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.create_gear")
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
            create_gear(
                mock_ctx,
                nickname="Fail",
                gear_type=1,
            )

        mock_db.close.assert_called_once()


class TestDeleteGear:
    """Tests for delete_gear tool."""

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.delete_gear")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_success(
        self, mock_get, mock_delete,
        mock_get_db, mock_ctx,
    ):
        """
        Test that delete_gear deletes gear via CRUD
        with correct user_id and gear_id.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = _make_gear_schema()

        result = delete_gear(mock_ctx, gear_id=1)

        assert "deleted successfully" in result
        mock_get.assert_called_once_with(
            42, 1, mock_db
        )
        mock_delete.assert_called_once_with(
            1, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_not_found(
        self, mock_get, mock_get_db, mock_ctx,
    ):
        """
        Test that delete_gear returns error for
        non-existent gear.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = None

        result = delete_gear(mock_ctx, gear_id=999)

        assert "not found" in result
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_user_isolation(
        self, mock_get, mock_get_db, mock_ctx,
    ):
        """
        Test that delete_gear passes user_id for
        ownership verification.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.return_value = None

        delete_gear(mock_ctx, gear_id=1)

        mock_get.assert_called_once_with(
            42, 1, mock_db
        )
        mock_db.close.assert_called_once()

    @patch(f"{MODULE}.get_db")
    @patch(f"{MODULE}.gear_crud.get_gear_user_by_id")
    def test_db_session_closed_on_exception(
        self, mock_get, mock_get_db, mock_ctx,
    ):
        """
        Test that DB session is closed even when
        CRUD raises an exception.
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            delete_gear(mock_ctx, gear_id=1)

        mock_db.close.assert_called_once()
