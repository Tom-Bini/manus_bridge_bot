# Guide de déploiement sur Digital Ocean

Ce document explique comment déployer le bot Crypto Bridge sur un droplet Digital Ocean.

## Méthode 1 : Déploiement direct

### Prérequis
- Un compte Digital Ocean
- Un droplet Ubuntu 22.04 (minimum 1 GB RAM recommandé)
- Un domaine pointant vers l'IP du droplet (optionnel)

### Étapes de déploiement

1. **Créer un droplet Digital Ocean**
   - Connectez-vous à votre compte Digital Ocean
   - Cliquez sur "Create" puis "Droplets"
   - Sélectionnez Ubuntu 22.04 x64
   - Choisissez un plan (Basic avec 1 GB RAM minimum recommandé)
   - Sélectionnez une région proche de vous
   - Ajoutez votre clé SSH ou créez un mot de passe
   - Cliquez sur "Create Droplet"

2. **Se connecter au droplet**
   ```bash
   ssh root@VOTRE_IP_DROPLET
   ```

3. **Cloner le dépôt Git**
   ```bash
   git clone https://github.com/votre-utilisateur/crypto_bridge_bot.git
   cd crypto_bridge_bot
   ```

4. **Exécuter le script de configuration**
   ```bash
   chmod +x deployment/setup.sh
   ./deployment/setup.sh
   ```

5. **Configurer les variables d'environnement**
   ```bash
   nano /opt/crypto_bridge_bot/.env
   ```
   
   Modifiez les variables suivantes :
   ```
   TELEGRAM_TOKEN=votre_token_telegram
   ADMIN_CHAT_IDS=id1,id2,id3
   ENCRYPTION_KEY=votre_clé_de_chiffrement
   JUMPER_API_KEY=votre_clé_api_jumper
   RELAY_API_KEY=votre_clé_api_relay
   ```

6. **Redémarrer le service**
   ```bash
   supervisorctl restart crypto_bridge_bot
   ```

7. **Vérifier le statut du service**
   ```bash
   supervisorctl status crypto_bridge_bot
   ```

## Méthode 2 : Déploiement avec Docker

### Prérequis
- Un compte Digital Ocean
- Un droplet Ubuntu 22.04 avec Docker installé
- Un domaine pointant vers l'IP du droplet (optionnel)

### Étapes de déploiement

1. **Créer un droplet Digital Ocean avec Docker**
   - Connectez-vous à votre compte Digital Ocean
   - Cliquez sur "Create" puis "Droplets"
   - Dans l'onglet "Marketplace", sélectionnez "Docker"
   - Choisissez un plan (Basic avec 1 GB RAM minimum recommandé)
   - Sélectionnez une région proche de vous
   - Ajoutez votre clé SSH ou créez un mot de passe
   - Cliquez sur "Create Droplet"

2. **Se connecter au droplet**
   ```bash
   ssh root@VOTRE_IP_DROPLET
   ```

3. **Cloner le dépôt Git**
   ```bash
   git clone https://github.com/votre-utilisateur/crypto_bridge_bot.git
   cd crypto_bridge_bot
   ```

4. **Créer un fichier .env**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Modifiez les variables comme indiqué dans la méthode 1.

5. **Construire l'image Docker**
   ```bash
   docker build -t crypto_bridge_bot -f deployment/Dockerfile .
   ```

6. **Lancer le conteneur**
   ```bash
   docker run -d --name crypto_bridge_bot --restart always -v $(pwd)/.env:/app/.env crypto_bridge_bot
   ```

7. **Vérifier le statut du conteneur**
   ```bash
   docker ps
   docker logs crypto_bridge_bot
   ```

## Configuration du bot Telegram

1. **Créer un bot Telegram**
   - Ouvrez Telegram et cherchez @BotFather
   - Envoyez la commande `/newbot`
   - Suivez les instructions pour créer un nouveau bot
   - Notez le token API qui vous est fourni

2. **Obtenir votre Chat ID**
   - Ouvrez Telegram et cherchez @userinfobot
   - Envoyez n'importe quel message à ce bot
   - Il vous répondra avec votre Chat ID
   - Ajoutez ce Chat ID à la variable ADMIN_CHAT_IDS dans le fichier .env

## Maintenance et surveillance

### Logs
Les logs du bot sont disponibles dans les fichiers suivants :
- `/var/log/crypto_bridge_bot.out.log` - Logs standard
- `/var/log/crypto_bridge_bot.err.log` - Logs d'erreur

Pour consulter les logs en temps réel :
```bash
tail -f /var/log/crypto_bridge_bot.out.log
```

### Redémarrage du service
Si vous devez redémarrer le service :

**Méthode 1 (Supervisor)**
```bash
supervisorctl restart crypto_bridge_bot
```

**Méthode 2 (Docker)**
```bash
docker restart crypto_bridge_bot
```

### Mise à jour du bot
Pour mettre à jour le bot avec une nouvelle version :

**Méthode 1 (Supervisor)**
```bash
cd /opt/crypto_bridge_bot
git pull
supervisorctl restart crypto_bridge_bot
```

**Méthode 2 (Docker)**
```bash
cd /chemin/vers/crypto_bridge_bot
git pull
docker build -t crypto_bridge_bot -f deployment/Dockerfile .
docker stop crypto_bridge_bot
docker rm crypto_bridge_bot
docker run -d --name crypto_bridge_bot --restart always -v $(pwd)/.env:/app/.env crypto_bridge_bot
```

## Sécurité

- Assurez-vous que votre fichier `.env` est sécurisé et n'est pas accessible publiquement
- Utilisez un pare-feu pour limiter l'accès à votre droplet
- Configurez SSH pour utiliser des clés plutôt que des mots de passe
- Mettez régulièrement à jour votre système avec `apt-get update && apt-get upgrade`

## Dépannage

### Le bot ne démarre pas
Vérifiez les logs d'erreur :
```bash
cat /var/log/crypto_bridge_bot.err.log
```

### Problèmes de connexion à Telegram
Vérifiez que votre token Telegram est correct et que votre droplet a accès à Internet.

### Problèmes de transactions
Vérifiez que les clés API pour les services de bridge sont correctes et que les wallets ont suffisamment de fonds.
