# Runbooks Opérationnels

## RB-001 : Backend API Down

**Symptômes** : Alertes Prometheus `BackendDown`, erreurs 502 sur le site

**Diagnostic** :
```bash
docker compose -f docker-compose.prod.yml ps backend
docker compose -f docker-compose.prod.yml logs --tail=50 backend
```

**Actions** :
1. Si le conteneur est `Exited` → redémarrer :
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```
2. Si erreur DB → vérifier la connexion PostgreSQL :
   ```bash
   docker compose -f docker-compose.prod.yml exec db pg_isready
   ```
3. Si OOM (Out of Memory) → augmenter la limite mémoire dans `docker-compose.prod.yml` ou réduire les workers
4. Si erreur de migration → appliquer les migrations manquantes :
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

**Escalade** : Si non résolu en 15min → rollback image précédente (RB-005)

---

## RB-002 : Base de Données Lente

**Symptômes** : Alerte `HighResponseTime`, timeouts dans les logs

**Diagnostic** :
```sql
-- Connexions actives
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Locks bloquants
SELECT pid, now() - query_start, query, wait_event
FROM pg_stat_activity
WHERE wait_event IS NOT NULL;

-- Requêtes lentes
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;
```

**Actions** :
1. Tuer les requêtes bloquées :
   ```sql
   SELECT pg_terminate_backend(<pid>);
   ```
2. Lancer VACUUM si tables gonflées :
   ```sql
   VACUUM ANALYZE conversations;
   VACUUM ANALYZE messages;
   ```
3. Si connexions saturées → redémarrer PgBouncer ou augmenter `max_connections`

---

## RB-003 : Redis Memory Full

**Symptômes** : Alerte `RedisHighMemory`, erreurs `OOM command not allowed`

**Diagnostic** :
```bash
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD INFO memory
```

**Actions** :
1. Identifier les clés volumineuses :
   ```bash
   redis-cli -a $REDIS_PASSWORD --bigkeys
   ```
2. Purger le cache ML si nécessaire (non critique) :
   ```bash
   redis-cli -a $REDIS_PASSWORD --scan --pattern "ml:*" | xargs redis-cli DEL
   ```
3. Augmenter `maxmemory` dans `redis.prod.conf` et redémarrer
4. **Ne jamais** faire `FLUSHALL` en production sans accord explicite

---

## RB-004 : File d'Attente Celery Saturée

**Symptômes** : RabbitMQ queue > 5000 messages, notifications en retard

**Diagnostic** :
```bash
# Via RabbitMQ management
curl http://localhost:15672/api/queues -u $RABBITMQ_USER:$RABBITMQ_PASSWORD

# Via Celery
docker compose exec celery_worker celery -A app.celery_app inspect active
```

**Actions** :
1. Augmenter les workers :
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale celery_worker=4
   ```
2. Si une tâche ML bloque → tuer le worker et redémarrer :
   ```bash
   docker compose -f docker-compose.prod.yml restart celery_worker
   ```
3. Purger les tâches expirées si nécessaire :
   ```bash
   docker compose exec celery_worker celery -A app.celery_app purge
   ```

---

## RB-005 : Rollback d'Urgence

**Symptômes** : Déploiement cassé, erreurs 500 massives post-déploiement

**Actions** :
```bash
cd /opt/chatbot

# Récupérer le tag stable précédent
PREV=$(cat .last_stable_tag 2>/dev/null || echo "main")
echo "Rolling back to: $PREV"

# Rollback images
docker compose -f docker-compose.prod.yml pull \
  ghcr.io/your-org/chatbot/backend:$PREV \
  ghcr.io/your-org/chatbot/frontend:$PREV

IMAGE_TAG=$PREV docker compose -f docker-compose.prod.yml \
  up -d --no-deps backend frontend

sleep 15
curl -f https://api.yourdomain.com/health && echo "Rollback OK"
```

Si migration Alembic nécessite rollback :
```bash
docker compose exec backend alembic downgrade -1
```

---

## RB-006 : Certificat SSL Expiré

**Symptômes** : Alerte `CertificateExpiringSoon`, erreurs SSL browser

**Actions** :
```bash
# Renouveler manuellement
docker run --rm \
  -v /opt/chatbot/infra/certbot/conf:/etc/letsencrypt \
  -v /opt/chatbot/infra/certbot/www:/var/www/certbot \
  certbot/certbot renew --force-renewal

# Recharger nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Vérifier la date d'expiration
echo | openssl s_client -connect api.yourdomain.com:443 2>/dev/null \
  | openssl x509 -noout -dates
```

---

## RB-007 : Webhook WhatsApp ne reçoit plus de messages

**Symptômes** : Plus de messages entrants depuis WhatsApp, `webhook_errors` en hausse

**Diagnostic** :
```bash
# Vérifier les logs webhook
docker compose logs --tail=100 backend | grep webhook

# Vérifier la signature
curl -X GET "https://api.yourdomain.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=$TOKEN&hub.challenge=test"
```

**Actions** :
1. Vérifier que `WHATSAPP_VERIFY_TOKEN` correspond à la configuration Meta
2. Vérifier que l'URL du webhook est accessible depuis l'extérieur : `curl -I https://api.yourdomain.com/webhook/whatsapp`
3. Reconfigurer le webhook dans [Meta Business Manager](https://business.facebook.com) si nécessaire
4. Vérifier la validité du `WHATSAPP_API_TOKEN`
