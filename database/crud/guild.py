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

    # GET ADMIN ROLE
    @classmethod
    async def get_admin_role(cls, guild_id):
        guild = await cls.get_or_create(guild_id)
        return guild.admin_role  # type: ignore

    # SET ADMIN ROLE 
    @classmethod
    async def set_admin_role(cls, guild_id, role):
        return await cls.update(
            {"guild_id": str(guild_id)},
            {"admin_role": str(role.id)},
        )

    # UNSET
    @classmethod
    async def unset_admin_role(cls, guild_id):
        return await cls.update(
            {"guild_id": str(guild_id)},
            {"admin_role": None},
        )