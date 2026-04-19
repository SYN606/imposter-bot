import os
import time
import logging
import traceback
import threading
import sys
import discord
from discord.ext import commands


# ========================
# SAFE SETTINGS LOAD
# ========================
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
from database.init import init_db


# ========================
# LOGGING
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger("imposter")


def log(msg):
    logger.info(msg)


def error(msg):
    logger.error(msg)


# ========================
# INTENTS
# ========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# ========================
# CONTROL FLAGS
# ========================
RELOAD_FLAG = False
STOP_FLAG = False


def keyboard_listener():
    global RELOAD_FLAG, STOP_FLAG

    while True:
        try:
            key = sys.stdin.read(1)

            if key.lower() == "r":
                print("\n[RELOAD REQUESTED]\n")
                RELOAD_FLAG = True

            elif key.lower() == "c":
                print("\n[STOP REQUESTED]\n")
                STOP_FLAG = True
                break

        except Exception:
            break


# ========================
# BOT
# ========================
class ImposterBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=dynamic_prefix,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        try:
            await init_db()
            log("✓ Database initialized")
        except Exception as e:
            error(f"DB init failed → {e}")

            if is_dev():
                traceback.print_exc()

        await self.load_extensions()

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

                module = os.path.join(root, file).replace(os.sep, ".")[:-3]

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


# ========================
# ENTRYPOINT
# ========================
def main():
    global RELOAD_FLAG, STOP_FLAG

    # start keyboard listener thread
    threading.Thread(target=keyboard_listener, daemon=True).start()

    while True:
        RELOAD_FLAG = False
        STOP_FLAG = False

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

        except KeyboardInterrupt:
            print("\nGraceful shutdown...\n")
            break

        except Exception as e:
            error(f"Crash → {e}")

            if is_dev():
                traceback.print_exc()

            time.sleep(5)

        # ========================
        # HANDLE FLAGS
        # ========================
        if STOP_FLAG:
            log("Stopped.")
            break

        if RELOAD_FLAG:
            log("Reloading bot...\n")
            continue


if __name__ == "__main__":
    main()