from database.crud.base import BaseCRUD
from database.models import GuildConfig


class GuildCRUD(BaseCRUD):
    model = GuildConfig

    @classmethod
    async def get_or_create(cls, guild_id):
        guild = await cls.get(guild_id=str(guild_id))

        if guild:
            return guild

        return await cls.create(guild_id=str(guild_id))

    @classmethod
    async def get_admin_role(cls, guild_id):
        guild = await cls.get_or_create(guild_id)
        return guild.admin_role if guild else "Admin"

    @classmethod
    async def set_admin_role(cls, guild_id, role_name):
        return await cls.update(
            {"guild_id": str(guild_id)},
            {"admin_role": role_name},
        )