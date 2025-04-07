"""
Module principal pour la logique de bridge.
Ce module intègre les différents services de bridge et l'agrégateur.
"""
import logging
from typing import Dict, List, Optional, Any
import schedule
import time
import random
from datetime import datetime, timedelta

from src.bridge_logic.bridge_aggregator import BridgeAggregator
from src.config.config import TRANSACTIONS_PER_DAY

logger = logging.getLogger(__name__)

class BridgeService:
    """Service principal pour la gestion des bridges cross-chain."""
    
    def __init__(self, wallet_service, jumper_api_key: str = None, relay_api_key: str = None):
        """
        Initialise le service de bridge.
        
        Args:
            wallet_service: Service de gestion des wallets
            jumper_api_key: Clé API pour Jumper/LI.FI (optionnel)
            relay_api_key: Clé API pour Relay (optionnel)
        """
        self.wallet_service = wallet_service
        self.aggregator = BridgeAggregator(jumper_api_key, relay_api_key)
        self.scheduled_transactions = {}
        self.notification_callbacks = []
    
    def register_notification_callback(self, callback):
        """
        Enregistre une fonction de callback pour les notifications.
        
        Args:
            callback: Fonction à appeler lors d'une notification
        """
        self.notification_callbacks.append(callback)
    
    def notify(self, message: str, transaction_data: Optional[Dict[str, Any]] = None):
        """
        Envoie une notification via tous les callbacks enregistrés.
        
        Args:
            message: Message de notification
            transaction_data: Données de la transaction (optionnel)
        """
        for callback in self.notification_callbacks:
            try:
                callback(message, transaction_data)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    def schedule_random_transactions(self, wallet_address: str, num_transactions: int = None):
        """
        Planifie des transactions aléatoires pour un wallet.
        
        Args:
            wallet_address: Adresse du wallet
            num_transactions: Nombre de transactions à planifier (par défaut: TRANSACTIONS_PER_DAY)
        """
        # Annuler les transactions précédemment planifiées pour ce wallet
        if wallet_address in self.scheduled_transactions:
            for job in self.scheduled_transactions[wallet_address]:
                schedule.cancel_job(job)
        
        # Générer des heures aléatoires pour les transactions
        num_tx = num_transactions if num_transactions is not None else TRANSACTIONS_PER_DAY
        transaction_times = self.aggregator.generate_random_transaction_times(num_tx)
        
        # Planifier les nouvelles transactions
        self.scheduled_transactions[wallet_address] = []
        
        for i, tx_time in enumerate(transaction_times):
            # Créer une fonction de transaction pour ce wallet
            def execute_transaction(wallet_addr=wallet_address, tx_index=i+1):
                logger.info(f"Exécution de la transaction planifiée {tx_index}/{num_tx} pour {wallet_addr}")
                result = self.execute_random_bridge(wallet_addr)
                if result:
                    self.notify(
                        f"Transaction {tx_index}/{num_tx} exécutée avec succès pour {wallet_addr}",
                        result
                    )
                else:
                    self.notify(
                        f"Échec de la transaction {tx_index}/{num_tx} pour {wallet_addr}"
                    )
            
            # Planifier la transaction
            job = schedule.every().day.at(tx_time.strftime("%H:%M:%S")).do(execute_transaction)
            self.scheduled_transactions[wallet_address].append(job)
            
            logger.info(f"Transaction {i+1}/{num_tx} planifiée pour {wallet_address} à {tx_time}")
        
        self.notify(
            f"{num_tx} transactions planifiées pour {wallet_address} aux heures suivantes: " +
            ", ".join([tx_time.strftime("%H:%M:%S") for tx_time in transaction_times])
        )
    
    def execute_random_bridge(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Exécute un bridge aléatoire pour un wallet.
        
        Args:
            wallet_address: Adresse du wallet
        
        Returns:
            Résultat de la transaction ou None en cas d'erreur
        """
        return self.aggregator.execute_random_bridge(self.wallet_service, wallet_address)
    
    def run_scheduler(self):
        """Exécute le planificateur de tâches."""
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des transactions.
        
        Returns:
            Liste des transactions effectuées
        """
        return self.aggregator.transaction_history
