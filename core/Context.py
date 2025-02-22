from __future__ import annotations

from discord.ext import commands
import discord
import asyncio
import io
import functools
from utilities.emotes import emojis
from typing import Literal, Optional, Union, List, Tuple, Any
from utilities.log import get_logger


__all__ = ("Context",)

CONFIRM_REACTIONS = (
    "\N{THUMBS UP SIGN}",
    "\N{THUMBS DOWN SIGN}",
)

class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        reacquire: bool,
        ctx: Context,
        delete_after: bool,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.ctx: Context = ctx
        self.reacquire: bool = reacquire
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "This confirmation dialog is not for you.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        if self.reacquire:
            await asyncio.sleep(0)
        if self.delete_after and self.message:
            await self.message.delete(delay=0)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()


class Context(commands.Context):
    """A custom implementation of commands.Context class."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        # we need this for our cache key strategy
        return f"<core.{self.bot.user.name} Context>"

    @property
    def session(self) -> Any:
        return self.bot.session

    async def modlog(self, *, guild_id: int=None) -> Optional[discord.TextChannel]:
        guild_id = guild_id or self.guild.id
        try:
            return await self.bot.getch(
                self.bot.get_channel,
                self.bot.fetch_channel,
                self.bot.server_config[self.guild.id]["action_log"]
            )
        except KeyError:
            if data := await self.bot.mongo.parrot_db.server_config.find_one({"_id": guild_id}):
                return await self.bot.getch(
                    self.bot.get_channel,
                    self.bot.fetch_channel,
                    self.bot.server_config[self.guild.id]["action_log"]
                )

    async def muterole(self,) -> Optional[discord.Role]:
        try:
            global_muted = discord.utils.find(lambda m: m.name.lower() == "muted", self.guild.roles)
            author_muted = discord.utils.find(lambda m: m.name.lower() == "muted", self.author.roles)
            return self.guild.get_role(
                self.bot.server_config[self.guild.id]["mute_role"]
            ) or global_muted or author_muted
        except KeyError:
            if data := await self.bot.mongo.parrot_db.server_config.find_one({"_id": self.guild.id}):
                return self.guild.get_role(
                    self.bot.server_config[self.guild.id]["mute_role"]
                )
    
    async def modrole(self,) -> Optional[discord.Role]:
        try:
            return self.guild.get_role(
                self.bot.server_config[self.guild.id]["mod_role"]
            )
        except KeyError:
            if data := await self.bot.mongo.parrot_db.server_config.find_one({"_id": self.guild.id}):
                return self.guild.get_role(
                    self.bot.server_config[self.guild.id]["mod_role"]
                )

    @discord.utils.cached_property
    def replied_reference(self) -> Optional[discord.Message]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    def with_type(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            await func(*args, **kwargs)

            # context = args[0] if isinstance(args[0], commands.Context) else args[1]
            # try:
            #     async with context.typing():
            #         await func(*args, **kwargs)
            # except discord.Forbidden:
            #     pass

        return wrapped

    async def send(
        self, content: Optional[str] = None, **kwargs
    ) -> Optional[discord.Message]:
        perms = self.channel.permissions_for(self.me)
        if not (perms.send_messages and perms.embed_links):
            try:
                await self.author.send(
                    "Bot don't have either Embed Links/Send Messages permission in that channel. "
                    "Please give sufficient permissions to the bot."
                )
            except discord.Forbidden as e:
                pass
            return

        return await super().send(content, **kwargs)

    async def reply(
        self, content: Optional[str] = None, **kwargs
    ) -> Optional[discord.Message]:
        perms = self.channel.permissions_for(self.me)
        if not (perms.send_messages and perms.embed_links):
            try:
                await self.author.send(
                    "Bot don't have either Embed Links/Send Messages permission in that channel. "
                    "Please give sufficient permissions to the bot."
                )
            except discord.Forbidden as e:
                pass
            return
        try:
            return await self.send(content, reference=kwargs.get("referenve") or self.message, **kwargs)
        except discord.HTTPException:  # message deleted
            return await self.send(content, **kwargs)

        # return await super().reply(content, **kwargs)

    async def entry_to_code(self, entries: List[Tuple[Any, Any]]) -> Optional[discord.Message]:
        width = max(len(str(a)) for a, b in entries)
        output = ["```"]
        for name, entry in entries:
            output.append(f"{name:<{width}}: {entry}")
        output.append("```")
        await self.send("\n".join(output))

    async def indented_entry_to_code(self, entries: List[Tuple[Any, Any]]) -> Optional[discord.Message]:
        width = max(len(str(a)) for a, b in entries)
        output = ["```"]
        for name, entry in entries:
            output.append(f"\u200b{name:>{width}}: {entry}")
        output.append("```")
        await self.send("\n".join(output))

    async def emoji(self, emoji: str) -> str:
        return emojis[emoji]

    async def prompt(
        self,
        message: str,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        reacquire: bool = True,
        author_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[bool]:
        """|coro|

        An interactive reaction confirmation dialog.
        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        reacquire: bool
            Whether to release the database connection and then acquire it
            again when we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """
        author_id = author_id or self.author.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            reacquire=reacquire,
            ctx=self,
            author_id=author_id,
        )
        view.message = await self.send(message, view=view, **kwargs)
        await view.wait()
        return view.value

    async def release(self, *, _for: Optional[int]=None) -> None:
        await asyncio.sleep(_for or 0)

    async def safe_send(
        self, content, *, escape_mentions=True, **kwargs
    ) -> Optional[discord.Message]:
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop("file", None)
            return await self.send(
                file=discord.File(fp, filename="message_too_long.txt"), **kwargs
            )  # must have `Attach Files` permissions
        return await self.send(content)

    async def bulk_add_reactions(
        self, message: discord.Message, *reactions: Union[discord.Emoji, str]
    ) -> None:
        coros = [
            asyncio.ensure_future(message.add_reaction(reaction))
            for reaction in reactions
        ]
        await asyncio.wait(coros)

    async def confirm(
        self,
        channel: discord.TextChannel,
        user: Union[discord.Member, discord.User],
        *args: Any,
        timeout: float = 60,
        delete_after: bool = False,
        **kwargs: Any,
    ) -> Optional[bool]:
        """|coro|
        
        Reaction based Prompt
        Parameters
        -----------
        channel: Channel
            Message that will be sent in the channel
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        user: Union[Member, User]
            The member who should respond to the prompt.
        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``None`` if deny due to timeout
        """

        message = await channel.send(*args, **kwargs)
        await self.bulk_add_reactions(message, *CONFIRM_REACTIONS)

        def check(payload: discord.RawReactionActionEvent) -> bool:
            return (
                payload.message_id == message.id
                and payload.user_id == user.id
                and str(payload.emoji) in CONFIRM_REACTIONS
            )

        try:
            payload = await self.bot.wait_for(
                "raw_reaction_add", check=check, timeout=timeout
            )
            return str(payload.emoji) == "\N{THUMBS UP SIGN}"
        except asyncio.TimeoutError:
            return None
        finally:
            if delete_after:
                await message.delete(delay=0)
