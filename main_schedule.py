import configparser
import datetime
import json

import discord

import database

from discord.ext import commands, tasks

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
guilds = json.loads(c["DISCORD"]["guilds"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = False
intents.guild_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")

    check_thresholds.start()


@tasks.loop(minutes=5)
async def check_thresholds():
    db_connection = database.get_db_connection()

    await bot.wait_until_ready()
    now = datetime.datetime.now()
    print(f"checking_thresholds: {now}")

    for guild in guilds:
        guild = int(guild)
        threshold_channel = bot.get_channel(database.get_alert_channel_in_db(db_connection, guild))
        for network in database.get_all_networks(db_connection):
            threshold: float = database.get_threshold_by_network(db_connection, network, guild)
            addresses = database.get_all_addresses_by_network(db_connection, network, guild)
            for address in addresses:
                try:
                    balance: float = database.get_balance(network, address)
                except Exception as e:
                    print(e)
                    db_connection.close()
                    return False

                database.update_balance(db_connection, network, address, balance)

                alerting = database.get_alerting_by_address(db_connection, network, address)
                token_abr = database.get_token_abr_by_network(db_connection, network)

                if (balance < threshold) and not alerting:
                    contacts = database.get_contacts_by_address(db_connection, address, guild)
                    if len(contacts) == 0 or contacts == "None":
                        print(f"**{addresses[address]} ({address[:6]}...{address[-4:]})** is below the threshold of {threshold} "
                              f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                        await threshold_channel.send(
                            f"**{addresses[address]} ({address[:6]}...{address[-4:]})** is below the threshold of {threshold} "
                            f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                    else:
                        print(
                            f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is below the threshold of {threshold} "
                            f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                        await threshold_channel.send(
                            f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is below the threshold of {threshold} "
                            f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                    database.set_alerting_by_address(db_connection, network, address, True)

                if (balance > threshold) and alerting:
                    contacts = database.get_contacts_by_address(db_connection, address, guild)
                    if len(contacts) == 0 or contacts == "None":
                        print(
                            f"**{addresses[address]} ({address[:6]}...{address[-4:]})** is back above the threshold of {threshold} "
                            f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                        await threshold_channel.send(
                            f"**{addresses[address]} ({address[:6]}...{address[-4:]})** is back above the threshold of {threshold} "
                            f"{token_abr}. It currently has a balance of {round(balance, 3)} {token_abr}.")
                    else:
                        print(
                            f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is back above the threshold of {threshold} "
                            f"{database.get_token_abr_by_network(db_connection, network)}")
                        await threshold_channel.send(
                            f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is back above the threshold of {threshold} "
                            f"{database.get_token_abr_by_network(db_connection, network)}")
                    database.set_alerting_by_address(db_connection, network, address, False)
    db_connection.close()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"the time: {now.strftime('%H:%M, %m/%d')}"))
    return True


bot.run(discord_token)
