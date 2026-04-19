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


def _format_field(name, value, emoji=None):
    if emoji:
        return f"{emoji} {name}", value
    return name, value


def make_embed(
    *,
    title,
    description=None,
    level="INFO",
    fields=None,
    footer=None,
    show_timestamp=True,
    use_emoji=True,
    highlight=False,      # highlight description (codeblock style)
    compact=False,        # force inline layout
):

    level = level.upper()
    config = LEVELS.get(level, LEVELS["INFO"])

    color = config["color"]
    emoji = EMOJIS.get(config["emoji"]) if use_emoji else None

    # title
    title = f"{emoji} {title}" if emoji else title

    # description styling
    if description and highlight:
        description = f"```{description}```"

    embed = discord.Embed(
        title=_safe(title, 256),
        description=_safe(description, 4096),
        color=color,
    )

    # fields (clean modern layout)
    if fields:
        for name, value, inline in fields[:25]:

            field_emoji = None
            if isinstance(name, tuple):
                name, field_emoji = name

            name, value = _format_field(name, value, field_emoji)

            embed.add_field(
                name=_safe(name, 256),
                value=_safe(value, 1024),
                inline=inline if not compact else True,
            )

    # subtle footer
    if footer:
        embed.set_footer(text=_safe(footer, 2048))

    if show_timestamp:
        embed.timestamp = discord.utils.utcnow()

    return embed