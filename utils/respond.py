from config.embeds import make_embed


class Respond:
    def __init__(self, ctx=None, interaction=None, channel=None):
        self.ctx = ctx
        self.interaction = interaction
        self.channel = channel

    async def _dispatch(self, embed=None, content=None, **kwargs):
        try:
            # ctx (prefix commands)
            if self.ctx:
                return await self.ctx.send(embed=embed, content=content, **kwargs)

            # interaction (slash commands)
            if self.interaction:
                if self.interaction.response.is_done():
                    return await self.interaction.followup.send(
                        embed=embed, content=content, **kwargs
                    )
                return await self.interaction.response.send_message(
                    embed=embed, content=content, **kwargs
                )

            # fallback (manual channel send)
            if self.channel:
                return await self.channel.send(embed=embed, content=content, **kwargs)

        except Exception as e:
            # last-resort fallback (no crash)
            try:
                if self.ctx:
                    return await self.ctx.send(f"Error: {e}")
                if self.channel:
                    return await self.channel.send(f"Error: {e}")
            except:  # noqa: E722
                return None

    async def send(
        self,
        title=None,
        description=None,
        level="INFO",
        fields=None,
        footer=None,
        content=None,
        **kwargs,
    ):
        embed = None

        if title or description:
            try:
                embed = make_embed(
                    title=title,
                    description=description,
                    level=level,
                    fields=fields,
                    footer=footer,
                    **kwargs,
                )
            except Exception as e:
                # fallback if embed builder fails
                content = content or f"{title}\n{description}\nError: {e}"

        return await self._dispatch(embed=embed, content=content)

    async def success(self, title, description=None, **kwargs):
        return await self.send(title, description, level="SUCCESS", **kwargs)

    async def error(self, title, description=None, **kwargs):
        return await self.send(title, description, level="ERROR", **kwargs)

    async def warning(self, title, description=None, **kwargs):
        return await self.send(title, description, level="WARNING", **kwargs)

    async def info(self, title, description=None, **kwargs):
        return await self.send(title, description, level="INFO", **kwargs)

    async def loading(self, title="Processing...", **kwargs):
        return await self.send(title, level="INFO", **kwargs)

    async def raw(self, content, **kwargs):
        return await self._dispatch(content=content, **kwargs)
