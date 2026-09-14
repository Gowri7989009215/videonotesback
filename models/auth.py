"""Authentication auxiliary DB operations (verification codes, reset tokens)."""

import uuid
from typing import Optional
from config.database import query_one, execute

async def store_verification_code(email: str, code: str):
    await execute("DELETE FROM verification_codes WHERE email = $1", email)
    sql = """
    INSERT INTO verification_codes (id, email, code, created_at, expires_at)
    VALUES ($1, $2, $3, NOW(), NOW() + INTERVAL '15 minutes')
    """
    code_id = str(uuid.uuid4())
    await execute(sql, code_id, email, code)

async def verify_code(email: str, code: str) -> bool:
    sql = """
    SELECT id FROM verification_codes
    WHERE email = $1 AND code = $2 AND expires_at > NOW()
    """
    row = await query_one(sql, email, code)
    if row:
        delete_sql = "DELETE FROM verification_codes WHERE email = $1"
        await execute(delete_sql, email)
        return True
    return False

async def store_password_reset_code(email: str, code: str):
    await execute("DELETE FROM password_resets WHERE email = $1", email)
    sql = """
    INSERT INTO password_resets (id, email, code, created_at, expires_at)
    VALUES ($1, $2, $3, NOW(), NOW() + INTERVAL '15 minutes')
    """
    reset_id = str(uuid.uuid4())
    await execute(sql, reset_id, email, code)

async def verify_password_reset_code(email: str, code: str) -> bool:
    sql = """
    SELECT id FROM password_resets
    WHERE email = $1 AND code = $2 AND expires_at > NOW()
    """
    row = await query_one(sql, email, code)
    if row:
        delete_sql = "DELETE FROM password_resets WHERE email = $1"
        await execute(delete_sql, email)
        return True
    return False
