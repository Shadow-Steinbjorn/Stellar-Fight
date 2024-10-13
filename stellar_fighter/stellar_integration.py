import json
import os
from stellar_sdk import Server, Keypair, Asset, TransactionBuilder, Network
from stellar_sdk.exceptions import NotFoundError, BadResponseError, BadRequestError
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DUmmy values
temp = Keypair.random()

# Stellar configuration
STELLAR_CONFIG = {
    "network": Network.TESTNET_NETWORK_PASSPHRASE,
    "horizon_url": "https://horizon-testnet.stellar.org",
    "issuer_secret": temp.secret,
    "asset_code": "StellarToken",
    "distribution_account_secret": temp.secret
}

server = Server(horizon_url=STELLAR_CONFIG["horizon_url"])

def create_and_fund_account():
    """Create a new Stellar account and fund it using Friendbot."""
    account = Keypair.random()
    public_key = account.public_key
    
    logger.info(f"Creating and funding account: {public_key}")
    friendbot_url = f"https://friendbot.stellar.org?addr={public_key}"
    response = requests.get(friendbot_url)
    
    if response.status_code == 200:
        logger.info(f"Account {public_key} created and funded successfully.")
        return account
    else:
        logger.error(f"Failed to create and fund account {public_key}.")
        return None

def setup_stellar_accounts():
    """Set up Stellar accounts with custom asset for the game."""
    issuer = create_and_fund_account()
    if not issuer:
        logger.error("Failed to create issuer account. Aborting setup.")
        return None, None

    distributor = create_and_fund_account()
    if not distributor:
        logger.error("Failed to create distributor account. Aborting setup.")
        return None, None

    asset = Asset(STELLAR_CONFIG["asset_code"], issuer.public_key)
    
    logger.info("Establishing trustline...")
    if not create_trustline(distributor, asset):
        logger.error("Failed to establish trustline. Aborting setup.")
        return None, None
    
    logger.info("Issuing initial amount to distributor...")
    initial_amount = "1000000"
    if not issue_asset(initial_amount, distributor.public_key, issuer):
        logger.error("Failed to issue initial amount. Aborting setup.")
        return None, None
    
    logger.info("Stellar setup complete!")
    STELLAR_CONFIG["issuer_secret"] = issuer.secret
    STELLAR_CONFIG["distribution_account_secret"] = distributor.secret
    return issuer, distributor

def save_account_keys(issuer, distributor):
    """Save the generated account keys to a file."""
    keys = {
        "issuer_public_key": issuer.public_key,
        "issuer_secret_key": issuer.secret,
        "distributor_public_key": distributor.public_key,
        "distributor_secret_key": distributor.secret
    }
    
    with open("stellar_account_keys.json", "w") as f:
        json.dump(keys, f)
    
    logger.info("Account keys saved to stellar_account_keys.json")

def load_account_keys():
    """Load the saved account keys from file."""
    try:
        with open("stellar_account_keys.json", "r") as f:
            keys = json.load(f)
        return keys
    except FileNotFoundError:
        logger.warning("stellar_account_keys.json not found.")
        return None

def initialize_game_stellar_setup():
    """Initialize the game's Stellar setup."""
    keys = load_account_keys()
    
    if keys:
        logger.info("Using existing Stellar accounts.")
        STELLAR_CONFIG["issuer_secret"] = keys["issuer_secret_key"]
        STELLAR_CONFIG["distribution_account_secret"] = keys["distributor_secret_key"]
    else:
        logger.info("Setting up new Stellar accounts...")
        issuer, distributor = setup_stellar_accounts()
        if issuer and distributor:
            save_account_keys(issuer, distributor)
            STELLAR_CONFIG["issuer_secret"] = issuer.secret
            STELLAR_CONFIG["distribution_account_secret"] = distributor.secret
        else:
            logger.error("Failed to set up Stellar accounts. Please try again.")
            return

    logger.info("Stellar setup initialized successfully!")
    
def create_guild_account(guild_name):
    """Create a new Stellar account for a guild and fund it using Friendbot."""
    account = Keypair.random()
    public_key = account.public_key
    
    logger.info(f"Creating and funding account for guild {guild_name}: {public_key}")
    friendbot_url = f"https://friendbot.stellar.org?addr={public_key}"
    response = requests.get(friendbot_url)
    
    if response.status_code == 200:
        logger.info(f"Account for guild {guild_name} created and funded successfully.")
        guild_data = {
            "name": guild_name,
            "public_key": public_key,
            "secret_key": account.secret
        }
        with open(f"{guild_name}_stellar_data.json", 'w') as f:
            json.dump(guild_data, f)
        return account
    else:
        logger.error(f"Failed to create and fund account for guild {guild_name}.")
        return None

def load_or_create_guild_account(guild_name):
    """Load existing guild account or create a new one if it doesn't exist."""
    guild_file = f"{guild_name}_stellar_data.json"
    if os.path.exists(guild_file):
        with open(guild_file, 'r') as f:
            guild_data = json.load(f)
        return Keypair.from_secret(guild_data["secret_key"])
    else:
        return create_guild_account(guild_name)

def setup_smart_contract(player_account, guild_account, daily_amount):
    """Set up a smart contract for daily token transfers from player to guild."""
    issuer = Keypair.from_secret(STELLAR_CONFIG["issuer_secret"])
    asset = Asset(STELLAR_CONFIG["asset_code"], issuer.public_key)

    server = Server(horizon_url=STELLAR_CONFIG["horizon_url"])
    player_stellar_account = server.load_account(player_account.public_key)

    transaction = (
        TransactionBuilder(
            source_account=player_stellar_account,
            network_passphrase=STELLAR_CONFIG["network"],
            base_fee=server.fetch_base_fee(),
        )
        .append_payment_op(
            destination=guild_account.public_key,
            asset=asset,
            amount=str(daily_amount),
            source=player_account.public_key,
        )
        .set_timeout(30)
        .build()
    )

    transaction.sign(player_account)
    
    try:
        response = server.submit_transaction(transaction)
        logger.info(f"Smart contract set up successfully for daily transfer of {daily_amount} tokens.")
        return response
    except (NotFoundError, BadResponseError, BadRequestError) as e:
        logger.error(f"Error setting up smart contract: {str(e)}")
        return None

def execute_daily_transfer(player_account, guild_account, daily_amount):
    """Execute the daily token transfer from player to guild."""
    issuer = Keypair.from_secret(STELLAR_CONFIG["issuer_secret"])
    asset = Asset(STELLAR_CONFIG["asset_code"], issuer.public_key)

    server = Server(horizon_url=STELLAR_CONFIG["horizon_url"])
    player_stellar_account = server.load_account(player_account.public_key)

    transaction = (
        TransactionBuilder(
            source_account=player_stellar_account,
            network_passphrase=STELLAR_CONFIG["network"],
            base_fee=server.fetch_base_fee(),
        )
        .append_payment_op(
            destination=guild_account.public_key,
            asset=asset,
            amount=str(daily_amount),
            source=player_account.public_key,
        )
        .set_timeout(30)
        .build()
    )

    transaction.sign(player_account)
    
    try:
        response = server.submit_transaction(transaction)
        logger.info(f"Daily transfer of {daily_amount} tokens executed successfully.")
        return response
    except (NotFoundError, BadResponseError, BadRequestError) as e:
        logger.error(f"Error executing daily transfer: {str(e)}")
        return None

def get_account(account_id):
    try:
        return server.load_account(account_id)
    except NotFoundError:
        logger.error(f"Account {account_id} not found.")
        return None

def create_trustline(account, asset):
    try:
        transaction = (
            TransactionBuilder(
                source_account=get_account(account.public_key),
                network_passphrase=STELLAR_CONFIG["network"],
                base_fee=server.fetch_base_fee(),
            )
            .append_change_trust_op(asset=asset)
            .set_timeout(30)
            .build()
        )
        transaction.sign(account)
        response = server.submit_transaction(transaction)
        logger.info(f"Trustline created successfully for account {account.public_key}")
        return response
    except (NotFoundError, BadResponseError, BadRequestError) as e:
        logger.error(f"Error creating trustline: {str(e)}")
        return None

def issue_asset(amount, destination, issuer):
    distribution_account = Keypair.from_secret(STELLAR_CONFIG["distribution_account_secret"])
    asset = Asset(STELLAR_CONFIG["asset_code"], issuer.public_key)

    try:
        transaction = (
            TransactionBuilder(
                source_account=get_account(issuer.public_key),
                network_passphrase=STELLAR_CONFIG["network"],
                base_fee=server.fetch_base_fee(),
            )
            .append_payment_op(destination=destination, asset=asset, amount=str(amount))
            .set_timeout(30)
            .build()
        )
        transaction.sign(issuer)
        response = server.submit_transaction(transaction)
        logger.info(f"Asset issued successfully: {amount} to {destination}")
        return response
    except (NotFoundError, BadResponseError, BadRequestError) as e:
        logger.error(f"Error issuing asset: {str(e)}")
        return None

def get_balance(account_id):
    try:
        account = server.accounts().account_id(account_id).call()
        for balance in account['balances']:
            if balance['asset_type'] != 'native' and balance['asset_code'] == STELLAR_CONFIG["asset_code"]:
                return float(balance['balance'])
        return 0
    except NotFoundError:
        logger.error(f"Account {account_id} not found when fetching balance.")
        return 0

def initialize_player_account(username):
    account = create_and_fund_account()
    if not account:
        logger.error(f"Failed to initialize account for player {username}")
        return None

    issuer = Keypair.from_secret(STELLAR_CONFIG["issuer_secret"])
    asset = Asset(STELLAR_CONFIG["asset_code"], issuer.public_key)
    
    if not create_trustline(account, asset):
        logger.error(f"Failed to create trustline for player {username}")
        return None
    
    initial_coins = 100
    if not issue_asset(initial_coins, account.public_key, issuer):
        logger.error(f"Failed to issue initial coins to player {username}")
        return None
    
    return {
        "username": username,
        "public_key": account.public_key,
        "secret_key": account.secret
    }

def update_player_coins(public_key, amount):
    current_balance = get_balance(public_key)
    issuer = Keypair.from_secret(STELLAR_CONFIG["issuer_secret"])
    
    if amount > 0:
        if not issue_asset(amount, public_key, issuer):
            logger.error(f"Failed to add {amount} coins to account {public_key}")
            return current_balance
    elif amount < 0 and abs(amount) <= current_balance:
        # For simplicity, we're not implementing a "burn" mechanism here.
        # In a real application, you'd want to properly handle reducing the balance.
        logger.warning(f"Coin reduction not implemented. Balance remains {current_balance}")
        return current_balance
    
    return get_balance(public_key)

def load_or_create_player_data(username):
    player_file = f"{username}_stellar_data.json"
    if os.path.exists(player_file):
        with open(player_file, 'r') as f:
            return json.load(f)
    else:
        player_data = initialize_player_account(username)
        if player_data:
            with open(player_file, 'w') as f:
                json.dump(player_data, f)
            return player_data
        else:
            logger.error(f"Failed to initialize player data for {username}")
            return None

def save_player_data(player_data):
    player_file = f"{player_data['username']}_stellar_data.json"
    with open(player_file, 'w') as f:
        json.dump(player_data, f)
    logger.info(f"Player data saved for {player_data['username']}")