"""
Module de gestion des wallets crypto.
Ce module permet de gérer plusieurs wallets crypto, de stocker de manière sécurisée
les clés privées et d'effectuer des opérations sur ces wallets.
"""
import json
import os
import logging
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from eth_account import Account
from web3 import Web3

from src.config.config import WALLET_ENCRYPTION_KEY, WALLETS_FILE

logger = logging.getLogger(__name__)

class WalletManager:
    """Gestionnaire de wallets crypto."""
    
    def __init__(self, encryption_key: str = None, wallets_file: str = None):
        """
        Initialise le gestionnaire de wallets.
        
        Args:
            encryption_key: Clé de chiffrement pour les clés privées
            wallets_file: Chemin vers le fichier de stockage des wallets
        """
        self.encryption_key = encryption_key or WALLET_ENCRYPTION_KEY
        self.wallets_file = wallets_file or WALLETS_FILE
        self.wallets = {}
        self.fernet = Fernet(self.encryption_key.encode() if self.encryption_key else Fernet.generate_key())
        
        # Charger les wallets existants
        self._load_wallets()
    
    def _load_wallets(self) -> None:
        """Charge les wallets depuis le fichier de stockage."""
        if os.path.exists(self.wallets_file):
            try:
                with open(self.wallets_file, 'r') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    decrypted_data = self.fernet.decrypt(encrypted_data.encode()).decode()
                    self.wallets = json.loads(decrypted_data)
                    logger.info(f"Chargement réussi de {len(self.wallets)} wallets")
                else:
                    logger.warning("Fichier de wallets vide, initialisation d'un nouveau dictionnaire")
                    self.wallets = {}
            except Exception as e:
                logger.error(f"Erreur lors du chargement des wallets: {e}")
                self.wallets = {}
        else:
            logger.info("Aucun fichier de wallets trouvé, initialisation d'un nouveau dictionnaire")
            self.wallets = {}
    
    def _save_wallets(self) -> None:
        """Sauvegarde les wallets dans le fichier de stockage."""
        try:
            encrypted_data = self.fernet.encrypt(json.dumps(self.wallets).encode()).decode()
            with open(self.wallets_file, 'w') as f:
                f.write(encrypted_data)
            logger.info(f"Sauvegarde réussie de {len(self.wallets)} wallets")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des wallets: {e}")
    
    def add_wallet(self, name: str, private_key: str) -> Dict[str, Any]:
        """
        Ajoute un wallet à partir de sa clé privée.
        
        Args:
            name: Nom du wallet
            private_key: Clé privée du wallet (format hexadécimal avec ou sans '0x')
        
        Returns:
            Dict contenant les informations du wallet ajouté
        """
        try:
            # Normaliser la clé privée
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            # Créer le compte à partir de la clé privée
            account = Account.from_key(private_key)
            address = account.address
            
            # Chiffrer la clé privée
            encrypted_key = self.fernet.encrypt(private_key.encode()).decode()
            
            # Ajouter le wallet
            wallet_info = {
                'name': name,
                'address': address,
                'encrypted_key': encrypted_key,
                'chains': {}  # Informations spécifiques à chaque chaîne
            }
            
            self.wallets[address] = wallet_info
            self._save_wallets()
            
            logger.info(f"Wallet '{name}' ajouté avec succès: {address}")
            return {
                'name': name,
                'address': address
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du wallet: {e}")
            raise ValueError(f"Impossible d'ajouter le wallet: {e}")
    
    def remove_wallet(self, address: str) -> bool:
        """
        Supprime un wallet.
        
        Args:
            address: Adresse du wallet à supprimer
        
        Returns:
            True si le wallet a été supprimé, False sinon
        """
        if address in self.wallets:
            del self.wallets[address]
            self._save_wallets()
            logger.info(f"Wallet supprimé avec succès: {address}")
            return True
        else:
            logger.warning(f"Wallet non trouvé: {address}")
            return False
    
    def get_wallets(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des wallets.
        
        Returns:
            Liste des wallets (sans les clés privées)
        """
        return [
            {
                'name': wallet['name'],
                'address': address,
                'chains': wallet.get('chains', {})
            }
            for address, wallet in self.wallets.items()
        ]
    
    def get_wallet(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un wallet.
        
        Args:
            address: Adresse du wallet
        
        Returns:
            Informations du wallet (sans la clé privée) ou None si le wallet n'existe pas
        """
        if address in self.wallets:
            wallet = self.wallets[address]
            return {
                'name': wallet['name'],
                'address': address,
                'chains': wallet.get('chains', {})
            }
        return None
    
    def get_private_key(self, address: str) -> Optional[str]:
        """
        Récupère la clé privée déchiffrée d'un wallet.
        
        Args:
            address: Adresse du wallet
        
        Returns:
            Clé privée déchiffrée ou None si le wallet n'existe pas
        """
        if address in self.wallets:
            try:
                encrypted_key = self.wallets[address]['encrypted_key']
                return self.fernet.decrypt(encrypted_key.encode()).decode()
            except Exception as e:
                logger.error(f"Erreur lors du déchiffrement de la clé privée: {e}")
                return None
        return None
    
    def update_wallet_info(self, address: str, chain_id: str, token_symbol: str, balance: float) -> bool:
        """
        Met à jour les informations d'un wallet pour une chaîne et un token spécifiques.
        
        Args:
            address: Adresse du wallet
            chain_id: Identifiant de la chaîne
            token_symbol: Symbole du token
            balance: Solde du token
        
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if address in self.wallets:
            if 'chains' not in self.wallets[address]:
                self.wallets[address]['chains'] = {}
            
            if chain_id not in self.wallets[address]['chains']:
                self.wallets[address]['chains'][chain_id] = {'tokens': {}}
            
            self.wallets[address]['chains'][chain_id]['tokens'][token_symbol] = balance
            self._save_wallets()
            return True
        return False
    
    def get_balance(self, address: str, chain_id: str, token_symbol: str) -> Optional[float]:
        """
        Récupère le solde d'un token pour un wallet et une chaîne spécifiques.
        
        Args:
            address: Adresse du wallet
            chain_id: Identifiant de la chaîne
            token_symbol: Symbole du token
        
        Returns:
            Solde du token ou None si les informations ne sont pas disponibles
        """
        if (address in self.wallets and 
            'chains' in self.wallets[address] and 
            chain_id in self.wallets[address]['chains'] and 
            'tokens' in self.wallets[address]['chains'][chain_id] and 
            token_symbol in self.wallets[address]['chains'][chain_id]['tokens']):
            return self.wallets[address]['chains'][chain_id]['tokens'][token_symbol]
        return None
