# 리스트, 대부분 카드 관련 명령어

import os
from discord.ext import commands
import requests
from trello.trello_auth import get_trello_id_for_user
from trello.trello_lookup import TrelloLookup
from commands.sprint_commands import Sprint
from commands.card_move_view import ListSelectViewForCardCreate, ListSelectViewForAssign, ListSelectViewForComplete
from data.user_mapping import get_trello_info
from dotenv import load_dotenv # .env 환경변수 불러오기

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
BOARD_ID = os.getenv("TRELLO_BOARD_ID")
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

# @commands.command(name="내카드")
# async def my_cards(ctx):
#     discord_id = str(ctx.author.id)
#     trello_id = get_trello_id_for_user(discord_id)
#
#     if not trello_id:
#         return await ctx.send("❌ 먼저 Trello 계정과 연동해 주세요. (`!연동 TrelloID`)")
#
#     cards = get_all_cards()
#     assigned = [card for card in cards if trello_id in [m['id'] for m in card.get('idMembers', [])]]
#
#     if not assigned:
#         return await ctx.send("📭 현재 담당하고 있는 카드는 없습니다.")
#
#     msg = "\n". join([f"-{card['name']}(보드: {card.get(idBoard)}"for card in assigned])
#     await ctx.send(f"📌 현재 담당 중인 카드:\n{msg}")

def setup(bot):
    @bot.command(name="내카드")
    async def my_cards(ctx):
        info = get_trello_info(ctx.author.id)
        if not info:
            await ctx.send("❌ Trello 계정이 연동되어 있지 않습니다.")
            return

        member_id = info["trello_member_id"]
        cards = TrelloLookup.get_cards_by_member(BOARD_ID, member_id)

        if not cards:
            await ctx.send("🃏 현재 담당 중인 카드는 없습니다.")
            return

        msg = "\n".join(f"📌{card['name']}" for card in cards)
        await ctx.send(f"📄 담당 카드 목록:\n{msg}")

    @bot.command(name="카드담당")
    async def assign_card(ctx, *, card_name):
            info = get_trello_info(ctx.author.id)
            if not info:
                await ctx.send("❌ Trello 계정이 연동되어 있지 않습니다.")
                return

            card_id = TrelloLookup.get_card_id_by_name(BOARD_ID, card_name)
            if not card_id:
                await ctx.send(f"❌ 카드 '{card_name}'을 찾을 수 없습니다.")
                return

            res = TrelloLookup.assign_member_to_card(card_id, info["trello_member_id"])
            if res.status_code == 200:
                await ctx.send(f"✅ 카드 `{card_name}`에 담당자로 추가되었습니다.")
            else:
                await ctx.send(f"⚠ 카드 할당 실패: {res.text}")

    @bot.command(name="카드담당메뉴")
    async def assign_cards_menu(ctx, board_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드를 찾을 수 없습니다.")

        await ctx.send(
            f"📋 `{board_name}`의 리스트를 선택하세요.",
            view=ListSelectViewForAssign(board_id)
        )

    @bot.command(name="카드담당해제")
    async def unassign_card(ctx, *, card_name):
        info = get_trello_info(ctx.author.id)
        if not info:
            await ctx.send("❌ Trello 계정이 연동되어 있지 않습니다.")
            return

        card_id = TrelloLookup.get_card_id_by_name(BOARD_ID, card_name)
        if not card_id:
            await ctx.send(f"❌ 카드 `{card_name}`을(를) 찾을 수 없습니다만.")
            return

        res = TrelloLookup.remove_member_from_card(card_id, info["trello_member_id"])
        if res.status_code == 200:
            await ctx.send(f"🗑️ 카드 '{card_name}'에서 담당자에서 제거되었습니다.")
        else:
            await ctx.send(f"⚠️담당자 제거 실패: {res.text}")

# 완료시 완료 라벨 추가 및 스프린트 DONE리스트로 자동으로 이동.
    @bot.command(name="카드완료")
    async def complete_card(ctx, *, card_name):
        card_id = TrelloLookup.get_card_id_by_name(BOARD_ID, card_name)
        if not card_id:
            await ctx.send(f"❌ 카드 `{card_name}`을(를) 찾을 수 없습니다.")
            return

        # 카드 정보 조회(이후 DONE 리스트 ID 조회시 활용
        card_info = TrelloLookup.get_card_info_by_id(card_id)
        if not card_info:
            return await ctx.send("❌ 카드 정보를 불러오지 못했습니다.")

        source_board_id = card_info["idBoard"]

        # DONE 리스트 ID 조회 (접미사 기반)
        done_list_id = TrelloLookup.get_list_id_endswith(source_board_id, "done")
        if not done_list_id:
            return await ctx.send("❌ 'DONE' 리스트를 찾을 수 없습니다.\n리스트 이름이 '....DONE'으로 끝나야 합니다.")

        # 카드 완료 마크 처리
        mark_res = TrelloLookup.mark_card_complete(card_id)
        if mark_res.status_code != 200:
            return await ctx.send(f"⚠️ 완료 처리 실패: {mark_res.text}")

        # 카드 이동 + 라벨추가 + 진행률 출력
        move_res = TrelloLookup.move_card_to_list(card_id, done_list_id)
        if move_res.status_code == 200:
            progress_msg = await Sprint.generate_sprint_progress(source_board_id)
            await ctx.send(f"✅ 카드 '{card_name}'가 완료로 표시되었고, DONE리스트로 이동했습니다.\n\n{progress_msg}")
        else:
            await ctx.send(f"⚠️카드 완료는 되었지만 이동 실패 : {move_res.text}")

    @bot.command(name="카드완료메뉴")
    async def complete_cards_menu(ctx, board_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드를 찾을 수 없습니다.")

        await ctx.send(
            f"📋 `{board_name}`의 리스트를 선택하세요.",
            view=ListSelectViewForComplete(board_id)
        )

    # 리스트 조회 : !리스트조회 보드이름
    @bot.command(name="리스트조회")
    async def list_lookup(ctx, board_name=None):
        if not board_name:
            return await ctx.send("❗ 사용법: `!리스트조회 보드이름` (예: `!리스트조회 pA`)")

        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습눼뒈")

        res = requests.get(f"{BASE_URL}/boards/{board_id}/lists", params={"key": TRELLO_KEY, "token": TRELLO_TOKEN})
        lists = res.json()
        if not lists:
            return await ctx.send("📭리스트가 없습니다.")

        msg = "\n".join([f"- {lst['name']} (ID: `{lst['id']}`)" for lst in lists])
        await ctx.send(f"📋 **{board_name}** 보드의 리스트 목록:\n{msg}")

    # 카드 조회 : !카드조회 보드이름 리스트이름
    @bot.command(name="카드조회")
    async def card_lookup(ctx, board_name, *, list_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습니다.")

        list_id = TrelloLookup.get_list_id_by_name(board_id, list_name)
        if not list_id:
            return await ctx.send("❌ 리스트 이름을 찾을 수 없습니다.")

        try:
            res = requests.get(
                f"{BASE_URL}/lists/{list_id}/cards",
                params={"key": TRELLO_KEY, "token": TRELLO_TOKEN},
                timeout=5  # 응답 지연 방지
            )

            # 상태 코드 확인
            if res.status_code != 200:
                await ctx.send(f"❌ Trello API 오류 (상태코드 : {res.status_code}")
                return

            try:
                cards = res.json()
            except Exception:
                await ctx.send("❌ Trello 응답이 JSON 형식이 아닙니다.")
                return

            if not cards:
                return await ctx.send("📭 카드가 없습니다.")

            msg = "\n".join([f"- {card['name']} (ID: `{card['id']}`)" for card in cards])
            await ctx.send(f" **{list_name}** 리스트의 카드 목록:\n{msg}")
        except requests.exceptions.RequestException as e:
            # 네트워크 오류 처리
            await ctx.send(f"❌ 요청중 오류 발생 : '{str(e)}'")

    # 카드 생성: !카드생성 보드이름 리스트이름 카드이름
    @bot.command(name="카드생성")
    async def create_card_cmd(ctx, board_name, list_name, *, card_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습눼뒈")

        list_id = TrelloLookup.get_list_id_by_name(board_id, list_name)
        if not list_id:
            return await ctx.send("❌ 리스트 이름을 찾을 수 없습니다.")

        card = TrelloLookup.create_card(card_name, list_id)
        await ctx.send(f"✅카드 **{card['name']}** 생성됨: {card.get('url')}")

    # 카드 생성 드롭다운 : !카드생성메뉴 보드이름
    @bot.command(name="카드생성메뉴")
    async def create_card(ctx, board_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드를 찾을 수 없습니다.")

        await ctx.send(
            f"📋 `{board_name}`의 리스트를 선택하세요 (접미사 카드 선택용).",
            view=ListSelectViewForCardCreate(board_id)
        )

    # #카드이동 명령어
    # @bot.command(name="카드이동")
    # async def move_card_menu(ctx, board_name, *, list_name):
    #     board_id = TrelloLookup.get_board_id_by_name(board_name)
    #     if not board_id:
    #         return await ctx.send("❌ 보드 이름을 찾을 수 없습니다.")
    #
    #     list_id = TrelloLookup.get_list_id_by_name(board_id, list_name)
    #     if not list_id:
    #         return await ctx.send("❌ 리스트 이름을 찾을 수 없습니다.")
    #
    #     cards = TrelloLookup.get_card(list_id)
    #     if cards == 0:
    #         return await ctx.send("❌ 카드 조회 실패")
    #     if not cards:
    #         return await ctx.send("📭 이동할 카드가 없습니다.")
    #
    #     options = [
    #         SelectionOption(labe=card["name"][:100], value=card["id"])
    #         for card in cards
    #     ]
    #
    #     #최대 25개 카드만 가능 (Discord 제한)
    #     if len(options) > 25:
    #         options = options[:25]
    #
    #     view = CardMoveView(options, board_id)

