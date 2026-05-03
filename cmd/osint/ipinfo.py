from discord.ext import commands
import discord
import aiohttp
import asyncio
import re

from utils.respond import Respond
from config.emojis import EMOJIS
from utils.permissions import check

IP_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


class IPInfo(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

        # GLOBAL COOLDOWN (for slash/manual use)
        self.global_cooldown = commands.CooldownMapping.from_cooldown(
            5, 60, commands.BucketType.default)

        # Prevent concurrent spam
        self.lock = asyncio.Lock()

    async def cog_load(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout, headers={"User-Agent": "ImposterBot/1.0"})

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # SAFE EMOJI FETCH
    def e(self, key):
        return EMOJIS.get(key) or ""

    # FETCH DATA
    async def fetch(self, ip: str):
        if not self.session:
            return None

        url = f"https://ipinfo.io/{ip}/json"

        try:
            async with self.session.get(url) as res:  # type: ignore

                if res.status == 429:
                    retry = res.headers.get("Retry-After")
                    return {
                        "rate_limited": True,
                        "retry_after": int(retry) if retry else 30
                    }

                if res.status != 200:
                    return None

                return await res.json()

        except asyncio.TimeoutError:
            return {"timeout": True}

        except Exception as e:
            print(f"[IPINFO FETCH ERROR] {e}")
            return None

    # FALLBACK RESPONSE
    async def fallback(self, target, msg: str):
        if target.get("ctx"):
            await target["ctx"].send(msg)

        elif target.get("interaction"):
            interaction = target["interaction"]

            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    # CORE LOGIC
    async def run(self, target, ip: str):
        r = Respond(**target)

        # SAFE DEFER
        if target.get("interaction"):
            interaction: discord.Interaction = target["interaction"]
            if not interaction.response.is_done():
                await interaction.response.defer()

        # PERMISSION CHECK
        allowed = await check(ctx=target.get("ctx"),
                              interaction=target.get("interaction"),
                              perms=None)

        if not allowed:
            return

        # VALIDATION
        if not IP_REGEX.match(ip):
            return await r.error("Invalid Input",
                                 "Provide a valid IPv4 address")

        # Prevent spam / race conditions
        async with self.lock:
            data = await self.fetch(ip)

        if not data:
            return await self.fallback(target, "Failed to fetch data")

        if data.get("timeout"):
            return await r.warning("Timeout", "API took too long")

        if data.get("rate_limited"):
            retry = data.get("retry_after", 30)
            return await r.warning(
                "API Rate Limited",
                f"Service is throttling requests. Retry in {retry}s")

        if data.get("bogon"):
            return await r.error("Invalid IP", "Private or reserved IP")

        try:
            ip_addr = data.get("ip", "N/A")
            city = data.get("city", "N/A")
            region = data.get("region", "N/A")
            country = data.get("country", "N/A")
            org = data.get("org", "N/A")
            loc = data.get("loc", "N/A")
            timezone = data.get("timezone", "N/A")

            map_link = (f"https://www.google.com/maps?q={loc}"
                        if loc != "N/A" else None)

            await r.send(
                title="IP Intelligence",
                description=ip_addr,
                highlight=True,
                level="INFO",
                fields=[
                    (("Location", ""), f"{city}, {region}, {country}", False),
                    (("ISP / Org", ""), org, False),
                    (("Coordinates", ""), loc, True),
                    (("Timezone", ""), timezone, True),
                    (("Map", ""),
                     f"[Open Map]({map_link})" if map_link else "N/A", False),
                ],
                footer="Imposter OSINT",
            )

        except Exception as e:
            print(f"[IPINFO ERROR] {e}")
            await self.fallback(target, "Something went wrong")

    # PREFIX COMMAND
    @commands.command(name="ipinfo")
    @commands.cooldown(2, 30, commands.BucketType.user)
    @commands.cooldown(5, 60, commands.BucketType.default)  # GLOBAL
    async def ipinfo_prefix(self, ctx: commands.Context, ip: str = None): # type: ignore
        r = Respond(ctx=ctx)

        if not ip:
            return await r.info("Usage", "ipinfo <ip_address>")

        await self.run({"ctx": ctx}, ip)

    # SLASH COMMAND
    @discord.app_commands.command(
        name="ipinfo", description="Get information about an IP address")
    @discord.app_commands.checks.cooldown(2, 30.0)
    async def ipinfo_slash(self, interaction: discord.Interaction, ip: str):
        # GLOBAL COOLDOWN CHECK
        bucket = self.global_cooldown.get_bucket(interaction)
        retry_after = bucket.update_rate_limit() # type: ignore

        if retry_after:
            r = Respond(interaction=interaction)
            return await r.warning(
                "Global Cooldown",
                f"Bot is busy. Try again in {round(retry_after)}s")

        await self.run({"interaction": interaction}, ip)

    # ERROR HANDLING
    @ipinfo_prefix.error
    async def prefix_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandOnCooldown):
            r = Respond(ctx=ctx)
            msg = f"You're going too fast. Try again in {round(error.retry_after)}s"
            await r.warning("Slow down", msg)

    @ipinfo_slash.error
    async def slash_error(self, interaction: discord.Interaction,
                          error: Exception):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            r = Respond(interaction=interaction)
            msg = f"You're going too fast. Try again in {round(error.retry_after)}s"
            await r.warning("Slow down", msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(IPInfo(bot))
