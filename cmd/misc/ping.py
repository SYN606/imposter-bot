from discord.ext import commands
import discord

from utils.respond import Respond
from config.emojis import EMOJIS


async def run(bot, target):
    latency = round(bot.latency * 1000)

    r = Respond(**target)

    # dynamic latency indicator
    if latency < 100:
        status = f"{EMOJIS.get('green_dot')} Excellent"
    elif latency < 200:
        status = f"{EMOJIS.get('warning')} Good"
    else:
        status = f"{EMOJIS.get('red_dot')} Slow"

    await r.send(
        title="Pong",
        description=f"Latency: `{latency}ms`\nStatus: {status}",
        level="SUCCESS",
        footer="Imposter • Network Diagnostics",
        use_emoji=True,
        separator=True,
    )


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_prefix(self, ctx):
        await run(self.bot, {"ctx": ctx})

    @discord.app_commands.command(name="ping", description="Check bot latency")
    async def ping_slash(self, interaction: discord.Interaction):
        await run(self.bot, {"interaction": interaction})


async def setup(bot):
    await bot.add_cog(Ping(bot))