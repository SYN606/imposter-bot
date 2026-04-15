import os
import time
import logging
import traceback
import discord
from discord.ext import commands


# safe settings load
try:
    from config import settings

    settings.validate()

    TOKEN = settings.TOKEN
    SYNC_COMMANDS = settings.SYNC_COMMANDS
    is_dev = settings.is_dev

except Exception as e:
    print("\n[CONFIG ERROR]")
    print(f"→ {e}")
    print("\nFix your .env file and restart.\n")
    exit(1)

from config.prefix import dynamic_prefix, normalize_prefix

# 🔥 DB IMPORT
from database.init import init_db


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger("imposter")


def log(msg):
    logger.info(msg)


def error(msg):
    logger.error(msg)


# intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# bot
class ImposterBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=dynamic_prefix,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        # ========================
        # DATABASE INIT
        # ========================
        try:
            await init_db()
            log("✓ Database initialized")
        except Exception as e:
            error(f"DB init failed → {e}")

            if is_dev():
                traceback.print_exc()

        # ========================
        # LOAD COMMANDS
        # ========================
        await self.load_extensions()

        # ========================
        # SYNC SLASH
        # ========================
        if SYNC_COMMANDS:
            try:
                await self.tree.sync()
                log("✓ Slash commands synced")
            except Exception as e:
                error(f"Slash sync failed → {e}")

    async def load_extensions(self):
        base = "cmd"

        if not os.path.isdir(base):
            return

        for root, _, files in os.walk(base):
            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue

                full_path = os.path.join(root, file)
                module = full_path.replace(os.sep, ".").replace("/", ".")[:-3]

                try:
                    await self.load_extension(module)
                    log(f"✓ {module}")
                except Exception as e:
                    error(f"✗ {module} → {e}")

                    if is_dev():
                        traceback.print_exc()

    async def on_ready(self):
        log(f"\nLogged in as {self.user} ({self.user.id})") # type: ignore
        log("Imposter is ready\n")

    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        try:
            message.content = normalize_prefix(message.content)
        except Exception as e:
            error(f"Message error → {e}")

            if is_dev():
                traceback.print_exc()

        await self.process_commands(message)


# entrypoint
def main():
    while True:
        bot = ImposterBot()

        try:
            log("Starting bot...\n")
            bot.run(TOKEN) # type: ignore

        except discord.errors.PrivilegedIntentsRequired:
            print("\n[INTENTS ERROR]")
            print("Enable in Developer Portal:")
            print("- MESSAGE CONTENT INTENT")
            print("- SERVER MEMBERS INTENT\n")
            break

        except discord.HTTPException as e:
            if e.status == 429:
                log("Rate limited → retrying in 60s\n")
                time.sleep(60)
                continue

            error(f"HTTP error → {e.status}")
            break

        except KeyboardInterrupt:
            print("\nStopped.\n")
            break

        except Exception as e:
            error(f"Crash → {e}")

            if is_dev():
                traceback.print_exc()

            time.sleep(30)


if __name__ == "__main__":
    main()
