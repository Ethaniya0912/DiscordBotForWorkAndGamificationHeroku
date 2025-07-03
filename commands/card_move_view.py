# commands/card_move_view.py

import discord
from discord.ext import commands
from trello.trello_lookup import TrelloLookup
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
BASE_URL = "https://api.trello.com/1"

#=============카드이동드롭다운=============

# ✅ 리스트 선택 드롭다운
class ListSelect(discord.ui.Select):
    def __init__(self, board_id):
        self.board_id = board_id

        lists = TrelloLookup.get_lists(board_id)
        options = [
            discord.SelectOption(
                label=l["name"],
                description=f"리스트 ID: {l['id']}"
            ) for l in lists
        ]

        super().__init__(
            placeholder="카드를 조회할 리스트를 선택하세요.",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_name = self.values[0]
        selected_list = next(
            l for l in TrelloLookup.get_lists(self.board_id) if l["name"] == selected_name
        )
        list_id = selected_list["id"]

        cards = TrelloLookup.get_card(list_id)
        if not cards:
            return await interaction.response.send_message(
                "📭 선택한 리스트에 카드가 없습니다.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"🃏 `{selected_name}`의 카드를 선택하세요.",
            view=discord.ui.View().add_item(CardSelect(cards, self.board_id)),
            ephemeral=True
        )

# ✅ 리스트 선택용 View
class ListSelectView(discord.ui.View):
    def __init__(self, board_id):
        super().__init__(timeout=60)
        self.add_item(ListSelect(board_id))


# ✅ 카드 선택 드롭다운
class CardSelect(discord.ui.Select):
    def __init__(self, cards, board_id):
        self.cards = cards
        self.board_id = board_id
        options = [
            discord.SelectOption(
                label=card["name"],
                description=f"카드 ID: {card['id']}"
            )
            for card in cards
        ]
        super().__init__(
            placeholder="이동할 카드를 선택하세요. (여러 개 선택 가능)",
            min_values=1,
            max_values=len(cards),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_card_names = self.values
        selected_cards = [c for c in self.cards if c["name"] in selected_card_names]
        card_ids = [c["id"] for c in selected_cards]

        await interaction.response.send_message(
            f"✅ {len(card_ids)}개 카드를 선택했습니다.\n이동할 리스트를 선택하세요.",
            view=TargetListView(card_ids, self.board_id),
            ephemeral=True
        )

# ✅ 이동 대상 리스트 선택 드롭다운
class TargetListView(discord.ui.View):
    def __init__(self, card_ids, board_id):
        super().__init__(timeout=60)
        self.add_item(TargetListSelect(card_ids, board_id))

class TargetListSelect(discord.ui.Select):
    def __init__(self, card_ids, board_id):
        self.card_ids = card_ids
        self.board_id = board_id

        lists = TrelloLookup.get_lists(board_id)
        options = [
            discord.SelectOption(
                label=list_["name"],
                description=f"리스트 ID: {list_['id']}"
            )
            for list_ in lists
        ]

        super().__init__(
            placeholder="이동할 리스트를 선택하세요.",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_list_name = self.values[0]
        selected_list = next(
            l for l in TrelloLookup.get_lists(self.board_id) if l["name"] == selected_list_name
        )
        list_id = selected_list["id"]

        success_count = 0
        fail_count = 0

        for card_id in self.card_ids:
            res = requests.put(
                f"{BASE_URL}/cards/{card_id}",
                params={
                    "idList": list_id,
                    "key": TRELLO_KEY,
                    "token": TRELLO_TOKEN
                }
            )
            if res.status_code == 200:
                success_count += 1
            else:
                fail_count += 1

        await interaction.response.send_message(
            f"📦 카드 {success_count}개를 `{selected_list_name}`로 이동했습니다.\n"
            + (f"❌ 실패: {fail_count}개" if fail_count > 0 else ""),
            ephemeral=True
        )

# ✅ Cog 클래스
class CardMoveView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="카드이동")
    async def move_card_menu(self, ctx, board_name):
        board_id = TrelloLookup.get_board_id_by_name(board_name)
        if not board_id:
            return await ctx.send("❌ 보드 이름을 찾을 수 없습니다.")

        # list_id = TrelloLookup.get_list_id_by_name(board_id, list_name)
        # if not list_id:
        #     return await ctx.send("❌ 리스트 이름을 찾을 수 없습니다.")

        # cards = TrelloLookup.get_card(list_id)
        # if cards == 0:
        #     return await ctx.send("❌ 카드 조회 실패")
        # if not cards:
        #     return await ctx.send("📭 리스트에 카드가 없습니다.")
        #
        # await ctx.send(
        #     f"🎯 `{list_name}`의 카드를 선택하세요.",
        #     view=discord.ui.View().add_item(CardSelect(cards, board_id))

        await ctx.send(
            f"📂 `{board_name}`의 리스트를 선택하세요.",
            view=ListSelectView(board_id)
        )

#==============카드생성================
# ✅ 백로그 리스트 선택
class ListSelectForCardCreate(discord.ui.Select):
    def __init__(self, board_id):
        self.board_id = board_id

        lists = TrelloLookup.get_lists(board_id)
        options = [
            discord.SelectOption(
                label=list_["name"],
                description=f"리스트 ID: {list_['id']}"
            )
            for list_ in lists
        ]

        super().__init__(
            placeholder="카드 접두사를 선택할 리스트를 고르세요 (예: 백로그)",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_list = next(
            l for l in TrelloLookup.get_lists(self.board_id) if l["name"] == self.values[0]
        )
        await interaction.response.send_message(
            f"📂 `{selected_list['name']}`의 카드 목록을 불러옵니다.",
            view=CardSelectForPrefix(self.board_id, selected_list["id"]),
            ephemeral=True
        )

class ListSelectViewForCardCreate(discord.ui.View):
    def __init__(self, board_id):
        super().__init__(timeout=60)
        self.add_item(ListSelectForCardCreate(board_id))


# ✅ 접미사 카드 선택
class CardSelectForPrefix(discord.ui.View):
    def __init__(self, board_id, list_id):
        super().__init__(timeout=120)
        self.board_id = board_id
        self.list_id = list_id

        cards = TrelloLookup.get_card(list_id)
        options = [
            discord.SelectOption(
                label=c["name"],
                description=f"카드 ID: {c['id']}"
            )
            for c in cards
        ]
        self.add_item(CardDropdownForPrefix(cards, board_id))


class CardDropdownForPrefix(discord.ui.Select):
    def __init__(self, cards, board_id):
        self.cards = cards
        self.board_id = board_id

        options = [
            discord.SelectOption(
                label=card["name"],
                description=f"카드 ID: {card['id']}"
            )
            for card in cards
        ]

        super().__init__(
            placeholder="접두사로 쓸 카드를 선택하세요.",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        prefix_card_name = self.values[0]

        await interaction.response.send_modal(
            CardNameInputModal(self.board_id, prefix_card_name)
        )

# ✅ 카드 이름 입력 Modal
class CardNameInputModal(discord.ui.Modal, title="새 카드 이름들 입력(쉼표로 구분)"):
    def __init__(self, board_id, prefix_card_name):
        super().__init__(timeout=300)
        self.board_id = board_id
        self.prefix = prefix_card_name

        self.card_names_input = discord.ui.TextInput(
            label="새 카드 이름들 (쉼표로 구분)",
            placeholder="예) 할일1, 할일2, 할일3",
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.card_names_input)

    async def on_submit(self, interaction: discord.Interaction):
        # final_name = f"{self.prefix} {self.card_name_input.value}"
        raw_input = self.card_names_input.value
        names = [n.strip() for n in raw_input.split(",") if n.strip()]

        if not names:
            return await interaction.response.send_message(
                "❌ 카드 이름을 입력하지 않았습니다.",
                ephemeral=True
            )
        await interaction.response.send_message(
            # f"✅ 카드 이름이 `{final_name}`으로 설정되었습니다.\n생성할 리스트를 선택하세요.",
            f"✅ {len(names)}개의 카드 이름을 입력했습니다.\n생성할 리스트를 선택하세요.",
            view=TargetListViewForCardCreate(self.board_id, names, self.prefix),
            ephemeral=True
        )


# ✅ 생성할 리스트 선택
class TargetListSelectForCardCreate(discord.ui.Select):
    def __init__(self, board_id, names, prefix):
        self.board_id = board_id
        self.names = names
        self.prefix = prefix

        lists = TrelloLookup.get_lists(board_id)
        options = [
            discord.SelectOption(
                label=l["name"],
                description=f"리스트 ID: {l['id']}"
            )
            for l in lists
        ]

        super().__init__(
            placeholder="카드를 생성할 리스트를 선택하세요.",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_list = next(
            l for l in TrelloLookup.get_lists(self.board_id) if l["name"] == self.values[0]
        )
        list_id = selected_list["id"]

        created_urls = []
        for name in self.names:
            final_name = f"{self.prefix} {name}"
            created = TrelloLookup.create_card(final_name, list_id)
            created_urls.append(f" - [{created.get('name')}]({created.get('url')})")

        await interaction.response.send_message(
            f"✅ 총 {len(created_urls)}개의 카드 생성 완료:\n" + "\n".join(created_urls),
            ephemeral=True
        )

class TargetListViewForCardCreate(discord.ui.View):
    def __init__(self, board_id, names, prefix):
        super().__init__(timeout=60)
        self.add_item(TargetListSelectForCardCreate(board_id, names, prefix))



# Cog 등록
async def setup(bot):
    await bot.add_cog(CardMoveView(bot))
