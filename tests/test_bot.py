"""
Script de test pour le bot Crypto Bridge.
Ce script permet de tester les différentes fonctionnalités du système.
"""
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestWalletManagement(unittest.TestCase):
    """Tests pour le système de gestion des wallets."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        from src.wallet_management.wallet_service import WalletService
        self.wallet_service = WalletService(encryption_key="test_key")
    
    def test_add_wallet(self):
        """Test de l'ajout d'un wallet."""
        # Utiliser une clé privée de test
        test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        result = self.wallet_service.add_wallet("test_wallet", test_private_key)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test_wallet")
        self.assertIn("address", result)
    
    def test_get_wallets(self):
        """Test de la récupération des wallets."""
        # Ajouter un wallet de test
        test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        self.wallet_service.add_wallet("test_wallet", test_private_key)
        
        wallets = self.wallet_service.get_wallets()
        
        self.assertIsNotNone(wallets)
        self.assertGreaterEqual(len(wallets), 1)
    
    def test_remove_wallet(self):
        """Test de la suppression d'un wallet."""
        # Ajouter un wallet de test
        test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        wallet = self.wallet_service.add_wallet("test_wallet", test_private_key)
        
        result = self.wallet_service.remove_wallet(wallet["address"])
        
        self.assertTrue(result)

class TestBridgeLogic(unittest.TestCase):
    """Tests pour la logique de bridge."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        from src.wallet_management.wallet_service import WalletService
        from src.bridge_logic.bridge_service import BridgeService
        
        # Créer des mocks pour les services externes
        self.wallet_service = MagicMock(spec=WalletService)
        self.bridge_service = BridgeService(self.wallet_service)
    
    @patch('src.bridge_logic.jumper_bridge.JumperBridgeService.get_quote')
    def test_bridge_aggregator(self, mock_get_quote):
        """Test de l'agrégateur de bridge."""
        # Configurer le mock
        mock_get_quote.return_value = {
            "action": {"fromChainId": "1"},
            "transactionRequest": {
                "to": "0x1234",
                "data": "0xabcd",
                "value": "0x0"
            }
        }
        
        # Tester la génération des heures de transaction
        transaction_times = self.bridge_service.aggregator.generate_random_transaction_times(2)
        
        self.assertEqual(len(transaction_times), 2)
        self.assertTrue(transaction_times[0] < transaction_times[1])  # Vérifier que les heures sont triées

class TestTelegramInterface(unittest.TestCase):
    """Tests pour l'interface Telegram."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        from src.telegram_interface.notification_service import NotificationService
        
        self.notification_service = NotificationService()
    
    def test_notification_service(self):
        """Test du service de notification."""
        # Créer un mock pour le callback
        mock_callback = MagicMock()
        
        # Enregistrer le callback
        self.notification_service.register_callback(mock_callback)
        
        # Envoyer une notification
        test_message = "Test notification"
        test_data = {"test": "data"}
        self.notification_service.send_notification(test_message, test_data)
        
        # Vérifier que le callback a été appelé avec les bons arguments
        mock_callback.assert_called_once_with(test_message, test_data)

def run_tests():
    """Exécute tous les tests."""
    logger.info("Exécution des tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    logger.info("Tests terminés.")

if __name__ == "__main__":
    run_tests()
