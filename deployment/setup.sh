"""
Script de configuration pour le déploiement sur Digital Ocean.
Ce script permet de configurer un droplet Digital Ocean pour le bot crypto.
"""
#!/bin/bash

# Mise à jour du système
apt-get update
apt-get upgrade -y

# Installation des dépendances système
apt-get install -y python3-pip python3-venv git supervisor

# Création du répertoire pour l'application
mkdir -p /opt/crypto_bridge_bot

# Clonage du dépôt (à remplacer par votre dépôt Git)
# git clone https://github.com/votre-utilisateur/crypto_bridge_bot.git /opt/crypto_bridge_bot

# Copie des fichiers (alternative au clonage Git)
cp -r /home/ubuntu/crypto_bridge_bot/* /opt/crypto_bridge_bot/

# Création de l'environnement virtuel
cd /opt/crypto_bridge_bot
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
pip install -r requirements.txt

# Création du fichier .env (à configurer manuellement)
cp .env.example .env

# Configuration de Supervisor
cat > /etc/supervisor/conf.d/crypto_bridge_bot.conf << EOF
[program:crypto_bridge_bot]
command=/opt/crypto_bridge_bot/venv/bin/python /opt/crypto_bridge_bot/src/main.py
directory=/opt/crypto_bridge_bot
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/crypto_bridge_bot.err.log
stdout_logfile=/var/log/crypto_bridge_bot.out.log
EOF

# Rechargement de la configuration de Supervisor
supervisorctl reread
supervisorctl update

echo "Configuration terminée. Veuillez éditer le fichier /opt/crypto_bridge_bot/.env pour configurer les variables d'environnement."
