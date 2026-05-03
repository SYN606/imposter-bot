from discord.ext import commands
import discord
import pyshorteners
import re
import asyncio
from urllib.parse import urlparse
from typing import Optional, Dict, Any

from utils.respond import Respond
from utils.permissions import check

URL_REGEX = re.compile(
    r'^(https?://)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d{1,5})?(/.*)?$')
DOMAIN_REGEX = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
SLUG_REGEX = re.compile(r'^[a-zA-Z0-9-]{1,20}$')


class MaskURL(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shortener = pyshorteners.Shortener()

        # GLOBAL COOLDOWN
        self.global_cooldown = commands.CooldownMapping.from_cooldown(
            5, 60, commands.BucketType.default)

        self.lock = asyncio.Lock()

    # HOMOGRAPH
    def apply_homograph(self, domain: str) -> str:
        chars = {'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с'}
        for latin, cyrillic in chars.items():
            domain = domain.replace(latin, cyrillic)
        return domain

    # MASK
    def mask_url(self,
                 domain: str,
                 slug: str,
                 short_url: str,
                 use_homograph: bool = False) -> str:
        parsed = urlparse(short_url)
        display = self.apply_homograph(domain) if use_homograph else domain
        return f"{parsed.scheme}://{display}-{slug}@{parsed.netloc}{parsed.path}"

    # CORE
    async def run(self, target: Dict[str, Any], web_url: str, brand: str,
                  slug: str, homo: str) -> None:

        r = Respond(**target)

        # SAFE DEFER
        if target.get("interaction"):
            interaction: discord.Interaction = target["interaction"]
            if not interaction.response.is_done():
                await interaction.response.defer()

        # PERMISSION CHECK
        allowed = await check(
            ctx=target.get("ctx"),
            interaction=target.get("interaction"),
        )

        if not allowed:
            return

        # VALIDATION
        if not URL_REGEX.match(web_url):
            return await r.error("Invalid URL", "Provide a valid target link")

        if not DOMAIN_REGEX.match(brand):
            return await r.error("Invalid Domain",
                                 "Provide a valid brand domain")

        if not SLUG_REGEX.match(slug):
            return await r.error("Invalid Slug",
                                 "Use alphanumeric/dashes (max 20 chars)")

        use_homograph = homo.lower() == "y"

        engines = [self.shortener.tinyurl, self.shortener.osdb]
        results: list[str] = []

        # Prevent concurrent API spam
        async with self.lock:
            for i, engine in enumerate(engines, 1):
                try:
                    short = engine.short(web_url)
                    masked = self.mask_url(brand, slug, short, use_homograph)
                    results.append(f"**Option {i}:** {masked}")
                except Exception:
                    results.append(f"**Option {i}:** Service unavailable")

        # RESPONSE
        await r.send(
            title="Masked Links Generated",
            description=web_url,
            highlight=True,
            level="WARNING",
            fields=[
                (("Brand"), brand, True),
                (("Slug"), slug, True),
                (("Homograph"), "Enabled" if use_homograph else "Disabled",
                 True),
                (("Results"), "\n".join(results), False),
            ],
            footer="SYN 606 • Mask Engine",
        )

    # PREFIX
    @commands.command(name="mask")
    @commands.cooldown(2, 30, commands.BucketType.user)
    @commands.cooldown(5, 60, commands.BucketType.default)  # GLOBAL
    async def mask_prefix(self,
                          ctx: commands.Context,
                          web_url: Optional[str] = None,
                          brand: Optional[str] = None,
                          slug: Optional[str] = None,
                          homo: str = "n") -> None:

        r = Respond(ctx=ctx)

        if web_url is None or brand is None or slug is None:
            return await r.info("Usage", "mask <url> <brand> <slug> [y/n]")

        await self.run({"ctx": ctx}, web_url, brand, slug, homo)

    # SLASH
    @discord.app_commands.command(name="mask",
                                  description="Generate disguised masked URLs")
    @discord.app_commands.describe(web_url="Target URL",
                                   brand="Domain to spoof",
                                   slug="Custom slug",
                                   homo="Use homograph (y/n)")
    @discord.app_commands.checks.cooldown(2, 30.0)
    async def mask_slash(self,
                         interaction: discord.Interaction,
                         web_url: str,
                         brand: str,
                         slug: str,
                         homo: str = "n") -> None:

        # GLOBAL COOLDOWN
        bucket = self.global_cooldown.get_bucket(interaction)
        retry_after = bucket.update_rate_limit() # type: ignore

        if retry_after:
            r = Respond(interaction=interaction)
            return await r.warning(
                "Global Cooldown",
                f"Bot is busy. Try again in {round(retry_after)}s")

        await self.run({"interaction": interaction}, web_url, brand, slug,
                       homo)

    # ERRORS
    @mask_prefix.error
    async def prefix_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandOnCooldown):
            r = Respond(ctx=ctx)
            msg = f"You're going too fast. Try again in {round(error.retry_after)}s"
            await r.warning("Slow down", msg)

    @mask_slash.error
    async def slash_error(self, interaction: discord.Interaction,
                          error: Exception):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            r = Respond(interaction=interaction)
            msg = f"You're going too fast. Try again in {round(error.retry_after)}s"
            await r.warning("Slow down", msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(MaskURL(bot))
