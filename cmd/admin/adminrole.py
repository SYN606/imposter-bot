from discord.ext import commands
import discord
from typing import Optional

from utils.respond import Respond
from database.crud.guild import GuildCRUD


class AdminRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================
    # CORE LOGIC
    # ========================
    async def run(self,
                  target,
                  action: str,
                  role: Optional[discord.Role] = None):
        r = Respond(**target)

        ctx = target.get("ctx")
        interaction = target.get("interaction")

        guild = ctx.guild if ctx else interaction.guild  # type: ignore

        if not guild:
            return await r.error("Error", "Guild not found")

        if action == "set":
            if role is None:
                return await r.error("Missing Role", "Provide a role to set")

            await GuildCRUD.set_admin_role(guild.id, role.name)
            return await r.success("Admin Role Set", f"Role → `{role.name}`")

        elif action == "unset":
            await GuildCRUD.set_admin_role(guild.id, "Admin")
            return await r.success("Admin Role Reset", "Defaulted to `Admin`")

        elif action == "list":
            role_name = await GuildCRUD.get_admin_role(guild.id)
            return await r.info("Admin Role", f"Current → `{role_name}`")

        return await r.error("Invalid Action", "Use: set | unset | list")

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
        r = Respond(ctx=ctx)

        if ctx.guild is None:
            return

        if ctx.guild.owner_id != ctx.author.id:
            return await r.error("Access Denied",
                                 "Only server owner can use this command")

        if not action:
            return await r.info("Usage", "adminrole <set|unset|list> [role]")

        await self.run({"ctx": ctx}, action.lower(), role)

    # ========================
    # SLASH COMMAND
    # ========================
    @discord.app_commands.command(name="adminrole",
                                  description="Manage admin role (Owner only)")
    @discord.app_commands.describe(action="set | unset | list",
                                   role="Role to set as admin")
    async def adminrole_slash(
        self,
        interaction: discord.Interaction,
        action: str,
        role: Optional[discord.Role] = None,
    ):
        r = Respond(interaction=interaction)

        if interaction.guild is None:
            return await r.error("Error", "Guild not found")

        if interaction.guild.owner_id != interaction.user.id:
            return await r.error("Access Denied",
                                 "Only server owner can use this command")

        await self.run({"interaction": interaction}, action.lower(), role)


async def setup(bot):
    await bot.add_cog(AdminRole(bot))
