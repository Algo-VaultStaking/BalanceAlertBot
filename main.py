import configparser
import json
import re

import discord
from discord import app_commands
from discord.ext import commands, tasks
from web3 import Web3

import database

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
ADMIN_ROLES = c["DISCORD"]["admin_roles"]
ephemeral = bool(True if str(c["DISCORD"]["ephemeral"]) == "True" else False)
guilds = json.loads(c["DISCORD"]["guilds"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
#    synced = await bot.tree.sync()
#    print(f"Synced {len(synced)} commands")


@bot.tree.command(name="add-address", description="Track the balance of a new address.")
@app_commands.describe(network="The network of the address.", address="The address to track.")
async def add_address(interaction: discord.Interaction, network: str, address: str, label: str):
    db_connection = database.get_db_connection()
    network = int(get_network_id(network))

    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        db_connection.close()
        return

    if not valid_address(address):
        await interaction.response.send_message(f"Address does not appear to be a valid.", ephemeral=ephemeral)
        db_connection.close()
        return

    address = Web3.toChecksumAddress(address)

    if address in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id).keys():
        await interaction.response.send_message(f"Address is already being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    addr_balance = database.get_balance(network, address)
    database.add_address_to_db(db_connection, network, address, label, addr_balance, interaction.guild_id)
    token_abr = database.get_token_abr_by_network(db_connection, network)

    await interaction.response.send_message(f"Address {address[:6]}...{address[-4:]} has been added to the "
                                            f"{database.get_network_name_by_id(db_connection, network)} watch list.\n"
                                            f"It has a balance of {round(addr_balance,3)} {token_abr}.", ephemeral=ephemeral)

    db_connection.close()


@bot.tree.command(name="remove-address", description="Stop tracking an address's balance.")
@app_commands.describe(network="The network of the address", address="The address or label to remove")
async def remove_address(interaction: discord.Interaction, network: str, address: str):
    db_connection = database.get_db_connection()
    network = get_network_id(network)
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        db_connection.close()
        return

    if address not in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id).keys() and \
            address not in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id).values():
        await interaction.response.send_message(f"Address/Label is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    if address[:2] == "0x":
        database.remove_address_from_db_by_address(db_connection, network, address, interaction.guild_id)
        await interaction.response.send_message(f"Address {address[:6]}...{address[-4:]} has been removed from the "
                                                f"{database.get_network_name_by_id(db_connection, network)} watch list.",
                                                ephemeral=ephemeral)
    else:
        database.remove_address_from_db_by_label(db_connection, network, address, interaction.guild_id)
        await interaction.response.send_message(f"{address} has been removed from the "
                                                f"{database.get_network_name_by_id(db_connection, network)} watch list.",
                                                ephemeral=ephemeral)

    db_connection.close()


@bot.tree.command(name="list-balances", description="List all address balances for a specific network.")
@app_commands.describe(network="The network to search.")
async def list_balances(interaction: discord.Interaction, network: str):
    db_connection = database.get_db_connection()
    network = get_network_id(network)
    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        db_connection.close()
        return

    network_name = database.get_network_name_by_id(db_connection, network)
    addresses = database.get_all_addresses_by_network(db_connection, network, interaction.guild_id)
    balances = database.get_balances_by_network(db_connection, network, interaction.guild_id)
    token = database.get_token_abr_by_network(db_connection, network)

    if addresses == {}:
        await interaction.response.send_message(f"No address are being tracked on {network_name}", ephemeral=ephemeral)
        db_connection.close()
        return

    response = f"The following addresses are being watched on {network_name}:"
    for addr in addresses:
        response = f"{response}\n{addresses[addr]} ({addr[:6]}...{addr[-4:]}) has a balance of {balances[addr]} {token}"

    await interaction.response.send_message(response, ephemeral=ephemeral)
    db_connection.close()


@bot.tree.command(name="list-all-balances", description="List all address balances for all networks.")
@app_commands.describe()
async def list_all_balances(interaction: discord.Interaction):
    db_connection = database.get_db_connection()
    response = ""
    for network in get_all_network_ids():
        network_name = database.get_network_name_by_id(db_connection, network)
        addresses = database.get_all_addresses_by_network(db_connection, network, interaction.guild_id)
        balances = database.get_balances_by_network(db_connection, network, interaction.guild_id)
        token = database.get_token_abr_by_network(db_connection, network)

        if addresses != {}:
            response += f"-- **{network_name}**:\n"
            for addr in addresses:
                response += f"**{addresses[addr]} ({addr[:6]}...{addr[-4:]})**: {balances[addr]} {token}\n"

            response += "\n"
    if response == "":
        response = "No addresses are being tracked."
    await interaction.response.send_message(response, ephemeral=ephemeral)
    db_connection.close()


@bot.tree.command(name="list-networks", description="List all available networks.")
@app_commands.describe()
async def list_networks(interaction: discord.Interaction):
    response = "The following networks are available, and either the name or ID can be used in commands:\n" \
               "Ethereum (ID: 1)\n" \
               "Ethereum Goerli (ID: 5)\n" \
               "Arbitrum (ID: 42161)\n" \
               "Arbitrum Goerli (ID: 421611)\n" \
               "BNB Chain (ID: 56)\n" \
               "BNB Chain Testnet (ID: 97)\n" \
               "Polygon (ID: 137)\n" \
               "Polygon Mumbai (ID: 80001)\n" \
               "Optimism (ID: 10)\n" \
               "Optimism Goerli (ID: 420)\n" \
               "Gnosis(ID: 100)"

    await interaction.response.send_message(response, ephemeral=ephemeral)


@bot.tree.command(name='add-contact', description='Add a contact for a specific address/label.')
@app_commands.describe(address="The address/label to add a contact for.", user="The contact to notify if the address is low.")
async def add_contacts(interaction: discord.Interaction, address: str, user: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id).keys() and \
            address not in database.get_all_addresses(db_connection, interaction.guild_id).values():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    if not re.search('^<@[0-9]*>$', user):
        await interaction.response.send_message(f"Please tag a user in the User field.", ephemeral=ephemeral)
        db_connection.close()
        return

    true_addr = database.get_addresses_by_label(db_connection, address, interaction.guild_id) if address[:2] != "0x" else address

    if user in database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id):
        await interaction.response.send_message(f"User is already a contact.", ephemeral=ephemeral)
        db_connection.close()
        return

    database.add_contacts_for_address(db_connection, user, true_addr, interaction.guild_id)

    message = address + " now has the following contacts: " + database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id)
    await interaction.response.send_message(message, ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name='remove-contact', description='Remove a contact for a specific address.')
@app_commands.describe(address="The address to remove a contact for.", user="The contact to remove from the address.")
async def remove_contacts(interaction: discord.Interaction, address: str, user: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id).keys() and \
            address not in database.get_all_addresses(db_connection, interaction.guild_id).values():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    true_addr = database.get_addresses_by_label(db_connection, address, interaction.guild_id) if address[:2] != "0x" else address

    if true_addr not in database.get_all_addresses(db_connection, interaction.guild_id).keys():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    database.remove_contacts_for_address(db_connection, true_addr, user, interaction.guild_id)
    contacts = database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id)
    if len(contacts) == 0 or contacts == "None":
        message = address + " does not have any contacts."
    else:
        message = address + " now has the following contacts: " + contacts
    await interaction.response.send_message(message, ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name='get-contacts', description='Get all contacts for a specific address.')
@app_commands.describe(address="The address to query.")
async def get_contacts(interaction: discord.Interaction, address: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id).keys() and \
            address not in database.get_all_addresses(db_connection, interaction.guild_id).values():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    true_addr = database.get_addresses_by_label(db_connection, address, interaction.guild_id) if address[:2] != "0x" else address

    if true_addr not in database.get_all_addresses(db_connection, interaction.guild_id).keys():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    contacts = database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id)
    if len(contacts) == 0 or contacts == "None":
        message = address + " does not have any contacts."
    else:
        message = address + " has the following contacts: " + contacts
    await interaction.response.send_message(message, ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name="set-threshold", description="[Admins only] Set a new threshold for a network.")
@app_commands.describe(network="The network to set the threshold.", threshold="The minimum tokens to alert on")
async def set_threshold(interaction: discord.Interaction, network: str, threshold: float):
    admin = False
    for role in interaction.user.roles:
        if str(role) in ADMIN_ROLES:
            admin = True

    if not admin:
        await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
        return

    db_connection = database.get_db_connection()
    network = get_network_id(network)

    if network == 0:
        await interaction.response.send_message(f"This chain is not supported.", ephemeral=ephemeral)
        db_connection.close()
        return

    database.set_threshold_in_db(db_connection, network, threshold, interaction.guild_id)
    await interaction.response.send_message(
        f"{database.get_network_name_by_id(db_connection, network)}'s threshold has been updated to {threshold}.", ephemeral=ephemeral)
    db_connection.close()
    return


@bot.tree.command(name="set-alerting-channel", description="[Admins only] Change which channel receives threshold alerts.")
@app_commands.describe(channel_id="The ID of the channel that should receive alert messages (right-click the channel, click Copy ID).")
async def set_alerting_channel(interaction: discord.Interaction, channel_id: str):
    admin = False
    for role in interaction.user.roles:
        if str(role) in ADMIN_ROLES:
            admin = True

    if not admin:
        await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
        return

    db_connection = database.get_db_connection()
    channel = int(channel_id)
    database.set_alert_channel_in_db(db_connection, channel, interaction.guild_id)
    await interaction.response.send_message(
        f"The alert channel has been updated to <#{database.get_alert_channel_in_db(db_connection, interaction.guild_id)}>.", ephemeral=ephemeral)
    db_connection.close()
    return


def get_all_network_ids():
    return [1, 5, 56, 97, 137, 80001, 42161, 421611, 10, 420]


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
    elif network.lower() == "optimism" or network.lower() == "optimism mainnet" or network == "10":
        return 10
    elif network.lower() == "optimism goerli" or network.lower() == "optimism testnet" or network == "420":
        return 420
    elif network.lower() == "gnosis" or network.lower() == "gnosis chain" or network == "100":
        return 100
    return 0


def valid_address(address):
    if len(address) == 42 and re.search('^0[xX][0-9a-fA-F]{40}', address) and ('[' not in address):
        return True
    return False


bot.run(discord_token)
