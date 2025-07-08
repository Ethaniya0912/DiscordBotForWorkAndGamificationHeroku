## 스프린트 파일에 정보를 저장하고 불러올때 활용하는 데이터관리파일
# 스프린트를 db 쿼리에 저장한 후, 캐시 메모리에 불러오기.

# import os
# import json
import asyncpg
from datetime import datetime


# SPRINT_META_FILE = "data/sprint_meta.json"
#
# def load_sprint_meta():
#     if os.path.exists(SPRINT_META_FILE):
#         with open(SPRINT_META_FILE, "r") as f:
#             return json.load(f)
#     return {}
#
# def save_sprint_meta(data):
#     with open(SPRINT_META_FILE, "w") as f:
#         json.dump(data, f, indent=2)
#
# def add_sprint_meta(list_id, name, due_date, created_by):
#     data = load_sprint_meta()
#     data[list_id] = {
#         "name": name,
#         "due": due_date,
#         "created_by": created_by
#     }
#     save_sprint_meta(data)
#
# def get_all_sprints():
#     return load_sprint_meta()

class SprintMetaManager:
    def __init__(self, pool):
        self.pool = pool
        self.cache = {} #  {List_id: {...}}
        print("sprint initializing...")

    async def load_cache(self):
        print("스프린트 캐시를 로딩중..")
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT list_id, name, due_date, created_by FROM sprint_meta")
            self.cache = {}
            for row in rows:
                self.cache[row["list_id"]] = {
                    "name": row["name"],
                    "due": row["due_date"].strftime("%Y-%m-%d %H:%M") if row["due_date"] else None,
                    "created_by": row["created_by"],
                }
            print("✅ Sprint 메타 캐시 로드 완료:", self.cache)
        except Exception as e:
            print("🚨 Sprint 캐시 로딩 실패:", e)

    async def add_sprint(self, list_id, name, due_date, created_by):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sprint_meta (list_id, name, due_date, created_by)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (list_id)
                DO UPDATE SET name=$2, due_date=$3, created_by=$4
                """,
                list_id,
                name,
                due_date,
                created_by,
            )
        # 캐시 갱신
        self.cache[list_id] = {
            "name": name,
            "due": due_date.strftime("%Y-%m-%d %H:%M") if due_date else None,
            "created_by": created_by,
        }
    async def get_all_sprint(self):
        return self.cache

    async def get_sprint(self, list_id):
        return self.cache.get(list_id)

    async def delete_sprint(self, list_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM sprint_meta WHERE list_id=$1", list_id)
        if list_id in self.cache:
            del self.cache[list_id]