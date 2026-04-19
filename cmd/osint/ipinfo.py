from discord.ext import commands
import discord
import aiohttp
import asyncio
import re

from utils.respond import Respond
from config.emojis import EMOJIS


IP_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


class IPInfo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": "ImposterBot/1.0"}
        )

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # SAFE EMOJI
    def e(self, key):
        return EMOJIS.get(key) or ""

    # FETCH
    async def fetch(self, ip):
        url = f"https://ipinfo.io/{ip}/json"

        try:
            async with self.session.get(url) as res: # type: ignore
                if res.status == 429:
                    return {"rate_limited": True}

                if res.status != 200:
                    return None

                return await res.json()

        except asyncio.TimeoutError:
            return {"timeout": True}

        except Exception as e:
            print(f"[IPINFO FETCH ERROR] {e}")
            return None

    # FALLBACK
    async def fallback(self, target, msg):
        if target.get("ctx"):
            await target["ctx"].send(f"⚠️ {msg}")

        elif target.get("interaction"):
            interaction = target["interaction"]

            if interaction.response.is_done():
                await interaction.followup.send(f"⚠️ {msg}")
            else:
                await interaction.response.send_message(f"⚠️ {msg}")

    # CORE
    async def run(self, target, ip):
        r = Respond(**target)

        # SAFE DEFER
        if target.get("interaction"):
            interaction = target["interaction"]
            if not interaction.response.is_done():
                await interaction.response.defer()

        # VALIDATION
        if not IP_REGEX.match(ip):
            return await r.error("Invalid Input", "Provide a valid IPv4 address")

        data = await self.fetch(ip)

        if not data:
            return await self.fallback(target, "Failed to fetch data")

        if data.get("timeout"):
            return await r.warning("Timeout", "API took too long")

        if data.get("rate_limited"):
            return await r.warning("Rate Limited", "Try again later")

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

            map_link = f"https://www.google.com/maps?q={loc}" if loc != "N/A" else None

            await r.send(
                title="IP Intelligence",
                description=ip_addr,
                highlight=True,
                level="INFO",
                fields=[
                    (("Location", self.e("arrow_point")),
                     f"{city}, {region}, {country}", False),
                    (("ISP / Org", self.e("developer")), org, False),
                    (("Coordinates", self.e("ping")), loc, True),
                    (("Timezone", self.e("message")), timezone, True),
                    (("Map", self.e("curved_arrow")),
                     f"[Open Map]({map_link})" if map_link else "N/A", False),
                ],
                footer="Imposter • OSINT",
            )

        except Exception as e:
            print(f"[IPINFO ERROR] {e}")
            await self.fallback(target, "Something went wrong")

    # PREFIX
    @commands.command(name="ipinfo")
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def ipinfo_prefix(self, ctx, ip: str = None): # type: ignore
        r = Respond(ctx=ctx)

        if not ip:
            return await r.info("Usage", "ipinfo <ip_address>")

        await self.run({"ctx": ctx}, ip)

    # SLASH
    @discord.app_commands.command(
        name="ipinfo",
        description="Get information about an IP address"
    )
    @discord.app_commands.checks.cooldown(2, 30.0)
    async def ipinfo_slash(self, interaction: discord.Interaction, ip: str):
        await self.run({"interaction": interaction}, ip)

    # ERRORS
    @ipinfo_prefix.error
    async def prefix_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            r = Respond(ctx=ctx)
            await r.warning("Cooldown",
                            f"Try again in `{round(error.retry_after)}s`")

    @ipinfo_slash.error
    async def slash_error(self, interaction, error):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            r = Respond(interaction=interaction)
            await r.warning("Cooldown",
                            f"Try again in `{round(error.retry_after)}s`")


async def setup(bot):
    await bot.add_cog(IPInfo(bot))