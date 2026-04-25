"""Tests for api_keys.models module."""

import api_keys.models as api_keys_models


class TestUserApiKeyModel:
    """Tests for UserApiKey model."""

    def test_table_name(self):
        """Test that table name is correct."""
        assert (
            api_keys_models.UserApiKey.__tablename__
            == "user_api_keys"
        )

    def test_columns_exist(self):
        """Test UserApiKey has all expected columns."""
        assert hasattr(
            api_keys_models.UserApiKey, "id"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "user_id"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "name"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "key_prefix"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "key_hash"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "created_at"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "last_used_at"
        )
        assert hasattr(
            api_keys_models.UserApiKey, "expires_at"
        )

    def test_id_is_primary_key(self):
        """Test id column is primary key."""
        assert (
            api_keys_models.UserApiKey.id.primary_key
        )

    def test_user_id_is_not_nullable(self):
        """Test user_id column is not nullable."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["user_id"]
        )
        assert col.nullable is False

    def test_name_max_length(self):
        """Test name column has max length 100."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["name"]
        )
        assert col.type.length == 100

    def test_key_prefix_max_length(self):
        """Test key_prefix column has max length 8."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["key_prefix"]
        )
        assert col.type.length == 8

    def test_key_hash_max_length(self):
        """Test key_hash column has max length 64."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["key_hash"]
        )
        assert col.type.length == 64

    def test_key_hash_is_unique(self):
        """Test key_hash column is unique."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["key_hash"]
        )
        assert col.unique is True

    def test_last_used_at_is_nullable(self):
        """Test last_used_at column is nullable."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["last_used_at"]
        )
        assert col.nullable is True

    def test_expires_at_is_nullable(self):
        """Test expires_at column is nullable."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["expires_at"]
        )
        assert col.nullable is True

    def test_created_at_is_not_nullable(self):
        """Test created_at column is not nullable."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["created_at"]
        )
        assert col.nullable is False

    def test_has_users_relationship(self):
        """Test UserApiKey has users relationship."""
        assert hasattr(
            api_keys_models.UserApiKey, "users"
        )

    def test_composite_index_exists(self):
        """Test composite index on user_id and name."""
        index_names = [
            idx.name
            for idx in (
                api_keys_models.UserApiKey
                .__table__.indexes
            )
        ]
        assert (
            "idx_user_api_keys_user_id_name"
            in index_names
        )

    def test_user_id_foreign_key(self):
        """Test user_id has foreign key to users.id."""
        col = (
            api_keys_models.UserApiKey.__table__
            .columns["user_id"]
        )
        fk_targets = [
            str(fk.target_fullname)
            for fk in col.foreign_keys
        ]
        assert "users.id" in fk_targets
