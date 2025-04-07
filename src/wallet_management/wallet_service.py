"""
Module principal pour la gestion des wallets.
Ce module intègre les différentes fonctionnalités de gestion des wallets.
"""
import logging
from typing import Dict, List, Optional, Any

from src.wallet_management.wallet_manager import WalletManager
from src.wallet_management.balance_checker import BalanceChecker
from src.wallet_management.transaction_manager import TransactionManager

logger = logging.getLogger(__name__)

class WalletService:
    """Service de gestion des wallets intégrant toutes les fonctionnalités."""
    
    def __init__(self, encryption_key: str = None, wallets_file: str = None):
        """
        Initialise le service de gestion des wallets.
        
        Args:
            encryption_key: Clé de chiffrement pour les clés privées
            wallets_file: Chemin vers le fichier de stockage des wallets
        """
        self.wallet_manager = WalletManager(encryption_key, wallets_file)
        self.balance_checker = BalanceChecker()
        self.transaction_manager = TransactionManager()
    
    def add_wallet(self, name: str, private_key: str) -> Dict[str, Any]:
        """
        Ajoute un wallet au système.
        
        Args:
            name: Nom du wallet
            private_key: Clé privée du wallet
        
        Returns:
            Informations du wallet ajouté
        """
        return self.wallet_manager.add_wallet(name, private_key)
    
    def remove_wallet(self, address: str) -> bool:
        """
        Supprime un wallet du système.
        
        Args:
            address: Adresse du wallet
        
        Returns:
            True si le wallet a été supprimé, False sinon
        """
        return self.wallet_manager.remove_wallet(address)
    
    def get_wallets(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des wallets.
        
        Returns:
            Liste des wallets
        """
        return self.wallet_manager.get_wallets()
    
    def get_wallet(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un wallet.
        
        Args:
            address: Adresse du wallet
        
        Returns:
            Informations du wallet ou None si le wallet n'existe pas
        """
        return self.wallet_manager.get_wallet(address)
    
    def update_balances(self, address: str) -> Dict[str, Dict[str, float]]:
        """
        Met à jour les soldes d'un wallet sur toutes les blockchains supportées.
        
        Args:
            address: Adresse du wallet
        
        Returns:
            Dictionnaire des soldes par blockchain et par token
        """
        balances = self.balance_checker.check_all_balances(address)
        
        # Mettre à jour les informations du wallet
        for chain_id, tokens in balances.items():
            for token_symbol, balance in tokens.items():
                self.wallet_manager.update_wallet_info(address, chain_id, token_symbol, balance)
        
        return balances
    
    def update_all_wallets_balances(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Met à jour les soldes de tous les wallets.
        
        Returns:
            Dictionnaire des soldes par wallet, par blockchain et par token
        """
        wallets = self.get_wallets()
        results = {}
        
        for wallet in wallets:
            address = wallet['address']
            results[address] = self.update_balances(address)
        
        return results
    
    def approve_token_for_bridge(self, wallet_address: str, chain_id: str, token_address: str, 
                               spender_address: str, amount: int) -> Optional[str]:
        """
        Approuve un contrat de bridge à dépenser des tokens.
        
        Args:
            wallet_address: Adresse du wallet
            chain_id: Identifiant de la blockchain
            token_address: Adresse du contrat du token
            spender_address: Adresse du contrat de bridge
            amount: Montant à approuver
        
        Returns:
            Hash de la transaction ou None en cas d'erreur
        """
        private_key = self.wallet_manager.get_private_key(wallet_address)
        if not private_key:
            logger.error(f"Clé privée non trouvée pour le wallet {wallet_address}")
            return None
        
        return self.transaction_manager.approve_token(
            chain_id, token_address, spender_address, amount, wallet_address, private_key
        )
    
    def send_transaction(self, wallet_address: str, chain_id: str, to_address: str, 
                       value: int, data: str = "") -> Optional[str]:
        """
        Envoie une transaction.
        
        Args:
            wallet_address: Adresse du wallet
            chain_id: Identifiant de la blockchain
            to_address: Adresse de destination
            value: Montant à envoyer en wei
            data: Données de la transaction (optionnel)
        
        Returns:
            Hash de la transaction ou None en cas d'erreur
        """
        private_key = self.wallet_manager.get_private_key(wallet_address)
        if not private_key:
            logger.error(f"Clé privée non trouvée pour le wallet {wallet_address}")
            return None
        
        return self.transaction_manager.send_transaction(
            chain_id, to_address, value, wallet_address, private_key, data
        )
    
    def wait_for_transaction(self, chain_id: str, tx_hash: str, timeout: int = 120) -> bool:
        """
        Attend la confirmation d'une transaction.
        
        Args:
            chain_id: Identifiant de la blockchain
            tx_hash: Hash de la transaction
            timeout: Délai d'attente en secondes
        
        Returns:
            True si la transaction a réussi, False sinon
        """
        receipt = self.transaction_manager.wait_for_transaction_receipt(chain_id, tx_hash, timeout)
        return self.transaction_manager.is_transaction_successful(receipt) if receipt else False
