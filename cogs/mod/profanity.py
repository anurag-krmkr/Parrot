from __future__ import annotations
import asyncio
from typing import Any, List, Optional

from discord.ext import tasks
import discord
import random
import re
from utilities.database import parrot_db
from utilities.infraction import warn
from core import Parrot, Cog, Context

with open("extra/duke_nekum.txt") as f:
    quotes = f.read().split("\n")


class Profanity(Cog):
    def __init__(self, bot: Parrot) -> None:
        self.bot = bot
        self.collection = parrot_db["server_config"]
        self.data = {}
        self.update_data.start()
        self.lock = asyncio.Lock()

    async def get_bad_words(self, message) -> Optional[List[str]]:
        try:
            return self.data[message.guild.id]
        except KeyError:
            return []

    def cog_unload(self) -> None:
        self.update_data.cancel()

    def isin(self, phrase: str, sentence: str) -> bool:
        word = re.escape(phrase)
        pattern = rf"\b{word}\b"
        return re.search(pattern, sentence) is not None

    async def _one_message_passive(self, message: discord.Message) -> Any:
        if message.author.bot or (not message.guild):
            return
        perms = message.author.guild_permissions

        if perms.administrator or perms.manage_messages or perms.manage_channels:
            return
        bad_words = await self.get_bad_words(message)

        if data := await self.collection.find_one(
            {"_id": message.guild.id, "automod.profanity.enable": {"$exists": True}}
        ):
            try:
                profanity = data["automod"]["profanity"]["enable"]
            except KeyError:
                return
            try:
                ignore = data["automod"]["profanity"]["channel"]
            except KeyError:
                ignore = []

            if ignore and (message.channel.id in ignore):
                return

            if (not bad_words) and profanity:
                try:
                    bad_words = data["automod"]["profanity"]["words"]
                except KeyError:
                    return

            if not bad_words:
                return

            try:
                to_delete = data["automod"]["profanity"]["autowarn"]["to_delete"]
            except KeyError:
                to_delete = True

            if to_delete:
                await message.delete(delay=0)

            try:
                to_warn = data["automod"]["profanity"]["autowarn"]["enable"]
            except KeyError:
                to_warn = False

            if to_warn:
                await warn(
                    message.guild,
                    message.author,
                    "Automod: Bad words usage",
                    moderator=self.bot.user,
                    message=message,
                    at=message.created_at,
                )
                ctx: Context = await self.bot.get_context(message, cls=Context)
                await self.bot.get_cog("Moderator").warn_task(target=message.author, ctx=ctx)

            if any(self.isin(word, message.content.lower()) for word in bad_words):
                await message.channel.send(
                    f"{message.author.mention} *{random.choice(quotes)}* **[Blacklisted Word] {'[Warning]' if to_warn else ''}**",
                    delete_after=10,
                )

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._one_message_passive(message)

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self._one_message_passive(after)

    def cog_unload(self):
        self.update_data.cancel()

    @tasks.loop(seconds=15)
    async def update_data(self):
        async with self.lock:
            async for data in self.collection.find({}):
                try:
                    bad_words = data["automod"]["profanity"]["words"]
                except KeyError:
                    return
                self.data[data["_id"]] = bad_words

    @update_data.before_loop
    async def before_data_update(self):
        await self.bot.wait_until_ready()
