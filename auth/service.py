"""
Authentication service layer: User registration, credentials verification,
and automatic workspace provisioning.
"""

import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from auth.security import hash_password, verify_password


def register_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    display_name: str,
    workspace_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registers a new user, hashes password, and creates a default personal workspace.
    Raises ValueError on invalid input or existing email.
    """
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("A valid email address is required.")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    
    clean_name = display_name.strip()
    if not clean_name:
        clean_name = normalized_email.split("@")[0].title()
    
    # Check if user already exists
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (normalized_email,)
    ).fetchone()
    if existing:
        raise ValueError("An account with this email address already exists.")
    
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(password)
    
    # Create user
    conn.execute(
        "INSERT INTO users (id, email, password_hash, display_name) VALUES (?, ?, ?, ?)",
        (user_id, normalized_email, pwd_hash, clean_name)
    )
    
    # Provision primary workspace
    ws_id = f"ws_{uuid.uuid4().hex[:12]}"
    ws_name = workspace_name.strip() if workspace_name and workspace_name.strip() else f"{clean_name}'s Store"
    
    conn.execute(
        "INSERT INTO workspaces (id, name, currency) VALUES (?, ?, ?)",
        (ws_id, ws_name, "INR")
    )
    
    # Associate user with workspace as owner
    conn.execute(
        "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, 'owner')",
        (ws_id, user_id)
    )
    
    return {
        "id": user_id,
        "email": normalized_email,
        "display_name": clean_name,
        "workspace": {
            "id": ws_id,
            "name": ws_name,
            "role": "owner"
        }
    }


def authenticate_user(
    conn: sqlite3.Connection,
    email: str,
    password: str
) -> Dict[str, Any]:
    """
    Authenticates a user by email and password.
    Returns user profile with authorized workspaces.
    Raises ValueError with generic message on authentication failure.
    """
    normalized_email = email.strip().lower()
    row = conn.execute(
        "SELECT id, email, password_hash, display_name FROM users WHERE email = ?",
        (normalized_email,)
    ).fetchone()
    
    if not row or not verify_password(password, row["password_hash"]):
        raise ValueError("Invalid email or password.")
    
    user_id = row["id"]
    
    # Fetch member workspaces
    ws_rows = conn.execute(
        """
        SELECT w.id, w.name, w.currency, wm.role
        FROM workspaces w
        JOIN workspace_members wm ON w.id = wm.workspace_id
        WHERE wm.user_id = ?
        ORDER BY w.created_at ASC
        """,
        (user_id,)
    ).fetchall()
    
    workspaces = [
        {"id": w["id"], "name": w["name"], "currency": w["currency"], "role": w["role"]}
        for w in ws_rows
    ]
    
    return {
        "id": user_id,
        "email": row["email"],
        "display_name": row["display_name"],
        "workspaces": workspaces
    }


def get_user_by_id(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile and workspaces by user_id."""
    row = conn.execute(
        "SELECT id, email, display_name FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    if not row:
        return None
    
    ws_rows = conn.execute(
        """
        SELECT w.id, w.name, w.currency, wm.role
        FROM workspaces w
        JOIN workspace_members wm ON w.id = wm.workspace_id
        WHERE wm.user_id = ?
        ORDER BY w.created_at ASC
        """,
        (user_id,)
    ).fetchall()
    
    workspaces = [
        {"id": w["id"], "name": w["name"], "currency": w["currency"], "role": w["role"]}
        for w in ws_rows
    ]
    
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "workspaces": workspaces
    }
