"""User database operations."""

import uuid
import asyncpg
from typing import Optional, Dict, Any
from config.database import query_one, execute

async def create_user(email: str, password_hash: str, name: Optional[str] = None, is_verified: bool = False) -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    display_name = name.strip() if name and name.strip() else email.split("@")[0]
    sql = """
    INSERT INTO users (id, name, email, password_hash, is_verified, created_at)
    VALUES ($1, $2, $3, $4, $5, NOW())
    RETURNING id, name, email, is_verified, created_at
    """
    row = await query_one(sql, user_id, display_name, email, password_hash, is_verified)
    return format_user_dict(row)

async def find_user_by_email(email: str) -> Optional[asyncpg.Record]:
    sql = "SELECT * FROM users WHERE email = $1"
    return await query_one(sql, email)

async def find_user_by_id(user_id: str) -> Optional[asyncpg.Record]:
    sql = "SELECT * FROM users WHERE id = $1::uuid"
    return await query_one(sql, user_id)

async def update_user_password(user_id: str, new_hash: str):
    sql = "UPDATE users SET password_hash = $2 WHERE id = $1::uuid"
    await execute(sql, user_id, new_hash)

async def mark_user_verified(email: str):
    sql = "UPDATE users SET is_verified = TRUE WHERE email = $1"
    await execute(sql, email)

async def create_oauth_user(email: str, name: Optional[str] = None, provider: str = "google", provider_id: str = "") -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    display_name = name.strip() if name and name.strip() else email.split("@")[0]
    sql = """
    INSERT INTO users (id, name, email, password_hash, google_id, is_verified, created_at)
    VALUES ($1, $2, $3, '', $4, TRUE, NOW())
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, google_id = EXCLUDED.google_id
    RETURNING id, name, email, is_verified, created_at
    """
    row = await query_one(sql, user_id, display_name, email, provider_id)
    return format_user_dict(row)

def format_user_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "name": row["name"] if row.get("name") else row["email"].split("@")[0],
        "email": row["email"],
        "isVerified": row.get("is_verified", True),
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }
