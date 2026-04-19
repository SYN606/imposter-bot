from utils.respond import Respond
from database.crud.guild import GuildCRUD


async def has_admin_role(member):
    try:
        role_name = await GuildCRUD.get_admin_role(member.guild.id)
    except Exception:
        role_name = "Admin"  # fallback

    for role in getattr(member, "roles", []):
        if role.name.lower() == role_name.lower():
            return True

    return False


def has_permissions(member, perms):
    if not perms:
        return True

    user_perms = member.guild_permissions

    for perm in perms:
        if not getattr(user_perms, perm, False):
            return False

    return True


async def check(ctx=None, interaction=None, perms=None, silent=False):
    user = None
    guild = None

    if ctx:
        user = ctx.author
        guild = ctx.guild
    elif interaction:
        user = interaction.user
        guild = interaction.guild

    if not user or not guild:
        return False

    # ========================
    # OWNER BYPASS
    # ========================
    if guild.owner_id == user.id:
        return True

    # ========================
    # ADMIN ROLE CHECK (DB)
    # ========================
    if not await has_admin_role(user):
        if not silent:
            r = Respond(ctx=ctx, interaction=interaction)
            await r.error("Access Denied", "Admin role required")
        return False

    # ========================
    # PERMISSION CHECK
    # ========================
    if not has_permissions(user, perms):
        if not silent:
            r = Respond(ctx=ctx, interaction=interaction)
            await r.error("Permission Denied", "Insufficient permissions")
        return False

    return True