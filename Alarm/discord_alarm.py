# 디스코드 관련 알람 정리

import os
import asyncio
from discord.ext import tasks, commands
from datetime import datetime
# import json
import asyncpg
from dotenv import load_dotenv # .env 환경변수 불러오기
from data.database import init_db_pool, get_db_pool


#.env 파일에서 환경변수 로드
load_dotenv()

# 환경 변수 불러오기
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

##sql 이전으로 폐기. - 앞으로 #처리된 것은 전부 sql 화.
# # 알림 정보 저장 파일 경로
# ALERT_FILE = "Alarm/alert_times.json"
#
# # 알림 데이터 로딩
# def load_alerts():
#     if os.path.exists(ALERT_FILE):
#         with open(ALERT_FILE, 'r') as f:
#             return json.load(f)
#     return {}
#
# # 알림 데이터 저장
# def save_alerts(data):
#     with open(ALERT_FILE, 'w') as f:
#         json.dump(data, f, indent=2)
#
#
# user_alerts = load_alerts()

class Discord_alarm(commands.Cog):
    # 이니셜라이즈. 여기서 스타트를 함.
    def __init__(self, bot):
        self.bot = bot
        self.pool = None

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot ready as {self.bot.user}.', flush=True)
        await self.bot.wait_until_ready()
        await init_db_pool() # 풀 초기화
        self.pool = get_db_pool()
        print("DB pool reset complete", flush=True)
        self.check_and_send_user_alerts.start()

    # 알림 추가 명령어
    @commands.command(aliases=["알람추가"])
    async def addalert(self, ctx, time: str):
        try:
            print("starting alarm adding.")
            user_id = ctx.author.id

            # HH:MM 형식 확인
            try:
                # 문자열을 datetime 객체로 먼저 파싱
                parsed_time = datetime.strptime(time, "%H:%M").time()

                # 형식을 맞춘 문자열로 다시 변환
                # formatted_time = parsed_time.strftime("%H:%M:%S")
            except ValueError:
                await ctx.send("시간 형식이 잘못 되었습니다. (예:15:30)")
                return

            print("💡 시간 파싱 완료:", parsed_time)

        ##SQL 이전으로 인한 JSON관련 코드 diff
        # if user_id not in user_alerts:
        #     user_alerts[user_id] = []
        #
        # if formatted_time in user_alerts[user_id]:
        #     await ctx.send(f"{ctx.author.mention} 이미 등록된 시간입니다.")
        # else:
        #     user_alerts[user_id].append(formatted_time)
        #     save_alerts(user_alerts)
        #     print(f"{user_alerts}")
        #     await ctx.send(f"{ctx.author.mention} 알림 시간 '{formatted_time}'이 등록되었습니다.")

        # PSQL
            async with self.pool.acquire() as conn: # pool 에서 가져오며, conn으로 저장.
                exists = await conn.fetchval(
                    "SELECT 1 FROM user_alerts WHERE user_id=$1 AND alert_time=$2",
                    user_id,
                    parsed_time
                )
                print("DB SELECT complete:", exists)

        # user id 는 첫번째 파라미터, formatted_time 은 두번째 파라미터.
        # asyncpg 가 안전하게 파라미터에 다음 값들을 집어넣는 방식이고 sql 인젝션 공격을 방지.
                if exists:
                    await ctx.send(f"{ctx.author.mention} 이미 등록된 시간입니다.")
                    return
                await conn.execute(
                    "INSERT INTO user_alerts (user_id, alert_time) VALUES ($1, $2)",
                    user_id,
                    parsed_time
                )
                print("DB INSERT 완료")

            # [:5]는 5문자열만 가져온다는 것. 뒤에 시:분 이외 초는 필요없음으로.
            await ctx.send(f"{ctx.author.mention} 알림 시간 '{parsed_time[:5]}' 이 등록되었습니다.")
        except Exception as e:
            print("X addalert exception occur:", e)
            await ctx.send(f"error occured: {e}")

    # 알람 확인 명령어
    @commands.command(aliases=["내알람"])
    async def myalerts(self, ctx):
        await ctx.send("디버그:명령어 진입")
        ## psql 이전으로 인한 json 관련 코드 제거
        # user_id = str(ctx.author.id)
        #
        # if user_alerts is None or user_id not in user_alerts or not user_alerts[user_id]:
        #     await ctx.send(f"{ctx.author.mention}, 등록된 알림 시간이 없습니다.")
        #     return
        #
        # alerts = user_alerts[user_id]
        # formatted_alerts = "\n".join(f"- {t}" for t in sorted(alerts))

        # psql 추가
        user_id = ctx.author.id
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT alert_time FROM user_alerts WHERE user_id=$1 ORDER BY alert_time",
                user_id
            )
        print("rows:", rows) # 로그생성
        if not rows:
            await ctx.send(f"{ctx.author.mention}, 등록된 알림 시간이 없습니다.")
            return
        formatted_alerts = "\n".join(f" - {r['alert_time'].strftime('%H:%M')}" for r in rows)

        await ctx.send(f"⏰{ctx.author.mention}님의 웰뤰 쉐궨 뭭뤡:\n{formatted_alerts}")

    # 알림 제거 명령어
    @commands.command(aliases=["알람제거"])
    async def removealert(self, ctx, time: str):
        
        ## psql 이전으로 인한 json 폐기
        # user_id = str(ctx.author.id)
        # 
        # if user_id in user_alerts and time in user_alerts[user_id]:
        #     user_alerts[user_id].remove(time)
        #     save_alerts(user_alerts)
        #     await ctx.send(f"{ctx.author.mention} 알림 시간 '{time}' 이 제거되었습니다.")
        # else:
        #     await ctx.send(f"{ctx.author.mention} 해당 시간은 등록되어 있지 않습니다.")

        ## psql 도입
        user_id = ctx.author.id
        try:
            parsed_time = datetime.strptime(time, "%H:%M")
            formatted_time = parsed_time.strftime("%H:%M:%S")
        except ValueError:
            await ctx.send("시간 형식이 잘못 되었습니다. (예:15:30)")
            return
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_alerts WHERE user_id=$1 AND alert_time=$2",
                user_id, # 파라미터 1
                formatted_time # 파라미터 2
            )
        if result == "DELETE 0":
            await ctx.send(f"{ctx.author.mention} 해당 시간은 등록되어있지 않습니다.")
        else:
            await ctx.send(f"{ctx.author.mention} 알림 시간 '{time}'이 제거되었습니다.")


    # 알림 루프 : 매 분마다 검사
    @tasks.loop(minutes=1)
    async def check_and_send_user_alerts(self):
        # now = datetime.now().strftime("%H:%M")
        now = datetime.now().strftime("%H:%M:%S")
        channel = self.bot.get_channel(CHANNEL_ID)

        if not channel:
            print("지정 채널을 찾을 수 없습니다.")
            return

        ## psql 이전으로 인한 json 관련코드 폐기
        # for user_id, times in user_alerts.items():
        #     if now in times:
        #         user = await self.bot.fetch_user(int(user_id))
        #         if user:
        #             await channel.send(f"⏰{user.mention}, 지금은 '{now}'입니다! 설정한 업무시간입니다. ")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT user_id FROM user_alerts WHERE alert_time=$1",
                now
            )
        for r in rows:
            user = await self.bot.fetch_user(r["user_id"])
            if user:
                await channel.send(f"⏰{user.mention}, 지금은 '{now[:5]}'입니다! 설정한 업무시간입니다.")

    # # 알림봇기능
    # @tasks.loop(minutes=1)
    # async def check_and_send_alerts():
    #     now = datetime.now()
    #     print(f'{now}')
    #     if now.hour in [0, 15, 19, 23] and now.minute in [58, 59, 0]:  # 오후 3시, 오후 7시 정각.
    #         channel = bot.get_channel(CHANNEL_ID)
    #         print(f'{channel}')
    #         if channel:
    #             await channel.send(f"⏰ 지금은 **{now.strftime('%p %I시')}**입니다! 오늘 작업을 정리하거나, 스프린트를 점검해보세요.")

# Cog 등록
async def setup(bot):
    await bot.add_cog(Discord_alarm(bot))