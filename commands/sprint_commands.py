# 스프린트 관련 명령어
import os
from discord.ext import commands
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv # .env 환경변수 불러오기
from trello.trello_lookup import TrelloLookup
from data.sprint_storage import SprintMetaManager
from data.database import get_db_pool

load_dotenv()
BOARD_ID = os.getenv("TRELLO_BOARD_ID")

class Sprint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meta_manager = SprintMetaManager(get_db_pool())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.meta_manager.load_cache()
        print("✅ Sprint 메타 캐시 로드 완료")

    # 스프린트 시작: !스프린트시작 보드이름 스프린트이름
    @commands.command(name="스프린트시작")
    async def sprint_start(self, ctx, board_name, sprint_name: str, days_until_due: int = 7):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습니다.")

        # 1. 스프린트 리스트 생성
        due_date = (datetime.utcnow() + timedelta(days=days_until_due)).strftime('%Y-%m-%d')
        lst = TrelloLookup.create_list_with_due(board_id, sprint_name, due_date)
        # 리스트 ID 가져오기 후 만료일 저장.
        list_id = lst.get("id")
        ## sql + 캐시화로 인한 주석화
        # add_sprint_meta(list_id, sprint_name, due_date, str(ctx.author.id))
        due_dt = datetime.strptime(due_date, "%Y-%m-%d")
        await self.meta_manager.add_sprint(list_id, sprint_name, due_dt, ctx.author.id)

        # 2. DONE 리스트 자동 생성
        done_list_name = f"{sprint_name}_DONE"
        done_list = TrelloLookup.create_list(board_id, done_list_name)

        if not done_list:
            return await ctx.send(f"⚠ 스프린트는 생성되었으나 DONE 보드 생성에 실패했습니다.")


        await ctx.send(
            f"🚀 스프린트 시작됨: '{sprint_name}'\n"
            f"만료일: '{due_date}'\n"
            f"리스트 ID: '{list_id}'\n"
            f"🆕 DONE 보드 생성됨: `{done_list_name}`"
        )

    # 스프린트 종료: !스프린트 종료 보드이름 스프린트이름
    @commands.command(name="스프린트종료")
    async def sprint_end(self, ctx, board_name, *, sprint_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습니다.")

        list_id = TrelloLookup.get_list_id_by_name(board_id, sprint_name)
        if not list_id:
            return await ctx.send("❌ 스프린트(리스트) 이름을 찾을 수 없습니다.")

        TrelloLookup.archive_list(list_id)
        await self.meta_manager.delete_sprint(list_id)
        await ctx.send(f"✅ 스프린트 종료됨 (리스트 ID: `{list_id}`)")

    # 스프린트 진행율을 확인하는 커맨드
    @commands.command(name="스프린트진행률")
    async def sprint_progress(self, ctx, board_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 해당 보드를 찾을 수 없습니다.")

        msg = await self.generate_sprint_progress(board_id)

        if not msg.strip():
            return await ctx.send("📭 진행 중인 스프린트를 찾을 수 없습니다.")

        await ctx.send(msg)

    #------------------정의 관련-----------------

    # 프로그레스바 아스키화
    def get_progress_bar(self, percent, length=20):
        filled_length = int(length * percent / 100)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"[{bar}]"

    async def generate_sprint_progress(self, board_id):
        all_sprints = await self.meta_manager.get_all_sprint()
        report = []

        for list_id, meta in all_sprints.items():
            sprint_name = meta["name"]
            due_date = meta["due"]

            # 해당 보드의 리스트인지 확인
            if not TrelloLookup.is_list_on_board(list_id, board_id):
                continue

            # DONE 리스트 찾기 (ex: Sprint1 DONE)
            done_list_id = TrelloLookup.get_list_id_endswith(board_id, sprint_name + "_DONE")
            if not done_list_id:
                report.append(f"⚠ `{sprint_name}`: DONE 리스트 없음")
                continue

            sprint_cards = TrelloLookup.get_card_count(list_id)
            done_cards = TrelloLookup.get_card_count(done_list_id)
            total_cards = sprint_cards + done_cards

            if total_cards == 0:
                progress = 0
            else:
                progress = round((done_cards / total_cards) * 100, 1)

            progress_bar = self.get_progress_bar(progress)
            report.append(f"📊 `{sprint_name}` 진행률: {progress}% ({done_cards}/{total_cards})\n{progress_bar}")

        return "\n".join(report)

async def setup(bot):
    await bot.add_cog(Sprint(bot))
