from typing import Dict, List, Union
import discord
import asyncio
import os
import exceptions

# TODO: Bot should verify that the proper numbers of arguments are added
# TODO: Bot should check .watchfiles to see if it's updated too

try:
    with open(".env", "r") as file:
        env_vars: Dict[str, str] = {}
        for line in file.read().splitlines():
            [key, value] = line.split("=")
            env_vars[key] = value
except FileNotFoundError:
    raise exceptions.EnvNotProvided("Provide .env file for BOT_TOKEN")

STUDENT_ID = env_vars.get("STUDENT_ID")
MENTOR_ID = env_vars.get("MENTOR_ID")
LOGGING_CHANNEL_ID = env_vars.get("LOGGING_CHANNEL_ID")
FILE_CHECK_INTERVAL = env_vars.get("FILE_CHECK_INTERVAL")
WATCHFILE_CHECK_INTERVAL = env_vars.get("WATCHFILE_CHECK_INTERVAL")
BOT_TOKEN = env_vars["BOT_TOKEN"]

if FILE_CHECK_INTERVAL is None:
    FILE_CHECK_INTERVAL = 3
else:
    FILE_CHECK_INTERVAL = int(FILE_CHECK_INTERVAL)
if WATCHFILE_CHECK_INTERVAL is None:
    WATCHFILE_CHECK_INTERVAL = 7
else:
    WATCHFILE_CHECK_INTERVAL = int(WATCHFILE_CHECK_INTERVAL)

MessageableChannel = Union[
    discord.TextChannel,
    discord.StageChannel,
    discord.VoiceChannel,
    discord.Thread,
    discord.DMChannel,
    discord.GroupChannel,
    discord.PartialMessageable,
]


def prepare_message(filepath: str, extension: str, code: str) -> str:
    if STUDENT_ID is None:
        return f"## {filepath} Changed \n```{extension}\n{code}\n```\n"
    return f"## {filepath} Changed \n```{extension}\n{code}\n```\n<@&{STUDENT_ID}>"


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


async def send_denial(message: discord.Message):
    await message.channel.send("Only mentors can watch for file changes")


class FileUpdateBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.background_tasks: List[asyncio.Task] = []
        self.default_background_tasks: Dict[str, asyncio.Task] = {}
        self.default_background_task_running: Dict[str, bool] = {}
        self.logging_channel: None | MessageableChannel = None

    async def log(self, message: str):
        if self.logging_channel is None:
            print(message)
        else:
            await self.logging_channel.send(message)

    async def on_ready(self):
        if LOGGING_CHANNEL_ID is not None:
            logging_channel = await self.fetch_channel(int(LOGGING_CHANNEL_ID))
            if not isinstance(logging_channel, MessageableChannel):
                print(f"I cannot send message in {LOGGING_CHANNEL_ID}")
            self.logging_channel = logging_channel
        else:
            print(
                "LOGGING_CHANNEL_ID is not provided in .env, Logging will be done in terminal now."
            )

        if MENTOR_ID is None:
            await self.log(
                "## WARNING \n Mentor_id is not provided, program needs mentor id to verify the person who is commanding it, now anyone can command it, thus anyone can access your files"
            )

        try:
            await self.watch_default_files()
        except FileNotFoundError:
            print("No default files to watch...")
        print("Bot is ready...")

    async def on_message(self, message):
        if message.content.startswith("$"):
            await self.handle_commands(message)

    async def watch_file(self, filepath: str, channel: MessageableChannel):
        await self.wait_until_ready()
        stamp = os.stat(filepath).st_mtime
        dot_index = filepath.find(".")
        extension = filepath[dot_index + 1 :]

        key = f"forum-watch|{channel.id}|{filepath}"
        while not self.is_closed() and self.default_background_task_running[key]:
            if has_file_updated(filepath, stamp):
                stamp = os.stat(filepath).st_mtime
                code = ""
                with open(filepath, "r") as file:
                    code = file.read()
                message = prepare_message(filepath, extension, code)
                await channel.send(message)

            await asyncio.sleep(FILE_CHECK_INTERVAL)

    async def forum_watch_file(
        self,
        filepath,
        channel: discord.ForumChannel,
    ) -> bool:
        await self.wait_until_ready()
        stamp = os.stat(filepath).st_mtime
        dot_index = filepath.find(".")
        extension = filepath[dot_index + 1 :]

        file_thread: discord.Thread | None = None
        for loop_thread in channel.threads:
            if loop_thread.name == filepath:
                file_thread = loop_thread

        if file_thread is None:
            code = ""
            with open(filepath, "r") as file:
                code = file.read()
            forum_content = f"```{extension}\n{code}\n```\n Current code"
            message = prepare_message(filepath, extension, code)
            file_thread_with_message = await channel.create_thread(
                name=filepath, content=forum_content
            )
            file_thread = file_thread_with_message.thread
            await file_thread.send(message)

        key = f"forum-watch|{channel.id}|{filepath}"
        while not self.is_closed() and self.default_background_task_running[key]:
            code = ""
            if has_file_updated(filepath, stamp):
                stamp = os.stat(filepath).st_mtime
                with open(filepath, "r") as file:
                    code = file.read()
                message = prepare_message(filepath, extension, code)
                forum_content = f"```{extension}\n{code}\n```\n Current code"
                [first_message] = [
                    message
                    async for message in file_thread.history(limit=1, oldest_first=True)
                ]
                if first_message is None:
                    raise exceptions.StarterMessageNotFound("starter_message is None")
                await first_message.edit(content=forum_content)
                await file_thread.send(message)
            await asyncio.sleep(FILE_CHECK_INTERVAL)
        return True

    async def handle_watchfile_command(
        self, line: str | None = None, key: str | None = None
    ) -> None:
        if line is not None:
            split_command = escapeable_split(line)
        elif key is not None:
            split_command = escapeable_split(key, "|")
        else:
            raise exceptions.NeitherLineNorKeyProvided(
                "Provide a line, or a key to handle_watchfile_command()"
            )

        command = split_command[0]
        match command:
            case "watch":
                [channel_id, filepath] = split_command[1:]
                if not os.path.exists(filepath):
                    await self.log(f"{filepath} does not exist")
                    return

                channel = await self.fetch_channel(channel_id)
                if not isinstance(channel, MessageableChannel):
                    await self.log(f"I cannot send message in <#{channel_id}>")
                    return

                key = f"{command}|{channel_id}|{filepath}"
                self.default_background_task_running[key] = True
                self.default_background_tasks[key] = self.loop.create_task(
                    self.watch_file(filepath, channel)
                )
                await self.log(f"Watching {filepath} 🤖 in <#{channel_id}>")
            case "forum-watch":
                [channel_id, filepath] = split_command[1:]
                if not os.path.exists(filepath):
                    await self.log(f"{filepath} does not exist")
                    return

                channel = await self.fetch_channel(channel_id)
                if not isinstance(channel, discord.ForumChannel):
                    await self.log(f"<#{channel_id}> is not a forum channel")
                    return

                key = f"{command}|{channel_id}|{filepath}"
                self.default_background_task_running[key] = True
                self.default_background_tasks[key] = self.loop.create_task(
                    self.forum_watch_file(filepath, channel)
                )
                await self.log(f"Watching {filepath} 🤖 in <#{channel_id}>")

    async def watch_default_files(self):
        filepath = ".watchfiles"
        while not os.path.exists(filepath) and not self.is_closed():
            await asyncio.sleep(WATCHFILE_CHECK_INTERVAL)
        commands = ""
        with open(filepath, "r") as file:
            commands = file.read().splitlines()
        for command in commands:
            await self.handle_watchfile_command(command)

        stamp = os.stat(filepath).st_mtime

        while not self.is_closed():
            if has_file_updated(filepath, stamp):
                stamp = os.stat(filepath).st_mtime
                # key is command|channel_name|filename
                # Conditions, if key in new tasks and running, keep running
                # if key in new taks, but not running, then start running
                # if new tasks does not exist in key, then add key and start running
                # if key not exists in new tasks, then stop runnig

                with open(filepath, "r") as file:
                    commands = file.read()
                    new_tasks: set[str] = {
                        command.replace(" ", "|") for command in commands.splitlines()
                    }
                keys = set(self.default_background_task_running.keys())
                for key in new_tasks.intersection(keys):
                    running = self.default_background_task_running[key]
                    if not running:
                        await self.handle_watchfile_command(key)
                for key in new_tasks.difference(keys):
                    await self.handle_watchfile_command(key)
                for key in keys.difference(new_tasks):
                    self.default_background_task_running[key] = False

            await asyncio.sleep(WATCHFILE_CHECK_INTERVAL)

    async def handle_commands(self, message: discord.Message):
        isMentor = await self.find_is_mentor(message)

        if not isMentor:
            await send_denial(message)
            return

        content = message.content
        split = escapeable_split(content)
        match split[0]:
            case "$hack":
                filepath = split[1]

                if not os.path.exists(filepath):
                    await message.channel.send(f"{filepath} does not exist")
                    return

                self.background_tasks.append(
                    self.loop.create_task(self.watch_file(filepath, message.channel))
                )
                with open("hacker.webp", "rb") as file:
                    gif = discord.File(file)
                    await message.channel.send("# Got it", file=gif)
            case "$watch":
                filepath = split[1]

                if not os.path.exists(filepath):
                    await message.channel.send(f"{filepath} does not exist")
                    return

                self.background_tasks.append(
                    self.loop.create_task(self.watch_file(filepath, message.channel))
                )
                await message.channel.send(f"Watching {filepath} 🤖")
            case "$forum-watch":
                forum_id = split[1]
                filepath = split[2]

                if not os.path.exists(filepath):
                    await message.channel.send(f"{filepath} does not exist")
                    return

                forum_channel = await self.fetch_channel(forum_id)
                if not isinstance(forum_channel, discord.ForumChannel):
                    await message.channel.send(
                        "Channel provided is not a forum channel"
                    )
                    return
                self.background_tasks.append(
                    self.loop.create_task(
                        self.forum_watch_file(filepath, forum_channel)
                    )
                )
                await message.channel.send(f"Watching {filepath} in <#{forum_id}> 🤖")

    async def find_is_mentor(self, message: discord.Message):
        if MENTOR_ID is None:
            return True
        isMentor = False
        author = message.author
        if not isinstance(author, discord.Member):
            return False
        for role in author.roles:
            if role.id == int(MENTOR_ID):
                isMentor = True
        return isMentor


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.guilds = True
    intents.message_content = True
    client = FileUpdateBot(intents=intents)
    client.run(BOT_TOKEN)
