from discord.ext import commands
import discord
import time

from utils.respond import Respond
from config.emojis import EMOJIS


async def run(bot, target):
    r = Respond(**target)

    start = time.perf_counter()

    try:
        # ========================
        # SAFE TRIGGER
        # ========================
        if target.get("ctx"):
            await target["ctx"].trigger_typing()

        elif target.get("interaction"):
            interaction = target["interaction"]

            if not interaction.response.is_done():
                await interaction.response.defer()

    except Exception as e:
        print(f"[PING TRIGGER ERROR] {e}")

    end = time.perf_counter()

    api_latency = round((end - start) * 1000)
    ws_latency = round(bot.latency * 1000)

    avg = (api_latency + ws_latency) // 2

    if avg < 100:
        status = f"{EMOJIS.get('green_dot')} Excellent"
    elif avg < 200:
        status = f"{EMOJIS.get('warning')} Good"
    else:
        status = f"{EMOJIS.get('red_dot')} Slow"

    try:
        await r.send(
            title="Pong",
            description=str(avg),
            highlight=True,
            level="SUCCESS",
            fields=[
                ("WebSocket", f"`{ws_latency} ms`", True),
                ("API", f"`{api_latency} ms`", True),
                ("Status", status, False),
            ],
            footer="Imposter • Network Diagnostics",
        )

    except Exception as e:
        # ========================
        # FAILSAFE (CRITICAL)
        # ========================
        print(f"[RESPOND FAIL] {e}")

        if target.get("ctx"):
            await target["ctx"].send(f"Pong: {avg} ms")

        elif target.get("interaction"):
            interaction = target["interaction"]

            if interaction.response.is_done():
                await interaction.followup.send(f"Pong: {avg} ms")
            else:
                await interaction.response.send_message(f"Pong: {avg} ms")


class Ping(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================
    # PREFIX
    # ========================
    @commands.command(name="ping")
    @commands.cooldown(3, 15, commands.BucketType.user)
    async def ping_prefix(self, ctx):
        await run(self.bot, {"ctx": ctx})

    # ========================
    # SLASH
    # ========================
    @discord.app_commands.command(name="ping", description="Check bot latency")
    @discord.app_commands.checks.cooldown(3, 15.0)
    async def ping_slash(self, interaction: discord.Interaction):
        await run(self.bot, {"interaction": interaction})

    # ========================
    # ERROR HANDLING
    # ========================
    @ping_prefix.error
    async def prefix_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            r = Respond(ctx=ctx)
            await r.warning(
                "Cooldown",
                f"Try again in `{round(error.retry_after)}s`"
            )

    @ping_slash.error
    async def slash_error(self, interaction, error):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            r = Respond(interaction=interaction)
            await r.warning(
                "Cooldown",
                f"Try again in `{round(error.retry_after)}s`"
            )


async def setup(bot):
    await bot.add_cog(Ping(bot))