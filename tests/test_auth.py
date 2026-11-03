import pytest
import sqlite3
from pathlib import Path
from database.connection import init_db, get_db
from auth.security import hash_password, verify_password, create_session_token, verify_session_token
from auth.service import register_user, authenticate_user, get_user_by_id


@pytest.fixture
def auth_db(tmp_path: Path):
    db_file = tmp_path / "test_auth.db"
    init_db(db_file)
    return db_file


def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_session_tokens():
    user_id = "usr_abc123"
    token = create_session_token(user_id)
    assert isinstance(token, str)
    verified = verify_session_token(token)
    assert verified == user_id

    # Test expired token
    assert verify_session_token(token, max_age=-1) is None
    # Test tampered token
    assert verify_session_token("invalid.token.tampered") is None


def test_register_and_authenticate(auth_db):
    with get_db(auth_db) as conn:
        res = register_user(
            conn,
            email="founder@store.com",
            password="StrongPassword123!",
            display_name="Founder Joe",
            workspace_name="Joe's Premium Goods"
        )
        assert res["email"] == "founder@store.com"
        assert res["workspace"]["name"] == "Joe's Premium Goods"
        assert res["workspace"]["role"] == "owner"

        # Duplicate email registration should fail
        with pytest.raises(ValueError, match="already exists"):
            register_user(
                conn,
                email="founder@store.com",
                password="AnotherPassword123!",
                display_name="Duplicate"
            )

        # Successful authentication
        auth_res = authenticate_user(conn, "founder@store.com", "StrongPassword123!")
        assert auth_res["email"] == "founder@store.com"
        assert len(auth_res["workspaces"]) == 1
        assert auth_res["workspaces"][0]["name"] == "Joe's Premium Goods"

        # Invalid password
        with pytest.raises(ValueError, match="Invalid email or password"):
            authenticate_user(conn, "founder@store.com", "WrongPassword!")

        # Nonexistent user
        with pytest.raises(ValueError, match="Invalid email or password"):
            authenticate_user(conn, "nobody@store.com", "StrongPassword123!")


def test_multi_user_workspace_isolation(auth_db):
    with get_db(auth_db) as conn:
        user_a = register_user(conn, "a@store.com", "PasswordA123!", "Alice", "Alice Store")
        user_b = register_user(conn, "b@store.com", "PasswordB123!", "Bob", "Bob Store")

        ws_a_id = user_a["workspace"]["id"]
        ws_b_id = user_b["workspace"]["id"]
        assert ws_a_id != ws_b_id

        # Verify Alice's memberships do not include Bob's workspace
        alice_data = get_user_by_id(conn, user_a["id"])
        alice_ws_ids = [w["id"] for w in alice_data["workspaces"]]
        assert ws_a_id in alice_ws_ids
        assert ws_b_id not in alice_ws_ids
