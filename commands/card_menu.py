# commands/card_menu.py

import discord
from discord.ext import commands
from trello.trello_lookup import TrelloLookup
from commands.card_move_view import ListSelectViewForMove, ListSelectViewForCardCreate, ListSelectViewForAssign, ListSelectViewForComplete

# Step 1: 보드 선택
class BoardSelect(discord.ui.Select):
    def __init__(self, actions):
        boards = TrelloLookup.get_all_boards()
        options = [
            discord.SelectOption(label=b["name"], value=b["id"])
            for b in boards
        ]
        self.actions = actions
        super().__init__(
            placeholder="보드를 선택하세요.",
            min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=ActionSelectView(self.values[0], self.actions),
            ephemeral=True
        )

class BoardSelectView(discord.ui.View):
    def __init__(self, actions):
        super().__init__(timeout=60)
        self.add_item(BoardSelect(actions))


# Step 2: 기능 선택
class ActionSelect(discord.ui.Select):
    def __init__(self, board_id, actions):
        self.board_id = board_id
        options = [
            discord.SelectOption(label=label, description=desc)
            for label, desc in actions.items()
        ]
        super().__init__(
            placeholder="실행할 기능을 선택하세요.",
            min_values=1, max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "카드 이동":
            await interaction.response.send_message(
                f"📦 `{selected}` 기능 실행:",
                view=ListSelectViewForMove(self.board_id), ephemeral=True)

        elif selected == "카드 완료":
            await interaction.response.send_message(
                f"✅ `{selected}` 기능 실행:",
                view=ListSelectViewForComplete(self.board_id), ephemeral=True)

        elif selected == "카드 담당":
            await interaction.response.send_message(
                f"👤 `{selected}` 기능 실행:",
                view=ListSelectViewForAssign(self.board_id), ephemeral=True)

        elif selected == "카드 생성":
            await interaction.response.send_message(
                f"📝 `{selected}` 기능 실행:",
                view=ListSelectViewForCardCreate(self.board_id), ephemeral=True)

class ActionSelectView(discord.ui.View):
    def __init__(self, board_id, actions):
        super().__init__(timeout=60)
        self.add_item(ActionSelect(board_id, actions))


# Cog 등록
class CardMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="카드메뉴")
    async def card_menu(self, ctx):
        actions = {
            "카드 이동": "카드를 다른 리스트로 이동",
            "카드 완료": "카드를 완료 처리하고 DONE으로 이동",
            "카드 담당": "카드에 본인을 담당자로 할당",
            "카드 생성": "카드를 생성"
        }
        await ctx.send("📋 보드를 먼저 선택하세요:", view=BoardSelectView(actions))


async def setup(bot):
    await bot.add_cog(CardMenu(bot))
