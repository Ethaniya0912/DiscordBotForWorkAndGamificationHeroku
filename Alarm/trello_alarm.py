# 트렐로 알람관련은 여기에

import os
import json
from datetime import datetime, timedelta
from discord.ext import tasks, commands
from dotenv import load_dotenv
from trello.trello_lookup import TrelloLookup
from data.sprint_storage import SprintMetaManager
from data.database import get_db_pool
import pytz
import discord

KST = pytz.timezone('Asia/Seoul')

load_dotenv()

# 환경 변수 로드
BOARD_ID = os.getenv("TRELLO_BOARD_ID")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

class TrelloAlarm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meta_manager = SprintMetaManager(get_db_pool())
        self.daily_sprint_check.start()

    @tasks.loop(time=datetime.strptime("22:00", "%H:%M").time())
    async def daily_sprint_check(self):
        now = datetime.now()
        sprint_lists = TrelloLookup.get_lists_with_due(BOARD_ID)

        all_sprints = await self.meta_manager.get_all_sprints()
        # report = []

        if not all_sprints:
            print("🔔 오늘 점검할 스프린트 없음")
            return

        messages = []

        # for sprint in sprint_lists:
        for list_id, meta in all_sprints.items():
            sprint_name = meta['name']
            due_str = meta.get("due")

            if due_str:
                #날짜만 있는 문자열 파싱
                due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                today = datetime.now().date()

                days_left = (due_date - today).days

                if days_left < 0:
                    messages.append(f"⚠️ `{sprint_name}` 스프린트는 이미 만료되었습니다.")
                elif days_left == 0:
                    messages.append(f"⏰ `{sprint_name}` 스프린트는 오늘 마감입니다!")
                else:
                    messages.append(f"📆 `{sprint_name}` 스프린트 마감까지 {days_left}일 남았습니다.")

        if messages:
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send("\n".join(messages))
            else:
                print("❌ 알림 채널을 찾을 수 없습니다.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📋 TrelloAlarm cog ready: {self.bot.user}")

async def setup(bot):
    await bot.add_cog(TrelloAlarm(bot))
