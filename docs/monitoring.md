# Guide de Monitoring

## Accès aux interfaces

| Service     | URL                                    | Credentials              |
|-------------|----------------------------------------|--------------------------|
| Grafana     | https://yourdomain.com/grafana         | `$GRAFANA_USER` / `$GRAFANA_PASSWORD` |
| Prometheus  | Interne seulement (port 9090)          | N/A                      |
| RabbitMQ    | Interne seulement (port 15672)         | `$RABBITMQ_USER`         |

## Dashboards Grafana

Importer ces dashboards depuis grafana.com :

- **Node Exporter Full** — ID `1860` — métriques système
- **PostgreSQL Database** — ID `9628` — métriques base de données
- **Redis Dashboard** — ID `11835` — métriques Redis
- **FastAPI Observability** — ID `16110` — métriques API

## Alertes configurées

| Alerte                | Seuil         | Sévérité |
|-----------------------|---------------|----------|
| BackendDown           | > 1 min       | critical |
| HighErrorRate         | > 5% sur 5min | warning  |
| HighResponseTime p95  | > 2s          | warning  |
| PostgresDown          | > 1 min       | critical |
| PostgresHighConnections | > 80%       | warning  |
| RedisDown             | > 1 min       | critical |
| RedisHighMemory       | > 85%         | warning  |
| HighCPU               | > 85% 10min   | warning  |
| HighMemory            | > 90%         | warning  |
| DiskSpaceLow          | < 10%         | warning  |

## Logs structurés

Les logs backend sont en format JSON. Exemple :

```json
{
  "timestamp": "2026-07-01T14:00:00Z",
  "level": "INFO",
  "logger": "app.bot.services",
  "message": "Processing message",
  "company_id": "...",
  "module": "services"
}
```

Agrégation avec Loki (optionnel) :

```bash
# Ajouter à docker-compose.prod.yml
loki:
  image: grafana/loki:2.9.0
  volumes:
    - loki_data:/loki
```

## OpenTelemetry Tracing

Traces disponibles si `OTEL_EXPORTER_OTLP_ENDPOINT` est défini.

Jaeger (visualisation des traces) :

```bash
docker run -d --name jaeger \
  -p 16686:16686 -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

Configurer dans `.env.prod` :

```
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=chatbot-backend
```
