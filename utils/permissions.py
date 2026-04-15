from config import settings
from utils.respond import Respond


def has_admin_role(member):
    role_name = settings._get("ADMIN_ROLE", "Admin")

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

    if ctx:
        user = ctx.author
    elif interaction:
        user = interaction.user

    if not user or not getattr(user, "guild", None):
        return False

    # OWNER BYPASS
    if user.guild.owner_id == user.id:
        return True

    # role check
    if not has_admin_role(user):
        if not silent:
            r = Respond(ctx=ctx, interaction=interaction)
            await r.error("Access Denied", "Admin role required")
        return False

    # permission check
    if not has_permissions(user, perms):
        if not silent:
            r = Respond(ctx=ctx, interaction=interaction)
            await r.error("Permission Denied", "Insufficient permissions")
        return False

    return True
