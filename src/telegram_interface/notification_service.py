"""
Module pour le système de notification du bot crypto.
Ce module permet d'envoyer des notifications via Telegram lorsque des transactions sont effectuées.
"""
import logging
from typing import Dict, List, Optional, Any, Callable
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Service de notification pour le bot crypto."""
    
    def __init__(self):
        """Initialise le service de notification."""
        self.callbacks = []
    
    def register_callback(self, callback: Callable[[str, Optional[Dict[str, Any]]], None]) -> None:
        """
        Enregistre une fonction de callback pour les notifications.
        
        Args:
            callback: Fonction à appeler lors d'une notification
        """
        self.callbacks.append(callback)
    
    def send_notification(self, message: str, transaction_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Envoie une notification via tous les callbacks enregistrés.
        
        Args:
            message: Message de notification
            transaction_data: Données de la transaction (optionnel)
        """
        for callback in self.callbacks:
            try:
                callback(message, transaction_data)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    def notify_transaction_started(self, wallet_address: str, from_chain: str, to_chain: str, 
                                 token_symbol: str, amount: str) -> None:
        """
        Envoie une notification de début de transaction.
        
        Args:
            wallet_address: Adresse du wallet
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            token_symbol: Symbole du token
            amount: Montant de la transaction
        """
        message = (
            f"🔄 Transaction démarrée\n\n"
            f"Wallet: {wallet_address}\n"
            f"De: {from_chain}\n"
            f"Vers: {to_chain}\n"
            f"Token: {token_symbol}\n"
            f"Montant: {amount}"
        )
        
        transaction_data = {
            "wallet_address": wallet_address,
            "from_chain": from_chain,
            "to_chain": to_chain,
            "token_symbol": token_symbol,
            "amount": amount,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
        
        self.send_notification(message, transaction_data)
    
    def notify_transaction_completed(self, transaction_data: Dict[str, Any]) -> None:
        """
        Envoie une notification de fin de transaction.
        
        Args:
            transaction_data: Données de la transaction
        """
        message = (
            f"✅ Transaction réussie\n\n"
            f"Service: {transaction_data.get('bridge_type')}\n"
            f"De: {transaction_data.get('from_chain')}\n"
            f"Vers: {transaction_data.get('to_chain')}\n"
            f"Token: {transaction_data.get('from_token')} → {transaction_data.get('to_token')}\n"
            f"Montant: {transaction_data.get('amount')}"
        )
        
        self.send_notification(message, transaction_data)
    
    def notify_transaction_failed(self, transaction_data: Dict[str, Any], error_message: str) -> None:
        """
        Envoie une notification d'échec de transaction.
        
        Args:
            transaction_data: Données de la transaction
            error_message: Message d'erreur
        """
        message = (
            f"❌ Transaction échouée\n\n"
            f"Service: {transaction_data.get('bridge_type')}\n"
            f"De: {transaction_data.get('from_chain')}\n"
            f"Vers: {transaction_data.get('to_chain')}\n"
            f"Token: {transaction_data.get('from_token')} → {transaction_data.get('to_token')}\n"
            f"Montant: {transaction_data.get('amount')}\n"
            f"Erreur: {error_message}"
        )
        
        # Mettre à jour le statut
        transaction_data["status"] = "failed"
        transaction_data["error"] = error_message
        
        self.send_notification(message, transaction_data)
    
    def notify_wallet_balance_updated(self, wallet_address: str, balances: Dict[str, Dict[str, float]]) -> None:
        """
        Envoie une notification de mise à jour des soldes d'un wallet.
        
        Args:
            wallet_address: Adresse du wallet
            balances: Soldes par chaîne et par token
        """
        message = f"💰 Soldes mis à jour pour {wallet_address}\n\n"
        
        for chain_id, tokens in balances.items():
            message += f"Chaîne: {chain_id}\n"
            for token_symbol, balance in tokens.items():
                message += f"  {token_symbol}: {balance}\n"
            message += "\n"
        
        self.send_notification(message, {
            "wallet_address": wallet_address,
            "balances": balances,
            "timestamp": datetime.now().isoformat()
        })
    
    def notify_system_status(self, status_message: str) -> None:
        """
        Envoie une notification de statut du système.
        
        Args:
            status_message: Message de statut
        """
        message = f"ℹ️ Statut du système\n\n{status_message}"
        
        self.send_notification(message, {
            "type": "system_status",
            "message": status_message,
            "timestamp": datetime.now().isoformat()
        })
