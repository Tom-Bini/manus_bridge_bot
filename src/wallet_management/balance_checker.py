"""
Module pour la vérification des soldes de wallets sur différentes blockchains.
Ce module permet d'interroger les blockchains pour obtenir les soldes réels des wallets.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from web3 import Web3
import json
import requests

from src.config.config import SUPPORTED_CHAINS, SUPPORTED_TOKENS

logger = logging.getLogger(__name__)

# Configuration des RPC URLs pour chaque blockchain
RPC_URLS = {
    "ethereum": "https://eth-mainnet.g.alchemy.com/v2/demo",
    "polygon": "https://polygon-mainnet.g.alchemy.com/v2/demo",
    "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/demo",
    "optimism": "https://opt-mainnet.g.alchemy.com/v2/demo",
    "avalanche": "https://api.avax.network/ext/bc/C/rpc",
    "binance-smart-chain": "https://bsc-dataseed.binance.org/",
    "base": "https://mainnet.base.org"
}

# ABI minimal pour les tokens ERC20
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

class BalanceChecker:
    """Classe pour vérifier les soldes des wallets sur différentes blockchains."""
    
    def __init__(self):
        """Initialise le vérificateur de soldes."""
        self.web3_connections = {}
        self.token_contracts = {}
        
        # Initialiser les connexions Web3 pour chaque blockchain
        for chain_id, rpc_url in RPC_URLS.items():
            try:
                self.web3_connections[chain_id] = Web3(Web3.HTTPProvider(rpc_url))
                logger.info(f"Connexion Web3 établie pour {chain_id}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la connexion Web3 pour {chain_id}: {e}")
    
    def get_token_contract(self, chain_id: str, token_address: str) -> Optional[Any]:
        """
        Récupère le contrat d'un token ERC20.
        
        Args:
            chain_id: Identifiant de la blockchain
            token_address: Adresse du contrat du token
        
        Returns:
            Contrat du token ou None en cas d'erreur
        """
        key = f"{chain_id}_{token_address}"
        if key in self.token_contracts:
            return self.token_contracts[key]
        
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            self.token_contracts[key] = contract
            return contract
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contrat du token {token_address} sur {chain_id}: {e}")
            return None
    
    def get_native_balance(self, chain_id: str, address: str) -> Optional[float]:
        """
        Récupère le solde en token natif d'un wallet.
        
        Args:
            chain_id: Identifiant de la blockchain
            address: Adresse du wallet
        
        Returns:
            Solde en token natif ou None en cas d'erreur
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            balance_wei = web3.eth.get_balance(Web3.to_checksum_address(address))
            balance = web3.from_wei(balance_wei, 'ether')
            return float(balance)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde natif pour {address} sur {chain_id}: {e}")
            return None
    
    def get_token_balance(self, chain_id: str, token_address: str, wallet_address: str) -> Optional[float]:
        """
        Récupère le solde d'un token ERC20 pour un wallet.
        
        Args:
            chain_id: Identifiant de la blockchain
            token_address: Adresse du contrat du token
            wallet_address: Adresse du wallet
        
        Returns:
            Solde du token ou None en cas d'erreur
        """
        contract = self.get_token_contract(chain_id, token_address)
        if not contract:
            return None
        
        try:
            balance_raw = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
            decimals = contract.functions.decimals().call()
            balance = balance_raw / (10 ** decimals)
            return float(balance)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde du token {token_address} pour {wallet_address} sur {chain_id}: {e}")
            return None
    
    def get_token_addresses(self, chain_id: str) -> Dict[str, str]:
        """
        Récupère les adresses des tokens supportés sur une blockchain.
        
        Args:
            chain_id: Identifiant de la blockchain
        
        Returns:
            Dictionnaire des adresses de tokens par symbole
        """
        # Cette fonction pourrait être améliorée pour récupérer dynamiquement les adresses
        # Pour l'instant, nous utilisons un mapping statique
        token_addresses = {
            "ethereum": {
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            },
            "polygon": {
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
            },
            # Autres blockchains...
        }
        
        return token_addresses.get(chain_id, {})
    
    def check_all_balances(self, wallet_address: str) -> Dict[str, Dict[str, float]]:
        """
        Vérifie tous les soldes d'un wallet sur toutes les blockchains supportées.
        
        Args:
            wallet_address: Adresse du wallet
        
        Returns:
            Dictionnaire des soldes par blockchain et par token
        """
        results = {}
        
        for chain_id in SUPPORTED_CHAINS:
            if chain_id not in self.web3_connections:
                continue
            
            chain_results = {}
            
            # Vérifier le solde natif
            native_balance = self.get_native_balance(chain_id, wallet_address)
            if native_balance is not None:
                native_symbol = "ETH"  # Par défaut
                if chain_id == "binance-smart-chain":
                    native_symbol = "BNB"
                elif chain_id == "avalanche":
                    native_symbol = "AVAX"
                
                chain_results[native_symbol] = native_balance
            
            # Vérifier les soldes des tokens
            token_addresses = self.get_token_addresses(chain_id)
            for symbol, address in token_addresses.items():
                balance = self.get_token_balance(chain_id, address, wallet_address)
                if balance is not None:
                    chain_results[symbol] = balance
            
            if chain_results:
                results[chain_id] = chain_results
        
        return results
