"""
Module d'intégration avec Relay pour les bridges cross-chain.
Ce module permet d'effectuer des bridges entre différentes blockchains via l'API Relay.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime

from src.config.config import BRIDGE_SERVICES

logger = logging.getLogger(__name__)

class RelayBridgeService:
    """Service d'intégration avec l'API Relay pour les bridges cross-chain."""
    
    def __init__(self, api_key: str = None):
        """
        Initialise le service de bridge Relay.
        
        Args:
            api_key: Clé API pour Relay (optionnel)
        """
        self.api_url = BRIDGE_SERVICES.get("relay", {}).get("api_url", "https://api.relay.link")
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key
    
    def get_chains(self) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère la liste des chaînes supportées par Relay.
        
        Returns:
            Liste des chaînes supportées ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/chains"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des chaînes supportées par Relay: {e}")
            return None
    
    def get_token_price(self, chain_id: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le prix d'un token sur une chaîne spécifique.
        
        Args:
            chain_id: Identifiant de la chaîne
            token_address: Adresse du contrat du token
        
        Returns:
            Prix du token ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/token-price"
            params = {
                "chainId": chain_id,
                "tokenAddress": token_address
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix du token: {e}")
            return None
    
    def get_quote(self, from_chain_id: str, to_chain_id: str, from_token_address: str, 
                 to_token_address: str, amount: str, sender_address: str, recipient_address: str = None) -> Optional[Dict[str, Any]]:
        """
        Obtient un devis pour un bridge entre deux blockchains.
        
        Args:
            from_chain_id: ID de la chaîne source
            to_chain_id: ID de la chaîne de destination
            from_token_address: Adresse du token source
            to_token_address: Adresse du token de destination
            amount: Montant à bridger (en unités du token)
            sender_address: Adresse du wallet source
            recipient_address: Adresse du wallet destinataire (optionnel, par défaut = sender_address)
        
        Returns:
            Devis pour le bridge ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/quote"
            
            data = {
                "fromChainId": from_chain_id,
                "toChainId": to_chain_id,
                "fromTokenAddress": from_token_address,
                "toTokenAddress": to_token_address,
                "fromAmount": amount,
                "fromAddress": sender_address,
                "toAddress": recipient_address or sender_address
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du devis Relay: {e}")
            return None
    
    def get_execution_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie le statut d'une exécution de bridge.
        
        Args:
            request_id: ID de la requête
        
        Returns:
            Statut de l'exécution ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/execution-status"
            params = {
                "requestId": request_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut d'exécution: {e}")
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
            if not quote or "tx" not in quote:
                logger.error("Devis invalide ou incomplet")
                return None
            
            tx = quote["tx"]
            
            return {
                "to": tx.get("to"),
                "data": tx.get("data"),
                "value": tx.get("value", "0"),
                "gas_limit": tx.get("gasLimit", "0"),
                "chain_id": quote.get("fromChainId"),
                "request_id": quote.get("requestId")
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données de transaction: {e}")
            return None
    
    def notify_transaction(self, request_id: str, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Notifie Relay d'une transaction.
        
        Args:
            request_id: ID de la requête
            tx_hash: Hash de la transaction
        
        Returns:
            Résultat de la notification ou None en cas d'erreur
        """
        try:
            url = f"{self.api_url}/transactions"
            
            data = {
                "requestId": request_id,
                "txHash": tx_hash
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Erreur lors de la notification de la transaction: {e}")
            return None
    
    def execute_bridge(self, wallet_service, wallet_address: str, from_chain_id: str, to_chain_id: str, 
                      from_token_address: str, to_token_address: str, amount: str) -> Optional[Dict[str, Any]]:
        """
        Exécute un bridge entre deux blockchains.
        
        Args:
            wallet_service: Service de gestion des wallets
            wallet_address: Adresse du wallet
            from_chain_id: ID de la chaîne source
            to_chain_id: ID de la chaîne de destination
            from_token_address: Adresse du token source
            to_token_address: Adresse du token de destination
            amount: Montant à bridger (en unités du token)
        
        Returns:
            Résultat de la transaction ou None en cas d'erreur
        """
        try:
            # Obtenir un devis
            quote = self.get_quote(
                from_chain_id,
                to_chain_id,
                from_token_address,
                to_token_address,
                amount,
                wallet_address
            )
            
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
                
                logger.info(f"Approbation nécessaire pour le token {from_token_address}")
                
                # Exécuter l'approbation
                approval_tx_hash = wallet_service.approve_token_for_bridge(
                    wallet_address,
                    tx_data["chain_id"],
                    from_token_address,
                    approval_data.get("spender"),
                    int(approval_data.get("amount", "0"), 16) if isinstance(approval_data.get("amount"), str) else int(approval_data.get("amount", "0"))
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
            tx_value = int(tx_data["value"], 16) if isinstance(tx_data["value"], str) and tx_data["value"].startswith("0x") else int(tx_data["value"])
            
            tx_hash = wallet_service.send_transaction(
                wallet_address,
                tx_data["chain_id"],
                tx_data["to"],
                tx_value,
                tx_data["data"]
            )
            
            if not tx_hash:
                logger.error("Échec de l'exécution de la transaction de bridge")
                return None
            
            logger.info(f"Transaction de bridge Relay initiée: {tx_hash}")
            
            # Notifier Relay de la transaction
            notification_result = self.notify_transaction(tx_data["request_id"], tx_hash)
            if not notification_result:
                logger.warning("Impossible de notifier Relay de la transaction")
            
            # Attendre la confirmation de la transaction
            tx_success = wallet_service.wait_for_transaction(
                tx_data["chain_id"],
                tx_hash,
                timeout=300
            )
            
            if not tx_success:
                logger.error("La transaction de bridge n'a pas été confirmée sur la chaîne source")
                return None
            
            logger.info(f"Transaction de bridge Relay confirmée sur la chaîne source: {tx_hash}")
            
            # Récupérer les informations de la transaction
            return {
                "tx_hash": tx_hash,
                "bridge_type": "relay",
                "request_id": tx_data["request_id"],
                "from_chain_id": from_chain_id,
                "to_chain_id": to_chain_id,
                "from_token": from_token_address,
                "to_token": to_token_address,
                "amount": amount,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge Relay: {e}")
            return None
