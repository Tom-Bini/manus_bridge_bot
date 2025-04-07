"""
Script principal du bot Crypto Bridge.
Ce script initialise et démarre tous les composants du système.
"""
import logging
import os
import threading
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crypto_bridge_bot.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Fonction principale qui initialise et démarre le bot."""
    try:
        logger.info("Démarrage du Bot Crypto Bridge...")
        
        # Importer les modules après la configuration du logging
        from src.wallet_management.wallet_service import WalletService
        from src.bridge_logic.bridge_service import BridgeService
        from src.telegram_interface.telegram_interface import TelegramInterface
        
        # Récupérer les clés API depuis les variables d'environnement
        encryption_key = os.getenv('ENCRYPTION_KEY')
        jumper_api_key = os.getenv('JUMPER_API_KEY')
        relay_api_key = os.getenv('RELAY_API_KEY')
        
        # Initialiser les services
        logger.info("Initialisation du service de gestion des wallets...")
        wallet_service = WalletService(encryption_key=encryption_key)
        
        logger.info("Initialisation du service de bridge...")
        bridge_service = BridgeService(wallet_service, jumper_api_key, relay_api_key)
        
        logger.info("Initialisation de l'interface Telegram...")
        telegram_interface = TelegramInterface(wallet_service, bridge_service)
        
        # Démarrer l'interface Telegram
        telegram_interface.start()
        
        # Démarrer le planificateur de bridge dans un thread séparé
        scheduler_thread = threading.Thread(target=bridge_service.run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        logger.info("Bot Crypto Bridge démarré avec succès!")
        
        # Maintenir le programme en cours d'exécution
        while True:
            time.sleep(60)
    
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()
