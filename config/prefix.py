from discord.ext import commands
import discord
import os

# env already loaded in main
PREFIX = (os.getenv("PREFIX") or "dv").strip()

if not PREFIX:
    PREFIX = "dv"


# ========================
# NORMALIZER
# ========================

def normalize_prefix(content: str):

    if not content:
        return content

    stripped = content.lstrip()

    if not stripped.lower().startswith(PREFIX.lower()):
        return content

    rest = stripped[len(PREFIX):].lstrip()
    return f"{PREFIX}{rest}"


# ========================
# PREFIX RESOLVER
# ========================

def dynamic_prefix(bot: commands.Bot, message: discord.Message):

    base = PREFIX

    if not message.content:
        return commands.when_mentioned_or(base)(bot, message)

    content = message.content.lstrip()

    # case-insensitive match
    if content.lower().startswith(base.lower()):
        actual = content[:len(base)]  # preserve user casing
        return commands.when_mentioned_or(actual)(bot, message)

    return commands.when_mentioned_or(base)(bot, message)