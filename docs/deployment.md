# Guide de Déploiement

## Prérequis

- Docker 24+ et Docker Compose v2
- Serveur Linux (Ubuntu 22.04 LTS recommandé)
- Domaine DNS configuré
- Ports 80 et 443 ouverts

## Installation initiale

### 1. Cloner le dépôt

```bash
git clone https://github.com/your-org/chatbot.git /opt/chatbot
cd /opt/chatbot
```

### 2. Configurer les variables d'environnement

```bash
cp backend/.env.prod.example backend/.env.prod
cp frontend/.env.prod.example frontend/.env.prod

# Éditer avec vos vraies valeurs
nano backend/.env.prod
nano frontend/.env.prod
```

Créer le fichier `.env` racine pour docker-compose :

```bash
cat > .env << EOF
POSTGRES_USER=chatbot
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=chatbot_prod
RABBITMQ_USER=chatbot
RABBITMQ_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)
GRAFANA_PASSWORD=$(openssl rand -hex 16)
PUBLIC_API_URL=https://api.yourdomain.com
EOF
```

### 3. Obtenir les certificats SSL (Let's Encrypt)

```bash
# Démarrer nginx temporairement pour la validation ACME
docker compose -f docker-compose.prod.yml up -d nginx

# Obtenir les certificats
docker run --rm \
  -v ./infra/certbot/conf:/etc/letsencrypt \
  -v ./infra/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  --webroot-path /var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com \
  --email admin@yourdomain.com --agree-tos --non-interactive
```

### 4. Lancer tous les services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 5. Appliquer les migrations

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 6. Créer le super-admin

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python create_superadmin.py
```

## Mise à jour

```bash
cd /opt/chatbot
git pull

# Pull nouvelles images
docker compose -f docker-compose.prod.yml pull

# Appliquer les migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Redémarrer avec zero-downtime
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# Nettoyer les anciennes images
docker image prune -f
```

## Vérification

```bash
# Status des services
docker compose -f docker-compose.prod.yml ps

# Logs en temps réel
docker compose -f docker-compose.prod.yml logs -f backend

# Health check
curl https://api.yourdomain.com/health
```

## Renouvellement SSL automatique

Ajouter dans crontab (`crontab -e`) :

```cron
0 3 * * * docker run --rm -v /opt/chatbot/infra/certbot/conf:/etc/letsencrypt -v /opt/chatbot/infra/certbot/www:/var/www/certbot certbot/certbot renew --quiet && docker compose -f /opt/chatbot/docker-compose.prod.yml exec nginx nginx -s reload
```

## Backup manuel

```bash
# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec db /backup.sh

# Backup Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
```
