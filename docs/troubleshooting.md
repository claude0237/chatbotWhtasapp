# Guide de Troubleshooting

## Diagnostic rapide

```bash
# Status global
docker compose -f docker-compose.prod.yml ps

# Logs d'un service
docker compose -f docker-compose.prod.yml logs --tail=100 <service>

# Stats ressources
docker stats --no-stream
```

## Problèmes courants

### Backend ne démarre pas

```bash
docker compose -f docker-compose.prod.yml logs backend
```

**Causes fréquentes :**
- `DATABASE_URL` incorrect → vérifier la connexion DB
- `SECRET_KEY` manquant → vérifier `.env.prod`
- Migrations non appliquées → `docker compose exec backend alembic upgrade head`
- Port déjà utilisé → `ss -tlnp | grep 8000`

### Erreur 502 Bad Gateway

```bash
docker compose -f docker-compose.prod.yml logs nginx
docker compose -f docker-compose.prod.yml ps backend
```

- Backend non démarré → redémarrer : `docker compose up -d backend`
- Backend surchargé → augmenter les replicas ou workers

### Base de données

```bash
# Connexion directe
docker compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Connexions actives
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

# Queries longues
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '30 seconds';

# Tuer une query
SELECT pg_terminate_backend(<pid>);
```

### Redis

```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD

# Stats
INFO stats
INFO memory

# Flush cache (ATTENTION — perte de sessions)
FLUSHDB
```

### Celery worker bloqué

```bash
docker compose -f docker-compose.prod.yml logs celery_worker

# Redémarrer
docker compose -f docker-compose.prod.yml restart celery_worker

# Inspecter les tâches actives
docker compose -f docker-compose.prod.yml exec celery_worker \
  celery -A app.celery_app inspect active
```

### Migrations Alembic

```bash
# Vérifier la version courante
docker compose -f docker-compose.prod.yml exec backend alembic current

# Historique
docker compose -f docker-compose.prod.yml exec backend alembic history

# Rollback d'une migration
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

### Certificats SSL expirés

```bash
# Renouveler manuellement
docker run --rm \
  -v ./infra/certbot/conf:/etc/letsencrypt \
  -v ./infra/certbot/www:/var/www/certbot \
  certbot/certbot renew --force-renewal

docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Disk full

```bash
# Espace disque
df -h

# Nettoyer Docker
docker system prune -af --volumes

# Logs Docker (limiter la taille dans docker-compose)
# Ajouter aux services :
# logging:
#   driver: json-file
#   options:
#     max-size: "10m"
#     max-file: "5"
```

## Rollback d'urgence

```bash
# Via GitHub Actions : déclencher le job "rollback" manuellement
# Ou manuellement :

cd /opt/chatbot
PREV_TAG=$(cat .last_stable_tag)
docker compose -f docker-compose.prod.yml pull
IMAGE_TAG=$PREV_TAG docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

## Contacts d'urgence

- Incidents critiques : créer une issue GitHub avec label `incident`
- Slack : canal `#ops-alerts`
