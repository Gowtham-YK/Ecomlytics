"""
FastAPI authentication and workspace authorization dependencies.
Enforces strict server-side authentication and workspace tenancy checks.
"""

from fastapi import Depends, HTTPException, Request, status
import sqlite3
from typing import Dict, Any, Generator, Optional
from database.connection import get_db, create_connection
from auth.security import verify_session_token
from auth.service import get_user_by_id


def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """Dependency yielding a managed database connection."""
    conn = create_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract session token from HttpOnly cookie or Authorization header."""
    cookie_token = request.cookies.get("ecomlytics_session")
    if cookie_token:
        return cookie_token
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    
    return None


async def get_current_user(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Enforces authentication on protected routes.
    Extracts session token, verifies signature and expiration,
    and returns authenticated user data.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in."
        )
    
    user_id = verify_session_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please sign in again."
        )
    
    user = get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found."
        )
    
    return user


async def get_current_workspace(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Enforces workspace membership and isolation.
    Resolves requested workspace from X-Workspace-ID header or workspace_id query parameter.
    Validates user is an authorized member of that workspace.
    Defaults to the user's primary workspace if not specified.
    """
    requested_ws_id = (
        request.headers.get("X-Workspace-ID")
        or request.query_params.get("workspace_id")
    )
    
    user_workspaces = current_user.get("workspaces", [])
    if not user_workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to any workspace."
        )
    
    if not requested_ws_id:
        # Default to primary workspace
        return user_workspaces[0]
    
    # Verify membership
    for ws in user_workspaces:
        if ws["id"] == requested_ws_id:
            return ws
            
    # User tried to access a workspace they do not belong to
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You are not a member of the requested workspace."
    )
