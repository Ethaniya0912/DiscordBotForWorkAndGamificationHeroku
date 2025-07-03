# 유저 정보 확인, Trello연동

import os
import discord
from discord.ext import commands
import requests
from trello.trello_lookup import TrelloLookup
from dotenv import load_dotenv
from data.user_mapping import save_user_mapping, get_trello_info

#.env 파일에서 API키 불러오기
load_dotenv()
KEY = os.getenv("TRELLO_KEY")
TOKEN = os.getenv(("TRELLO_TOKEN"))

# @commands.command(name="연동")
# async def link_trello(ctx, trello_id: str):
#     discord_id = str(ctx.author.id)
#     set_trello_id_for_user(discord_id, trello_id)
#     await ctx.send(f"✅ `{trello_id}` 와 성공적으로 연동되었습니다.")
#
# @commands.command(name="내정보")
# async def my_info(ctx):
#     discord_id = str(ctx.author.id)
#     trello_id = get_trello_id_for_user(discord_id)
#
#     if trello_id:
#         await ctx.send(f"🔗 당신은 Trello ID `{trello_id}` 와 연동되어 있습니다.")
#     else:
#         await ctx.send("❌ 아직 Trello 계정과 연동되어 있지 않습니다. `!연동 TrelloID` 명령어로 연동해 주세요.")

# 유저가 트렐로 유저네임을 기입시, 유저네임을 대입해서 id를 찾는 과정.
async def fetch_trello_member_id(username: str):
    url = f"https://api.trello.com/1/members/{username}"
    params = {"key": KEY, "token": TOKEN}
    res = requests.get(url, params=params)

    if res.status_code == 200:
        return res.json()["id"]
    else:
        return None

def setup(bot):
    @bot.command(name="연동")
    async def link_trello(ctx,trello_username: str =None):
        if trello_username is None:
            return await ctx.send("📌 Trello 사용자명을 입력해주세요. 예: `!연동 트렐로유저별명`")

        #찾은 id를 member_id로 저장 후 디스코드 id와 매핑, 이후 연동.
        member_id = await fetch_trello_member_id(trello_username)
        print(f'{member_id}')
        if member_id:
            save_user_mapping(ctx.author.id, member_id, trello_username)
            await ctx.send(f"✅ `{trello_username}` 와 연동 완료!\nTrello 유저이름: '{trello_username}'\nTrello ID: `{member_id}`")
        else:
            await ctx.send(f"❌ Trello 사용자 `{trello_username}` 를 찾을 수 없습니다.")

    # 내정보 명령어 기입시, 연동되어있는지 아닌지 확인해줌.
    @bot.command(name="내정보")
    async def my_info(ctx):
        trello_info = get_trello_info(ctx.author.id)
        print(f'{trello_info}')
        if trello_info:
            await ctx.send(f"📎 현재 연동된 Trello 유저네임: '{trello_info['trello_user_name']}'\n🆔현재 연동된 Trello ID: `{trello_info['trello_member_id']}`")
        else:
            await ctx.send("❌ Trello 계정이 연동되어 있지 않습니다.\n`!연동 Trello 사용자명` 으로 연동해주세요.")