# Backend — WhatsApp SaaS Platform

API REST construite avec **FastAPI** (Python 3.12), **SQLAlchemy 2.0 async**, **PostgreSQL + pgvector**.

---

## Démarrage Rapide

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # puis éditer .env
alembic upgrade head
python create_superadmin.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Swagger UI** : http://localhost:8000/docs  
- **ReDoc** : http://localhost:8000/redoc

---

## Structure des Modules

```
app/
├── main.py            # Point d'entrée FastAPI, montage des routers
├── config.py          # Settings (pydantic-settings, lit .env)
├── database/          # Session async SQLAlchemy
├── auth/              # Authentification JWT + RBAC
├── users/             # Utilisateurs
├── companies/         # Entreprises (super admin)
├── channels/          # Abstraction canaux + credentials WhatsApp
├── whatsapp/          # Webhook Meta + envoi messages
├── conversations/     # Conversations et messages
├── customers/         # Contacts clients
├── bot/               # Moteur chatbot (engine.py)
├── knowledge/         # Base de connaissances
├── ml/                # Pipeline RAG + LLM
├── products/          # Catalogue produits
├── reservations/      # Réservations
├── analytics/         # Statistiques
├── notifications/     # Notifications
├── jobs/              # Tâches planifiées
├── upload/            # Upload fichiers
├── monitoring/        # Configuration logs
└── utils/             # Utilitaires (chiffrement Fernet)
```

---

## Pattern Commun à Tous les Modules

Chaque module respecte une architecture en couches stricte :

```
models/__init__.py        → Table SQLAlchemy (ORM)
schemas/__init__.py       → Schémas Pydantic (validation)
repositories/__init__.py  → Accès base de données
services/__init__.py      → Logique métier
controllers/__init__.py   → Routes HTTP FastAPI
routes/__init__.py        → Export du router
```

---

## Module : `auth`

**Rôle** : Authentification JWT et contrôle d'accès basé sur les rôles (RBAC).

### Fichiers clés

**`auth/services/__init__.py`**  
- `hash_password(password)` → hache avec Argon2  
- `verify_password(plain, hashed)` → vérifie le hash  
- `create_access_token(user_id)` → génère un JWT signé  
- `verify_token(token)` → décode et valide le JWT, retourne l'utilisateur  

**`auth/dependencies/__init__.py`**  
Dépendances FastAPI injectées dans les routes :

| Dépendance | Rôle |
|-----------|------|
| `get_current_user` | Lit le Bearer token, retourne l'utilisateur |
| `get_current_active_user` | Vérifie `is_active` + statut entreprise |
| `get_current_company_id` | Extrait le `company_id` du JWT |
| `require_company_admin` | Bloque si rôle < `COMPANY_ADMIN` |
| `require_super_admin` | Bloque si rôle ≠ `SUPER_ADMIN` |

### Rôles RBAC

```
SUPER_ADMIN    → Accès total, gestion de toutes les entreprises
COMPANY_ADMIN  → Gestion de son entreprise, ses utilisateurs
AGENT          → Gestion conversations, réponse aux messages
READ_ONLY      → Lecture seule
```

### Endpoints `POST /auth/`

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/auth/login` | Connexion → retourne `access_token` + `refresh_token` |
| POST | `/auth/refresh` | Renouvelle le token d'accès |
| GET | `/auth/me` | Retourne l'utilisateur authentifié |

---

## Module : `companies`

**Rôle** : Gestion des entreprises clientes (SUPER_ADMIN uniquement).

### Modèle `Company`

```python
id, name, slug (unique), description, logo_url, website
email, phone, address
is_active     # False → tous les users bloqués
is_suspended  # True  → tous les users bloqués
deleted_at    # non utilisé (suppression hard delete)
```

### `CompanySettings` (1:1 avec Company)

```python
timezone, language, currency, theme_color
custom_domain, settings (JSON)
```

### Endpoints `GET|POST /companies/`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/companies/` | SUPER_ADMIN | Liste toutes les entreprises |
| POST | `/companies/` | SUPER_ADMIN | Crée une entreprise + settings |
| GET | `/companies/{id}` | SUPER_ADMIN | Détail entreprise |
| PUT | `/companies/{id}` | SUPER_ADMIN | Mise à jour |
| DELETE | `/companies/{id}` | SUPER_ADMIN | Suppression hard (cascade) |
| POST | `/companies/{id}/activate` | SUPER_ADMIN | Active l'entreprise |
| POST | `/companies/{id}/deactivate` | SUPER_ADMIN | Désactive (bloque tous les users) |
| POST | `/companies/{id}/suspend` | SUPER_ADMIN | Suspend |

> La suppression est un **hard delete** avec cascade PostgreSQL sur toutes les tables liées (users, conversations, messages, produits, etc.).

---

## Module : `users`

**Rôle** : Gestion des utilisateurs d'une entreprise.

### Modèle `User`

```python
id, company_id (FK cascade), email (unique), password_hash
first_name, last_name, phone, avatar_url
role (UserRoleEnum), is_active, is_verified
two_factor_enabled, last_login_at
```

### Endpoints `/users/`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/users/` | COMPANY_ADMIN | Liste les users de l'entreprise |
| POST | `/users/` | COMPANY_ADMIN | Crée un utilisateur |
| GET | `/users/{id}` | Auth | Détail utilisateur |
| PUT | `/users/{id}` | COMPANY_ADMIN | Mise à jour (incl. mot de passe optionnel) |
| DELETE | `/users/{id}` | COMPANY_ADMIN | Soft delete |

> Le `PUT` accepte un champ `password` optionnel : s'il est fourni, il est haché via `AuthService.hash_password()` avant sauvegarde.

---

## Module : `channels`

**Rôle** : Abstraction des canaux de communication. Chaque entreprise a un `Channel` de type `WHATSAPP` avec ses credentials chiffrés.

### Modèles

**`Channel`** : représente un canal (type, status, company_id)  
**`ChannelConfiguration`** : paires clé/valeur (`phone_number_id`, `waba_id`, `display_phone_number`)  
**`ChannelCredential`** : valeurs sensibles **chiffrées Fernet** (`ACCESS_TOKEN`)

### Endpoints `/channels/`

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/channels/whatsapp/credentials` | Sauvegarde Phone Number ID + Access Token + WABA ID |
| GET | `/channels/whatsapp/credentials` | Retourne les credentials (token masqué) |

### Chiffrement des credentials

```python
# utils/encryption.py
encrypt_credential(value, key)   # Fernet.encrypt()
decrypt_credential(value, key)   # Fernet.decrypt()
```

La clé Fernet est dans `CREDENTIAL_ENCRYPTION_KEY` du `.env`.

---

## Module : `whatsapp`

**Rôle** : Interface avec l'API Meta Cloud — webhook entrant, envoi de messages.

### Webhook entrant (sans auth)

```
GET  /whatsapp/webhook  → vérification Meta (hub.challenge)
POST /whatsapp/webhook  → réception messages/statuts
```

**Flux du webhook POST :**
1. Extrait `phone_number_id` depuis `entry[0].changes[0].value.metadata`
2. Recherche le `Channel` correspondant en BDD → trouve le `company_id`
3. Si company désactivée/suspendue → ignore l'événement
4. Crée/retrouve le `Customer` (contact WhatsApp)
5. Crée/retrouve la `Conversation`
6. Sauvegarde le `Message`
7. Si bot actif et pas d'agent humain → appelle `BotEngine.process()`
8. Envoie la réponse du bot via l'API Meta

### Envoi de messages (authentifié)

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/whatsapp/messages/send` | Envoie un message texte |
| POST | `/whatsapp/templates/send` | Envoie un template approuvé |
| GET | `/whatsapp/messages` | Liste les messages de l'entreprise |
| GET | `/whatsapp/templates` | Liste les templates |
| GET | `/whatsapp/templates/active` | Templates approuvés uniquement |
| POST | `/whatsapp/templates` | Crée un template |
| GET | `/whatsapp/webhook/info` | Infos webhook (super admin) |

---

## Module : `bot`

**Rôle** : Moteur chatbot natif (sans LLM obligatoire).

### `engine.py` — `BotEngine`

Classe centrale. Méthode principale : `process(company_id, phone_number, message_text)`.

**Ordre de priorité :**
1. Contact en cours de scénario → `_advance_scenario()`
2. Message = trigger d'un scénario → démarrage scénario
3. Message = mot-clé → réponse directe
4. Fallback → `unknown_message` de la config

### Types de Steps

| Type | Comportement |
|------|-------------|
| `text` | Collecte libre, avance linéairement |
| `choice` | Attend un mot parmi `choices{}`, route vers branche ou DEFAULT |
| `condition` | Évalue avec `equals`/`contains`/`starts_with`/`default` |
| `catalogue` | Affiche les produits, avance **immédiatement** (pas d'attente) |
| `handoff` | Retourne `__HANDOFF__:<message>`, webhook change statut conversation |

### Interpolation dans les messages

```
{step_1_answer}          → réponse collectée au step 1
{catalogue:Matelas}      → liste des produits de la catégorie "Matelas"
{catalogue}              → tous les produits
```

### `BotConversationState`

Table BDD qui stocke l'état en cours pour chaque contact :
```python
company_id, phone_number, scenario_id
current_step   # index du step courant
collected_data # dict JSON {step_1_answer: "...", ...}
retry_count    # nb de fois que le bot a relancé sans réponse
last_bot_message
```

### Endpoints `/bot/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST/PUT | `/bot/config` | Configuration bot (welcome, away, closing, unknown messages) |
| GET/POST | `/bot/scenarios` | Scénarios |
| PUT/DELETE | `/bot/scenarios/{id}` | Modifier/supprimer scénario |
| GET/POST | `/bot/keywords` | Mots-clés |
| PUT/DELETE | `/bot/keywords/{id}` | Modifier/supprimer mot-clé |

### `jobs/followup.py`

Tâche planifiée (toutes les minutes) : si un contact n'a pas répondu depuis N minutes, le bot renvoie `last_bot_message` (jusqu'à `max_retries` fois).

---

## Module : `conversations`

**Rôle** : Gestion des conversations et messages entre agents et clients.

### Modèles

**`Conversation`**
```python
company_id, customer_id, channel_id
status    # OPEN, CLOSED, WAITING, BOT
priority  # LOW, NORMAL, HIGH, URGENT
assigned_to (FK User)
```

**`Message`**
```python
conversation_id, sender_type (BOT/CUSTOMER/AGENT)
content, message_type (TEXT/IMAGE/DOCUMENT/...)
status (SENT/DELIVERED/READ/FAILED)
whatsapp_message_id
```

### Endpoints `/conversations/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/conversations/` | Liste conversations (filtrable par status) |
| GET | `/conversations/{id}` | Détail + messages |
| PUT | `/conversations/{id}` | Mise à jour (status, assigned_to) |
| POST | `/conversations/{id}/messages` | Envoie un message agent |
| POST | `/conversations/{id}/assign` | Assigne à un agent |
| POST | `/conversations/{id}/close` | Ferme la conversation |
| GET | `/conversations/{id}/bot-state` | État bot actif pour ce contact |

---

## Module : `customers`

**Rôle** : Contacts WhatsApp de chaque entreprise.

### Modèle `Customer`

```python
company_id, phone_number (unique par company), display_name
email, notes, tags (JSON), is_blocked
whatsapp_profile_name
```

### Endpoints `/customers/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/customers/` | Liste (recherche par nom/téléphone) |
| POST | `/customers/` | Crée un contact |
| GET | `/customers/{id}` | Détail |
| PUT | `/customers/{id}` | Mise à jour |
| DELETE | `/customers/{id}` | Suppression |

---

## Module : `products`

**Rôle** : Catalogue produits utilisé par le bot (step `catalogue`).

### Modèles

**`ProductCategory`** : `name`, `description`, `company_id`  
**`Product`** : `name`, `description`, `price`, `currency`, `stock`, `is_active`, `category_id`, `company_id`

### Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST | `/products/categories/` | Catégories |
| PUT/DELETE | `/products/categories/{id}` | Modifier/supprimer |
| GET/POST | `/products/` | Produits (filtrable par catégorie) |
| PUT/DELETE | `/products/{id}` | Modifier/supprimer |
| GET | `/companies/{company_id}/products` | Produits publics (utilisé par bot) |

---

## Module : `knowledge`

**Rôle** : Base de connaissances en articles (catégories + articles). Utilisée par le moteur ML/RAG.

### Modèles

**`KnowledgeCategory`** : `name`, `description`, `company_id`  
**`KnowledgeBase`** : `title`, `content`, `category_id`, `company_id`, `embedding` (pgvector)

### Endpoints `/knowledge/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST | `/knowledge/categories/` | Catégories |
| GET/POST | `/knowledge/` | Articles |
| PUT/DELETE | `/knowledge/{id}` | Modifier/supprimer |
| POST | `/knowledge/search` | Recherche sémantique par embedding |

---

## Module : `ml`

**Rôle** : Pipeline RAG (Retrieval Augmented Generation) — ingestion de documents, génération d'embeddings, inférence LLM.

### Sous-modules

**`ml/engine/__init__.py` — `MLEngine`**  
Orchestrateur principal. Méthode `process_with_fallback()` :
1. Tente la réponse ML (RAG + LLM)
2. Si confiance < seuil → fallback vers réponse native

**`ml/rag/__init__.py` — `RAGEngine`**  
- `generate_with_retrieval()` → cherche les documents similaires par embedding pgvector, injecte dans le prompt LLM
- `generate_with_history()` → idem avec historique conversation

**`ml/llm/__init__.py`**  
Factory de providers LLM : `get_llm_provider("openai"|"anthropic"|"ollama")`

### Endpoints `/ml/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST/PUT | `/ml/config` | Config fournisseur IA (provider, model, temperature) |
| POST | `/ml/ingest` | Lance l'ingestion d'un document |
| GET | `/ml/documents` | Liste documents ingérés |
| DELETE | `/ml/documents/{id}` | Supprime document + embeddings |
| POST | `/ml/chat` | Test direct du pipeline ML |
| GET | `/ml/performance` | Métriques de performance |

---

## Module : `reservations`

**Rôle** : Système de réservation (services, créneaux, réservations).

### Modèles

**`Service`** : `name`, `duration_minutes`, `price`, `company_id`  
**`TimeSlot`** : `service_id`, `start_time`, `end_time`, `capacity`, `booked_count`  
**`Reservation`** : `customer_id`, `service_id`, `slot_id`, `status`, `company_id`

### Endpoints `/reservations/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST | `/reservations/services/` | Services |
| GET/POST | `/reservations/slots/` | Créneaux |
| GET/POST | `/reservations/` | Réservations |
| PUT | `/reservations/{id}` | Modifier réservation |

---

## Module : `analytics`

**Rôle** : Statistiques pour le dashboard.

### Endpoints `/analytics/`

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/analytics/conversations` | Stats conversations (volume, statuts, temps réponse) |
| GET | `/analytics/messages` | Volume messages par période |
| GET | `/analytics/customers` | Nouveaux contacts, rétention |
| GET | `/analytics/bot` | Taux de résolution bot, scénarios les plus utilisés |

---

## Module : `upload`

**Rôle** : Upload de fichiers (images, documents pour ML).

### Endpoint

```
POST /upload/
Content-Type: multipart/form-data
→ Sauvegarde dans static/uploads/
→ Retourne l'URL publique /static/uploads/<filename>
```

---

## Base de Données

### Session async

```python
# database/__init__.py
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

`get_db()` est injecté via `Depends(get_db)` dans toutes les routes.

### Migrations Alembic

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1        # revenir en arrière
alembic history             # voir l'historique
```

---

## Commandes Développement

```bash
# Serveur avec rechargement automatique
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
pytest
pytest -v --cov=app --cov-report=html

# Qualité code
ruff check app/
black app/
mypy app/

# Sécurité
bandit -r app/
```
