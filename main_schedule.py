import configparser

import discord

import database
from database import get_db_connection

from discord.ext import commands, tasks

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
threshold_response_channel = int(c["DISCORD"]["threshold_response_channel"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = False
intents.guild_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)
start = True

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
    check_thresholds.start()


@tasks.loop(seconds=30)
async def check_thresholds():
    db_connection = get_db_connection()

    await bot.wait_until_ready()
    print("updating validators")
    threshold_channel = bot.get_channel(threshold_response_channel)
    error_channel = bot.get_channel(e_channel)
    for network in database.get_all_networks(db_connection):
        threshold: float = database.get_threshold_by_network(db_connection, network)
        for address in database.get_all_addresses_by_network(db_connection, network):

            balance: float = database.get_balance(network, address)
            database.update_balance(db_connection, network, address, balance)
            alerting = database.get_alerting_by_address(db_connection, network, address)

            if (balance < threshold) and not alerting:
                contacts = database.get_contacts_by_address(db_connection, address)
                await threshold_channel.send(f"{contacts}, **{address}** is below the threshold of {threshold} "
                                             f"{database.get_token_abr_by_network(db_connection, network)}")
                database.set_alerting_by_address(db_connection, network, address, True)

            if (balance > threshold) and alerting:
                contacts = database.get_contacts_by_address(db_connection, address)
                await threshold_channel.send(f"{contacts}, **{address}** is below the threshold of {threshold} "
                                             f"{database.get_token_abr_by_network(db_connection, network)}")
                database.set_alerting_by_address(db_connection, network, address, True)

    db_connection.close()
    return


bot.run(discord_token)
