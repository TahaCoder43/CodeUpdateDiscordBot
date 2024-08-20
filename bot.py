from typing import Union
import discord
import asyncio
import os

with open(".env", "r") as file:
    env_vars = {}
    for line in file.read().splitlines():
        [key, value] = line.split("=")
        env_vars[key] = value

STUDENT_ID = int(env_vars["STUDENT_ID"])
MENTOR_ID = int(env_vars["MENTOR_ID"])
BOT_TOKEN = env_vars["BOT_TOKEN"]

MessageableChannel = Union[
    discord.TextChannel,
    discord.StageChannel,
    discord.VoiceChannel,
    discord.Thread,
    discord.DMChannel,
    discord.GroupChannel,
    discord.PartialMessageable,
]


def escapeable_split(string: str, splitter: str = " ", include_splitter: bool = False):
    split_list = []
    word = ""
    ESCAPE = "\\"
    escaped = False
    for letter in string:
        if letter == ESCAPE:
            escaped = True
            continue
        if letter == splitter and not escaped:
            split_list.append(word)
            word = ""
            if not include_splitter:
                continue
        elif escaped:
            escaped = False
            if letter != splitter:
                word += ESCAPE
        word += letter
    if word != "":
        split_list.append(word)
    return split_list


def has_file_updated(file, current_stamp):
    new_stamp = os.stat(file).st_mtime
    return new_stamp != current_stamp


class FileUpdateBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print("Bot is ready...")

    async def on_message(self, message):
        if message.content.startswith("$"):
            await handle_commands(message, self)

    async def watch_file(self, filepath: str, channel: MessageableChannel):
        await self.wait_until_ready()
        stamp = os.stat(filepath).st_mtime

        while not self.is_closed():
            if has_file_updated(filepath, stamp):
                stamp = os.stat(filepath).st_mtime
                code = ""
                with open(filepath, "r") as file:
                    code = file.read()
                code = f"## Code Changed \n```html\n{code}\n```\n<@&{STUDENT_ID}>"

                await channel.send(code)

            await asyncio.sleep(3)


async def send_denial(message: discord.Message):
    await message.channel.send("Only mentors can watch for file changes")


async def find_is_mentor(message: discord.Message):
    isMentor = False
    author = message.author
    if not isinstance(author, discord.Member):
        return False
    for role in author.roles:
        if role.id == MENTOR_ID:
            isMentor = True
    return isMentor


async def handle_commands(message: discord.Message, client: FileUpdateBot):
    isMentor = find_is_mentor(message)

    if not isMentor:
        await send_denial(message)
        return

    content = message.content
    split = escapeable_split(content)
    match split[0]:
        case "$watch":
            filepath = split[1]
            client.bg_task = client.loop.create_task(
                client.watch_file(filepath, message.channel)
            )
            await message.channel.send(f"Watching {filepath} 🤖")


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.guilds = True
    intents.message_content = True
    client = FileUpdateBot(intents=intents)
    client.run(env_vars["BOT_TOKEN"])
