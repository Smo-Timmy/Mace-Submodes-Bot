import discord
from discord.ext import commands, tasks
import os
import asyncio
import webserver
from itertools import cycle

TOKEN = os.environ["DISCORD_TOKEN"]

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

status_messages = cycle([
    "Mace Pot", 
    "OG Mace", 
    "Rod Mace", 
    "Rocket Mace", 
    "DiaMace", 
    "Classic Mace", 
    "LT Mace"
])

@tasks.loop(seconds=180)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status_messages)))

@bot.event
async def on_ready():
    print('Hello! Mace Submodes Bot is Ready!')
    change_status.start() 
    try:
        sync_commands = await bot.tree.sync()
        print(f"Synced {len(sync_commands)} commands.")

    except Exception as e:
        print("An error with syncing application commands has occured:", e)

@bot.tree.command(name="hello", description="Says hello back to the person who ran the command.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"{interaction.user.mention} Hello there!", ephemeral=True)


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

webserver.keep_alive()
asyncio.run(main())
