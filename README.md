"""
Documentation principale du bot Crypto Bridge.
Ce fichier contient la documentation complète du projet.
"""

# Bot Crypto Bridge avec Interface Telegram

## Vue d'ensemble

Le Bot Crypto Bridge est une solution automatisée pour gérer plusieurs wallets crypto et effectuer des bridges entre différentes blockchains. Le bot utilise les services Jumper (LI.FI), Stargate et Relay pour exécuter des transactions cross-chain de manière aléatoire et automatique. Une interface Telegram permet de contrôler le bot et de recevoir des notifications sur les transactions effectuées.

## Fonctionnalités principales

- **Gestion de wallets multiples** : Stockage sécurisé des clés privées avec chiffrement
- **Vérification des soldes** : Suivi des soldes sur différentes blockchains
- **Bridges automatiques** : Exécution de 2 transactions aléatoires par jour
- **Planification aléatoire** : Les transactions sont effectuées à des moments aléatoires
- **Interface Telegram** : Contrôle du bot et réception de notifications
- **Support multi-chaînes** : Compatible avec Ethereum, Polygon, Arbitrum, Optimism, Avalanche, BSC, Base, etc.
- **Support multi-bridges** : Utilisation de Jumper, Stargate et Relay

## Architecture du système

Le système est organisé en plusieurs modules :

1. **Gestion des wallets** (`wallet_management`) :
   - `wallet_manager.py` : Stockage sécurisé des clés privées
   - `balance_checker.py` : Vérification des soldes
   - `transaction_manager.py` : Gestion des transactions
   - `wallet_service.py` : Service intégré pour la gestion des wallets

2. **Logique de bridge** (`bridge_logic`) :
   - `jumper_bridge.py` : Intégration avec Jumper/LI.FI
   - `stargate_bridge.py` : Intégration avec Stargate
   - `relay_bridge.py` : Intégration avec Relay
   - `bridge_aggregator.py` : Sélection du meilleur service
   - `bridge_service.py` : Service intégré pour les bridges

3. **Interface Telegram** (`telegram_interface`) :
   - `telegram_bot.py` : Bot Telegram pour le contrôle
   - `notification_service.py` : Service de notification
   - `telegram_interface.py` : Intégration avec le reste du système

4. **Configuration et utilitaires** (`config`, `utils`) :
   - `config.py` : Configuration du système
   - Utilitaires divers

## Commandes Telegram

Le bot Telegram supporte les commandes suivantes :

- `/start` - Démarrer le bot
- `/help` - Afficher l'aide
- `/add_wallet <nom> <clé_privée>` - Ajouter un wallet
- `/list_wallets` - Lister les wallets
- `/remove_wallet <adresse>` - Supprimer un wallet
- `/check_balance <adresse>` - Vérifier les soldes d'un wallet
- `/schedule_transactions <adresse> [nombre]` - Planifier des transactions aléatoires
- `/execute_bridge <adresse>` - Exécuter un bridge aléatoire immédiatement
- `/transaction_history` - Afficher l'historique des transactions
- `/status` - Vérifier le statut du bot

## Configuration

La configuration du bot se fait via un fichier `.env` qui doit contenir les variables suivantes :

```
# Configuration Telegram
TELEGRAM_TOKEN=votre_token_telegram
ADMIN_CHAT_IDS=id1,id2,id3

# Sécurité
ENCRYPTION_KEY=votre_clé_de_chiffrement

# APIs des services de bridge
JUMPER_API_KEY=votre_clé_api_jumper
RELAY_API_KEY=votre_clé_api_relay

# Configuration des transactions
TRANSACTIONS_PER_DAY=2
MIN_TRANSACTION_INTERVAL_HOURS=1
MAX_TRANSACTION_INTERVAL_HOURS=12
```

## Déploiement

Le bot peut être déployé sur un droplet Digital Ocean de deux manières :

1. **Déploiement direct** : Utilisation du script `setup.sh`
2. **Déploiement Docker** : Utilisation du Dockerfile

Consultez le fichier `deployment/README.md` pour des instructions détaillées sur le déploiement.

## Sécurité

Le bot implémente plusieurs mesures de sécurité :

- Chiffrement des clés privées
- Authentification des utilisateurs Telegram
- Stockage sécurisé des variables d'environnement
- Validation des entrées utilisateur

## Dépannage

### Problèmes courants

1. **Le bot ne répond pas** :
   - Vérifiez que le service est en cours d'exécution
   - Vérifiez les logs pour des erreurs

2. **Erreurs de transaction** :
   - Vérifiez les soldes des wallets
   - Vérifiez la validité des clés API

3. **Problèmes de notification** :
   - Vérifiez que votre Chat ID est correctement configuré
   - Vérifiez que le bot a les permissions nécessaires

### Logs

Les logs du bot sont disponibles dans les fichiers suivants :
- `crypto_bridge_bot.log` - Logs de l'application
- `/var/log/crypto_bridge_bot.out.log` - Logs standard (déploiement)
- `/var/log/crypto_bridge_bot.err.log` - Logs d'erreur (déploiement)

## Développement

Pour contribuer au développement du bot :

1. Clonez le dépôt
2. Installez les dépendances : `pip install -r requirements.txt`
3. Créez un fichier `.env` avec la configuration nécessaire
4. Exécutez les tests : `python -m tests.test_bot`
5. Lancez le bot : `python src/main.py`

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
