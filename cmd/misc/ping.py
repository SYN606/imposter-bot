from discord.ext import commands
import discord

from utils.respond import Respond


async def run(bot, target):
    latency = round(bot.latency * 1000)

    r = Respond(**target)

    await r.success("Pong", f"Latency: `{latency}ms`")


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # prefix command
    @commands.command(name="ping")
    async def ping_prefix(self, ctx):
        await run(self.bot, {"ctx": ctx})

    # slash command
    @discord.app_commands.command(name="ping", description="Check bot latency")
    async def ping_slash(self, interaction: discord.Interaction):
        await run(self.bot, {"interaction": interaction})


async def setup(bot):
    await bot.add_cog(Ping(bot))
