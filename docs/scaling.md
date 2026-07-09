# Guide de Scaling

## Scaling Horizontal du Backend

### Augmenter les réplicas

```bash
# Via docker-compose
docker compose -f docker-compose.prod.yml up -d --scale backend=4

# Vérifier
docker compose -f docker-compose.prod.yml ps backend
```

### Nginx load balancing (déjà configuré)

Le bloc `upstream backend_api` dans `nginx.prod.conf` utilise `least_conn` — il distribue automatiquement vers les réplicas disponibles.

### Variables à ajuster selon la charge

Dans `backend/.env.prod` :

```ini
# Gunicorn workers = (2 × CPU) + 1
# Pour 4 vCPU → 9 workers
GUNICORN_WORKERS=9

# SQLAlchemy connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

## Scaling de la Base de Données

### Connection pooling avec PgBouncer

Ajouter PgBouncer entre le backend et PostgreSQL pour les connexions de courte durée :

```yaml
# À ajouter dans docker-compose.prod.yml
pgbouncer:
  image: pgbouncer/pgbouncer:1.21.0
  environment:
    DATABASES_HOST: db
    DATABASES_PORT: 5432
    DATABASES_DBNAME: ${POSTGRES_DB}
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
    PGBOUNCER_DEFAULT_POOL_SIZE: 50
  networks:
    - internal
```

Modifier `DATABASE_URL` dans le backend pour pointer vers `pgbouncer:5432`.

### Read Replicas

Pour les requêtes analytics lourdes, configurer une réplique PostgreSQL :

```yaml
db-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  command: |
    postgres -c primary_conninfo='host=db user=replicator password=...'
             -c hot_standby=on
```

Diriger les requêtes read-only vers le replica dans les repositories analytiques.

## Scaling de Celery

```bash
# Plus de workers
docker compose -f docker-compose.prod.yml up -d --scale celery_worker=4

# Queues dédiées par priorité
celery worker -Q ml --concurrency=2       # ML intensive
celery worker -Q notifications --concurrency=8  # I/O bound
celery worker -Q default --concurrency=4
```

## Scaling Redis

### Redis Sentinel (haute disponibilité)

```yaml
redis-master:
  image: redis:7-alpine
redis-sentinel:
  image: redis:7-alpine
  command: redis-sentinel /etc/redis/sentinel.conf
```

### Redis Cluster (sharding)

Pour > 10 GB de données cache, migrer vers Redis Cluster avec 6 nœuds (3 masters + 3 replicas).

## Optimisation des Index PostgreSQL

Requêtes pour identifier les index manquants :

```sql
-- Tables sans index sur FK
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE n_distinct < 0 AND tablename IN ('messages', 'notifications', 'analytics_metrics');

-- Requêtes lentes (activer pg_stat_statements)
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

Index recommandés à ajouter si manquants :

```sql
CREATE INDEX CONCURRENTLY idx_messages_conversation_created
  ON messages(conversation_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_notifications_user_unread
  ON notifications(user_id, is_read) WHERE is_read = false;

CREATE INDEX CONCURRENTLY idx_analytics_company_type_ts
  ON analytics_metrics(company_id, metric_type, timestamp DESC);
```

## Seuils d'alerte pour scaling

| Métrique | Action recommandée |
|----------|-------------------|
| CPU backend > 70% pendant 10min | Ajouter 1 réplica |
| DB connexions > 150 | Activer PgBouncer |
| Redis mémoire > 80% | Augmenter `maxmemory` ou scale |
| Celery queue > 1000 tâches | Ajouter worker |
| p95 latency > 1s | Profiler et optimiser |
