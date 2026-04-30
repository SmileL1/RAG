"""JWT 签发/验证 + bcrypt 密码哈希。

直接使用 bcrypt 库，绕过 passlib 与 bcrypt>=4.0 的兼容性问题
（passlib 1.7.x 内部会传入 >72 字节测试密码，触发 bcrypt 4.0 的长度限制报错）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(username: str, is_admin: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": username, "is_admin": is_admin, "exp": expire},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token: str) -> tuple[str, bool]:
    """返回 (username, is_admin)；失败抛 JWTError。"""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return str(payload["sub"]), bool(payload.get("is_admin", False))
