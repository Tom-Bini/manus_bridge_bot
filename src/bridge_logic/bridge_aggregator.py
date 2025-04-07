"""
Module d'agrégation des services de bridge pour les transactions cross-chain.
Ce module permet de choisir le meilleur service de bridge pour chaque transaction.
"""
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time

from src.bridge_logic.jumper_bridge import JumperBridgeService
from src.bridge_logic.stargate_bridge import StargateBridgeService
from src.bridge_logic.relay_bridge import RelayBridgeService
from src.config.config import TRANSACTIONS_PER_DAY, MIN_TRANSACTION_INTERVAL_HOURS, MAX_TRANSACTION_INTERVAL_HOURS

logger = logging.getLogger(__name__)

class BridgeAggregator:
    """Agrégateur de services de bridge pour les transactions cross-chain."""
    
    def __init__(self, jumper_api_key: str = None, relay_api_key: str = None):
        """
        Initialise l'agrégateur de bridges.
        
        Args:
            jumper_api_key: Clé API pour Jumper/LI.FI (optionnel)
            relay_api_key: Clé API pour Relay (optionnel)
        """
        self.jumper_service = JumperBridgeService(jumper_api_key)
        self.stargate_service = StargateBridgeService()
        self.relay_service = RelayBridgeService(relay_api_key)
        
        # Mapping des services disponibles
        self.services = {
            "jumper": self.jumper_service,
            "stargate": self.stargate_service,
            "relay": self.relay_service
        }
        
        # Historique des transactions
        self.transaction_history = []
    
    def get_supported_chains(self) -> Dict[str, List[str]]:
        """
        Récupère la liste des chaînes supportées par chaque service.
        
        Returns:
            Dictionnaire des chaînes supportées par service
        """
        supported_chains = {}
        
        # Jumper/LI.FI
        jumper_chains = self.jumper_service.get_chains()
        if jumper_chains:
            supported_chains["jumper"] = [chain.get("key") for chain in jumper_chains]
        
        # Stargate
        from src.bridge_logic.stargate_bridge import STARGATE_CHAINS
        supported_chains["stargate"] = list(STARGATE_CHAINS.keys())
        
        # Relay
        relay_chains = self.relay_service.get_chains()
        if relay_chains:
            supported_chains["relay"] = [str(chain.get("id")) for chain in relay_chains]
        
        return supported_chains
    
    def select_random_service(self, from_chain: str, to_chain: str, token_symbol: str) -> str:
        """
        Sélectionne un service de bridge aléatoire compatible avec les paramètres.
        
        Args:
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            token_symbol: Symbole du token
        
        Returns:
            Nom du service sélectionné
        """
        # Vérifier quels services supportent cette combinaison
        supported_services = []
        
        # Jumper/LI.FI supporte presque toutes les combinaisons
        supported_services.append("jumper")
        
        # Stargate a des limitations spécifiques
        from src.bridge_logic.stargate_bridge import STARGATE_CHAINS, STARGATE_POOLS
        if (from_chain in STARGATE_CHAINS and to_chain in STARGATE_CHAINS and 
            token_symbol in STARGATE_POOLS and 
            from_chain in STARGATE_POOLS[token_symbol] and 
            to_chain in STARGATE_POOLS[token_symbol]):
            supported_services.append("stargate")
        
        # Relay est également assez flexible
        supported_services.append("relay")
        
        # Sélectionner un service aléatoire parmi ceux supportés
        return random.choice(supported_services)
    
    def generate_random_transaction_times(self, num_transactions: int = None) -> List[datetime]:
        """
        Génère des heures aléatoires pour les transactions quotidiennes.
        
        Args:
            num_transactions: Nombre de transactions à générer (par défaut: TRANSACTIONS_PER_DAY)
        
        Returns:
            Liste des heures de transaction
        """
        import datetime as dt
        from datetime import datetime, timedelta
        
        num_tx = num_transactions if num_transactions is not None else TRANSACTIONS_PER_DAY
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Définir la plage horaire (par exemple, entre 8h et 22h)
        start_hour = 8
        end_hour = 22
        
        # Générer des heures aléatoires
        transaction_times = []
        for _ in range(num_tx):
            # Générer une heure aléatoire entre start_hour et end_hour
            random_hour = random.randint(start_hour, end_hour)
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)
            
            tx_time = today.replace(hour=random_hour, minute=random_minute, second=random_second)
            
            # Si l'heure générée est dans le passé, la reporter à demain
            if tx_time < now:
                tx_time = tx_time + timedelta(days=1)
            
            transaction_times.append(tx_time)
        
        # Trier les heures
        transaction_times.sort()
        
        return transaction_times
    
    def select_random_transaction(self, wallet_address: str, available_chains: List[str], 
                                available_tokens: Dict[str, Dict[str, float]]) -> Tuple[str, str, str, str, float]:
        """
        Sélectionne une transaction aléatoire parmi les possibilités.
        
        Args:
            wallet_address: Adresse du wallet
            available_chains: Liste des chaînes disponibles
            available_tokens: Dictionnaire des tokens disponibles par chaîne avec leurs soldes
        
        Returns:
            Tuple (from_chain, to_chain, token_symbol, token_address, amount)
        """
        # Filtrer les chaînes avec des tokens disponibles
        valid_chains = []
        for chain in available_chains:
            if chain in available_tokens and available_tokens[chain]:
                valid_chains.append(chain)
        
        if not valid_chains:
            logger.error("Aucune chaîne valide avec des tokens disponibles")
            return None
        
        # Sélectionner une chaîne source aléatoire
        from_chain = random.choice(valid_chains)
        
        # Sélectionner un token aléatoire sur cette chaîne
        available_tokens_on_chain = available_tokens[from_chain]
        if not available_tokens_on_chain:
            logger.error(f"Aucun token disponible sur la chaîne {from_chain}")
            return None
        
        token_symbol = random.choice(list(available_tokens_on_chain.keys()))
        token_address = available_tokens_on_chain[token_symbol].get("address")
        token_balance = available_tokens_on_chain[token_symbol].get("balance", 0)
        
        # Vérifier si le solde est suffisant
        if token_balance <= 0:
            logger.error(f"Solde insuffisant pour le token {token_symbol} sur la chaîne {from_chain}")
            return None
        
        # Sélectionner une chaîne de destination différente
        other_chains = [chain for chain in valid_chains if chain != from_chain]
        if not other_chains:
            logger.error("Aucune chaîne de destination disponible")
            return None
        
        to_chain = random.choice(other_chains)
        
        # Calculer un montant aléatoire à bridger (entre 10% et 90% du solde)
        min_percentage = 10
        max_percentage = 90
        percentage = random.randint(min_percentage, max_percentage)
        amount = token_balance * percentage / 100
        
        return (from_chain, to_chain, token_symbol, token_address, amount)
    
    def execute_random_bridge(self, wallet_service, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Exécute un bridge aléatoire pour un wallet.
        
        Args:
            wallet_service: Service de gestion des wallets
            wallet_address: Adresse du wallet
        
        Returns:
            Résultat de la transaction ou None en cas d'erreur
        """
        try:
            # Mettre à jour les soldes du wallet
            balances = wallet_service.update_balances(wallet_address)
            if not balances:
                logger.error(f"Impossible de récupérer les soldes pour le wallet {wallet_address}")
                return None
            
            # Préparer les données pour la sélection aléatoire
            available_chains = list(balances.keys())
            available_tokens = {}
            
            for chain, tokens in balances.items():
                available_tokens[chain] = {}
                for token_symbol, balance in tokens.items():
                    # TODO: Récupérer l'adresse du token
                    token_address = "0x..."  # À remplacer par la vraie adresse
                    available_tokens[chain][token_symbol] = {
                        "address": token_address,
                        "balance": balance
                    }
            
            # Sélectionner une transaction aléatoire
            transaction = self.select_random_transaction(wallet_address, available_chains, available_tokens)
            if not transaction:
                logger.error("Impossible de sélectionner une transaction aléatoire")
                return None
            
            from_chain, to_chain, token_symbol, token_address, amount = transaction
            
            # Sélectionner un service aléatoire
            service_name = self.select_random_service(from_chain, to_chain, token_symbol)
            service = self.services[service_name]
            
            logger.info(f"Exécution d'un bridge aléatoire: {from_chain} -> {to_chain}, {amount} {token_symbol} via {service_name}")
            
            # Exécuter le bridge
            if service_name == "jumper":
                result = service.execute_bridge(
                    wallet_service,
                    wallet_address,
                    from_chain,
                    to_chain,
                    token_symbol,
                    token_symbol,
                    str(amount)
                )
            elif service_name == "stargate":
                result = service.execute_bridge(
                    wallet_service,
                    wallet_address,
                    from_chain,
                    to_chain,
                    token_symbol,
                    str(amount),
                    token_address
                )
            elif service_name == "relay":
                result = service.execute_bridge(
                    wallet_service,
                    wallet_address,
                    from_chain,
                    to_chain,
                    token_address,
                    token_address,  # Même token sur la chaîne de destination
                    str(amount)
                )
            
            if result:
                # Ajouter à l'historique des transactions
                self.transaction_history.append({
                    **result,
                    "service": service_name
                })
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge aléatoire: {e}")
            return None
