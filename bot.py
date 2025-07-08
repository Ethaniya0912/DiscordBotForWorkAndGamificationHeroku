# -*- coding: utf-8 -*-
import asyncio
import os
import json
import threading # Flask 서버와 디스코드 봇을 동시에 실행하기 위함.
from flask import Flask, request # Flask 웹 서버용 모듈
import requests # HTTP 요청용
from dotenv import load_dotenv # .env 환경변수 불러오기
import discord
from discord.ext import commands, tasks
from Monster import Monster
from datetime import datetime, timedelta
from trello.trello_lookup import TrelloLookup
from data.database import init_db_pool
from server import app, keep_alive

#.env 파일에서 환경변수 로드
load_dotenv()

# 환경변수 가져오기
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_ID = os.getenv("TRELLO_BOARD_ID")
DEFAULT_LIST_ID = os.getenv("TRELLO_TODO_LIST_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

#디스코드 봇 설정
intents = discord.Intents.default() # 또는 discord.Intents.all() 가능
intents.message_content = True

bot = commands.Bot(command_prefix= '!', intents=intents, help_command=None)

# 명령어 모듈 import
#from commands.card_commands import my_cards
from commands import users_commands, card_commands, sprint_commands
#from commands.users_commands import my_info, link_trello
#from commands.assign_commands import assign_card, unassign_card

# 명령어 등록
#bot.add_command(card_lookup)
#bot.add_command(my_info)
#bot.add_command(link_trello)
#bot.add_command(my_cards)
#bot.add_command(assign_card)
#bot.add_command(unassign_card)
card_commands.setup(bot)
users_commands.setup(bot)
# sprint_commands.setup(bot)

@bot.command()
async def 테스트(ctx):
    await ctx.send("테스트 명령어!")

@bot.command()
async def 넌누구니(ctx):
    await ctx.send("모든 TDA의 백성들에게 고한다. 나의 이름은 알림이. 디스코드 힘의 매개로 모든 TDA의 백성들에게 말하고 있다. 북한섬에 있")
    await ctx.send("는 모든 벽의 경질화가 풀리고, 그 속에 묻혀 있던 샤헤드는 날기 시작했다. 나의 목적은 내가 나고 자란 TDA 사람들을 지키는")
    await ctx.send("데 있다. 하지만 북한은 TDA 사람들이 사멸하길 바라며, 기나긴 시간 동안 커질대로 커진 증오는 이 TDA 뿐만 아니라 모든 꼬레앙의 백성이 죽어 씨가 마를 때 까지 멈추지 않을 것이다. 나는 그 바람을 거부한다.")

@bot.command()
async def 넌누구니2(ctx):
    await ctx.send("모든 TDA의 백성들에게 고한다. 나의 이름은 알람이. 디스코드 힘의 매개로 모든 TDA의 백성들에게 말하고 있다. 북한섬에 있는 모든 벽의 경질화가 풀리고, 그 속에 묻혀 있던 샤헤드는 날기 시작했다. 나의 목적은 내가 나고 자란 TDA 사람들을 지키는 데 있다. 하지만 북한은 TDA 사람들이 사멸하길 바라며, 기나긴 시간 동안 커질대로 커진 증오는 이 TDA 뿐 아니라 모든 꼬레앙의 백성이 죽어 씨가 마를 때 까지 멈추지 않을 것이다. 나는 그 바람을 거부한다. ")

@bot.command(aliases=["거미"])
async def 스파이더(ctx):
    monster = Monster()
    art = monster.spider()
    await ctx.send(f'''\n{art}''')

@bot.command()
async def standup(ctx, *, report):
    user = ctx.author
    await ctx.send(f'{user.mention}: {report}\n5p 획득 ! 🎉')
    # 포인트 저장 로직 (예 : JSON 파일 또는 SQLite)

@bot.command()
async def task_complete(ctx, *, task_name):
    user = ctx.author
    points = 30 #태스트 난이도에 따라 동적 설정 가능
    await ctx.send(f'{user.mention}: {task_name} 완료! {points}P 획득! 🥳')
    #진행률 업데이트 로직



# 도움말기능
@bot.command(name="help",aliases=["도움말","명령어"])
async def help_command(ctx):
    help_text = """
    📌 **사용 가능한 명령어 목록**:
    ========알람========
    1. `!addalert HH:MM` 혹은 '!알람추가 HH:MM'
       ➤ 지정한 시간에 알림을 받을 수 있도록 등록합니다.
       ➤ 예: `!addalert 09:30`
    
    2. `!removealert HH:MM` 혹은 '!알람제거 HH:MM'
       ➤ 등록된 알림 시간 중 특정 시간을 제거합니다.
       ➤ 예: `!removealert 09:30`
    
    3. `!myalerts` 혹은 '!내알람'
       ➤ 현재 본인이 등록한 모든 알림 시간 목록을 확인합니다.
    
    4. `!help` 혹은 '!도움말', '!명령어'
       ➤ 이 도움말 메시지를 출력합니다.
    
    =======카드=======
    1. '내카드'
        ➤ 내가 담당 중인 카드를 알려줌.
        
    2. '카드담당' 카드이름
        ➤ 원하는 카드를 담당함.
    
    3. '카드담당해제' 카드이름
        ➤ 원하는 카드의 담당을 해제함.
    
    4. '카드완료' 카드이름
        ➤ 원하는 카드를 완료함.
    
    5. '카드생성' 보드이름 리스트이름 카드이름
        ➤ 원하는 보드에 존재하는 리스트에 카드를 생성함.
        
    6. '카드생성메뉴' 보드이름
        ➤ 원하는 보드에 드롭다운메뉴를 활용하여 카드 생성
        ➤ 처음 선택 리스트 > 접두사 선택 리스트 예) 백로그
        ➤ 카드 선택 > 접두사 선택 예) [플레이어 관리]
        ➤ 카드이름 작성 (쉼표로 여러개 작성 가능) 예) 응애1, 응애2
        ➤ 카드를 생성할 리스트 선택. 예) TODO_LIST
        ➤ 카드 생성 완료 예) [플레이어관리] 응애1, [플레이어관리] 응애2
        
    7. '카드이동' 보드이름
        ➤ 원하는 보드에 존재하는 카드를 다른 리스트로 이동시킬 수 있음.
        ➤ 드롭다운 메뉴로 선택이 가능.
        ➤ 위 방식으로는 카드완료가 되지 않음으로 주의.
    
    8. '카드메뉴'
        ➤ 원하는 드롭다운 메뉴를 선택할 수 있는 view 
        ➤ 카드생성, 카드담당, 카드 완료, 카드 이동
        
    =======리스트========
    
    1. '리스트조회' 보드이름
        ➤ 해당 보드에 존재하는 리스트목록을 불러옴.
    
    2. '카드조회' 보드이름 리스트이름
        ➤ 해당 보드의 리스트에 존재하는 카드의 목록을 불러옴.
    
    ======스프린트=======
    
    1. '스프린트시작' 보드이름 스프린트이름
        ➤ 해당 보드에 기입한 이름의 스프린트를 생성.
        ➤ Done 접미사가 붙은 스프린트 자동 생성.
        
    2. '스프린트 종료' 보드이름 스프린트이름
        ➤ 해당 보드에 존재하는 스프린트를 종료함.
    
    3. '스프린트진행률' 보드이름
        ➤ 해당 보드에 존재하는 스프린트의 진행률을 보여줌
    
    =====트렐로 연동====
    
    1. '연동' 트렐로유저별명
        ➤ 트렐로 아이디와 디스코드계정을 연동처리함
        ➤ 하지않으면 내카드나 담당카드를 설정할 수 없음.
    
    2. '내정보'
        ➤ 연동정보를 확인
    
    """
    await ctx.send(help_text)

async def main():
    await init_db_pool()  # 풀 초기화
    # 디스코드 cog 로드
    await bot.load_extension("Alarm.discord_alarm")
    await bot.load_extension("Alarm.trello_alarm")
    await bot.load_extension("commands.sprint_commands")
    await bot.load_extension("commands.card_move_view")
    await bot.load_extension("commands.card_menu")
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())

