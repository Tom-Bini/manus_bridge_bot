"""
Module d'intégration avec l'API LI.FI/Jumper pour les bridges cross-chain.
Ce module permet d'effectuer des bridges entre différentes blockchains via l'API LI.FI.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime

from src.config.config import BRIDGE_SERVICES

logger = logging.getLogger(__name__)

class JumperBridgeService:
    """Service d'intégration avec l'API LI.FI/Jumper pour les bridges cross-chain."""
    
    def __init__(self, api_key: str = None):
        """
        Initialise le service de bridge Jumper.
        
        Args:
            api_key: Clé API pour LI.FI/Jumper (optionnel)
        """
        self.api_url = BRIDGE_SERVICES.get("jumper", {}).get("api_url", "https://li.quest/v1")
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key
    
    def get_quote(self, from_chain: str, to_chain: str, from_token: str, to_token: str, 
                 from_amount: str, from_address: str) -> Optional[Dict[str, Any]]:
        """
        Obtient un devis pour un bridge entre deux blockchains.
        
        Args:
            from_chain: Chaîne source (ex: "ETH", "POL")
            to_chain: Chaîne de destination (ex: "ARB", "OPT")
            from_token: Token source (ex: "USDC", "ETH")
            to_token: Token de destination (ex: "USDC", "ETH")
            from_amount: Montant à bridger (en unités du token)
            from_address: Adresse du wallet source
        
        Returns:
            Devis pour le bridge ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/quote"
            params = {
                "fromChain": from_chain,
                "toChain": to_chain,
                "fromToken": from_token,
                "toToken": to_token,
                "fromAmount": from_amount,
                "fromAddress": from_address
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du devis Jumper: {e}")
            return None
    
    def get_status(self, tx_hash: str, bridge_type: str, from_chain: str, to_chain: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie le statut d'une transaction de bridge.
        
        Args:
            tx_hash: Hash de la transaction
            bridge_type: Type de bridge utilisé
            from_chain: Chaîne source
            to_chain: Chaîne de destination
        
        Returns:
            Statut de la transaction ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/status"
            params = {
                "txHash": tx_hash,
                "bridge": bridge_type,
                "fromChain": from_chain,
                "toChain": to_chain
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut de la transaction Jumper: {e}")
            return None
    
    def get_chains(self) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère la liste des chaînes supportées par LI.FI/Jumper.
        
        Returns:
            Liste des chaînes supportées ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/chains"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des chaînes supportées par Jumper: {e}")
            return None
    
    def get_tokens(self, chain_id: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère la liste des tokens supportés par LI.FI/Jumper.
        
        Args:
            chain_id: Identifiant de la chaîne (optionnel)
        
        Returns:
            Liste des tokens supportés ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/tokens"
            params = {}
            
            if chain_id:
                params["chains"] = chain_id
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tokens supportés par Jumper: {e}")
            return None
    
    def get_connections(self, from_chain: str = None, to_chain: str = None) -> Optional[Dict[str, Any]]:
        """
        Récupère les connexions possibles entre les chaînes.
        
        Args:
            from_chain: Chaîne source (optionnel)
            to_chain: Chaîne de destination (optionnel)
        
        Returns:
            Connexions possibles ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/connections"
            params = {}
            
            if from_chain:
                params["fromChain"] = from_chain
            
            if to_chain:
                params["toChain"] = to_chain
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des connexions Jumper: {e}")
            return None
    
    def prepare_transaction_data(self, quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prépare les données de transaction à partir d'un devis.
        
        Args:
            quote: Devis obtenu via get_quote
        
        Returns:
            Données de transaction ou None en cas d'erreur
        """
        try:
            # Extraire les informations nécessaires du devis
            if not quote or "transactionRequest" not in quote:
                logger.error("Devis invalide ou incomplet")
                return None
            
            tx_request = quote["transactionRequest"]
            
            return {
                "to": tx_request.get("to"),
                "data": tx_request.get("data"),
                "value": tx_request.get("value", "0"),
                "gasLimit": tx_request.get("gasLimit", "0"),
                "gasPrice": tx_request.get("gasPrice", "0"),
                "chain_id": quote.get("action", {}).get("fromChainId")
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données de transaction: {e}")
            return None
    
    def execute_bridge(self, wallet_service, wallet_address: str, from_chain: str, to_chain: str, 
                      from_token: str, to_token: str, amount: str) -> Optional[Dict[str, Any]]:
        """
        Exécute un bridge entre deux blockchains.
        
        Args:
            wallet_service: Service de gestion des wallets
            wallet_address: Adresse du wallet
            from_chain: Chaîne source
            to_chain: Chaîne de destination
            from_token: Token source
            to_token: Token de destination
            amount: Montant à bridger
        
        Returns:
            Résultat de la transaction ou None en cas d'erreur
        """
        try:
            # Obtenir un devis
            quote = self.get_quote(from_chain, to_chain, from_token, to_token, amount, wallet_address)
            if not quote:
                logger.error("Impossible d'obtenir un devis pour le bridge")
                return None
            
            # Préparer les données de transaction
            tx_data = self.prepare_transaction_data(quote)
            if not tx_data:
                logger.error("Impossible de préparer les données de transaction")
                return None
            
            # Vérifier si une approbation est nécessaire
            if "approvalData" in quote and quote["approvalData"]:
                approval_data = quote["approvalData"]
                
                logger.info(f"Approbation nécessaire pour le token {from_token}")
                
                # Exécuter l'approbation
                approval_tx_hash = wallet_service.approve_token_for_bridge(
                    wallet_address,
                    tx_data["chain_id"],
                    approval_data.get("tokenAddress"),
                    approval_data.get("spenderAddress"),
                    int(approval_data.get("amount", "0"), 16)
                )
                
                if not approval_tx_hash:
                    logger.error("Échec de l'approbation du token")
                    return None
                
                # Attendre la confirmation de l'approbation
                approval_success = wallet_service.wait_for_transaction(
                    tx_data["chain_id"],
                    approval_tx_hash,
                    timeout=180
                )
                
                if not approval_success:
                    logger.error("L'approbation du token n'a pas été confirmée")
                    return None
                
                logger.info(f"Approbation du token réussie: {approval_tx_hash}")
            
            # Exécuter la transaction de bridge
            tx_hash = wallet_service.send_transaction(
                wallet_address,
                tx_data["chain_id"],
                tx_data["to"],
                int(tx_data["value"], 16) if isinstance(tx_data["value"], str) and tx_data["value"].startswith("0x") else int(tx_data["value"]),
                tx_data["data"]
            )
            
            if not tx_hash:
                logger.error("Échec de l'exécution de la transaction de bridge")
                return None
            
            logger.info(f"Transaction de bridge initiée: {tx_hash}")
            
            # Attendre la confirmation de la transaction
            tx_success = wallet_service.wait_for_transaction(
                tx_data["chain_id"],
                tx_hash,
                timeout=300
            )
            
            if not tx_success:
                logger.error("La transaction de bridge n'a pas été confirmée sur la chaîne source")
                return None
            
            logger.info(f"Transaction de bridge confirmée sur la chaîne source: {tx_hash}")
            
            # Récupérer les informations de la transaction
            bridge_type = quote.get("tool")
            
            return {
                "tx_hash": tx_hash,
                "bridge_type": bridge_type,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_token": from_token,
                "to_token": to_token,
                "amount": amount,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge: {e}")
            return None
