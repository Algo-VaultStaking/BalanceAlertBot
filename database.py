import configparser
import datetime
import json

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
                    "balance DOUBLE(28, 18),"
                    "alerting BOOL,"
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
        cur.execute( f"INSERT INTO Networks VALUES(421611, \"Arbitrum Goerli\", \"Arb Goerli ETH\", \"Arb Goerli ETH\");")

        cur.execute(f"INSERT INTO Thresholds VALUES(1, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(5, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(56, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(97, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(137, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(80001, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(42161, 0.5, 837853470136467517);")
        cur.execute(f"INSERT INTO Thresholds VALUES(421611, 0.5, 837853470136467517);")

        cur.execute(f"INSERT INTO Thresholds VALUES(1, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(5, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(56, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(97, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(137, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(80001, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(42161, 0.5, 454734546869551114);")
        cur.execute(f"INSERT INTO Thresholds VALUES(421611, 0.5, 454734546869551114);")

        cur.execute(f"INSERT INTO Guilds VALUES(837853470136467517, 1001486994511237120);")  # Vault Staking
        cur.execute(f"INSERT INTO Guilds VALUES(454734546869551114, 953971443996180510);")  # Connext

        conn.commit()

        cur.close()
        conn.close()
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_threshold_by_network(db_connection, network: int, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT defaultThreshold FROM Networks WHERE networkID={network} AND guild={guild};"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


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


def add_address_to_db(db_connection, network: int, address: str, balance: float, guild: int):
    cur = db_connection.cursor()
    threshold = get_threshold_by_network(db_connection, network, guild)
    addr_list = get_all_addresses_by_network(db_connection, network, guild)
    if address not in addr_list:
        cur.execute(f"INSERT INTO Contacts VALUES (\"{address}\", null, {guild});")
    cur.execute(f"INSERT INTO Addresses VALUES ({network}, \"{address}\", {balance}, 0, {guild});")
    db_connection.commit()
    return


def remove_address_from_db(db_connection, network, address, guild: int):
    cur = db_connection.cursor()
    command = f"DELETE FROM Addresses WHERE network={network} AND address=\"{address}\" AND guild={guild};"
    cur.execute(command)
    db_connection.commit()
    return


def get_all_addresses_by_network(db_connection, network: int, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address FROM Addresses WHERE network={network} AND guild={guild};"

    cur.execute(command)
    result = cur.fetchall()
    addressList = []
    for addr in result:
        addressList.append(addr[0])

    return addressList


def get_all_addresses(db_connection, guild: int):
    cur = db_connection.cursor()
    command = f"SELECT address FROM Addresses WHERE guild={guild};"

    cur.execute(command)
    result = cur.fetchall()
    addressList = []
    for addr in result:
        addressList.append(addr[0])

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


def set_threshold_in_db(db_connection, network: int, threshold: float, guild: int):
    cur = db_connection.cursor()
    command = f"UPDATE Networks " \
              f"SET defaultThreshold = {threshold} " \
              f"WHERE networkID = {network} AND guild={guild};"
    cur.execute(command)
    db_connection.commit()
    return None


def get_contacts_by_address(db_connection, address: str, guild: int):
    conn = db_connection
    cur = conn.cursor()
    command = f"SELECT contacts FROM Contacts WHERE address = '{address}' AND guild={guild};"
    try:
        cur.execute(command)
        fetch = cur.fetchall()[0][0]
        result = fetch if fetch is not None else "Team"
    except Exception as e:
        print(f"Error: {e}")
        result = "Team"
    return result


def add_contacts_for_address(db_connection, contacts: str, address: str, guild: int):
    cur = db_connection.cursor()
    current_contacts = get_contacts_by_address(db_connection, address, guild)
    new_contacts = (current_contacts + ", " + contacts) if current_contacts != "Team" else contacts
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


def get_balance(network: int, address: str):
    start = datetime.datetime.now()
    request = json.loads(requests.get(f"https://api.covalenthq.com/v1/{network}/address/{address}/balances_v2/"
                                      f"?quote-currency=USD&format=JSON&nft=false&no-nft-fetch=false&key=ckey_3f4ecca3d97f4afdaf0b4fb4739").text)

    end = datetime.datetime.now()
    print(f"retrieved balance of {address} in: " + str(end - start))

    for token in request["data"]["items"]:
        if token["native_token"]:
            balance = int(token["balance"]) / int(10 ** token["contract_decimals"])
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
