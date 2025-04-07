"""
Module d'intégration avec Stargate pour les bridges cross-chain.
Ce module permet d'effectuer des bridges entre différentes blockchains via Stargate.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime
from web3 import Web3

from src.config.config import BRIDGE_SERVICES

logger = logging.getLogger(__name__)

# ABI minimal pour le routeur Stargate
STARGATE_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint16", "name": "_dstChainId", "type": "uint16"},
            {"internalType": "uint256", "name": "_srcPoolId", "type": "uint256"},
            {"internalType": "uint256", "name": "_dstPoolId", "type": "uint256"},
            {"internalType": "address payable", "name": "_refundAddress", "type": "address"},
            {"internalType": "uint256", "name": "_amountLD", "type": "uint256"},
            {"internalType": "uint256", "name": "_minAmountLD", "type": "uint256"},
            {"internalType": "bytes", "name": "_to", "type": "bytes"},
            {"internalType": "bytes", "name": "_payload", "type": "bytes"},
            {"internalType": "bytes", "name": "_additionalData", "type": "bytes"}
        ],
        "name": "swap",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint16", "name": "_dstChainId", "type": "uint16"},
            {"internalType": "uint256", "name": "_srcPoolId", "type": "uint256"},
            {"internalType": "uint256", "name": "_dstPoolId", "type": "uint256"},
            {"internalType": "address payable", "name": "_refundAddress", "type": "address"}
        ],
        "name": "quoteLayerZeroFee",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Mapping des chaînes et pools Stargate
STARGATE_CHAINS = {
    "ethereum": {"id": 1, "router": "0x8731d54E9D02c286767d56ac03e8037C07e01e98"},
    "bsc": {"id": 2, "router": "0x4a364f8c717cAAD9A442737Eb7b8A55cc6cf18D8"},
    "avalanche": {"id": 6, "router": "0x45A01E4e04F14f7A4a6702c74187c5F6222033cd"},
    "polygon": {"id": 9, "router": "0x45A01E4e04F14f7A4a6702c74187c5F6222033cd"},
    "arbitrum": {"id": 10, "router": "0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614"},
    "optimism": {"id": 11, "router": "0xB0D502E938ed5f4df2E681fE6E419ff29631d62b"},
    "base": {"id": 30, "router": "0x45f5b7eDBCB52D6BF06C80395498097B6A8e9251"}
}

# Mapping des pools Stargate
STARGATE_POOLS = {
    "USDC": {
        "ethereum": 1,
        "bsc": 1,
        "avalanche": 1,
        "polygon": 1,
        "arbitrum": 1,
        "optimism": 1,
        "base": 1
    },
    "USDT": {
        "ethereum": 2,
        "bsc": 2,
        "avalanche": 2,
        "polygon": 2,
        "arbitrum": 2,
        "optimism": 2,
        "base": 2
    },
    "ETH": {
        "ethereum": 13,
        "bsc": 0,
        "avalanche": 0,
        "polygon": 0,
        "arbitrum": 13,
        "optimism": 13,
        "base": 13
    }
}

class StargateBridgeService:
    """Service d'intégration avec Stargate pour les bridges cross-chain."""
    
    def __init__(self):
        """Initialise le service de bridge Stargate."""
        self.web3_connections = {}
        self.router_contracts = {}
        
        # Initialiser les connexions Web3 pour chaque blockchain
        for chain_name, chain_data in STARGATE_CHAINS.items():
            try:
                from src.wallet_management.transaction_manager import RPC_URLS
                if chain_name in RPC_URLS:
                    self.web3_connections[chain_name] = Web3(Web3.HTTPProvider(RPC_URLS[chain_name]))
                    
                    # Initialiser le contrat du routeur
                    router_address = chain_data["router"]
                    self.router_contracts[chain_name] = self.web3_connections[chain_name].eth.contract(
                        address=Web3.to_checksum_address(router_address),
                        abi=STARGATE_ROUTER_ABI
                    )
                    
                    logger.info(f"Connexion Stargate établie pour {chain_name}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la connexion Stargate pour {chain_name}: {e}")
    
    def get_chain_id(self, chain_name: str) -> Optional[int]:
        """
        Récupère l'ID de chaîne Stargate pour une chaîne donnée.
        
        Args:
            chain_name: Nom de la chaîne
        
        Returns:
            ID de chaîne Stargate ou None si la chaîne n'est pas supportée
        """
        if chain_name in STARGATE_CHAINS:
            return STARGATE_CHAINS[chain_name]["id"]
        return None
    
    def get_pool_id(self, token_symbol: str, chain_name: str) -> Optional[int]:
        """
        Récupère l'ID de pool Stargate pour un token et une chaîne donnés.
        
        Args:
            token_symbol: Symbole du token
            chain_name: Nom de la chaîne
        
        Returns:
            ID de pool Stargate ou None si le token ou la chaîne n'est pas supporté
        """
        if token_symbol in STARGATE_POOLS and chain_name in STARGATE_POOLS[token_symbol]:
            return STARGATE_POOLS[token_symbol][chain_name]
        return None
    
    def quote_fee(self, from_chain: str, to_chain: str, token_symbol: str, refund_address: str) -> Optional[int]:
        """
        Estime les frais de bridge via Stargate.
        
        Args:
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            token_symbol: Symbole du token
            refund_address: Adresse de remboursement
        
        Returns:
            Frais estimés en wei ou None en cas d'erreur
        """
        try:
            if from_chain not in self.router_contracts:
                logger.error(f"Chaîne source non supportée par Stargate: {from_chain}")
                return None
            
            dst_chain_id = self.get_chain_id(to_chain)
            if dst_chain_id is None:
                logger.error(f"Chaîne de destination non supportée par Stargate: {to_chain}")
                return None
            
            src_pool_id = self.get_pool_id(token_symbol, from_chain)
            dst_pool_id = self.get_pool_id(token_symbol, to_chain)
            
            if src_pool_id is None or dst_pool_id is None:
                logger.error(f"Token non supporté par Stargate sur les chaînes spécifiées: {token_symbol}")
                return None
            
            # Appeler la fonction quoteLayerZeroFee
            router_contract = self.router_contracts[from_chain]
            fee, _ = router_contract.functions.quoteLayerZeroFee(
                dst_chain_id,
                src_pool_id,
                dst_pool_id,
                Web3.to_checksum_address(refund_address)
            ).call()
            
            return fee
        except Exception as e:
            logger.error(f"Erreur lors de l'estimation des frais Stargate: {e}")
            return None
    
    def prepare_swap_params(self, from_chain: str, to_chain: str, token_symbol: str, 
                          amount: int, min_amount: int, recipient_address: str) -> Optional[Dict[str, Any]]:
        """
        Prépare les paramètres pour un swap Stargate.
        
        Args:
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            token_symbol: Symbole du token
            amount: Montant à bridger
            min_amount: Montant minimum à recevoir
            recipient_address: Adresse du destinataire
        
        Returns:
            Paramètres de swap ou None en cas d'erreur
        """
        try:
            dst_chain_id = self.get_chain_id(to_chain)
            if dst_chain_id is None:
                logger.error(f"Chaîne de destination non supportée par Stargate: {to_chain}")
                return None
            
            src_pool_id = self.get_pool_id(token_symbol, from_chain)
            dst_pool_id = self.get_pool_id(token_symbol, to_chain)
            
            if src_pool_id is None or dst_pool_id is None:
                logger.error(f"Token non supporté par Stargate sur les chaînes spécifiées: {token_symbol}")
                return None
            
            # Encoder l'adresse du destinataire
            to_address_bytes = Web3.to_bytes(hexstr=recipient_address)
            
            return {
                "dst_chain_id": dst_chain_id,
                "src_pool_id": src_pool_id,
                "dst_pool_id": dst_pool_id,
                "refund_address": recipient_address,
                "amount": amount,
                "min_amount": min_amount,
                "to_address_bytes": to_address_bytes,
                "payload": b'',
                "additional_data": b''
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des paramètres de swap Stargate: {e}")
            return None
    
    def execute_bridge(self, wallet_service, wallet_address: str, from_chain: str, to_chain: str, 
                      token_symbol: str, amount: str, token_address: str = None) -> Optional[Dict[str, Any]]:
        """
        Exécute un bridge via Stargate.
        
        Args:
            wallet_service: Service de gestion des wallets
            wallet_address: Adresse du wallet
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            token_symbol: Symbole du token
            amount: Montant à bridger (en unités du token)
            token_address: Adresse du contrat du token (optionnel)
        
        Returns:
            Résultat de la transaction ou None en cas d'erreur
        """
        try:
            if from_chain not in self.router_contracts:
                logger.error(f"Chaîne source non supportée par Stargate: {from_chain}")
                return None
            
            # Convertir le montant en entier
            web3 = self.web3_connections[from_chain]
            amount_wei = web3.to_wei(amount, 'ether') if token_symbol == "ETH" else int(amount)
            min_amount_wei = int(amount_wei * 0.97)  # 3% de slippage
            
            # Si c'est un token ERC20, approuver le routeur Stargate
            if token_symbol != "ETH" and token_address:
                router_address = STARGATE_CHAINS[from_chain]["router"]
                
                logger.info(f"Approbation nécessaire pour le token {token_symbol}")
                
                # Exécuter l'approbation
                approval_tx_hash = wallet_service.approve_token_for_bridge(
                    wallet_address,
                    from_chain,
                    token_address,
                    router_address,
                    amount_wei
                )
                
                if not approval_tx_hash:
                    logger.error("Échec de l'approbation du token")
                    return None
                
                # Attendre la confirmation de l'approbation
                approval_success = wallet_service.wait_for_transaction(
                    from_chain,
                    approval_tx_hash,
                    timeout=180
                )
                
                if not approval_success:
                    logger.error("L'approbation du token n'a pas été confirmée")
                    return None
                
                logger.info(f"Approbation du token réussie: {approval_tx_hash}")
            
            # Préparer les paramètres de swap
            swap_params = self.prepare_swap_params(
                from_chain,
                to_chain,
                token_symbol,
                amount_wei,
                min_amount_wei,
                wallet_address
            )
            
            if not swap_params:
                logger.error("Impossible de préparer les paramètres de swap")
                return None
            
            # Estimer les frais de bridge
            fee = self.quote_fee(from_chain, to_chain, token_symbol, wallet_address)
            if fee is None:
                logger.error("Impossible d'estimer les frais de bridge")
                return None
            
            # Préparer la transaction
            router_contract = self.router_contracts[from_chain]
            router_address = STARGATE_CHAINS[from_chain]["router"]
            
            # Construire les données de transaction
            tx_data = router_contract.encodeABI(
                fn_name="swap",
                args=[
                    swap_params["dst_chain_id"],
                    swap_params["src_pool_id"],
                    swap_params["dst_pool_id"],
                    Web3.to_checksum_address(swap_params["refund_address"]),
                    swap_params["amount"],
                    swap_params["min_amount"],
                    swap_params["to_address_bytes"],
                    swap_params["payload"],
                    swap_params["additional_data"]
                ]
            )
            
            # Exécuter la transaction
            tx_value = fee if token_symbol != "ETH" else (fee + amount_wei)
            
            tx_hash = wallet_service.send_transaction(
                wallet_address,
                from_chain,
                router_address,
                tx_value,
                tx_data
            )
            
            if not tx_hash:
                logger.error("Échec de l'exécution de la transaction de bridge")
                return None
            
            logger.info(f"Transaction de bridge Stargate initiée: {tx_hash}")
            
            # Attendre la confirmation de la transaction
            tx_success = wallet_service.wait_for_transaction(
                from_chain,
                tx_hash,
                timeout=300
            )
            
            if not tx_success:
                logger.error("La transaction de bridge n'a pas été confirmée sur la chaîne source")
                return None
            
            logger.info(f"Transaction de bridge Stargate confirmée sur la chaîne source: {tx_hash}")
            
            return {
                "tx_hash": tx_hash,
                "bridge_type": "stargate",
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_token": token_symbol,
                "to_token": token_symbol,
                "amount": amount,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge Stargate: {e}")
            return None
