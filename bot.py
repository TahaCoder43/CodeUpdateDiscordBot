import discord
import asyncio
import os

with open(".env", "r") as file:
    env_vars = {}
    for line in file.read().splitlines():
        [key, value] = line.split("=")
        env_vars[key] = value

class FileUpdateBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.filename = "./index.html"
        self.stamp = os.stat(self.filename).st_mtime

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.file_update_check())

    async def on_ready(self):
        print("Bot is ready...")

    async def file_update_check(self):
        await self.wait_until_ready()
        channel = await self.fetch_channel(int(env_vars["CHANNEL"]))

        while not self.is_closed():
            new_stamp = os.stat(self.filename).st_mtime
            if new_stamp != self.stamp:
                self.stamp = new_stamp
                text = ""
                with open(self.filename, "r") as file:
                    text = file.read()
                text = f"## Code Changed \n```html\n{text}\n```\n<@{env_vars["TAG_USER"]}>"

                await channel.send(text)

            await asyncio.sleep(3)

intents = discord.Intents.default()
intents.guilds = True
client = FileUpdateBot(intents=intents)
client.run(env_vars["BOT_TOKEN"])
