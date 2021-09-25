from __future__ import annotations

from core import Parrot, Cog
from utilities.database import parrot_db, ticket_update
import discord
from datetime import datetime

collection = parrot_db['ticket']


class OnReaction(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot: Parrot):
        self.bot = bot

    async def log(self, guild, channel, description, status):
        embed = discord.Embed(title='Parrot Ticket Bot',
                              timestamp=datetime.utcnow(),
                              description=f"```\n{description}\n```",
                              color=discord.Color.blue())
        embed.add_field(name='Status', value=status)
        embed.set_footer(text=f"{guild.name}")
        await channel.send(embed=embed)

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        pass

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        guild = self.bot.get_guild(guild_id)
        data = await collection.find_one({'_id': guild_id})
        if not data:
            return
        user_id = payload.user_id
        member = guild.get_member(user_id)
        if member.bot:
            return
        channel_id = payload.channel_id
        channel = self.bot.get_channel(channel_id)

        message_id = payload.message_id
        emoji = payload.emoji.name

        if message_id == data['message_id'] and channel_id == data[
                'channel_id']:
            message = await channel.fetch_message(message_id)
        else:
            return
        if (message is not None) and (emoji == '✉️'):
            try:
                await message.remove_reaction("✉️", member)
            except Exception:
                return await channel.send(
                    'Missing Manage Message permisssion to work properly',
                    delete_after=10)

            ticket_number = data['ticket-counter'] + 1
            cat = guild.get_channel(data['category'])

            ticket_channel = await guild.create_text_channel(
                "ticket-{}".format(ticket_number), category=cat)
            await ticket_channel.set_permissions(guild.get_role(guild.id),
                                                 send_messages=False,
                                                 read_messages=False,
                                                 view_channel=False)

            for role_id in data["valid-roles"]:
                role = guild.get_role(role_id)

                await ticket_channel.set_permissions(role,
                                                     send_messages=True,
                                                     read_messages=True,
                                                     add_reactions=True,
                                                     embed_links=True,
                                                     attach_files=True,
                                                     read_message_history=True,
                                                     external_emojis=True)

            await ticket_channel.set_permissions(member,
                                                 send_messages=True,
                                                 read_messages=True,
                                                 add_reactions=True,
                                                 embed_links=True,
                                                 attach_files=True,
                                                 read_message_history=True,
                                                 external_emojis=True)

            em = discord.Embed(
                title="New ticket from {}#{}".format(member.name,
                                                     member.discriminator),
                description="{}".format('Pls wait while you reach you'),
                color=0x00a8ff)

            await ticket_channel.send(embed=em)
            await ticket_channel.send("To close the ticket, type `[p]close`")
            await ticket_channel.send(
                "To save the ticket transcript, type `[p]save`")
            await ticket_channel.send(f'{member.mention}', delete_after=2)
            pinged_msg_content = ""
            non_mentionable_roles = []
            if data["pinged-roles"]:
                for role_id in data["pinged-roles"]:
                    role = guild.get_role(role_id)
                    pinged_msg_content += role.mention
                    pinged_msg_content += " "
                    if role.mentionable:
                        pass
                    else:
                        await role.edit(mentionable=True)
                        non_mentionable_roles.append(role)
                await ticket_channel.send(pinged_msg_content)
                for role in non_mentionable_roles:
                    await role.edit(mentionable=False)

            ticket_channel_ids = data["ticket-channel-ids"]
            ticket_channel_ids.append(ticket_channel.id)
            post = {
                'ticket-counter': ticket_number,
                'ticket-channel-ids': ticket_channel_ids
            }
            await ticket_update(guild.id, post)

            log_channel = guild.get_channel(data['log'])
            await self.log(
                guild, log_channel,
                f"ticket-{ticket_number} opened by, {member.name}#{member.discriminator} ({member.id})",
                'RUNNING')

    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        pass

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        pass

    @Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        pass

    @Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        pass

    @Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        pass

    @Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        pass


def setup(bot):
    bot.add_cog(OnReaction(bot))
