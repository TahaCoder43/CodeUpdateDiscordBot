# CodeUpdate discord bot

Bots that upload code from file when it changes to discord server

put some files in the same folder as bot.py then use relative path to watch them and it will send the file in the server whenever it changes

make sure to provide in env

1. `MENTOR_ID` ID of moderator or teacher role that will be able to start the bot watching code
2. `STUDENT_ID` ID of student or whichever role that will get pinged to the code
3. `BOT_TOKEN` which is your bot token 

## Setup

You will have to create the bot yourself and copy paste in the code and run it

make sure to give the bot the neccesary permissions

## Usage

type in `$watch filepath` in any channel and it would send the code whenever it's changed in that channel

you can use "\" to escape spaces in filepath
