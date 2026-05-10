import random

import discord
from discord.ext import commands, tasks


class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.activities = [
            discord.Game(name="inside unsecured networks"),
            discord.Activity(
                type=discord.ActivityType.watching, name="every connection"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="encrypted traffic"
            ),
            discord.Activity(
                type=discord.ActivityType.playing, name="with reconnaissance systems"
            ),
            discord.CustomActivity(name="Some traces never disappear."),
            discord.CustomActivity(name="Monitoring exposed targets..."),
            discord.CustomActivity(name="Threat surface detected."),
            discord.CustomActivity(name="Nothing stays hidden forever."),
            discord.CustomActivity(name="Powered by SYN606"),
        ]

    async def cog_load(self):

        self.rotate_presence.start()

    async def cog_unload(self):

        self.rotate_presence.cancel()

    # Safe interval for Discord API
    @tasks.loop(hours=1)
    async def rotate_presence(self):

        if not self.bot.is_ready():
            return

        try:
            await self.bot.change_presence(
                status=discord.Status.idle, activity=random.choice(self.activities)
            )

        except Exception:
            pass

    @rotate_presence.before_loop
    async def before_rotate_presence(self):

        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Presence(bot))
