import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 글로벌 풀 객체
_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DATABASE_URL)
    return _pool

def get_db_pool():
    if _pool is None:
        raise Exception("DB 풀이 초기화되지 않았습니다. init_db_pool()을 먼저 호출하세요.")
    return _pool
