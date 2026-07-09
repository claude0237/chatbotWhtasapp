# Architecture Technique

## Vue d'ensemble

ChatBot SaaS est une plateforme multi-tenant permettant aux entreprises de déployer des chatbots WhatsApp avec IA.

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└──────────┬──────────────────────────────┬───────────────────────┘
           │                              │
    ┌──────▼──────┐               ┌───────▼───────┐
    │   Nginx      │               │  WhatsApp API  │
    │  (Reverse    │               │   (Webhook)    │
    │   Proxy)     │               └───────┬───────┘
    └──────┬──────┘                        │
           │                               │
    ┌──────▼──────────────────────────────▼──────┐
    │              FastAPI Backend                 │
    │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
    │  │  Auth    │ │  Bot     │ │  Webhook   │  │
    │  │  Module  │ │  Engine  │ │  Handler   │  │
    │  └──────────┘ └──────────┘ └────────────┘  │
    │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
    │  │Notifica- │ │Analytics │ │  Products  │  │
    │  │  tions   │ │  Module  │ │  Reservat. │  │
    │  └──────────┘ └──────────┘ └────────────┘  │
    └──────┬──────────────────┬───────────────────┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │ PostgreSQL   │    │   Redis      │
    │ (Primary DB) │    │  (Cache +    │
    └─────────────┘    │   Sessions)  │
                        └─────────────┘
    ┌─────────────────────────────────┐
    │     Celery Workers              │
    │  ML Inference | Notifications   │
    │  Analytics    | Email/SMS       │
    └────────────────┬────────────────┘
                     │
              ┌──────▼──────┐
              │  RabbitMQ    │
              │  (Queue)     │
              └─────────────┘
```

## Stack Technologique

### Backend
- **Framework** : FastAPI (Python 3.11)
- **ORM** : SQLAlchemy 2.0 async
- **Base de données** : PostgreSQL 15
- **Cache** : Redis 7
- **Queue** : Celery + RabbitMQ
- **Auth** : JWT (argon2 hashing)
- **Serveur** : Gunicorn + Uvicorn workers

### Frontend
- **Framework** : Next.js 14 (React 18)
- **Styles** : TailwindCSS
- **State** : React hooks
- **HTTP** : fetch API
- **Temps réel** : WebSocket natif

### Infrastructure
- **Containerisation** : Docker + Docker Compose
- **Reverse proxy** : Nginx
- **CI/CD** : GitHub Actions
- **Monitoring** : Prometheus + Grafana
- **Tracing** : OpenTelemetry

## Modules Backend

| Module | Responsabilité |
|--------|---------------|
| `auth` | Authentification JWT, 2FA, refresh tokens |
| `users` | Gestion utilisateurs et rôles |
| `companies` | Multi-tenancy, isolation des données |
| `conversations` | Gestion des conversations WhatsApp |
| `messages` | Stockage et traitement des messages |
| `bot` | Moteur de bot natif (keywords, scénarios) |
| `ml` | Moteur ML (RAG, LLM, embeddings) |
| `knowledge` | Base de connaissances vectorielle |
| `notifications` | Système de notifications temps réel |
| `analytics` | Métriques et rapports |
| `products` | Catalogue produits e-commerce |
| `reservations` | Système de réservations |
| `whatsapp` | Intégration API WhatsApp Business |

## Diagramme de Séquence — Réception Message WhatsApp

```
WhatsApp API → Nginx → FastAPI Webhook
    → Verify signature
    → Extract message data
    → Find/Create Customer
    → Find/Create Conversation
    → Save Message
    → BotEngine.process_message()
        → match_keyword?  → return response
        → execute_scenario? → return response
        → search_knowledge_base? → return response
        → handle_reservation_query? → return response
        → handle_product_query? → return response
        → ML Engine (if enabled)
            → embed message
            → vector search (RAG)
            → LLM call
            → return response
        → unknown_message fallback
    → Send response via WhatsApp API
    → Emit events (analytics, notifications)
    → Return HTTP 200 to WhatsApp
```

## Diagramme de Séquence — Authentification

```
Client → POST /api/v1/auth/login
    → Validate credentials
    → Verify password hash (argon2)
    → Check 2FA if enabled
    → Generate access_token (30min)
    → Generate refresh_token (7 days)
    → Store refresh_token hash in DB
    → Return tokens

Client → GET /api/v1/... (with Bearer token)
    → Decode JWT
    → Verify signature
    → Check expiry
    → Load user from DB
    → Check is_active, is_verified
    → Inject user in request context
```

## Multi-tenancy

Chaque requête est isolée par `company_id` :

- Chaque `User` appartient à une `Company`
- Chaque ressource (`Conversation`, `Product`, etc.) a un `company_id`
- Les contrôleurs vérifient `current_company_id == resource.company_id`
- Les repositories filtrent par `company_id`

## Schéma de Base de Données (Entités principales)

```
companies (id, name, email, subscription_plan, is_active)
    │
    ├── users (id, company_id, email, role, is_active)
    ├── conversations (id, company_id, customer_id, channel, status)
    │       └── messages (id, conversation_id, content, direction, type)
    ├── bot_configurations (id, company_id, bot_type, ml_enabled)
    │       ├── bot_keywords (id, config_id, keyword, response)
    │       └── bot_scenarios (id, config_id, trigger_keyword, steps)
    ├── knowledge_entries (id, company_id, title, content)
    ├── notifications (id, user_id, type, title, is_read)
    ├── notification_preferences (id, user_id, type, enabled, channel)
    ├── products (id, company_id, name, price, stock)
    │       └── product_categories (id, company_id, name, parent_id)
    ├── services (id, company_id, name, duration, price)
    │       ├── availability_slots (id, service_id, start_time, end_time)
    │       └── reservations (id, company_id, service_id, slot_id, status)
    └── analytics_metrics (id, company_id, metric_type, value, timestamp)
```
