import configparser
import json
import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
ADMIN_ROLES = c["DISCORD"]["admin_roles"]
ephemeral = bool(True if str(c["DISCORD"]["ephemeral"]) == "True" else False)
guilds = json.loads(c["DISCORD"]["guilds"])
threshold_response_channel = int(c["DISCORD"]["threshold_response_channel"])
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
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
    check_thresholds.start()


@bot.tree.command(name="add-address", description="Track the balance of a new address.")
@app_commands.describe(network="The network of the address.", address="The address to track.")
async def add_address(interaction: discord.Interaction, network: str, address: str, label: str):
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

    if address in database.get_all_addresses_by_network(db_connection, network, interaction.guild_id).keys():
        await interaction.response.send_message(f"Address is already being tracked.", ephemeral=ephemeral)
        db_connection.close()
        return

    await interaction.response.send_message(f"Address {address[:6]}...{address[-4:]} has been added to the "
                                            f"{database.get_network_name_by_id(db_connection, network)} watch list. ", ephemeral=ephemeral)

    addr_balance = database.get_balance(network, address)
    database.add_address_to_db(db_connection, network, address, label, addr_balance, interaction.guild_id)

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


@bot.tree.command(name='add-contact', description='Add a contact for a specific address/label.')
@app_commands.describe(address="The address/label to add a contact for.", user="The contact to notify if the address is low.")
async def add_contacts(interaction: discord.Interaction, address: str, user: str):
    db_connection = database.get_db_connection()
    if address not in database.get_all_addresses(db_connection, interaction.guild_id).keys() and \
            address not in database.get_all_addresses(db_connection, interaction.guild_id).values():
        await interaction.response.send_message(f"Address is not being tracked.", ephemeral=ephemeral)
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
    message = address + " now has the following contacts: " + database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id)
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
    message = address + " has the following contacts: " + database.get_contacts_by_address(db_connection, true_addr, interaction.guild_id)
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


@tasks.loop(minutes=1)
async def check_thresholds():
    db_connection = database.get_db_connection()

    await bot.wait_until_ready()
    print("updating validators")
    threshold_channel = bot.get_channel(threshold_response_channel)

    for guild in guilds:
        guild = int(guild)
        for network in database.get_all_networks(db_connection):
            threshold: float = database.get_threshold_by_network(db_connection, network, guild)
            addresses = database.get_all_addresses_by_network(db_connection, network, guild)
            for address in addresses:

                balance: float = database.get_balance(network, address)
                database.update_balance(db_connection, network, address, balance)
                alerting = database.get_alerting_by_address(db_connection, network, address)

                if (balance < threshold) and not alerting:
                    contacts = database.get_contacts_by_address(db_connection, address, guild)
                    await threshold_channel.send(f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is below the threshold of {threshold} "
                                                 f"{database.get_token_abr_by_network(db_connection, network)}")
                    database.set_alerting_by_address(db_connection, network, address, True)

                if (balance > threshold) and alerting:
                    contacts = database.get_contacts_by_address(db_connection, address, guild)
                    await threshold_channel.send(f"{contacts}, **{addresses[address]} ({address[:6]}...{address[-4:]})** is back above the threshold of {threshold} "
                                                 f"{database.get_token_abr_by_network(db_connection, network)}")
                    database.set_alerting_by_address(db_connection, network, address, False)

    db_connection.close()
    return


bot.run(discord_token)
