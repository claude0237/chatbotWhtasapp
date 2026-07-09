# WhatsApp SaaS Platform

Plateforme **multi-tenant** clé-en-main permettant à des entreprises (restaurants, boutiques, services…) de connecter leur numéro **WhatsApp Business**, gérer leurs conversations en temps réel, automatiser les réponses via un **chatbot à scénarios**, et administrer leur équipe — le tout depuis une interface web unifiée.

Un super-administrateur gère l'ensemble des entreprises clientes depuis un panneau dédié.

---

## 🏗️ Stack Technique

| Couche | Technologie |
|--------|------------|
| Backend API | FastAPI 0.138, Python 3.12 |
| ORM / Migrations | SQLAlchemy 2.0 async, Alembic |
| Base de données | PostgreSQL 14+ avec pgvector |
| Cache / Files d'attente | Redis 8, Celery 5 |
| Authentification | JWT (python-jose), Argon2 (passlib) |
| Frontend | Next.js 14, React 18, Tailwind CSS |
| HTTP Client | httpx (async) |
| IA / ML | OpenAI, Anthropic, sentence-transformers, scikit-learn |
| Stockage fichiers | Local (static/) ou S3 compatible |

---

## 📁 Structure du Projet

```
chatboot/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── main.py             # Point d'entrée — monte tous les routers
│   │   ├── config.py           # Variables d'environnement (pydantic-settings)
│   │   ├── database/           # Session SQLAlchemy async
│   │   ├── auth/               # JWT, dépendances RBAC
│   │   ├── users/              # CRUD utilisateurs
│   │   ├── companies/          # CRUD entreprises (super admin)
│   │   ├── channels/           # Abstraction canaux + credentials WhatsApp
│   │   ├── whatsapp/           # Envoi/réception messages, webhook Meta
│   │   ├── conversations/      # Conversations et messages
│   │   ├── customers/          # Contacts/clients de chaque entreprise
│   │   ├── bot/                # Moteur chatbot (engine.py), scénarios, mots-clés
│   │   ├── knowledge/          # Base de connaissances (catégories + articles)
│   │   ├── ml/                 # Pipeline RAG + LLM (ingestion, embeddings, inférence)
│   │   ├── products/           # Catalogue produits + catégories
│   │   ├── reservations/       # Services, créneaux, réservations
│   │   ├── analytics/          # Statistiques conversations et bot
│   │   ├── notifications/      # Notifications internes
│   │   ├── jobs/               # Tâches planifiées (follow-up bot)
│   │   ├── upload/             # Upload de fichiers
│   │   ├── monitoring/         # Configuration des logs
│   │   └── utils/              # Utilitaires (chiffrement)
│   ├── alembic/                # Migrations de base de données
│   ├── requirements.txt        # Dépendances production
│   ├── requirements-dev.txt    # Dépendances développement
│   ├── pyproject.toml          # Métadonnées projet + outils (ruff, mypy, pytest)
│   ├── .env.example            # Template variables d'environnement
│   └── README.md               # Documentation backend détaillée
├── frontend/                   # Application Next.js
│   ├── src/
│   │   ├── app/                # Pages (App Router Next.js 14)
│   │   │   ├── auth/           # Login
│   │   │   ├── dashboard/      # Tableau de bord
│   │   │   ├── conversations/  # Conversations temps réel
│   │   │   ├── customers/      # Gestion contacts
│   │   │   ├── bot/            # Configuration chatbot + simulation
│   │   │   ├── catalogue/      # Produits et catégories
│   │   │   ├── knowledge/      # Base de connaissances
│   │   │   ├── whatsapp/       # Connexion WhatsApp + messages
│   │   │   ├── companies/      # Panneau super admin entreprises
│   │   │   ├── users/          # Gestion utilisateurs
│   │   │   ├── documents/      # Upload documents ML
│   │   │   ├── ml-config/      # Config fournisseur IA
│   │   │   └── ml-performance/ # Performance du modèle ML
│   │   ├── components/         # Composants réutilisables (AppLayout, etc.)
│   │   ├── hooks/              # Hooks React (useAuth, useHashTab)
│   │   └── lib/                # Client axios (api.ts)
│   ├── package.json
│   └── README.md               # Documentation frontend détaillée
├── docs/                       # Documentation technique complémentaire
├── exemple_conf_scenario.md    # Exemples de configuration de scénarios bot
├── .gitignore
└── README.md                   # Ce fichier
```

---

## 🚀 Installation et Démarrage

### Prérequis

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 14+** avec extension `pgvector`
- **Redis 7+**

### 1. Base de données

```sql
-- Se connecter à PostgreSQL
psql -U postgres

CREATE DATABASE whatsapp_saas;
\c whatsapp_saas
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### 2. Backend

```bash
cd backend

# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# → Éditer .env avec vos valeurs (voir section Configuration)

# Appliquer les migrations
alembic upgrade head

# Créer le super administrateur
python create_superadmin.py

# Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend

npm install

# Créer le fichier d'environnement
# Créer frontend/.env.local avec :
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

npm run dev
```

### Accès

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## ⚙️ Configuration — Variables d'Environnement

Toutes les variables sont dans `backend/.env` (copier depuis `.env.example`) :

```env
# Application
APP_NAME=WhatsApp SaaS Platform
APP_ENV=development
APP_DEBUG=true
APP_VERSION=0.1.0

# Serveur
HOST=0.0.0.0
PORT=8000

# Base de données PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/whatsapp_saas
DATABASE_SYNC_URL=postgresql://user:password@localhost:5432/whatsapp_saas

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# JWT — générer une clé forte pour la production
JWT_SECRET_KEY=votre-cle-secrete-longue
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Chiffrement des credentials WhatsApp par entreprise
# Générer avec : python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CREDENTIAL_ENCRYPTION_KEY=votre-cle-fernet

# CORS (URLs du frontend séparées par virgule)
CORS_ORIGINS=http://localhost:3000

# Celery (utilise Redis)
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3

# WhatsApp Meta API
WHATSAPP_API_VERSION=v25.0
WHATSAPP_WEBHOOK_VERIFY_TOKEN=votre-token-verification-webhook

# IA (optionnel — activer selon le fournisseur choisi)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Logs
LOG_LEVEL=INFO
```

> **Note WhatsApp par entreprise** : les `phone_number_id`, `access_token`, `waba_id` de chaque entreprise cliente sont stockés **chiffrés en base de données** via le module `channels`, pas dans `.env`.

---

## 🏛️ Architecture Technique

### Flux de données

```
Client WhatsApp (utilisateur final)
    │  message entrant
    ▼
Meta Cloud API
    │  POST /api/v1/whatsapp/webhook
    ▼
Backend FastAPI
    │  routing par phone_number_id → company_id
    ├── Sauvegarde message en BDD
    ├── Détection humain/bot en contrôle
    └── BotEngine.process()
            ├── Scénario en cours → _advance_scenario()
            ├── Trigger scénario → démarrage scénario
            ├── Mot-clé → réponse directe
            └── Fallback → unknown_message
    │  réponse générée
    ▼
Meta Cloud API
    │  envoi réponse au client WhatsApp
    ▼
Frontend Next.js (polling toutes les 5s)
    │  affichage conversation
    ▼
Agent humain (peut prendre la main)
```

### Pattern Architecture Backend

Chaque module suit le même pattern en 4 couches :

```
controllers/__init__.py   → Routes FastAPI, validation HTTP, réponses JSON
services/__init__.py      → Logique métier, orchestration
repositories/__init__.py  → Accès BDD SQLAlchemy (SELECT, INSERT, UPDATE, DELETE)
models/__init__.py        → Modèles SQLAlchemy (tables)
schemas/__init__.py       → Schémas Pydantic (validation entrées/sorties)
```

### Multi-tenancy

Chaque requête authentifiée passe par `get_current_company_id()` qui extrait le `company_id` du JWT. Toutes les requêtes BDD filtrent sur ce `company_id` — un utilisateur ne peut jamais accéder aux données d'une autre entreprise.

```
JWT → company_id → filtre automatique sur toutes les queries
```

---

## 🔐 Sécurité

- **JWT Bearer** : tokens d'accès (480 min) + refresh (7 jours)
- **Argon2** : hachage des mots de passe (résistant aux GPUs)
- **Fernet** : chiffrement symétrique des tokens WhatsApp en BDD
- **RBAC** : 4 rôles — `SUPER_ADMIN`, `COMPANY_ADMIN`, `AGENT`, `READ_ONLY`
- **Isolation multi-tenant** : `company_id` sur toutes les tables et toutes les queries
- **Blocage entreprise** : si `is_active=False` ou `is_suspended=True`, tous les utilisateurs de l'entreprise sont bloqués

---

## 🤖 Moteur Chatbot

Le chatbot est un moteur **natif sans LLM** (règles + scénarios) avec option ML.

### Types de steps dans un scénario

| Type | Comportement |
|------|-------------|
| `text` | Collecte une réponse libre, avance linéairement |
| `choice` | Attend un mot-clé parmi des choix, route vers une branche |
| `condition` | Évalue la réponse avec des opérateurs (equals, contains…) |
| `catalogue` | Affiche le catalogue produits, avance automatiquement |
| `handoff` | Transfère à un agent humain (change le statut conversation) |

### Variables d'interpolation

Dans les messages des steps :
```
{prenom}          → prénom du client (si collecté)
{step_1_answer}   → réponse collectée au step 1
{catalogue:NomCategorie}  → liste des produits d'une catégorie
```

Voir `exemple_conf_scenario.md` pour des exemples complets.

---

## 🔧 Commandes Utiles

### Backend
```bash
# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Tests
pytest
pytest --cov=app --cov-report=html

# Qualité code
ruff check app/
black app/
mypy app/
```

### Frontend
```bash
npm run dev          # Développement
npm run build        # Build production
npm run lint         # ESLint
```

---

## 📚 Documentation Détaillée

- [`backend/README.md`](backend/README.md) — tous les modules, endpoints et explications du code
- [`frontend/README.md`](frontend/README.md) — pages, hooks, composants
- [`exemple_conf_scenario.md`](exemple_conf_scenario.md) — exemples de scénarios bot complets
- [`docs/`](docs/) — documentation technique complémentaire

---

## 📄 Licence

Propriétaire — tous droits réservés.
