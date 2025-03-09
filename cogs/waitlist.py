import discord
from discord.utils import get
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import time

COOLDOWN_TIME = 7 * 24 * 60 * 60

playerInfoDict = {}
currentlyTesting = {"macepot": [],
                    "ogmace": [],
                    "rodmace": [],
                    "rocketmace": [],
                    "diamace": [],
                    "classicmace": [],
                    "ltmace": []}
testingQueues = {"macepot": [],
                 "ogmace": [],
                 "rodmace": [],
                 "rocketmace": [],
                 "diamace": [],
                 "classicmace": [],
                 "ltmace": []}
active_queues = {}

REGIONS = ["NA", "EU", "AS", "AU", "ME", "SA", "AF"]
GAMEMODES = ["macepot", 
             "ogmace", 
             "rodmace", 
             "rocketmace", 
             "diamace", 
             "classicmace", 
             "ltmace"]
GAMEMODES_TIERS = ["Mace Pot", 
                   "OG Mace", 
                   "Rod Mace", 
                   "Rocket Mace", 
                   "DiaMace", 
                   "Classic Mace", 
                   "LT Mace"]
WAITLIST_NAMES = ["MacePot Waitlist", 
                  "OGMace Waitlist", 
                  "RodMace Waitlist", 
                  "RocketMace Waitlist", 
                  "DiaMace Waitlist", 
                  "ClassicMace Waitlist", 
                  "LTMace Waitlist"]
TESTER_ROLES = ["Mace Pot Tester", 
                "OG Mace Tester", 
                "Rod Mace Tester", 
                "Rocket Mace Tester", 
                "DiaMace Tester",
                "Classic Mace Tester", 
                "LT Mace Tester"]
SUBMODES_RANKS = ["Submodes Master", 
                  "Submodes Ace", 
                  "Submodes Specialist", 
                  "Submodes Cadet", 
                  "Submodes Novice", 
                  "Submodes Rookie"]
HIGHTIERS = ["HT1", "LT1", "HT2", "LT2", "HT3"]

intents = discord.Intents.default()
intents.messages = True
player_region = ""

class Waitlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    @app_commands.command(name="reqtest", description="Request Test Textbox")
    @app_commands.checks.has_permissions(administrator=True)
    async def reqtest(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if channel is None:
            await interaction.response.send_message("Invalid/No Channel", ephemeral=True)
        else:
            reqtest_description = """
            Upon applying, you will be added to a waitlist channel.
            Here you will be pinged when a tester of your region is available.

            • Region should be the region of the server you wish to test on

            • Gamemode should be the mace gamemode you wish to test on

            • Username should be the name of the account you will be testing on

            **🛑 Failure to provide authentic information will result in a denied test.**"""

            embeded_msg = discord.Embed(title="📝 Evaluation Testing Waitlist", description=reqtest_description, color=discord.Color.red())
            await channel.send(embed=embeded_msg, view=RequestTestUI())
            await interaction.response.send_message("Request Test Message Created", ephemeral=True)

    @app_commands.command(name="forcetest", description="Force Test a player")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
    gamemode=[
        app_commands.Choice(name="Mace Pot", value="macepot"),
        app_commands.Choice(name="OG Mace", value="ogmace"),
        app_commands.Choice(name="Rod Mace", value="rodmace"),
        app_commands.Choice(name="Rocket Mace", value="rocketmace"),
        app_commands.Choice(name="DiaMace", value="diamace"),
        app_commands.Choice(name="LT Mace", value="ltmace"),
        app_commands.Choice(name="Classic Mace", value="classicmace")
    ]
    )
    async def forcetest(self, interaction: discord.Interaction, user: discord.Member, gamemode: app_commands.Choice[str]):
        try:
            testee_id = user.id
            LoadInfoDict()
            waitlist_role = WAITLIST_NAMES[list.index(GAMEMODES, gamemode)]
            role_to_remove = get(interaction.guild.roles, name=waitlist_role)
            await interaction.user.remove_roles(role_to_remove)
            try:
                playerInfoDict[testee_id]["testing_gamemodes"].remove(gamemode_upper)
            except:
                pass
            gamemode_upper = gamemode.name
            username = playerInfoDict[testee_id]["mc_user"]
            tester = interaction.user.mention
            region = playerInfoDict[testee_id]["player_region"]
            previous_tier = playerInfoDict[testee_id]["tiers"][gamemode_upper]
            if not previous_tier:
                previous_tier = "Unranked"
            ticket_category = discord.utils.get(interaction.guild.categories, name=gamemode_upper)
            testee_user = interaction.guild.get_member(testee_id)
            tester_user = interaction.guild.get_member(interaction.user.id)
            channel = await interaction.guild.create_text_channel(f"{testee_user}-{tester_user}", category=ticket_category)
            playerInfoDict[testee_id]["testing_ticket_ids"][gamemode_upper] = channel.id
            testing_message = discord.Embed(title=f"{user.name}'s Information", color=discord.Color.blue())
            testing_message.add_field(name="Tester:",value=tester,inline=False)
            testing_message.add_field(name="Region:",value=region,inline=False)
            testing_message.add_field(name="Username:",value=username,inline=False)
            testing_message.add_field(name="Previous Rank:",value=previous_tier,inline=False)
            testing_message.set_thumbnail(url=interaction.user.avatar)
            await channel.send(content=f"{user.mention} {interaction.user.mention}", embed=testing_message)
            WriteInfoDict()
            await interaction.response.send_message(f"New Testing Ticket Created: {channel.mention}", ephemeral=True)
        except:
            await interaction.response.send_message(f"{user.mention} is unverified, please tell the user to verify first.", ephemeral=True)
            await channel.delete()
    
    @app_commands.command(name="forcetier", description="Give a player a tier without them openin a ticket")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
    gamemode=[
        app_commands.Choice(name="Mace Pot", value="macepot"),
        app_commands.Choice(name="OG Mace", value="ogmace"),
        app_commands.Choice(name="Rod Mace", value="rodmace"),
        app_commands.Choice(name="Rocket Mace", value="rocketmace"),
        app_commands.Choice(name="DiaMace", value="diamace"),
        app_commands.Choice(name="LT Mace", value="ltmace"),
        app_commands.Choice(name="Classic Mace", value="classicmace")
    ],
    tier=[
        app_commands.Choice(name="HT1", value="HT1"),
        app_commands.Choice(name="LT1", value="LT1"),
        app_commands.Choice(name="HT2", value="HT2"),
        app_commands.Choice(name="LT2", value="LT2"),
        app_commands.Choice(name="HT3", value="HT3"),
        app_commands.Choice(name="LT3", value="LT3"),
        app_commands.Choice(name="HT4", value="HT4"),
        app_commands.Choice(name="LT4", value="LT4"),
        app_commands.Choice(name="HT5", value="HT5"),
        app_commands.Choice(name="LT5", value="LT5"),
    ]
    )
    async def forcetier(self, interaction: discord.Interaction, user: discord.Member, gamemode: app_commands.Choice[str], tier: app_commands.Choice[str]):
        LoadInfoDict()
        try:
            previous_tier = playerInfoDict[user.id]["tiers"][gamemode]
            if previous_tier:
                previous_tier_role = discord.utils.get(interaction.guild.roles, name=f"{previous_tier} {gamemode}")
                if previous_tier_role:
                    await interaction.user.remove_roles(previous_tier_role)
            playerInfoDict[user.id]["tiers"][gamemode.name] = tier.name
            roles_to_remove = [discord.utils.get(interaction.guild.roles, name=role) for role in SUBMODES_RANKS]
            roles_to_remove = [role for role in roles_to_remove if role] 
            if roles_to_remove:
                await user.remove_roles(*roles_to_remove)
            submodes_rank = discord.utils.get(interaction.guild.roles, name=CalculateSubmodesRank(user))
            await interaction.user.add_roles(submodes_rank)
            WriteInfoDict()
            await interaction.response.send_message(f"{user.mention}'s {gamemode.name} tier has been successfully modified to {tier.name}.", ephemeral=True)
        except:
            await interaction.response.send_message(f"{user.mention} is unverified, please tell the user to verify first.", ephemeral=True)
    
    @app_commands.command(name="cooldownreset", description="Reset a player's testing cooldown")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
    gamemode=[
        app_commands.Choice(name="Mace Pot", value="macepot"),
        app_commands.Choice(name="OG Mace", value="ogmace"),
        app_commands.Choice(name="Rod Mace", value="rodmace"),
        app_commands.Choice(name="Rocket Mace", value="rocketmace"),
        app_commands.Choice(name="DiaMace", value="diamace"),
        app_commands.Choice(name="LT Mace", value="ltmace"),
        app_commands.Choice(name="Classic Mace", value="classicmace")
    ]
    )
    async def cdreset(self, interaction: discord.Interaction, user: discord.Member, gamemode: app_commands.Choice[str]): 
        LoadInfoDict()
        try:
            playerInfoDict[user.id]["testing_cooldowns"][gamemode.name] = 0.0
            await interaction.response.send_message(f"Cooldown has been reset for {user.mention}.", ephemeral=True)
            WriteInfoDict()
        except:
            await interaction.response.send_message(f"{user.mention} is unverified, please tell the user to verify first.", ephemeral=True)

    @app_commands.command(name="forceverify", description="Force verify a player")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
    region=[
        app_commands.Choice(name="NA", value="NA"),
        app_commands.Choice(name="EU", value="EU"),
        app_commands.Choice(name="AS", value="AS"),
        app_commands.Choice(name="AU", value="AU"),
        app_commands.Choice(name="ME", value="ME"),
        app_commands.Choice(name="SA", value="SA"),
        app_commands.Choice(name="AF", value="AF")
    ]
    )
    async def forceverify(self, interaction: discord.Interaction, user: discord.Member, mc_user: str, region: app_commands.Choice[str], testing_server: str):
        LoadInfoDict()
        if user.id not in playerInfoDict:
            playerInfoDict[user.id] = {
                "mc_user": "",
                "player_region": "",
                "testing_gamemodes": [],
                "testing_server": "",
                "testing_ticket_ids": {"Mace Pot": 0, "OG Mace": 0, "Rod Mace": 0, "Rocket Mace": 0, "DiaMace": 0, "LTMace": 0, "Classic Mace": 0},
                "tiers": {"Mace Pot": "", "OG Mace": "", "Rod Mace": "", "Rocket Mace": "", "DiaMace": "", "LTMace": "", "Classic Mace": ""},
                "testing_cooldowns": {"Mace Pot": 0.0, "OG Mace": 0.0, "Rod Mace": 0.0, "Rocket Mace": 0.0, "DiaMace": 0.0, "LTMace": 0.0, "Classic Mace": 0.0}
            }
        playerInfoDict[user.id]["mc_user"] = mc_user
        playerInfoDict[user.id]["player_region"] = region.value
        playerInfoDict[user.id]["testing_server"] = testing_server
        WriteInfoDict()
        await interaction.response.send_message(f"You have force verified {user.mention}", ephemeral=True)

    @app_commands.command(name="add", description="Add a player to a testing ticket")
    async def add(self, interaction: discord.Interaction, member: discord.Member):
        channel_name = interaction.channel.name
        testee_user = channel_name.split("-")[0]
        testee_account = discord.utils.get(interaction.guild.members, name=testee_user)
        if testee_account:
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = True
            overwrite.send_messages = True
            await interaction.channel.set_permissions(member, overwrite=overwrite)
            await interaction.response.send_message(f"{member.mention} has been added to this ticket.")
        else:
            await interaction.response.send_message("This is not a testing ticket!", ephemeral=True)   

    @app_commands.command(name="remove", description="remove a player from a testing ticket")
    async def remove(self, interaction: discord.Interaction, member: discord.Member):
        channel_name = interaction.channel.name
        testee_user = channel_name.split("-")[0]
        testee_account = discord.utils.get(interaction.guild.members, name=testee_user)
        if testee_account:
            await interaction.channel.set_permissions(member, overwrite=None)
            await interaction.response.send_message(f"{member.mention} has been removed from this ticket.")
        else:
            await interaction.response.send_message("This is not a testing ticket!", ephemeral=True)   

    @app_commands.command(name="leave", description="Leave the Queue or Waitlist")
    @app_commands.choices(
    gamemode=[
        app_commands.Choice(name="Mace Pot", value="macepot"),
        app_commands.Choice(name="OG Mace", value="ogmace"),
        app_commands.Choice(name="Rod Mace", value="rodmace"),
        app_commands.Choice(name="Rocket Mace", value="rocketmace"),
        app_commands.Choice(name="DiaMace", value="diamace"),
        app_commands.Choice(name="LT Mace", value="ltmace"),
        app_commands.Choice(name="Classic Mace", value="classicmace")
    ]
    )
    async def leave(self, interaction: discord.Interaction, gamemode : app_commands.Choice[str]):
        gamemode = gamemode.value
        if interaction.user.id in testingQueues[gamemode]:
            testingQueues[gamemode].remove(interaction.user.id)
            await interaction.response.send_message("You have left the Queue", ephemeral=True)
        else:
            if gamemode not in GAMEMODES:
                await interaction.response.send_message("Invalid Gamemode", ephemeral=True)
                return
            waitlist_role = WAITLIST_NAMES[list.index(GAMEMODES, gamemode)]
            testing_gamemode = GAMEMODES_TIERS[list.index(GAMEMODES, gamemode)]
            if any(role.name == waitlist_role for role in interaction.user.roles):
                LoadInfoDict()
                if interaction.user.id in playerInfoDict:
                    playerInfoDict[interaction.user.id]["testing_gamemodes"].remove(testing_gamemode)
                WriteInfoDict()
                role_to_remove = get(interaction.guild.roles, name=waitlist_role)
                await interaction.user.remove_roles(role_to_remove)
                await interaction.response.send_message("You have left the Waitlist", ephemeral=True)
            else:
                await interaction.response.send_message("You are not in the Queue or Waitlist", ephemeral=True)

    @app_commands.command(name="next", description="Move the Waitlist")
    @app_commands.checks.has_role("Verified Tester")
    async def next(self, interaction: discord.Interaction):
        for gamemode, user_list in currentlyTesting.items():
            if interaction.user.id in user_list:
                LoadInfoDict()
                gamemode_index = list.index(GAMEMODES, gamemode)
                gamemode_upper = GAMEMODES_TIERS[gamemode_index]
                testee_id = testingQueues[gamemode][0]
                username = playerInfoDict[testee_id]["mc_user"]
                tester = interaction.user.mention
                region = playerInfoDict[testee_id]["player_region"]
                previous_tier = playerInfoDict[testee_id]["tiers"][gamemode_upper]
                playerInfoDict[testee_id]["testing_gamemodes"].remove(gamemode_upper)
                waitlist_role = WAITLIST_NAMES[list.index(GAMEMODES, gamemode)]
                role_to_remove = get(interaction.guild.roles, name=waitlist_role)
                await interaction.user.remove_roles(role_to_remove)
                ticket_category = discord.utils.get(interaction.guild.categories, name=gamemode_upper)
                testee_user = interaction.guild.get_member(testee_id)
                tester_user = interaction.guild.get_member(interaction.user.id)
                channel = await interaction.guild.create_text_channel(f"{testee_user}-{tester_user}", category=ticket_category)
                playerInfoDict[testee_id]["testing_ticket_ids"][gamemode_upper] = channel.id
                testing_message = discord.Embed(title=f"<@!{testee_id}>'s Information", color=discord.Color.blue())
                testing_message.add_field(name="Tester:",value=tester,inline=False)
                testing_message.add_field(name="Region:",value=region,inline=False)
                testing_message.add_field(name="Username:",value=username,inline=False)
                testing_message.add_field(name="Previous Rank:",value=previous_tier,inline=False)
                testing_message.set_thumbnail(url=interaction.user.avatar)
                await channel.send(content=f"<@!{testee_id}> {interaction.user.mention}", embed=testing_message)
                WriteInfoDict()
                testingQueues[gamemode].pop(0)
                await interaction.response.send_message(f"New Testing Ticket Created: {channel.mention}", ephemeral=True)
                return
        await interaction.response.send_message("You are currently not testing", ephemeral=True)

    @app_commands.command(name="start", description="Start the Waitlist")
    @app_commands.checks.has_role("Verified Tester")
    @app_commands.choices(
    gamemode=[
        app_commands.Choice(name="Mace Pot", value="macepot"),
        app_commands.Choice(name="OG Mace", value="ogmace"),
        app_commands.Choice(name="Rod Mace", value="rodmace"),
        app_commands.Choice(name="Rocket Mace", value="rocketmace"),
        app_commands.Choice(name="DiaMace", value="diamace"),
        app_commands.Choice(name="LT Mace", value="ltmace"),
        app_commands.Choice(name="Classic Mace", value="classicmace")
    ]
    )
    async def start(self, interaction: discord.Interaction, gamemode : app_commands.Choice[str]):
        gamemode = gamemode.value
        if not gamemode in GAMEMODES:
            await interaction.response.send_message("Invalid Gamemode", ephemeral=True)
            return
        gamemode_index = list.index(GAMEMODES, gamemode)
        tester_role = TESTER_ROLES[gamemode_index]
        waitlist_role = WAITLIST_NAMES[gamemode_index]
        if not tester_role:
            await interaction.response.send_message("Tester Role does not Exist", ephemeral=True)
            return
        if any(role.name == tester_role for role in interaction.user.roles):
            for gmTesting, user_list in currentlyTesting.items():
                if interaction.user.id in user_list:
                    await interaction.response.send_message(f"You are already testing in {GAMEMODES_TIERS[list.index(GAMEMODES, gmTesting)]}", ephemeral=True)
                    break
            waitlist_channel = get(interaction.guild.channels, name=waitlist_role.replace(" ", "-").lower()) 
            currentlyTesting[gamemode].append(interaction.user.id)
            await interaction.response.send_message("Waitlist has started", ephemeral=True)
            await update_queue(waitlist_channel, gamemode)
        else:
            await interaction.response.send_message("You do not have permission to open this waitlist", ephemeral=True)

    @app_commands.command(name="stop", description="Stop the Waitlist")
    @app_commands.checks.has_role("Verified Tester")
    async def stop(self, interaction: discord.Interaction):
        for gmTesting, user_list in currentlyTesting.items():
            if interaction.user.id in user_list:
                if not gmTesting in GAMEMODES:
                    await interaction.response.send_message("Invalid Gamemode", ephemeral=True)
                    return
                gamemode_index = list.index(GAMEMODES, gmTesting)
                tester_role = TESTER_ROLES[gamemode_index]
                waitlist_role = WAITLIST_NAMES[gamemode_index]
                if not tester_role:
                    await interaction.response.send_message("Tester Role does not Exist", ephemeral=True)
                    return
                if any(role.name == tester_role for role in interaction.user.roles):
                    waitlist_channel = get(interaction.guild.channels, name=waitlist_role.replace(" ", "-").lower()) 
                    if interaction.user.id in currentlyTesting[gmTesting]:
                        currentlyTesting[gmTesting].remove(interaction.user.id)
                        await stop_queue(waitlist_channel, gmTesting)
                        await interaction.response.send_message("Waitlist has stopped", ephemeral=True)
                    else:
                        await interaction.response.send_message("You are currently not testing", ephemeral=True)
                else:
                    await interaction.response.send_message("You do not have permission to stop this waitlist", ephemeral=True)        
                break
    
    @app_commands.command(name="skip", description="Skip this ticket")
    @app_commands.checks.has_role("Verified Tester")
    async def skip(self, interaction: discord.Interaction):
        channel_name = interaction.channel.name
        gamemode = interaction.channel.category.name
        testee_user = channel_name.split("-")[0]
        testee_account = discord.utils.get(interaction.guild.members, name=testee_user)
        LoadInfoDict()
        if testee_account:
            try:
                playerInfoDict[testee_account.id]["testing_ticket_ids"][gamemode] = 0
                WriteInfoDict()
                discontinued = discord.Embed(title=f"Test discontinued", description="Closing in 5 seconds...", color=discord.Color.blue())
                await interaction.response.send_message(embed=discontinued)
                await asyncio.sleep(5)
                await interaction.channel.delete()
            except:
                await interaction.response.send_message("You are not verified. Please reverify", ephemeral=True)   
        else:
            await interaction.response.send_message("This is not a testing ticket!", ephemeral=True)   

    @app_commands.command(name="close", description="Close this ticket")
    @app_commands.checks.has_role("Verified Tester")
    @app_commands.choices(
    tier=[
        app_commands.Choice(name="Test Discontinued", value="Test Discontinued"),
        app_commands.Choice(name="HT1", value="HT1"),
        app_commands.Choice(name="LT1", value="LT1"),
        app_commands.Choice(name="HT2", value="HT2"),
        app_commands.Choice(name="LT2", value="LT2"),
        app_commands.Choice(name="HT3", value="HT3"),
        app_commands.Choice(name="LT3", value="LT3"),
        app_commands.Choice(name="HT4", value="HT4"),
        app_commands.Choice(name="LT4", value="LT4"),
        app_commands.Choice(name="HT5", value="HT5"),
        app_commands.Choice(name="LT5", value="LT5"),
    ]
    )
    async def close(self, interaction: discord.Interaction, tier : app_commands.Choice[str]):
        channel_name = interaction.channel.name
        gamemode = interaction.channel.category.name
        testee_user = channel_name.split("-")[0]
        testee_account = discord.utils.get(interaction.guild.members, name=testee_user)
        LoadInfoDict()
        if testee_account:
            try:
                if tier.value == "Test Discontinued":
                    playerInfoDict[testee_account.id]["testing_ticket_ids"][gamemode] = 0
                    discontinued = discord.Embed(title=f"Test discontinued", description="Closing in 5 seconds...", color=discord.Color.blue())
                    await interaction.response.send_message(embed=discontinued)
                    await asyncio.sleep(5)
                    await interaction.channel.delete()
                    return
                results_channel = discord.utils.get(interaction.guild.channels, name="🏆┃results")
                if results_channel:
                    tier_role = discord.utils.get(interaction.guild.roles, name=f"{tier.value} {gamemode}")
                    if tier_role:
                        await interaction.user.add_roles(tier_role)
                    else:
                        await interaction.response.send_message("Tier role does not exist", ephemeral=True)
                        return
                    previous_tier = playerInfoDict[testee_account.id]["tiers"][gamemode]
                    if not previous_tier:
                        previous_tier = "Unranked"
                    else:
                        previous_tier_role = discord.utils.get(interaction.guild.roles, name=f"{previous_tier} {gamemode}")
                        if previous_tier_role:
                            await interaction.user.remove_roles(previous_tier_role)
                    playerInfoDict[testee_account.id]["tiers"][gamemode] = tier.value
                    roles_to_remove = [discord.utils.get(interaction.guild.roles, name=role) for role in SUBMODES_RANKS]
                    roles_to_remove = [role for role in roles_to_remove if role] 
                    if roles_to_remove:
                        await testee_account.remove_roles(*roles_to_remove)
                    submodes_rank = discord.utils.get(interaction.guild.roles, name=CalculateSubmodesRank(testee_account))
                    await interaction.user.add_roles(submodes_rank)
                    username = playerInfoDict[testee_account.id]["mc_user"]
                    tester = interaction.user.mention
                    region = playerInfoDict[testee_account.id]["player_region"]
                    playerInfoDict[testee_account.id]["testing_ticket_ids"][gamemode] = 0
                    playerInfoDict[testee_account.id]["testing_cooldowns"][gamemode] = time.time()
                    embeded_msg = discord.Embed(title=f"{gamemode} Test Result 🏆", color=discord.Color.red())
                    embeded_msg.add_field(name="Tester:",value=tester,inline=False)
                    embeded_msg.add_field(name="Region:",value=region,inline=False)
                    embeded_msg.add_field(name="Username:",value=username,inline=False)
                    embeded_msg.add_field(name="Previous Rank:",value=previous_tier,inline=False)
                    embeded_msg.add_field(name="Rank Earned:",value=tier.value,inline=False)
                    embeded_msg.set_thumbnail(url=interaction.user.avatar)
                    WriteInfoDict()
                    await results_channel.send(content=testee_account.mention, embed=embeded_msg)
                    closing = discord.Embed(title=f"Tier received: {tier.value}", description="Closing in 5 seconds...", color=discord.Color.blue())
                    await interaction.response.send_message(embed=closing)
                    await asyncio.sleep(5)
                    await interaction.channel.delete()
                else:
                    await interaction.response.send_message("Results channel does not exist", ephemeral=True)   
            except:
                await interaction.response.send_message("You are not verified. Please reverify", ephemeral=True)   
        else:
            await interaction.response.send_message("This is not a testing ticket!", ephemeral=True)   
    

async def update_queue(channel: discord.TextChannel, gamemode = str):
    if channel.id in active_queues:
        return
    waitlist_message = f"""
    ⏱️ The queue updates every 1 minute.
    Use `/leave` if you wish to be removed from the waitlist or queue.

    __**Queue**__:
    
    **Active Testers**:
    """
    for index, user_id in enumerate(currentlyTesting[gamemode], start=1):
        waitlist_message += f"{index}. <@!{user_id}>\n"
    
    embeded_msg = discord.Embed(title=f"Tester(s) Available!", description=waitlist_message, color=discord.Color.blue())
    message = await channel.send(content="@here", embed=embeded_msg, view=WaitlistButton())

    async def update_loop():
        try:
            while True:
                await asyncio.sleep(60) 
                waitlist_message = f"""
                ⏱️ The queue updates every 1 minute.
                Use `/leave` if you wish to be removed from the waitlist or queue.

                __**Queue**__:
                """
                for index, user_id in enumerate(testingQueues[gamemode], start=1):
                    waitlist_message += f"{index}. <@!{user_id}>\n"

                waitlist_message += """
                **Active Testers**:
                """
                
                for index, user_id in enumerate(currentlyTesting[gamemode], start=1):
                    waitlist_message += f"{index}. <@!{user_id}>\n"
                
                embeded_msg = discord.Embed(title=f"Tester(s) Available!", description=waitlist_message, color=discord.Color.blue())
                await message.edit(content="@here", embed=embeded_msg)
        except asyncio.CancelledError:
            await message.delete()

    task = asyncio.create_task(update_loop())
    active_queues[channel.id] = task

class WaitlistButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        button = discord.ui.Button(label="Join Queue", style=discord.ButtonStyle.blurple)
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        gamemode_lower = interaction.channel.name.replace("-waitlist", "")
        if interaction.user.id in testingQueues[gamemode_lower]:
            await interaction.response.send_message("You are already in the queue for this gamemode.", ephemeral=True)
            return
        try:
            LoadInfoDict()
            gamemode_index = list.index(GAMEMODES, gamemode_lower)
            gamemode = GAMEMODES_TIERS[gamemode_index]
            if gamemode in playerInfoDict[interaction.user.id]["testing_gamemodes"]:
                gamemode = gamemode.replace(" ", "").lower()
                testingQueues[gamemode].append(interaction.user.id)
                await interaction.response.send_message("You have joined the queue.", ephemeral=True)
            else:
                await interaction.response.send_message("You have not joined the waitlist for this gamemode.", ephemeral=True)
        except KeyError:
            await interaction.response.send_message("You have no player data associated with you. Please leave and rejoin the waitlist.", ephemeral=True)

async def stop_queue(channel: discord.TextChannel, gamemode=str):
    if not currentlyTesting[gamemode]:
        task = active_queues.pop(channel.id, None)
        if task:
            task.cancel()

class RequestTestUI(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(JoinWaitlistDropdown())
        button = discord.ui.Button(label="Verify", style=discord.ButtonStyle.blurple)
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificationModal())

class JoinWaitlistDropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=gamemode) for gamemode in GAMEMODES_TIERS]
        super().__init__(placeholder="Pick a Gamemode...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        try:
            LoadInfoDict()
            time_since_last = time.time() - playerInfoDict[interaction.user.id]["testing_cooldowns"][selected_value]
            if time_since_last < COOLDOWN_TIME:
                remaining_time = COOLDOWN_TIME - time_since_last
                remaining_days = int(remaining_time // (24 * 60 * 60))
                remaining_hours = int((remaining_time % (24 * 60 * 60)) // 3600)
                remaining_minutes = int((remaining_time % 3600) // 60)
                await interaction.response.send_message(f"You are on cooldown, try again in {remaining_days} days, {remaining_hours} hours, and {remaining_minutes} minutes.", ephemeral=True)
                return
            if playerInfoDict[interaction.user.id]["testing_server"] == "":
                await interaction.response.send_message("You have to verify before entering the waitlist", ephemeral=True)
                return
            if playerInfoDict[interaction.user.id]["tiers"][selected_value] in HIGHTIERS:
                if playerInfoDict[interaction.user.id]["tiers"][selected_value] == "HT1":
                    await interaction.response.send_message(f"You are HT1 in {selected_value}, you cannot test further.", ephemeral=True)
                    return
                testee_id = interaction.user.id
                LoadInfoDict()
                username = playerInfoDict[testee_id]["mc_user"]
                region = playerInfoDict[testee_id]["player_region"]
                previous_tier = playerInfoDict[testee_id]["tiers"][selected_value]
                if not previous_tier:
                    previous_tier = "Unranked"
                ticket_category = discord.utils.get(interaction.guild.categories, name=selected_value)
                testee_user = interaction.guild.get_member(testee_id)
                tier_index = HIGHTIERS.index(previous_tier) - 1
                tier = HIGHTIERS[tier_index]
                channel = await interaction.guild.create_text_channel(f"{testee_user}-{tier}", category=ticket_category)
                playerInfoDict[testee_id]["testing_ticket_ids"][selected_value] = channel.id
                testing_message = discord.Embed(title=f"{interaction.user.name}'s Information", color=discord.Color.blue())
                testing_message.add_field(name="Region:",value=region,inline=False)
                testing_message.add_field(name="Username:",value=username,inline=False)
                testing_message.add_field(name="Previous Rank:",value=previous_tier,inline=False)
                testing_message.set_thumbnail(url=interaction.user.avatar)
                await channel.send(content=interaction.user.mention, embed=testing_message)
                WriteInfoDict()
                await interaction.response.send_message(f"New High Testing Ticket Created: {channel.mention}", ephemeral=True)
                return
            waitlist_role = discord.utils.get(interaction.guild.roles, name=WAITLIST_NAMES[list.index(GAMEMODES_TIERS, selected_value)])
            if playerInfoDict[interaction.user.id]["testing_ticket_ids"][selected_value] != 0:
                await interaction.response.send_message(f'You already have a ticket open for this gamemode: <#{playerInfoDict[interaction.user.id]["testing_ticket_ids"][selected_value]}>', ephemeral=True) 
                return
            if not waitlist_role:
                await interaction.response.send_message("Waitlist Role does not Exist", ephemeral=True)
                return
            if waitlist_role in interaction.user.roles:
                await interaction.response.send_message("You have already joined the Waitlist for this gamemode", ephemeral=True)
                return
            await interaction.user.add_roles(waitlist_role)
            playerInfoDict[interaction.user.id]["testing_gamemodes"].append(selected_value)
            WriteInfoDict()
            await interaction.response.send_message("You have joined the Waitlist", ephemeral=True)
        except KeyError:
            await interaction.response.send_message("You have to verify before entering the waitlist", ephemeral=True)
            
class VerificationModal(discord.ui.Modal, title="Verify your account details"):
    mc_user = discord.ui.TextInput(label="Your Minecraft Username", placeholder="e.g. Blubbie_", required=True, style=discord.TextStyle.short)
    player_region = discord.ui.TextInput(label="Your Region", placeholder="e.g. NA, EU, AS", required=True, style=discord.TextStyle.short)
    testing_server = discord.ui.TextInput(label="Your Preferred Testing Server", placeholder="e.g. na.catpvp.xyz", required=True, style=discord.TextStyle.short)
    
    async def on_submit(self, interaction: discord.Interaction):
        player_region = self.player_region.value.replace(" ", "").upper()
        if not player_region in REGIONS:
            await interaction.response.send_message("Invalid Region", ephemeral=True)
            return
        LoadInfoDict()
        if interaction.user.id not in playerInfoDict:
            playerInfoDict[interaction.user.id] = {
                "mc_user": "",
                "player_region": "",
                "testing_gamemodes": [],
                "testing_server": "",
                "testing_ticket_ids": {"Mace Pot": 0, "OG Mace": 0, "Rod Mace": 0, "Rocket Mace": 0, "DiaMace": 0, "LT Mace": 0, "Classic Mace": 0},
                "tiers": {"Mace Pot": "", "OG Mace": "", "Rod Mace": "", "Rocket Mace": "", "DiaMace": "", "LT Mace": "", "Classic Mace": ""},
                "testing_cooldowns": {"Mace Pot": 0.0, "OG Mace": 0.0, "Rod Mace": 0.0, "Rocket Mace": 0.0, "DiaMace": 0.0, "LT Mace": 0.0, "Classic Mace": 0.0}
            }
        playerInfoDict[interaction.user.id]["mc_user"] = self.mc_user.value
        playerInfoDict[interaction.user.id]["player_region"] = self.player_region.value
        playerInfoDict[interaction.user.id]["testing_server"] = self.testing_server.value
        WriteInfoDict()
        await interaction.response.send_message("You have successfully verified. You may join the waitlist", ephemeral=True)

def CalculateSubmodesRank(user_id):
    points = 0
    for gamemode in playerInfoDict[user_id]["tiers"]:
        tier = playerInfoDict[user_id]["tiers"][gamemode]
        if tier != "":
            match tier:
                case "HT1":
                    points += 60
                case "LT1":
                    points += 44
                case "HT2":
                    points += 28
                case "LT2":
                    points += 16
                case "HT3":
                    points += 10
                case "LT3":
                    points += 6
                case "HT4":
                    points += 4
                case "LT4":
                    points += 3
                case "HT5":
                    points += 2
                case "LT5":
                    points += 1
    rank = ""
    if points >= 200:
        rank = SUBMODES_RANKS[0]
    elif points >= 100:
        rank = SUBMODES_RANKS[1]
    elif points >= 50:
        rank = SUBMODES_RANKS[2]
    elif points >= 20:
        rank = SUBMODES_RANKS[3]
    elif points >= 10:
        rank = SUBMODES_RANKS[4]
    else:
        rank = SUBMODES_RANKS[5]
    
    return rank

def LoadInfoDict():
    global playerInfoDict
    with open("playerInfoDict.json", "r") as f:
        playerInfoDict = json.load(f)
    playerInfoDict = {int(key): value for key, value in playerInfoDict.items()}

def WriteInfoDict():
    global playerInfoDict
    with open("playerInfoDict.json", "w") as f:
        json.dump(playerInfoDict, f, indent=4)

async def setup(bot):
    await bot.add_cog(Waitlist(bot))
