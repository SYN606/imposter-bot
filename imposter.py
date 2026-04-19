import os
import logging
import traceback
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

from config.prefix import dynamic_prefix, normalize
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


def log_error(msg):
    logger.error(msg)


# ========================
# INTENTS
# ========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


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
        # DB init
        try:
            await init_db()
            log("✓ Database initialized")
        except Exception as e:
            log_error(f"DB init failed → {e}")
            if is_dev():
                traceback.print_exc()

        # load commands
        await self.load_extensions()

        # sync slash
        if SYNC_COMMANDS:
            try:
                await self.tree.sync()
                log("✓ Slash commands synced")
            except Exception as e:
                log_error(f"Slash sync failed → {e}")

    async def load_extensions(self):
        base = "cmd"

        if not os.path.isdir(base):
            log("No cmd folder found")
            return

        for root, _, files in os.walk(base):
            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue

                module = os.path.join(root, file).replace(os.sep, ".")[:-3]

                try:
                    log(f"Loading: {module}")
                    await self.load_extension(module)
                    log(f"✓ Loaded {module}")
                except Exception as e:
                    log_error(f"✗ Failed {module} → {e}")
                    if is_dev():
                        traceback.print_exc()

    async def on_ready(self):
        log(f"\nLogged in as {self.user} ({self.user.id})")  # type: ignore
        log("Imposter is ready\n")

        print("=== COMMANDS LOADED ===")
        for cmd in self.commands:
            print(f"- {cmd.name}")

    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        try:
            # 🔥 FORCE PREFIX NORMALIZATION
            message.content = normalize(message.content)

        except Exception as e:
            log_error(f"[NORMALIZE ERROR] {e}")
            if is_dev():
                traceback.print_exc()

        await self.process_commands(message)

    # ========================
    # GLOBAL ERROR HANDLER
    # ========================
    async def on_command_error(self, ctx, err):
        log_error(f"[COMMAND ERROR] {err}")

        try:
            await ctx.send(f"⚠️ {str(err)}")
        except Exception:
            pass


# ========================
# ENTRYPOINT
# ========================
def main():
    bot = ImposterBot()

    try:
        log("Starting bot...\n")
        bot.run(TOKEN)  # type: ignore

    except discord.errors.PrivilegedIntentsRequired:
        print("\n[INTENTS ERROR]")
        print("Enable in Developer Portal:")
        print("- MESSAGE CONTENT INTENT")
        print("- SERVER MEMBERS INTENT\n")

    except KeyboardInterrupt:
        log("Shutting down gracefully...")
        print("Shutting down gracefully...")

        try:
            if bot.loop and not bot.loop.is_closed():
                bot.loop.run_until_complete(bot.close())
        except Exception:
            pass

    except Exception as e:
        log_error(f"Crash → {e}")
        if is_dev():
            traceback.print_exc()


if __name__ == "__main__":
    main()