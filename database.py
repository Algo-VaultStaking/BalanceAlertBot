import configparser
import datetime
import json

from web3 import Web3
import mariadb

# Load config
import requests

c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

DB_USER = str(c["DATABASE"]["user"])
DB_PASSWORD = str(c["DATABASE"]["password"])
DB_HOST = str(c["DATABASE"]["host"])
DB_NAME = str(c["DATABASE"]["name"])


# Connect to MariaDB Platform
def get_db_connection():
    try:
        conn = mariadb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=3306,
            database=DB_NAME
        )

        return conn

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        exit()


def initial_setup():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print(1)
        cur.execute("DROP TABLE Addresses;")
        cur.execute("DROP TABLE Networks;")
        cur.execute("DROP TABLE Contacts;")
        cur.execute("DROP TABLE Thresholds;")
        cur.execute("DROP TABLE Guilds;")

        cur.execute("CREATE TABLE Addresses("
                    "network INT, "
                    "address VARCHAR(70), "
                    "label VARCHAR(70), "
                    "balance DOUBLE(28, 18), "
                    "alerting BOOL, "
                    "guild BIGINT);")

        cur.execute("CREATE TABLE Networks("
                    "networkID INT, "
                    "networkName VARCHAR(70), "
                    "tokenName VARCHAR(50), "
                    "tokenAbr VARCHAR(25));")

        cur.execute("CREATE TABLE Contacts("
                    "address VARCHAR(70), "
                    "contacts VARCHAR(250),"
                    "guild BIGINT);")

        cur.execute("CREATE TABLE Thresholds("
                    "networkID INT, "
                    "defaultThreshold DOUBLE(15, 10),"
                    "guild BIGINT);")

        cur.execute("CREATE TABLE Guilds("
                    "guild BIGINT, "
                    "threshold_alert_channel BIGINT);")
        print(3)
        cur.execute(f"INSERT INTO Networks VALUES(1, \"Ethereum Mainnet\", \"Ether\", \"ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(5, \"Goerli Testnet\", \"Goerli ETH\", \"Goerli ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(56, \"BNB Chain Mainnet\", \"Binance Coin\", \"BNB\");")
        cur.execute(f"INSERT INTO Networks VALUES(97, \"BNB Chain Testnet\", \"Binance Coin\", \"BNB (testnet)\");")
        cur.execute(f"INSERT INTO Networks VALUES(137, \"Polygon Mainnet\", \"Matic\", \"Matic\");")
        cur.execute(f"INSERT INTO Networks VALUES(80001, \"Mumbai Testnet\", \"MaticMum\", \"MaticMum\");")
        cur.execute(f"INSERT INTO Networks VALUES(42161, \"Arbitrum Mainnet\", \"Arbitrum ETH\", \"Arbitrum ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(421611, \"Arbitrum Goerli\", \"Arb Goerli ETH\", \"Arb Goerli ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(10, \"Optimism Mainnet\", \"Optimism ETH\", \"Optimism ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(420, \"Optimism Goerli\", \"Opt Goerli ETH\", \"Opt Goerli ETH\");")
        cur.execute(f"INSERT INTO Networks VALUES(100, \"Gnosis Chain\", \"xDai\", \"xDai\");")

        cur.execute(f"INSERT INTO Thresholds VALUES(1, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(5, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(56, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(97, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(137, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(80001, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(42161, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(421611, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(10, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(420, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(100, 0.5, 837853470136467517);")

        cur.execute(f"INSERT INTO Thresholds VALUES(1, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(5, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(56, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(97, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(137, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(80001, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(42161, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(421611, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(10, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(420, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(100, 0.5, 454734546869551114);")

        cur.execute(f"INSERT INTO Thresholds VALUES(1, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(5, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(56, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(97, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(137, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(80001, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(42161, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(421611, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(10, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(420, 0.5, 992549151134982234);")
        cur.execute(f"INSERT INTO Thresholds VALUES(100, 0.5, 992549151134982234);")

        cur.execute(f"INSERT INTO Guilds VALUES(837853470136467517, 1001486994511237120);")  # Vault Staking
        cur.execute(f"INSERT INTO Guilds VALUES(454734546869551114, 953971443996180510);")  # Connext Public
        cur.execute(f"INSERT INTO Guilds VALUES(992549151134982234, 953971443996180510);")  # Connext Private

        conn.commit()

        cur.close()
        conn.close()
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_threshold_by_network(db_connection, network: int, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT defaultThreshold FROM Thresholds WHERE networkID={network} and guild={guild};"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def set_threshold_in_db(db_connection, network: int, threshold: float, guild: int):
    cur = db_connection.cursor()
    command = f"UPDATE Thresholds " \
              f"SET defaultThreshold = {threshold} " \
              f"WHERE networkID = {network} " \
              f"AND guild = {guild};"
    cur.execute(command)
    db_connection.commit()
    return None


def get_alert_channel_in_db(db_connection, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT threshold_alert_channel " \
              f"FROM Guilds " \
              f"WHERE guild = {guild};"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def set_alert_channel_in_db(db_connection, channel: int, guild: int):
    cur = db_connection.cursor()
    command = f"UPDATE Guilds " \
              f"SET threshold_alert_channel = {channel} " \
              f"WHERE guild = {guild};"
    cur.execute(command)
    db_connection.commit()
    return None


def get_token_abr_by_network(db_connection, network: int):
    cur = db_connection.cursor()
    command = f"SELECT tokenAbr FROM Networks WHERE networkID={network};"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def get_network_name_by_id(db_connection, network: int):
    cur = db_connection.cursor()
    command = f"SELECT networkName FROM Networks WHERE networkID={network};"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def add_address_to_db(db_connection, network: int, address: str, label: str, balance: float, guild: int):
    cur = db_connection.cursor()
    addr_list = get_all_addresses_by_network(db_connection, network, guild)
    if address not in addr_list:
        cur.execute(f"INSERT INTO Contacts VALUES (\"{address}\", null, {guild});")
    cur.execute(f"INSERT INTO Addresses VALUES ({network}, \"{address}\", \"{label}\", {balance}, 0, {guild});")
    db_connection.commit()
    return


def remove_address_from_db_by_address(db_connection, network, address, guild: int):
    cur = db_connection.cursor()
    command = f"DELETE FROM Addresses WHERE network={network} AND address=\"{address}\" AND guild={guild};"
    cur.execute(command)
    db_connection.commit()
    return


def remove_address_from_db_by_label(db_connection, network, label, guild: int):
    cur = db_connection.cursor()
    command = f"DELETE FROM Addresses WHERE network={network} AND label=\"{label}\" AND guild={guild};"
    cur.execute(command)
    db_connection.commit()
    return


def get_all_addresses_by_network(db_connection, network: int, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address, label FROM Addresses WHERE network={network} AND guild={guild};"

    cur.execute(command)
    result = cur.fetchall()
    addressList = {}
    for addr, label in result:
        addressList[addr] = str(label)

    return addressList


def get_all_addresses(db_connection, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address, label FROM Addresses WHERE guild={guild};"

    cur.execute(command)
    result = cur.fetchall()
    addressList = {}
    for addr, label in result:
        addressList[addr] = str(label)

    return addressList


def get_all_networks(db_connection):
    cur = db_connection.cursor()
    command = f"SELECT networkID FROM Networks;"

    cur.execute(command)
    result = cur.fetchall()
    networkList = []
    for net in result:
        networkList.append(net[0])

    return networkList


def get_addresses_by_label(db_connection, label: str, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address FROM Addresses WHERE label=\"{label}\" AND guild={guild};"

    cur.execute(command)
    result = cur.fetchall()[0][0]

    return result


def get_label_by_address(db_connection, address: str, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT label FROM Addresses WHERE address=\"{address}\" AND guild={guild};"

    cur.execute(command)
    result = cur.fetchall()[0][0]

    return result


def get_contacts_by_address(db_connection, address: str, guild: int):
    conn = db_connection
    cur = conn.cursor()
    command = f"SELECT contacts FROM Contacts WHERE address = '{address}' AND guild={guild};"
    try:
        cur.execute(command)
        fetch = cur.fetchall()[0][0]
        result = fetch if fetch is not None else "None"
    except Exception as e:
        print(f"Error: {e}")
        result = "Team"
    return result


def add_contacts_for_address(db_connection, contacts: str, address: str, guild: int):
    cur = db_connection.cursor()
    current_contacts = get_contacts_by_address(db_connection, address, guild)
    if len(current_contacts) == 0 or current_contacts == "Team" or current_contacts == "None":
        new_contacts = contacts
    else:
        new_contacts = current_contacts + ", " + contacts
    command = f"UPDATE Contacts " \
              f"SET contacts = '{new_contacts}' " \
              f"WHERE address = '{address}' AND guild={guild};"
    cur.execute(command)
    db_connection.commit()


def remove_contacts_for_address(db_connection, address: str, user: str, guild: int):
    conn = db_connection
    cur = conn.cursor()
    contacts = str(get_contacts_by_address(db_connection, address, guild)).split(", ")
    if user in contacts:
        contacts.remove(user)
    new_contacts = str(", ".join(contacts))
    command = f"UPDATE Contacts " \
              f"SET contacts = '{new_contacts}' " \
              f"WHERE address = '{address}' AND guild={guild};"

    cur.execute(command)
    conn.commit()

    return None


def remove_contacts_for_label(db_connection, label: str, user: str, guild: int):
    conn = db_connection
    cur = conn.cursor()
    address = get_addresses_by_label(db_connection, label, guild)
    contacts = str(get_contacts_by_address(db_connection, address, guild)).split(", ")
    if user in contacts:
        contacts.remove(user)
    new_contacts = str(", ".join(contacts))
    command = f"UPDATE Contacts " \
              f"SET contacts = '{new_contacts}' " \
              f"WHERE address = '{address}' AND guild={guild};"
    cur.execute(command)
    conn.commit()

    return None


def get_balances_by_network(db_connection, network: int, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address, balance FROM Addresses WHERE network={network} AND guild={guild};"
    cur.execute(command)
    result = cur.fetchall()
    addressList = {}
    for addr, balance in result:
        addressList[addr] = float(round(balance, 3))

    return addressList


def get_balance(network: int, address: str):
    rpc_url = ""

    if network == 1:
        rpc_url = "https://mainnet.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 5:
        rpc_url = "https://goerli.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 56:
        rpc_url = "https://bsc-dataseed1.binance.org/"
    elif network == 97:
        rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545"
    elif network == 137:
        rpc_url = "https://polygon-rpc.com"
    elif network == 80001:
        rpc_url = "https://rpc-mumbai.maticvigil.com"
    elif network == 42161:
        rpc_url = "https://arbitrum-mainnet.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 421611:
        rpc_url = "https://arbitrum-goerli.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 10:
        rpc_url = "https://optimism-mainnet.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 420:
        rpc_url = "https://optimism-goerli.infura.io/v3/5669c7eb29464cbe8957e4ca088a05a6"
    elif network == 100:
        rpc_url = "http://gnosis-rpc.vaultstaking.com:8545"
    else:
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    balance = int(w3.eth.getBalance(address)) / int(1e18)

    return balance


def get_balance_covalent(network: int, address: str):
    start = datetime.datetime.now()
    request = json.loads(requests.get(f"https://api.covalenthq.com/v1/{network}/address/{address}/balances_v2/"
                                      f"?quote-currency=USD&format=JSON&nft=false&no-nft-fetch=false&key=ckey_3f4ecca3d97f4afdaf0b4fb4739").text)

    end = datetime.datetime.now()
    print(f"retrieved balance of {address} in: " + str(end - start))

    for token in request["data"]["items"]:
        if token["native_token"]:
            decimals = token["contract_decimals"]
            balance = int(token["balance"]) / int(10 ** decimals)
            print(f"{network} decimals {decimals}")
            return balance


def update_balance(db_connection, network: int, address: str, balance: float):
    cur = db_connection.cursor()
    command = f"UPDATE Addresses " \
              f"SET balance = {balance} " \
              f"WHERE network = {network} " \
              f"AND address = \"{address}\";"
    cur.execute(command)
    db_connection.commit()
    return None


def get_alerting_by_address(db_connection, network: int, address: str):
    cur = db_connection.cursor()
    command = f"SELECT alerting FROM Addresses WHERE network={network} AND address=\"{address}\";"
    try:
        cur.execute(command)
        result: bool = cur.fetchall()[0][0]
    except Exception as e:
        result = False
    return result


def set_alerting_by_address(db_connection, network: int, address: str, alerting: bool):
    cur = db_connection.cursor()
    command = f"UPDATE Addresses " \
              f"SET alerting = {alerting} " \
              f"WHERE network = {network} " \
              f"AND address = \"{address}\";"
    cur.execute(command)
    db_connection.commit()
    return None


def get_thresholds_alert_channel_by_guild(db_connection, guild):
    cur = db_connection.cursor()
    command = f"SELECT threshold_alert_channel FROM Guilds WHERE guild={guild};"
    cur.execute(command)
    cur.execute(command)
    result: int = cur.fetchall()[0][0]
    return result


# def get_admin_roles_by_guild(db_connection, guild):
#    cur = db_connection.cursor()
#    command = f"SELECT admin_roles FROM Guilds WHERE guild={guild};"
#    cur.execute(command)
#    cur.execute(command)
#    result: list = cur.fetchall()[0][0]
#    return result
