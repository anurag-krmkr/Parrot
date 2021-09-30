from __future__ import annotations

import discord
from discord.ext import commands

from utilities.paginator import Paginator
from utilities.config import DEV_LOGO
from core import Parrot, Cog
from cogs.help.method import common_command_formatting, get_command_signature

ignored = ('jishaku', 'rtfm', 'helpcog', 'owner', 'utility')
owner_url = "[Made by Ritik Ranjan](https://discord.com/users/741614468546560092)"


class HelpCommand(commands.HelpCommand):
    """Shows help about the bot, a command, or a category"""
    def __init__(self, *args, **kwargs):
        super().__init__(command_attrs={
            'help':
            'Shows help about the bot, a command, or a category'
        },
                         **kwargs)

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))

    async def send_command_help(self, command):
        embed = discord.Embed(colour=discord.Colour(0x55ddff))
        common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        change_log_msg = await bot.change_log

        em_list = []

        description = f"```ini\n[Default '@Parrot#9209']\n```"

        embed = discord.Embed(color=discord.Colour(0x55ddff))

        embed.set_author(
            name=
            f"Server: {self.context.guild.name or self.context.author.name}",
            icon_url=self.context.guild.icon.url or self.context.me.avatar.url)

        embed.description = description + f"**Important Links**\n• [Invite the bot]({bot.invite})\n• [Support Server]({bot.support_server})\n• [Bot is Open Source]({bot.github})\n• {owner_url}"
        embed.set_thumbnail(url=self.context.me.avatar.url)
        CATEGORY = '\n'
        for cog in mapping:
            if cog and cog.get_commands():
                if cog.qualified_name.lower() in ignored:
                    pass
                else:
                    CATEGORY = CATEGORY + str(
                        cog.qualified_name).upper() + '\n'
        embed.add_field(name="Categories", value=f"```{CATEGORY}```")
        embed.add_field(
            name="Latest News",
            value=
            f"{change_log_msg.content[:512:]}... [Read More]({change_log_msg.jump_url})"
        )
        embed.set_footer(text=f"Page 1/{10} | Built with ❤️ and `discord.py`",
                         icon_url=f"{DEV_LOGO}")

        em_list.append(embed)
        i = 1
        for cog, cmds in mapping.items():
            if cog and cog.get_commands():
                if cog.qualified_name.lower() in ignored: pass
                else:
                    em = discord.Embed(
                        description=
                        f"```ini\n[{cog.description if cog.description else 'No help available :('}]\n```\n"
                        f"**Commands**```\n{', '.join([cmd.name for cmd in cmds])}\n```",
                        color=discord.Colour(0x55ddff))
                    em.set_author(name=f"COG: {str(cog).upper()}")
                    em.set_footer(
                        text=
                        f"Page {i+1}/{10} | Built with ❤️ and `discord.py`",
                        icon_url=f"{DEV_LOGO}")
                    em_list.append(em)
                    em.set_thumbnail(url=self.context.me.avatar.url)
                    i += 1

        paginator = Paginator(pages=em_list)
        await paginator.start(self.context)

    async def send_group_help(self, group):

        em_list = []
        cmds = list(group.commands)

        e = discord.Embed(
            title=
            f"Help with group {group.name}{' | ' if group.aliases else ''}{' | '.join(group.aliases) if group.aliases else ''}",
            color=discord.Colour(0x55ddff),
            description=
            f"Sub commands\n```\n{', '.join([cmd.name for cmd in cmds])}\n```")

        e.set_footer(
            text=f"Page 1/{len(cmds)+1} | Built with ❤️ and `discord.py`",
            icon_url=f"{DEV_LOGO}")
        e.set_thumbnail(url=self.context.me.avatar.url)
        em_list.append(e)

        i = 1
        for cmd in cmds:
            e = discord.Embed(
                title=f"Help with {cmd.qualified_name}",
                description=
                f"```{cmd.help if cmd.help else 'No description.'}```\n",
                color=discord.Colour(0x55ddff))
            e.add_field(
                name="Usage",
                value=
                f"```\n[p]{group.qualified_name}{'|' if group.aliases else ''}{'|'.join(group.aliases) if group.aliases else ''} {cmd.name}{'|' if cmd.aliases else ''}{'|'.join(cmd.aliases if cmd.aliases else '')} {cmd.signature}\n```",
                inline=False)
            e.add_field(
                name="Aliases",
                value=
                f"```\n{', '.join(group.aliases) if group.aliases else 'NA'}\n```",
                inline=False)
            e.set_footer(
                text=
                f"Page {i+1}/{len(cmds)+1} | Built with ❤️ and `discord.py`",
                icon_url=f"{DEV_LOGO}")
            em_list.append(e)
            e.set_thumbnail(url=self.context.me.avatar.url)
            i += 1

        paginator = Paginator(pages=em_list)
        await paginator.start(self.context)

    async def send_cog_help(self, cog):

        em_list = []

        embed = discord.Embed(
            title=f'{str(cog.qualified_name).capitalize()} Commands',
            description=
            f"```\n{cog.description if cog.description else 'NA'}\n```\nCommands\n```\n{', '.join([cmd.name for cmd in cog.get_commands()])}\n```",
            color=discord.Colour(0x55ddff))
        embed.set_footer(
            text=
            f"Page 1/{len(cog.get_commands())+1} | Built with ❤️ and `discord.py`",
            icon_url=f"{DEV_LOGO}")
        em_list.append(embed)
        i = 1
        for cmd in cog.get_commands():
            if cog.get_commands():
                if cmd.hidden: pass
                else:
                    em = discord.Embed(title=f"Help with {cmd.name}",
                                       description=f"```\n{cmd.help}\n```",
                                       color=discord.Colour(0x55ddff))
                    em.add_field(
                        name=f"Usage",
                        value=f"```\n{get_command_signature(cmd)}\n```")
                    em.add_field(
                        name="Aliases",
                        value=
                        f"```\n{', '.join(cmd.aliases if cmd.aliases else 'NA')}\n```"
                    )

                    em.set_footer(
                        text=
                        f"Page {i+1}/{len(cog.get_commands())+1} | Built with ❤️ and `discord.py`"
                    )
                    em_list.append(em)
                    i += 1

        paginator = Paginator(pages=em_list)
        await paginator.start(self.context)


class HelpCog(Cog):
    """Shows help about the bot, a command, or a category"""
    def __init__(self, bot: Parrot):
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command