# CodeUpdate discord bot

Bots that upload code from file when it changes to discord server


## Setup

Dependencies: Python, discordpy library

You will have to create the bot yourself on discord, get the token and copy paste in the code and run it using python

make sure to give the bot the neccesary permissions

## Basic Usage

type in `$watch {{filepath}}` in any channel and it would send the code whenever it's changed in that channel

Note: you can use "\" to escape spaces in filepath

put .watchfiles in the same folder as the bot, and put in the relevant commands as shown in features heading

## Features

1. Use `$watch {{filepath}}` command to watch files
2. Use `$hack {{filepath}}` command for funzies which works like $watch, but instead sends a hacker gif "with got" it message when commanded
3. Use `$forum-watch {{forum-channel-id}} {{filepath}}` command to watch files in forum-channel, a new forum-thread will be created for each file, and when code is updated, it's initial message is updated with the code, and the code updates is sent as a new message
4. Add `.watchfiles` in the same directory as `bot.py` to specify commands (one command on one line) that will run on bot startup, watch file syntax is `watch {{id-of-channel-to-send-in}} {{filepath}}`, and for forum-watch `forum-watch {{id-of-forum-to-send-in}} {{filepath}}`
5. Bot also watches .watchfiles for updates
6. Bot logs in a channel which can be provided using `LOGGING_CHANNEL_ID` in `.env`

## Env values

### Mandatory to run bot

- `BOT_TOKEN` which is your bot token 

### Risky to not provide

- `MENTOR_ID` ID of moderator or teacher role that will be able to command the bot. If not provided anyone can command the bot, thus if your running it on your system, then anyone can access the files on your system

### Recommended

- `STUDENT_ID` ID of student or whichever role that will get pinged to the code
- `LOGGING_CHANNEL_ID` Channel where your bot will log, if not provided bot will log in terminal

### Extra Configuration

- `FILE_CHECK_INTERVAL` After how much time should the Bot check the files to be watched (unit is seconds) (default: 3)
- `WATCHFILE_CHECK_INTERVAL` After how much time should the Bot if default files to be watched have been changed (in .watchfiles) (unit is seconds) (default: 7)

