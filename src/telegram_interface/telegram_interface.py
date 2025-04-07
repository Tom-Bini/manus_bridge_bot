"""
Module d'intégration pour l'interface Telegram.
Ce module permet d'intégrer l'interface Telegram avec le reste du système.
"""
import logging
import threading
from typing import Dict, List, Optional, Any

from src.telegram_interface.telegram_bot import TelegramBot
from src.telegram_interface.notification_service import NotificationService

logger = logging.getLogger(__name__)

class TelegramInterface:
    """Classe d'intégration pour l'interface Telegram."""
    
    def __init__(self, wallet_service=None, bridge_service=None):
        """
        Initialise l'interface Telegram.
        
        Args:
            wallet_service: Service de gestion des wallets
            bridge_service: Service de gestion des bridges
        """
        self.wallet_service = wallet_service
        self.bridge_service = bridge_service
        self.notification_service = NotificationService()
        self.telegram_bot = TelegramBot(wallet_service, bridge_service)
        self.bot_thread = None
    
    def start(self):
        """Démarre l'interface Telegram dans un thread séparé."""
        # Enregistrer le callback de notification du bot Telegram
        self.notification_service.register_callback(self.telegram_bot.notification_callback)
        
        # Enregistrer le service de notification auprès du service de bridge
        if self.bridge_service:
            self.bridge_service.register_notification_callback(self.notification_service.send_notification)
        
        # Démarrer le bot dans un thread séparé
        self.bot_thread = threading.Thread(target=self.telegram_bot.start)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        logger.info("Interface Telegram démarrée")
    
    def stop(self):
        """Arrête l'interface Telegram."""
        if self.telegram_bot:
            self.telegram_bot.stop()
        
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)
        
        logger.info("Interface Telegram arrêtée")
    
    def send_notification(self, message: str, transaction_data: Optional[Dict[str, Any]] = None):
        """
        Envoie une notification via le service de notification.
        
        Args:
            message: Message de notification
            transaction_data: Données de la transaction (optionnel)
        """
        self.notification_service.send_notification(message, transaction_data)
