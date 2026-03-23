import discord
from .emojis import EMOJIS

LEVELS = {
    "INFO": {"color": 0x2B2D31, "emoji": "announcement"},
    "SUCCESS": {"color": 0x1F8B4C, "emoji": "success"},
    "WARNING": {"color": 0xF0B232, "emoji": "warning"},
    "ERROR": {"color": 0xDA373C, "emoji": "fail"},
    "DEBUG": {"color": 0x5865F2, "emoji": "developer"},
    "SYSTEM": {"color": 0x8E44AD, "emoji": "okay"},
}


def _safe(text, limit):
    if not text:
        return None
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _separator():
    # clean modern divider
    return "─" * 30


def make_embed(
    *,
    title,
    description=None,
    level="INFO",
    fields=None,
    footer=None,
    show_timestamp=True,
    use_emoji=True,
    separator=True,
):

    level = level.upper()
    config = LEVELS.get(level, LEVELS["INFO"])

    color = config["color"]
    emoji = EMOJIS.get(config["emoji"]) if use_emoji else None

    # title with emoji
    title = f"{emoji} {title}" if emoji else title

    # build description with separator
    desc_parts = []

    if separator:
        desc_parts.append(_separator())

    if description:
        desc_parts.append(description)

    final_description = "\n".join(desc_parts) if desc_parts else None

    embed = discord.Embed(
        title=_safe(title, 256),
        description=_safe(final_description, 4096),
        color=color,
    )

    # fields
    if fields:
        for name, value, inline in fields[:25]:
            embed.add_field(
                name=_safe(name, 256),
                value=_safe(value, 1024),
                inline=inline,
            )

    # footer
    if footer:
        embed.set_footer(text=_safe(footer, 2048))

    if show_timestamp:
        embed.timestamp = discord.utils.utcnow()

    return embed