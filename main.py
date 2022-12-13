import configparser
import re

import discord
from discord import app_commands
from discord.ext import commands

import database

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True
ephemeral = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
#    synced = await bot.tree.sync()
#    print(f"Synced {len(synced)} commands")


@bot.tree.command(name="add-address")
@app_commands.describe(network="Which network?", address="The address to track")
async def add_address(interaction: discord.Interaction, network: str, address: str):
    db_connection = database.get_db_connection()
    address = address.lower()
    network = int(get_network_id(network))
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        db_connection.close()
        return

    if not valid_address(address):
        await interaction.response.send_message(f"Address does not appear to be a valid.", ephemeral=ephemeral)
        db_connection.close()
        return

    if address in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id):
        await interaction.response.send_message(f"Address is already being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    await interaction.response.send_message(f"Address {address[:6]}...{address[-4:]} has been added to the "
                                            f"{database.get_network_name_by_id(db_connection, network)} watch list. ", ephemeral=ephemeral)

    addr_balance = database.get_balance(network, address)
    database.add_address_to_db(db_connection, network, address, addr_balance, interaction.guild_id)

    db_connection.close()


@bot.tree.command(name="remove-address")
@app_commands.describe(network="Which network?", address="The address to remove")
async def remove_address(interaction: discord.Interaction, network: str, address: str):
    db_connection = database.get_db_connection()
    network = get_network_id(network)
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        return

    if address not in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id):
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        return

    database.remove_address_from_db(db_connection, network, address, interaction.guild_id)

    await interaction.response.send_message(f"Address {address[:6]}...{address[-4:]} has been removed from the "
                                            f"{database.get_network_name_by_id(db_connection, network)} watch list.", ephemeral=ephemeral)
    db_connection.close()


@bot.tree.command(name="list-addresses")
@app_commands.describe(network="Which network?")
async def list_addresses(interaction: discord.Interaction, network: str):
    db_connection = database.get_db_connection()
    network = get_network_id(network)
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        return

    addresses = database.get_all_addresses_by_network(db_connection, network, interaction.guild_id)

    response = f"The following addresses are being watched on {database.get_network_name_by_id(db_connection, network)}:\n"
    for addr in addresses:
        response = response + addr + "\n"

    await interaction.response.send_message(response, ephemeral=ephemeral)
    db_connection.close()


@bot.tree.command(name='add-contact', description='add-contacts @user1 (@user2...)')
async def add_contacts(interaction: discord.Interaction, address: str, user: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id):
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    database.add_contacts_for_address(db_connection, user, address, interaction.guild_id)
    message = address + " now has the following contacts: " + database.get_contacts_by_address(db_connection, address, interaction.guild_id)
    await interaction.response.send_message(message, ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name='remove-contact', description='$contacts-remove [validator id] @user1 (@user2...)')
# @commands.has_any_role(*secrets.LISTENER_ROLES)
async def remove_contacts(interaction: discord.Interaction, address: str, user: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id):
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    database.remove_contacts_for_address(db_connection, address, user, interaction.guild_id)
    message = address + " now has the following contacts: " + database.get_contacts_by_address(db_connection, address, interaction.guild_id)
    await interaction.response.send_message(message, ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name='get-contacts', description='$contacts-remove [validator id] @user1 (@user2...)')
# @commands.has_any_role(*secrets.LISTENER_ROLES)
async def get_contacts(interaction: discord.Interaction, address: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id):
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return
    message = address + " has the following contacts: " + database.get_contacts_by_address(db_connection, address, interaction.guild_id)
    await interaction.response.send_message(message)
    db_connection.close()
    return


@bot.tree.command(name="set-threshold")
@app_commands.describe(network="Which network?", threshold="The amount to alert on")
async def set_threshold(interaction: discord.Interaction, network: str, threshold: float):
    # error handling
    db_connection = database.get_db_connection()
    network = get_network_id(network)
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        return

    database.set_threshold_in_db(db_connection, network, threshold, interaction.guild_id)
    await interaction.response.send_message(
        f"{database.get_network_name_by_id(db_connection, network)}'s threshold has been updated to {threshold}.", ephemeral=ephemeral)
    db_connection.close()
    return


def get_network_id(network: str):
    if network.lower() == "ethereum" or network.lower() == "ethereum mainnet" or network == "1":
        return 1
    elif network.lower() == "goerli" or network.lower() == "ethereum goerli" or network.lower() == "goerli testnet" or network == "5":
        return 5
    elif network.lower() == "bnb chain" or network.lower() == "bnb" or network.lower() == "bsc chain" or network == "56":
        return 56
    elif network.lower() == "bnb chain testnet" or network.lower() == "bnb testnet" or network.lower() == "bsc chain testnet" or network == "97":
        return 97
    elif network.lower() == "polygon" or network.lower() == "polygon mainnet" or network == "137":
        return 137
    elif network.lower() == "mumbai" or network.lower() == "polygon mumbai" or network.lower() == "polygon testnet" or network.lower() == "mumbai testnet" or network == "80001":
        return 80001
    elif network.lower() == "arbitrum" or network.lower() == "arbitrum mainnet" or network == "42161":
        return 42161
    elif network.lower() == "arbitrum goerli" or network.lower() == "arbitrum testnet" or network == "421611":
        return 421611
    return 0


def valid_address(address):
    if len(address) == 42 and re.search('0[xX][0-9a-fA-F]{40}', address) and ('[' not in address):
        return True
    return False


bot.run(discord_token)
