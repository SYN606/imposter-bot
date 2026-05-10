import time
import platform
from datetime import datetime
import discord
import psutil
from discord.ext import commands
from config.emojis import EMOJIS


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    def get_ping_status(self, ping: float):
        if ping < 100:
            return (EMOJIS["green_dot"], "Excellent")

        elif ping < 200:
            return (EMOJIS["success"], "Good")

        elif ping < 400:
            return (EMOJIS["warning"], "Average")

        return (EMOJIS["red_dot"], "Poor")

    def get_uptime(self):
        delta = datetime.utcnow() - self.start_time

        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{days}d {hours}h {minutes}m {seconds}s"

    @commands.hybrid_command(
        name="ping", description="Displays bot latency and system statistics."
    )
    async def ping(self, ctx: commands.Context):

        async with ctx.typing():
            start = time.perf_counter()

            loading_message = await ctx.send(
                f"{EMOJIS['rounded_loading']} Measuring bot latency..."
            )
            end = time.perf_counter()

            # Latencies
            api_latency = round(self.bot.latency * 1000, 2)
            message_latency = round((end - start) * 1000, 2)

            # System Stats
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent

            # Status
            status_emoji, status_text = self.get_ping_status(api_latency)
            embed = discord.Embed(
                title=(f"{EMOJIS['ping']} Pong!"),
                description=(
                    f"{status_emoji} Current bot performance status: **{status_text}**"
                ),
                color=0x22D3EE,
            )
            embed.add_field(
                name=(f"{EMOJIS['arrow_point']} API Latency"),
                value=f"`{api_latency}ms`",
                inline=True,
            )
            embed.add_field(
                name=(f"{EMOJIS['message']} Message Latency"),
                value=f"`{message_latency}ms`",
                inline=True,
            )
            embed.add_field(
                name=(f"{EMOJIS['developer']} CPU Usage"),
                value=f"`{cpu_usage}%`",
                inline=True,
            )
            embed.add_field(
                name=(f"{EMOJIS['boost']} RAM Usage"),
                value=f"`{ram_usage}%`",
                inline=True,
            )
            embed.add_field(
                name=(f"{EMOJIS['announcement']} Uptime"),
                value=f"`{self.get_uptime()}`",
                inline=True,
            )
            embed.add_field(
                name=(f"{EMOJIS['github']} Python"),
                value=f"`{platform.python_version()}`",
                inline=True,
            )
            embed.set_footer(text=(f"{self.bot.user.name} • System Operational"))
            embed.timestamp = discord.utils.utcnow()
            await loading_message.edit(content=None, embed=embed)


async def setup(bot):
    await bot.add_cog(Ping(bot))
