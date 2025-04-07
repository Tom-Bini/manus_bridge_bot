"""
Module pour la gestion des transactions sur différentes blockchains.
Ce module permet d'envoyer des transactions et d'interagir avec les blockchains.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from web3 import Web3
from eth_account import Account
import time

from src.config.config import SUPPORTED_CHAINS

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

class TransactionManager:
    """Classe pour gérer les transactions sur différentes blockchains."""
    
    def __init__(self):
        """Initialise le gestionnaire de transactions."""
        self.web3_connections = {}
        
        # Initialiser les connexions Web3 pour chaque blockchain
        for chain_id, rpc_url in RPC_URLS.items():
            try:
                self.web3_connections[chain_id] = Web3(Web3.HTTPProvider(rpc_url))
                logger.info(f"Connexion Web3 établie pour {chain_id}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la connexion Web3 pour {chain_id}: {e}")
    
    def get_gas_price(self, chain_id: str) -> Optional[int]:
        """
        Récupère le prix du gaz sur une blockchain.
        
        Args:
            chain_id: Identifiant de la blockchain
        
        Returns:
            Prix du gaz en wei ou None en cas d'erreur
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            return web3.eth.gas_price
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix du gaz sur {chain_id}: {e}")
            return None
    
    def get_nonce(self, chain_id: str, address: str) -> Optional[int]:
        """
        Récupère le nonce d'une adresse sur une blockchain.
        
        Args:
            chain_id: Identifiant de la blockchain
            address: Adresse du wallet
        
        Returns:
            Nonce ou None en cas d'erreur
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            return web3.eth.get_transaction_count(Web3.to_checksum_address(address))
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du nonce pour {address} sur {chain_id}: {e}")
            return None
    
    def approve_token(self, chain_id: str, token_address: str, spender_address: str, 
                     amount: int, wallet_address: str, private_key: str) -> Optional[str]:
        """
        Approuve un contrat à dépenser des tokens.
        
        Args:
            chain_id: Identifiant de la blockchain
            token_address: Adresse du contrat du token
            spender_address: Adresse du contrat autorisé à dépenser
            amount: Montant à approuver
            wallet_address: Adresse du wallet
            private_key: Clé privée du wallet
        
        Returns:
            Hash de la transaction ou None en cas d'erreur
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            
            # ABI minimal pour la fonction approve
            abi = [
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_spender", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ]
            
            contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abi)
            
            # Préparer la transaction
            nonce = self.get_nonce(chain_id, wallet_address)
            if nonce is None:
                return None
            
            gas_price = self.get_gas_price(chain_id)
            if gas_price is None:
                return None
            
            # Estimer le gaz nécessaire
            tx = contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                amount
            ).build_transaction({
                'chainId': web3.eth.chain_id,
                'gas': 100000,  # Valeur par défaut, sera estimée
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Estimer le gaz
            try:
                gas_estimate = web3.eth.estimate_gas(tx)
                tx['gas'] = gas_estimate
            except Exception as e:
                logger.warning(f"Erreur lors de l'estimation du gaz, utilisation de la valeur par défaut: {e}")
            
            # Signer la transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            
            # Envoyer la transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation du token {token_address} pour {spender_address} sur {chain_id}: {e}")
            return None
    
    def send_transaction(self, chain_id: str, to_address: str, value: int, 
                        wallet_address: str, private_key: str, data: str = "") -> Optional[str]:
        """
        Envoie une transaction sur une blockchain.
        
        Args:
            chain_id: Identifiant de la blockchain
            to_address: Adresse de destination
            value: Montant à envoyer en wei
            wallet_address: Adresse du wallet
            private_key: Clé privée du wallet
            data: Données de la transaction (optionnel)
        
        Returns:
            Hash de la transaction ou None en cas d'erreur
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            
            # Préparer la transaction
            nonce = self.get_nonce(chain_id, wallet_address)
            if nonce is None:
                return None
            
            gas_price = self.get_gas_price(chain_id)
            if gas_price is None:
                return None
            
            # Créer la transaction
            tx = {
                'to': Web3.to_checksum_address(to_address),
                'value': value,
                'gas': 21000,  # Valeur par défaut pour un transfert simple
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id,
            }
            
            if data:
                tx['data'] = data
                # Estimer le gaz pour les transactions avec des données
                try:
                    gas_estimate = web3.eth.estimate_gas(tx)
                    tx['gas'] = gas_estimate
                except Exception as e:
                    logger.warning(f"Erreur lors de l'estimation du gaz, utilisation de la valeur par défaut: {e}")
            
            # Signer la transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            
            # Envoyer la transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la transaction sur {chain_id}: {e}")
            return None
    
    def wait_for_transaction_receipt(self, chain_id: str, tx_hash: str, timeout: int = 120) -> Optional[Dict]:
        """
        Attend la confirmation d'une transaction.
        
        Args:
            chain_id: Identifiant de la blockchain
            tx_hash: Hash de la transaction
            timeout: Délai d'attente en secondes
        
        Returns:
            Reçu de la transaction ou None en cas d'erreur ou de timeout
        """
        if chain_id not in self.web3_connections:
            logger.error(f"Blockchain non supportée: {chain_id}")
            return None
        
        try:
            web3 = self.web3_connections[chain_id]
            
            # Convertir le hash en bytes si nécessaire
            if isinstance(tx_hash, str) and tx_hash.startswith('0x'):
                tx_hash = web3.to_bytes(hexstr=tx_hash)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    receipt = web3.eth.get_transaction_receipt(tx_hash)
                    if receipt is not None:
                        return dict(receipt)
                except Exception:
                    # Transaction pas encore minée
                    pass
                
                time.sleep(2)
            
            logger.warning(f"Timeout en attendant la confirmation de la transaction {tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'attente de la confirmation de la transaction: {e}")
            return None
    
    def is_transaction_successful(self, receipt: Dict) -> bool:
        """
        Vérifie si une transaction a été exécutée avec succès.
        
        Args:
            receipt: Reçu de la transaction
        
        Returns:
            True si la transaction a réussi, False sinon
        """
        return receipt is not None and receipt.get('status') == 1
