from __future__ import annotations

from .config import botconfig
from core import Parrot


def setup(bot: Parrot):
    bot.add_cog(botconfig(bot))
