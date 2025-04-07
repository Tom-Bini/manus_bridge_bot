"""
Configuration du bot crypto.
Ce fichier contient les paramètres de configuration pour le bot.
"""
import os
from typing import Dict, List, Optional

# Configuration des services de bridge
BRIDGE_SERVICES = {
    "jumper": {
        "api_url": "https://li.quest/v1",
        "enabled": True
    },
    "stargate": {
        "enabled": True
    },
    "relay": {
        "api_url": "https://api.relay.link",
        "enabled": True
    }
}

# Configuration Telegram
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_CHAT_IDS: List[int] = [int(id) for id in os.getenv("ADMIN_CHAT_IDS", "").split(",") if id]

# Configuration des transactions
TRANSACTIONS_PER_DAY: int = 2
MIN_TRANSACTION_INTERVAL_HOURS: int = 1
MAX_TRANSACTION_INTERVAL_HOURS: int = 23

# Configuration des wallets
WALLET_ENCRYPTION_KEY: str = os.getenv("WALLET_ENCRYPTION_KEY", "")
WALLETS_FILE: str = os.getenv("WALLETS_FILE", "wallets.encrypted.json")

# Configuration des blockchains supportées
SUPPORTED_CHAINS = [
    "ethereum",
    "polygon",
    "arbitrum",
    "optimism",
    "avalanche",
    "binance-smart-chain",
    "base"
]

# Configuration des tokens supportés
SUPPORTED_TOKENS = {
    "USDC": {
        "name": "USD Coin",
        "decimals": 6
    },
    "USDT": {
        "name": "Tether USD",
        "decimals": 6
    },
    "DAI": {
        "name": "Dai Stablecoin",
        "decimals": 18
    },
    "ETH": {
        "name": "Ethereum",
        "decimals": 18
    },
    "WETH": {
        "name": "Wrapped Ethereum",
        "decimals": 18
    }
}

# Configuration des limites de transaction
DEFAULT_MIN_AMOUNT_USD: float = 10.0
DEFAULT_MAX_AMOUNT_USD: float = 100.0

# Configuration du déploiement
DEPLOYMENT = {
    "digital_ocean": {
        "droplet_size": "s-1vcpu-1gb",
        "region": "fra1"
    }
}
