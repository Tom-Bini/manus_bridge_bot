FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers du projet
COPY . /app/

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le fichier .env.example vers .env (à configurer)
RUN cp .env.example .env

# Configuration de Supervisor
COPY deployment/supervisor.conf /etc/supervisor/conf.d/crypto_bridge_bot.conf

# Exposer le port (si nécessaire)
# EXPOSE 8080

# Commande de démarrage
CMD ["supervisord", "-n"]
