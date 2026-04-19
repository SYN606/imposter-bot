from discord.ext import commands
import discord
from typing import Optional

from utils.respond import Respond
from database.crud.guild import GuildCRUD


class AdminRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================
    # HELPERS
    # ========================
    def is_owner(self, user, guild):
        return guild and user.id == guild.owner_id

    def get_guild(self, target):
        ctx = target.get("ctx")
        interaction = target.get("interaction")
        return ctx.guild if ctx else interaction.guild  # type: ignore

    # ========================
    # CORE
    # ========================
    async def run(self,
                  target,
                  action: str,
                  role: Optional[discord.Role] = None):
        r = Respond(**target)
        guild = self.get_guild(target)

        if not guild:
            return await self.fallback(target, "Guild not found")

        action = action.lower().strip()

        try:
            # ========================
            # SET
            # ========================
            if action == "set":
                if not role:
                    return await r.error("Missing Role", "Provide a role")

                await GuildCRUD.set_admin_role(guild.id, role)

                return await r.success("Admin Role Set",
                                       f"Role → {role.mention}")

            # ========================
            # UNSET
            # ========================
            elif action == "unset":
                await GuildCRUD.unset_admin_role(guild.id)

                return await r.success("Admin Role Removed",
                                       "No admin role configured")

            # ========================
            # LIST
            # ========================
            elif action == "list":
                role_id = await GuildCRUD.get_admin_role(guild.id)

                if not role_id:
                    return await r.info("Admin Role", "No admin role set")

                try:
                    role_obj = guild.get_role(int(role_id))
                except Exception:
                    role_obj = None

                if not role_obj:
                    return await r.warning("Admin Role",
                                           "Configured role no longer exists")

                return await r.info("Admin Role",
                                    f"Current → {role_obj.mention}")

            # ========================
            # INVALID
            # ========================
            return await r.error("Invalid Action", "Use: set | unset | list")

        except Exception as e:
            print(f"[ADMINROLE ERROR] {e}")
            return await self.fallback(target, "Something went wrong")

    # ========================
    # FALLBACK (CRITICAL)
    # ========================
    async def fallback(self, target, msg):
        if target.get("ctx"):
            await target["ctx"].send(f"⚠️ {msg}")

        elif target.get("interaction"):
            interaction = target["interaction"]

            if interaction.response.is_done():
                await interaction.followup.send(f"⚠️ {msg}")
            else:
                await interaction.response.send_message(f"⚠️ {msg}")

    # ========================
    # PREFIX COMMAND
    # ========================
    @commands.command(name="adminrole")
    async def adminrole_prefix(
        self,
        ctx,
        action: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ):
        if not ctx.guild:
            return

        r = Respond(ctx=ctx)

        if not self.is_owner(ctx.author, ctx.guild):
            return await r.error("Access Denied", "Owner only command")

        if not action:
            return await r.info("Usage", "adminrole <set|unset|list> [role]")

        await self.run({"ctx": ctx}, action, role)

    # ========================
    # SLASH COMMAND
    # ========================
    @discord.app_commands.command(name="adminrole",
                                  description="Manage admin role (Owner only)")
    @discord.app_commands.describe(action="set | unset | list",
                                   role="Role to set")
    async def adminrole_slash(
        self,
        interaction: discord.Interaction,
        action: str,
        role: Optional[discord.Role] = None,
    ):
        # SAFE DEFER
        if not interaction.response.is_done():
            await interaction.response.defer()

        r = Respond(interaction=interaction)

        if not interaction.guild:
            return await self.fallback({"interaction": interaction},
                                       "Guild not found")

        if not self.is_owner(interaction.user, interaction.guild):
            return await r.error("Access Denied", "Owner only command")

        await self.run({"interaction": interaction}, action, role)


async def setup(bot):
    await bot.add_cog(AdminRole(bot))
