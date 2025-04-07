"""
Module pour l'interface Telegram du bot crypto.
Ce module permet de créer et gérer un bot Telegram pour contrôler les opérations
de bridge crypto et recevoir des notifications.
"""
import logging
from typing import Dict, List, Optional, Any, Callable
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_IDS

logger = logging.getLogger(__name__)

class TelegramBot:
    """Classe pour gérer l'interface Telegram du bot crypto."""
    
    def __init__(self, wallet_service=None, bridge_service=None):
        """
        Initialise le bot Telegram.
        
        Args:
            wallet_service: Service de gestion des wallets
            bridge_service: Service de gestion des bridges
        """
        self.token = TELEGRAM_TOKEN
        self.admin_chat_ids = [int(chat_id) for chat_id in ADMIN_CHAT_IDS]
        self.wallet_service = wallet_service
        self.bridge_service = bridge_service
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /start.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            logger.warning(f"Tentative d'accès non autorisé par l'utilisateur {user_id}")
            return
        
        await update.message.reply_text(
            f"Bienvenue dans le Bot Crypto Bridge!\n\n"
            f"Ce bot vous permet de gérer des wallets crypto et d'effectuer des bridges automatiques "
            f"entre différentes blockchains via Jumper, Stargate et Relay.\n\n"
            f"Utilisez /help pour voir la liste des commandes disponibles."
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /help.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        help_text = (
            "Commandes disponibles:\n\n"
            "/start - Démarrer le bot\n"
            "/help - Afficher cette aide\n"
            "/add_wallet <nom> <clé_privée> - Ajouter un wallet\n"
            "/list_wallets - Lister les wallets\n"
            "/remove_wallet <adresse> - Supprimer un wallet\n"
            "/check_balance <adresse> - Vérifier les soldes d'un wallet\n"
            "/schedule_transactions <adresse> [nombre] - Planifier des transactions aléatoires\n"
            "/execute_bridge <adresse> - Exécuter un bridge aléatoire immédiatement\n"
            "/transaction_history - Afficher l'historique des transactions\n"
            "/status - Vérifier le statut du bot et afficher les boutons de débogage\n"
        )
        
        await update.message.reply_text(help_text)
    
    async def add_wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /add_wallet.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.wallet_service:
            await update.message.reply_text("Service de gestion des wallets non disponible.")
            return
        
        # Vérifier les arguments
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /add_wallet <nom> <clé_privée>")
            return
        
        name = context.args[0]
        private_key = context.args[1]
        
        try:
            # Supprimer le message contenant la clé privée pour des raisons de sécurité
            await update.message.delete()
            
            # Ajouter le wallet
            result = self.wallet_service.add_wallet(name, private_key)
            
            if result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Wallet '{name}' ajouté avec succès!\nAdresse: {result['address']}"
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Erreur lors de l'ajout du wallet."
                )
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du wallet: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Erreur: {str(e)}"
            )
    
    async def list_wallets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /list_wallets.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.wallet_service:
            await update.message.reply_text("Service de gestion des wallets non disponible.")
            return
        
        try:
            wallets = self.wallet_service.get_wallets()
            
            if not wallets:
                await update.message.reply_text("Aucun wallet trouvé.")
                return
            
            response = "Wallets disponibles:\n\n"
            
            for wallet in wallets:
                response += f"Nom: {wallet['name']}\n"
                response += f"Adresse: {wallet['address']}\n"
                
                if 'chains' in wallet and wallet['chains']:
                    response += "Chaînes:\n"
                    for chain_id, chain_data in wallet['chains'].items():
                        response += f"  - {chain_id}:\n"
                        if 'tokens' in chain_data:
                            for token, balance in chain_data['tokens'].items():
                                response += f"    {token}: {balance}\n"
                
                response += "\n"
            
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des wallets: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def remove_wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /remove_wallet.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.wallet_service:
            await update.message.reply_text("Service de gestion des wallets non disponible.")
            return
        
        # Vérifier les arguments
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /remove_wallet <adresse>")
            return
        
        address = context.args[0]
        
        try:
            result = self.wallet_service.remove_wallet(address)
            
            if result:
                await update.message.reply_text(f"Wallet {address} supprimé avec succès!")
            else:
                await update.message.reply_text(f"Wallet {address} non trouvé.")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du wallet: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def check_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /check_balance.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.wallet_service:
            await update.message.reply_text("Service de gestion des wallets non disponible.")
            return
        
        # Vérifier les arguments
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /check_balance <adresse>")
            return
        
        address = context.args[0]
        
        try:
            # Envoyer un message de chargement
            message = await update.message.reply_text("Vérification des soldes en cours...")
            
            # Mettre à jour les soldes
            balances = self.wallet_service.update_balances(address)
            
            if not balances:
                await message.edit_text(f"Aucun solde trouvé pour le wallet {address}.")
                return
            
            response = f"Soldes pour le wallet {address}:\n\n"
            
            for chain_id, tokens in balances.items():
                response += f"Chaîne: {chain_id}\n"
                for token_symbol, balance in tokens.items():
                    response += f"  {token_symbol}: {balance}\n"
                response += "\n"
            
            await message.edit_text(response)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des soldes: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def schedule_transactions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /schedule_transactions.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.bridge_service:
            await update.message.reply_text("Service de bridge non disponible.")
            return
        
        # Vérifier les arguments
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /schedule_transactions <adresse> [nombre]")
            return
        
        address = context.args[0]
        num_transactions = int(context.args[1]) if len(context.args) > 1 else None
        
        try:
            # Planifier les transactions
            self.bridge_service.schedule_random_transactions(address, num_transactions)
            
            num_tx = num_transactions if num_transactions is not None else 2  # Valeur par défaut
            await update.message.reply_text(
                f"{num_tx} transactions aléatoires planifiées pour le wallet {address}.\n"
                f"Vous recevrez des notifications lorsque les transactions seront exécutées."
            )
        except Exception as e:
            logger.error(f"Erreur lors de la planification des transactions: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def execute_bridge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /execute_bridge.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.bridge_service:
            await update.message.reply_text("Service de bridge non disponible.")
            return
        
        # Vérifier les arguments
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /execute_bridge <adresse>")
            return
        
        address = context.args[0]
        
        try:
            # Envoyer un message de chargement
            message = await update.message.reply_text("Exécution d'un bridge aléatoire en cours...")
            
            # Exécuter un bridge aléatoire
            result = self.bridge_service.execute_random_bridge(address)
            
            if result:
                response = (
                    f"Bridge exécuté avec succès!\n\n"
                    f"Service: {result.get('bridge_type')}\n"
                    f"De: {result.get('from_chain')} ({result.get('from_token')})\n"
                    f"Vers: {result.get('to_chain')} ({result.get('to_token')})\n"
                    f"Montant: {result.get('amount')}\n"
                    f"Hash de transaction: {result.get('tx_hash')}\n"
                    f"Statut: {result.get('status')}"
                )
                await message.edit_text(response)
            else:
                await message.edit_text("Erreur lors de l'exécution du bridge.")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def transaction_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /transaction_history.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        if not self.bridge_service:
            await update.message.reply_text("Service de bridge non disponible.")
            return
        
        try:
            history = self.bridge_service.get_transaction_history()
            
            if not history:
                await update.message.reply_text("Aucune transaction dans l'historique.")
                return
            
            response = "Historique des transactions:\n\n"
            
            for i, tx in enumerate(history, 1):
                response += f"Transaction {i}:\n"
                response += f"Service: {tx.get('bridge_type')}\n"
                response += f"De: {tx.get('from_chain')} ({tx.get('from_token')})\n"
                response += f"Vers: {tx.get('to_chain')} ({tx.get('to_token')})\n"
                response += f"Montant: {tx.get('amount')}\n"
                response += f"Hash: {tx.get('tx_hash')}\n"
                response += f"Statut: {tx.get('status')}\n"
                response += f"Date: {tx.get('timestamp')}\n\n"
            
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique des transactions: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère la commande /status.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        user_id = update.effective_user.id
        
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")
            return
        
        try:
            wallet_count = len(self.wallet_service.get_wallets()) if self.wallet_service else 0
            
            response = (
                f"Statut du Bot Crypto Bridge:\n\n"
                f"Wallets configurés: {wallet_count}\n"
            )
            
            if self.bridge_service:
                tx_history = self.bridge_service.get_transaction_history()
                tx_count = len(tx_history) if tx_history else 0
                response += f"Transactions effectuées: {tx_count}\n"
            
            response += f"Bot opérationnel: Oui"
            
            # Créer des boutons pour les wallets disponibles
            keyboard = []
            if self.wallet_service:
                wallets = self.wallet_service.get_wallets()
                for wallet in wallets:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🔄 Exécuter bridge pour {wallet['name']}",
                            callback_data=f"debug_bridge:{wallet['address']}"
                        )
                    ])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            if reply_markup:
                await update.message.reply_text(response, reply_markup=reply_markup)
            else:
                await update.message.reply_text(response + "\n\nAucun wallet disponible pour le débogage.")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {e}")
            await update.message.reply_text(f"Erreur: {str(e)}")
    
    async def handle_debug_bridge_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gère les callbacks des boutons de débogage pour exécuter un bridge.
        
        Args:
            update: Mise à jour Telegram
            context: Contexte de la conversation
        """
        query = update.callback_query
        user_id = query.from_user.id
        
        if user_id not in self.admin_chat_ids:
            await query.answer("Vous n'êtes pas autorisé à utiliser cette fonction.")
            return
        
        # Extraire l'adresse du wallet du callback_data
        callback_data = query.data
        if not callback_data.startswith("debug_bridge:"):
            await query.answer("Callback invalide.")
            return
        
        wallet_address = callback_data.split(":", 1)[1]
        
        try:
            # Informer l'utilisateur que l'action est en cours
            await query.answer("Exécution d'un bridge en cours...")
            
            # Mettre à jour le message avec un indicateur de chargement
            await query.edit_message_text(
                f"{query.message.text}\n\n⏳ Exécution d'un bridge pour {wallet_address} en cours..."
            )
            
            # Exécuter un bridge aléatoire
            if self.bridge_service:
                result = self.bridge_service.execute_random_bridge(wallet_address)
                
                if result:
                    # Mettre à jour le message avec le résultat
                    response = (
                        f"{query.message.text}\n\n"
                        f"✅ Bridge exécuté avec succès!\n\n"
                        f"Service: {result.get('bridge_type')}\n"
                        f"De: {result.get('from_chain')} ({result.get('from_token')})\n"
                        f"Vers: {result.get('to_chain')} ({result.get('to_token')})\n"
                        f"Montant: {result.get('amount')}\n"
                        f"Hash: {result.get('tx_hash')}\n"
                        f"Statut: {result.get('status')}"
                    )
                    
                    # Recréer les boutons
                    keyboard = []
                    if self.wallet_service:
                        wallets = self.wallet_service.get_wallets()
                        for wallet in wallets:
                            keyboard.append([
                                InlineKeyboardButton(
                                    f"🔄 Exécuter bridge pour {wallet['name']}",
                                    callback_data=f"debug_bridge:{wallet['address']}"
                                )
                            ])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                    
                    await query.edit_message_text(response, reply_markup=reply_markup)
                else:
                    await query.edit_message_text(
                        f"{query.message.text}\n\n❌ Erreur lors de l'exécution du bridge."
                    )
            else:
                await query.edit_message_text(
                    f"{query.message.text}\n\nService de bridge non disponible."
                )
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du bridge via bouton de débogage: {e}")
            await query.edit_message_text(
                f"{query.message.text}\n\n❌ Erreur: {str(e)}"
            )
    
    async def send_notification(self, message: str, transaction_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Envoie une notification à tous les administrateurs.
        
        Args:
            message: Message à envoyer
            transaction_data: Données de la transaction (optionnel)
        """
        if not self.application:
            logger.error("Application Telegram non initialisée")
            return
        
        notification_text = message
        
        if transaction_data:
            notification_text += "\n\n"
            notification_text += f"Service: {transaction_data.get('bridge_type')}\n"
            notification_text += f"De: {transaction_data.get('from_chain')} ({transaction_data.get('from_token')})\n"
            notification_text += f"Vers: {transaction_data.get('to_chain')} ({transaction_data.get('to_token')})\n"
            notification_text += f"Montant: {transaction_data.get('amount')}\n"
            notification_text += f"Hash: {transaction_data.get('tx_hash')}\n"
            notification_text += f"Statut: {transaction_data.get('status')}"
        
        for chat_id in self.admin_chat_ids:
            try:
                await self.application.bot.send_message(chat_id=chat_id, text=notification_text)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification à {chat_id}: {e}")
    
    def notification_callback(self, message: str, transaction_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Callback pour les notifications du service de bridge.
        
        Args:
            message: Message de notification
            transaction_data: Données de la transaction (optionnel)
        """
        # Créer une tâche asynchrone pour envoyer la notification
        asyncio.create_task(self.send_notification(message, transaction_data))
    
    def start(self) -> None:
        """Démarre le bot Telegram."""
        if not self.token:
            logger.error("Token Telegram non configuré")
            return
        
        try:
            # Créer l'application
            self.application = Application.builder().token(self.token).build()
            
            # Ajouter les gestionnaires de commandes
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("add_wallet", self.add_wallet_command))
            self.application.add_handler(CommandHandler("list_wallets", self.list_wallets_command))
            self.application.add_handler(CommandHandler("remove_wallet", self.remove_wallet_command))
            self.application.add_handler(CommandHandler("check_balance", self.check_balance_command))
            self.application.add_handler(CommandHandler("schedule_transactions", self.schedule_transactions_command))
            self.application.add_handler(CommandHandler("execute_bridge", self.execute_bridge_command))
            self.application.add_handler(CommandHandler("transaction_history", self.transaction_history_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            
            # Ajouter le gestionnaire de callback pour les boutons de débogage
            self.application.add_handler(CallbackQueryHandler(self.handle_debug_bridge_callback, pattern="^debug_bridge:"))
            
            # Enregistrer le callback de notification
            if self.bridge_service:
                self.bridge_service.register_notification_callback(self.notification_callback)
            
            # Démarrer le bot
            self.application.run_polling()
            
            logger.info("Bot Telegram démarré")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot Telegram: {e}")
    
    def stop(self) -> None:
        """Arrête le bot Telegram."""
        if self.application:
            self.application.stop()
            logger.info("Bot Telegram arrêté")
