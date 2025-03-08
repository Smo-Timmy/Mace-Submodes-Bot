import discord
from discord.ext import commands
import os
import asyncio
import webserver

TOKEN = os.environ["DISCORD_TOKEN"]

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

bot_status = "Mace Submodes"

@bot.event
async def on_ready():
    print('Hello! Mace Submodes Bot is Ready!')
    await bot.change_presence(activity=discord.Game(bot_status))
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