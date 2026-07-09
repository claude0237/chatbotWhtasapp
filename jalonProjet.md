# Jalons du Projet - WhatsApp SaaS Platform

## Vue d'ensemble

Ce document définit le découpage du projet en phases indépendantes et livrables. Chaque phase a des objectifs clairs, des livrables mesurables et des critères de validation stricts.

---

## Phase 0 : Initialisation et Infrastructure

**Objectif** : Mettre en place l'environnement de développement, les outils et la structure de projet.

**Durée estimée** : 2-3 jours

### Tâches

#### 0.1 Structure de projet
- [ ] Créer la structure de dossiers backend
- [ ] Créer la structure de dossiers frontend
- [ ] Initialiser les dépôts Git
- [ ] Configurer .gitignore
- [ ] Créer les fichiers README

#### 0.2 Backend setup
- [ ] Installer Python 3.12
- [ ] Créer virtual environment
- [ ] Installer les dépendances (FastAPI, SQLAlchemy, Alembic, etc.)
- [ ] Configurer pyproject.toml ou requirements.txt
- [ ] Configurer pre-commit (black, ruff, mypy)
- [ ] Configurer pytest

#### 0.3 Frontend setup
- [ ] Initialiser projet React + Vite
- [ ] Installer Tailwind CSS
- [ ] Installer React Router
- [ ] Installer TanStack Query
- [ ] Installer Axios
- [ ] Configurer ESLint + Prettier

#### 0.4 Infrastructure locale
- [ ] Installer PostgreSQL 14+ avec extension pgvector
- [ ] Installer Redis 7+
- [ ] Créer la base de données whatsapp_saas
- [ ] Activer l'extension pgvector
- [ ] Démarrer le serveur Redis
- [ ] Configurer les variables d'environnement (.env.example)
- [ ] Tester la connexion PostgreSQL
- [ ] Tester la connexion Redis

#### 0.5 Documentation initiale
- [ ] Documenter la structure de projet
- [ ] Documenter les commandes de développement
- [ ] Créer le guide de contribution

**Livrables**
- Structure de projet complète
- Environnement de développement fonctionnel
- PostgreSQL et Redis installés localement
- Documentation initiale

**Critères de validation**
- PostgreSQL est installé et l'extension pgvector est activée
- Redis est installé et fonctionne
- La base de données whatsapp_saas est créée
- `pytest` fonctionne sans erreur
- `npm run dev` démarre le frontend
- `uvicorn app.main:app --reload` démarre le backend

---

## Phase 1 : Authentification et Multi-tenancy

**Objectif** : Implémenter le système d'authentification JWT et l'isolation multi-tenant stricte.

**Durée estimée** : 5-7 jours

### Tâches

#### 1.1 Base de données - Schéma de base
- [ ] Créer la migration Alembic initiale
- [ ] Définir le modèle `Company`
- [ ] Définir le modèle `User`
- [ ] Définir le modèle `Role`
- [ ] Définir le modèle `Permission`
- [ ] Définir le modèle `UserRole`
- [ ] Définir le modèle `CompanySettings`
- [ ] Ajouter les index sur `company_id`
- [ ] Activer Row Level Security (RLS) sur PostgreSQL

#### 1.2 Repository Layer
- [ ] Créer `CompanyRepository`
- [ ] Créer `UserRepository`
- [ ] Créer `RoleRepository`
- [ ] Créer `PermissionRepository`
- [ ] Tests unitaires des repositories

#### 1.3 Service Layer - Auth
- [ ] Créer `AuthService`
  - [ ] Méthode `register()`
  - [ ] Méthode `login()`
  - [ ] Méthode `refresh_token()`
  - [ ] Méthode `logout()`
  - [ ] Méthode `verify_token()`
- [ ] Implémenter le hachage de mot de passe (Argon2id)
- [ ] Créer `UserService`
- [ ] Créer `CompanyService`
- [ ] Tests unitaires des services

#### 1.4 JWT Implementation
- [ ] Créer le système de JWT Access Token
- [ ] Créer le système de Refresh Token
- [ ] Créer le middleware d'authentification
- [ ] Créer le middleware de vérification company_id
- [ ] Implémenter la rotation des refresh tokens

#### 1.5 Controllers et Routes
- [ ] Créer `AuthController`
  - [ ] POST `/api/v1/auth/register`
  - [ ] POST `/api/v1/auth/login`
  - [ ] POST `/api/v1/auth/refresh`
  - [ ] POST `/api/v1/auth/logout`
  - [ ] POST `/api/v1/auth/verify`
- [ ] Créer `CompaniesController`
  - [ ] POST `/api/v1/companies`
  - [ ] GET `/api/v1/companies/{id}`
  - [ ] PUT `/api/v1/companies/{id}`
- [ ] Créer `UsersController`
  - [ ] GET `/api/v1/users`
  - [ ] POST `/api/v1/users`
  - [ ] PUT `/api/v1/users/{id}`
  - [ ] DELETE `/api/v1/users/{id}`
- [ ] Tests d'intégration API

#### 1.6 RBAC (Role Based Access Control)
- [ ] Définir les rôles : SUPER_ADMIN, COMPANY_ADMIN, AGENT, READ_ONLY
- [ ] Créer le système de permissions
- [ ] Créer le middleware de vérification des permissions
- [ ] Décorateur `@require_permission()`
- [ ] Décorateur `@require_role()`

#### 1.7 Frontend - Auth
- [ ] Créer la page Login
- [ ] Créer la page Register
- [ ] Créer le contexte Auth
- [ ] Créer le hook useAuth
- [ ] Créer le service API auth
- [ ] Implémenter le stockage des tokens (httpOnly cookies)
- [ ] Créer le ProtectedRoute
- [ ] Créer le layout PublicLayout
- [ ] Créer le layout AuthenticatedLayout

#### 1.8 Sécurité multi-tenant
- [ ] Créer le middleware d'injection company_id
- [ ] Tests de sécurité cross-tenant
- [ ] Audit logs pour les actions sensibles
- [ ] Vérification automatique du company_id dans toutes les requêtes

**Livrables**
- Système d'authentification JWT fonctionnel
- Isolation multi-tenant stricte avec RLS
- RBAC implpémenté
- Frontend authentification complet
- Tests de sécurité multi-tenant

**Critères de validation**
- Un utilisateur ne peut jamais accéder aux données d'une autre entreprise
- Les tokens expirent correctement et sont rafraîchis
- Les permissions sont correctement appliquées
- Les tests de sécurité passent à 100%

---

## Phase 2 : Abstraction Channel et WhatsApp

**Objectif** : Créer l'abstraction pour les canaux de communication et implémenter WhatsApp.

**Durée estimée** : 5-7 jours

### Tâches

#### 2.1 Base de données - Channel
- [ ] Définir le modèle `Channel` (abstraction)
- [ ] Définir le modèle `ChannelConfiguration`
- [ ] Définir le modèle `ChannelCredential` (chiffrés)
- [ ] Définir le modèle `ChannelMessage`
- [ ] Définir le modèle `ChannelWebhookLog`
- [ ] Migrations Alembic

#### 2.2 Channel Abstraction
- [ ] Créer l'interface `ChannelProvider`
  - [ ] Méthode `send_message()`
  - [ ] Méthode `receive_webhook()`
  - [ ] Méthode `verify_webhook()`
  - [ ] Méthode `get_message_status()`
  - [ ] Méthode `send_template()`
- [ ] Créer `ChannelFactory`
- [ ] Tests unitaires de l'abstraction

#### 2.3 WhatsApp Implementation
- [ ] Créer `WhatsAppChannelProvider`
  - [ ] Implémentation de `send_message()`
  - [ ] Implémentation de `receive_webhook()`
  - [ ] Implémentation de `verify_webhook()`
  - [ ] Support des messages texte
  - [ ] Support des images
  - [ ] Support des vidéos
  - [ ] Support des documents (PDF)
  - [ ] Support des messages audio
  - [ ] Support des templates
- [ ] Créer `WhatsAppService`
- [ ] Tests unitaires WhatsApp

#### 2.4 Webhook Handler
- [ ] Créer le webhook endpoint `/webhooks/whatsapp`
- [ ] Créer le middleware de vérification de signature WhatsApp
- [ ] Créer le système de queue pour les webhooks (Celery)
- [ ] Logs des webhooks reçus
- [ ] Gestion des erreurs de webhook

#### 2.5 Repository Channel
- [ ] Créer `ChannelRepository`
- [ ] Créer `ChannelMessageRepository`
- [ ] Tests unitaires

#### 2.6 Controllers Channel
- [ ] Créer `ChannelsController`
  - [ ] POST `/api/v1/companies/{id}/channels`
  - [ ] GET `/api/v1/companies/{id}/channels`
  - [ ] PUT `/api/v1/companies/{id}/channels/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/channels/{id}`
  - [ ] POST `/api/v1/companies/{id}/channels/{id}/verify`
  - [ ] POST `/api/v1/companies/{id}/channels/{id}/test`
- [ ] Tests d'intégration

#### 2.7 Frontend - Channels
- [ ] Créer la page Channels
- [ ] Créer le composant WhatsAppConfigForm
- [ ] Créer le service API channels
- [ ] Créer le hook useChannels
- [ ] Interface de connexion WhatsApp
- [ ] Interface de vérification webhook
- [ ] Interface d'envoi de message test

**Livrables**
- Abstraction Channel fonctionnelle
- Implémentation WhatsApp complète
- Webhook handler robuste
- Interface de configuration WhatsApp
- Tests d'intécration

**Critères de validation**
- L'abstraction permet d'ajouter un nouveau canal sans modifier le code existant
- Les webhooks WhatsApp sont reçus et traités correctement
- L'envoi de messages fonctionne (texte, média, templates)
- Les credentials sont chiffrés en base de données

---

## Phase 3 : Gestion des Clients et Conversations

**Objectif** : Implémenter la gestion des clients WhatsApp et le système de conversations.

**Durée estimée** : 7-10 jours

### Tâches

#### 3.1 Base de données - Clients et Conversations
- [ ] Définir le modèle `Customer`
  - [ ] phone_number (unique par company)
  - [ ] name
  - [ ] profile_picture_url
  - [ ] metadata
- [ ] Définir le modèle `Conversation`
  - [ ] customer_id
  - [ ] channel_id
  - [ ] status (OPEN, WAITING, AI, AGENT, CLOSED, ARCHIVED)
  - [ ] assigned_agent_id
  - [ ] priority (LOW, MEDIUM, HIGH, URGENT)
  - [ ] tags
  - [ ] last_activity_at
- [ ] Définir le modèle `Message`
  - [ ] conversation_id
  - [ ] sender_type (CUSTOMER, AGENT, BOT)
  - [ ] sender_id
  - [ ] content
  - [ ] message_type (TEXT, IMAGE, VIDEO, DOCUMENT, AUDIO)
  - [ ] media_url
  - [ ] external_message_id (WhatsApp message ID)
  - [ ] status (SENT, DELIVERED, READ, FAILED)
- [ ] Définir le modèle `ConversationNote`
  - [ ] conversation_id
  - [ ] user_id
  - [ ] content (note interne)
- [ ] Migrations Alembic
- [ ] Index sur customer.phone_number + company_id
- [ ] Index sur conversation.status + company_id

#### 3.2 Repository Layer
- [ ] Créer `CustomerRepository`
- [ ] Créer `ConversationRepository`
- [ ] Créer `MessageRepository`
- [ ] Créer `ConversationNoteRepository`
- [ ] Tests unitaires

#### 3.3 Service Layer
- [ ] Créer `CustomerService`
  - [ ] Méthode `get_or_create()`
  - [ ] Méthode `update_profile()`
- [ ] Créer `ConversationService`
  - [ ] Méthode `create_conversation()`
  - [ ] Méthode `assign_to_agent()`
  - [ ] Méthode `change_status()`
  - [ ] Méthode `add_tag()`
  - [ ] Méthode `archive()`
- [ ] Créer `MessageService`
  - [ ] Méthode `send_message()`
  - [ ] Méthode `receive_message()`
  - [ ] Méthode `update_status()`
  - [ ] Méthode `get_history()`
- [ ] Tests unitaires

#### 3.4 Event System
- [ ] Créer le système d'événements
- [ ] Définir les événements :
  - [ ] `MessageReceived`
  - [ ] `MessageSent`
  - [ ] `ConversationCreated`
  - [ ] `ConversationAssigned`
  - [ ] `ConversationStatusChanged`
  - [ ] `CustomerCreated`
  - [ ] `CustomerUpdated`
- [ ] Créer `EventBus`
- [ ] Créer `EventHandler`
- [ ] Intégration avec RabbitMQ/Redis Streams

#### 3.5 Controllers
- [ ] Créer `CustomersController`
  - [ ] GET `/api/v1/companies/{id}/customers`
  - [ ] GET `/api/v1/companies/{id}/customers/{id}`
  - [ ] PUT `/api/v1/companies/{id}/customers/{id}`
- [ ] Créer `ConversationsController`
  - [ ] GET `/api/v1/companies/{id}/conversations`
  - [ ] GET `/api/v1/companies/{id}/conversations/{id}`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/assign`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/status`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/tags`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/archive`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/notes`
- [ ] Créer `MessagesController`
  - [ ] GET `/api/v1/companies/{id}/conversations/{id}/messages`
  - [ ] POST `/api/v1/companies/{id}/conversations/{id}/messages`
- [ ] Tests d'intégration

#### 3.6 Frontend - Conversations
- [ ] Créer la page Conversations
- [ ] Créer le composant ConversationList
- [ ] Créer le composant ConversationDetail
- [ ] Créer le composant MessageList
- [ ] Créer le composant MessageInput
- [ ] Créer le composant ConversationFilters
- [ ] Créer le service API conversations
- [ ] Créer le service API messages
- [ ] Créer le hook useConversations
- [ ] Créer le hook useMessages
- [ ] Implémenter le polling ou WebSocket pour les messages en temps réel
- [ ] Interface d'assignation à un agent
- [ ] Interface de changement de statut
- [ ] Interface de notes internes

#### 3.7 Frontend - Customers
- [ ] Créer la page Customers
- [ ] Créer le composant CustomerList
- [ ] Créer le composant CustomerDetail
- [ ] Créer le service API customers
- [ ] Créer le hook useCustomers

**Livrables**
- Système de gestion des clients complet
- Système de conversations fonctionnel
- Event system opérationnel
- Interface de gestion des conversations
- Interface de messagerie en temps réel

**Critères de validation**
- Les conversations sont correctement isolées par entreprise
- Les messages sont envoyés et reçus en temps réel
- L'assignation à un agent fonctionne
- Les événements sont correctement émis et traités
- L'historique des messages est complet

---

## Phase 4 : Bot Engine Natif

**Objectif** : Implémenter le moteur de bot natif basé sur des règles et scénarios.

**Durée estimée** : 5-7 jours

### Tâches

#### 4.1 Base de données - Bot Natif
- [ ] Définir le modèle `BotConfiguration`
  - [ ] bot_type (NATIVE, ML, HYBRID)
  - [ ] name
  - [ ] welcome_message
  - [ ] away_message
  - [ ] closing_message
  - [ ] unknown_message
  - [ ] language
  - [ ] timezone
  - [ ] avatar_url
  - [ ] native_rules (JSONB)
- [ ] Définir le modèle `BotScenario`
  - [ ] name
  - [ ] trigger_keyword
  - [ ] steps (JSONB - flow du scénario)
  - [ ] is_active
- [ ] Définir le modèle `BotKeyword`
  - [ ] keyword
  - [ ] response
  - [ ] category
- [ ] Migrations Alembic

#### 4.2 Repository Layer
- [ ] Créer `BotConfigurationRepository`
- [ ] Créer `BotScenarioRepository`
- [ ] Créer `BotKeywordRepository`
- [ ] Tests unitaires

#### 4.3 Service Layer - Bot Natif
- [ ] Créer `NativeBotEngine`
  - [ ] Méthode `process_message()`
  - [ ] Méthode `match_keyword()`
  - [ ] Méthode `execute_scenario()`
  - [ ] Méthode `get_welcome_message()`
  - [ ] Méthode `get_away_message()`
  - [ ] Méthode `get_unknown_message()`
- [ ] Créer `BotConfigurationService`
  - [ ] Méthode `create_configuration()`
  - [ ] Méthode `update_configuration()`
  - [ ] Méthode `get_active_configuration()`
- [ ] Tests unitaires

#### 4.4 Controllers
- [ ] Créer `BotConfigurationController`
  - [ ] GET `/api/v1/companies/{id}/bot/config`
  - [ ] POST `/api/v1/companies/{id}/bot/config`
  - [ ] PUT `/api/v1/companies/{id}/bot/config`
- [ ] Créer `BotScenarioController`
  - [ ] GET `/api/v1/companies/{id}/bot/scenarios`
  - [ ] POST `/api/v1/companies/{id}/bot/scenarios`
  - [ ] PUT `/api/v1/companies/{id}/bot/scenarios/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/bot/scenarios/{id}`
- [ ] Créer `BotKeywordController`
  - [ ] GET `/api/v1/companies/{id}/bot/keywords`
  - [ ] POST `/api/v1/companies/{id}/bot/keywords`
  - [ ] PUT `/api/v1/companies/{id}/bot/keywords/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/bot/keywords/{id}`
- [ ] Tests d'intégration

#### 4.5 Frontend - Bot Natif
- [ ] Créer la page Bot Configuration
- [ ] Créer le composant BotConfigForm
  - [ ] Configuration générale (nom, langue, messages)
  - [ ] Choix du mode (NATIVE, ML, HYBRIDE)
- [ ] Créer le composant ScenarioBuilder
  - [ ] Interface visuelle pour créer des scénarios
  - [ ] Éditeur de flow
- [ ] Créer le composant KeywordManager
  - [ ] Liste des keywords
  - [ ] Ajout/Modification/Suppression
- [ ] Créer le service API bot
- [ ] Créer le hook useBotConfig

#### 4.6 Intégration avec Conversations
- [ ] Intégrer le NativeBotEngine dans MessageService
- [ ] Router automatiquement les messages vers le bot
- [ ] Gérer le transfert bot → agent
- [ ] Gérer le transfert agent → bot

**Livrables**
- Moteur de bot natif fonctionnel
- Système de scénarios visuel
- Gestion des keywords
- Interface de configuration du bot
- Intégration avec les conversations

**Critères de validation**
- Le bot répond correctement aux keywords
- Les scénarios s'exécutent correctement
- Le transfert vers un agent fonctionne
- La configuration est prise en compte sans redémarrage

---

## Phase 5 : Base de Connaissances

**Objectif** : Implémenter la base de connaissances (FAQ) pour le bot.

**Durée estimée** : 4-5 jours

### Tâches

#### 5.1 Base de données - Knowledge Base
- [ ] Définir le modèle `KnowledgeBase`
  - [ ] company_id
  - [ ] title
  - [ ] content
  - [ ] category
  - [ ] source_type (FAQ, MANUAL, IMPORTED)
  - [ ] source_id
  - [ ] metadata (JSONB)
  - [ ] version
  - [ ] is_active
- [ ] Définir le modèle `KnowledgeCategory`
  - [ ] name
  - [ ] parent_id
  - [ ] icon
- [ ] Migrations Alembic
- [ ] Index sur category + company_id

#### 5.2 Repository Layer
- [ ] Créer `KnowledgeBaseRepository`
- [ ] Créer `KnowledgeCategoryRepository`
- [ ] Tests unitaires

#### 5.3 Service Layer
- [ ] Créer `KnowledgeBaseService`
  - [ ] Méthode `create_entry()`
  - [ ] Méthode `update_entry()`
  - [ ] Méthode `delete_entry()`
  - [ ] Méthode `search()`
  - [ ] Méthode `get_by_category()`
- [ ] Créer `KnowledgeCategoryService`
- [ ] Tests unitaires

#### 5.4 Controllers
- [ ] Créer `KnowledgeBaseController`
  - [ ] GET `/api/v1/companies/{id}/knowledge`
  - [ ] POST `/api/v1/companies/{id}/knowledge`
  - [ ] PUT `/api/v1/companies/{id}/knowledge/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/knowledge/{id}`
  - [ ] GET `/api/v1/companies/{id}/knowledge/categories`
  - [ ] POST `/api/v1/companies/{id}/knowledge/categories`
- [ ] Tests d'intégration

#### 5.5 Frontend - Knowledge Base
- [ ] Créer la page Knowledge Base
- [ ] Créer le composant KnowledgeList
- [ ] Créer le composant KnowledgeForm
  - [ ] Éditeur de question/réponse
  - [ ] Sélection de catégorie
- [ ] Créer le composant CategoryManager
- [ ] Créer le service API knowledge
- [ ] Créer le hook useKnowledge
- [ ] Interface de recherche

#### 5.6 Intégration avec Bot Natif
- [ ] Intégrer la recherche dans NativeBotEngine
- [ ] Rechercher dans la base de connaissances avant de répondre "unknown"

**Livrables**
- Base de connaissances fonctionnelle
- Gestion des catégories
- Interface de gestion FAQ
- Intégration avec le bot natif
- Recherche dans les connaissances

**Critères de validation**
- Les entrées sont correctement isolées par entreprise
- La recherche fonctionne correctement
- Les catégories sont hiérarchiques
- Le bot utilise la base de connaissances

---

## Phase 6 : Infrastructure ML - Ingestion et Embeddings

**Objectif** : Mettre en place le pipeline d'ingestion de documents et le système d'embeddings.

**Durée estimée** : 7-10 jours

### Tâches

#### 6.1 Infrastructure
- [ ] Installer pgvector extension dans PostgreSQL
- [ ] Configurer le stockage vectoriel
- [ ] Installer les dépendances ML (sentence-transformers, openai, etc.)
- [ ] Configurer Redis pour le cache d'embeddings

#### 6.2 Base de données - ML
- [ ] Ajouter le champ `embedding` (VECTOR) à `knowledge_base`
- [ ] Définir le modèle `Document`
  - [ ] file_name
  - [ ] file_type (PDF, WORD, EXCEL, MARKDOWN)
  - [ ] file_path (S3/MinIO)
  - [ ] file_size
  - [ ] status (UPLOADING, PROCESSING, COMPLETED, FAILED)
  - [ ] chunk_count
  - [ ] processed_at
- [ ] Définir le modèle `DocumentChunk`
  - [ ] document_id
  - [ ] content
  - [ ] chunk_index
  - [ ] embedding (VECTOR)
  - [ ] metadata
- [ ] Définir le modèle `IngestionJob`
  - [ ] source_type
  - [ ] source_config (JSONB)
  - [ ] status (PENDING, RUNNING, COMPLETED, FAILED)
  - [ ] started_at
  - [ ] completed_at
  - [ ] error_message
- [ ] Migrations Alembic

#### 6.3 Repository Layer ML
- [ ] Créer `DocumentRepository`
- [ ] Créer `DocumentChunkRepository`
- [ ] Créer `IngestionJobRepository`
- [ ] Tests unitaires

#### 6.4 Service Layer - Ingestion
- [ ] Créer `PDFExtractor`
  - [ ] Méthode `extract_text()`
  - [ ] Méthode `extract_metadata()`
- [ ] Créer `WordExtractor`
- [ ] Créer `ExcelExtractor`
- [ ] Créer `MarkdownExtractor`
- [ ] Créer `TextChunker`
  - [ ] Méthode `chunk_by_paragraph()`
  - [ ] Méthode `chunk_by_token()`
  - [ ] Méthode `chunk_by_semantic()`
- [ ] Tests unitaires des extractors

#### 6.5 Service Layer - Embeddings
- [ ] Créer l'interface `EmbeddingProvider`
  - [ ] Méthode `generate_embedding()`
  - [ ] Méthode `generate_batch_embeddings()`
- [ ] Créer `OpenAIEmbeddingProvider`
- [ ] Créer `LocalEmbeddingProvider` (sentence-transformers)
- [ ] Créer `EmbeddingService`
  - [ ] Méthode `embed_document()`
  - [ ] Méthode `embed_text()`
  - [ ] Méthode `batch_embed()`
  - [ ] Cache Redis des embeddings
- [ ] Tests unitaires

#### 6.6 Service Layer - Ingestion Pipeline
- [ ] Créer `KnowledgeIngestionService`
  - [ ] Méthode `ingest_document()`
  - [ ] Méthode `ingest_from_database()`
  - [ ] Méthode `reindex_all()`
  - [ ] Méthode `delete_document()`
- [ ] Intégration avec Celery pour les tâches asynchrones
- [ ] Créer les workers Celery
- [ ] Tests unitaires

#### 6.7 Vector Store
- [ ] Créer `VectorStoreService`
  - [ ] Méthode `add_vectors()`
  - [ ] Méthode `search_similar()`
  - [ ] Méthode `delete_vectors()`
  - [ ] Implémentation pgvector
- [ ] Tests unitaires

#### 6.8 Controllers
- [ ] Créer `DocumentsController`
  - [ ] POST `/api/v1/companies/{id}/documents/upload`
  - [ ] GET `/api/v1/companies/{id}/documents`
  - [ ] GET `/api/v1/companies/{id}/documents/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/documents/{id}`
- [ ] Créer `IngestionController`
  - [ ] POST `/api/v1/companies/{id}/ingestion/from-db`
  - [ ] POST `/api/v1/companies/{id}/ingestion/reindex`
  - [ ] GET `/api/v1/companies/{id}/ingestion/jobs/{id}`
- [ ] Tests d'intégration

#### 6.9 Frontend - Documents
- [ ] Créer la page Documents
- [ ] Créer le composant DocumentUpload
  - [ ] Drag & drop
  - [ ] Progress bar
  - [ ] Support PDF, Word, Excel
- [ ] Créer le composant DocumentList
- [ ] Créer le service API documents
- [ ] Créer le hook useDocuments
- [ ] Interface de suivi des jobs d'ingestion

#### 6.10 Stockage fichiers
- [ ] Configurer MinIO ou S3
- [ ] Créer le service `StorageService`
- [ ] Gestion des uploads
- [ ] Gestion des suppressions

**Livrables**
- Pipeline d'ingestion de documents fonctionnel
- Système d'embeddings opérationnel
- Vector store pgvector intégré
- Interface d'upload de documents
- Workers Celery pour les tâches asynchrones

**Critères de validation**
- Les documents sont correctement extraits (PDF, Word, Excel)
- Le chunking fonctionne correctement
- Les embeddings sont générés et stockés
- La recherche sémantique fonctionne
- Les jobs asynchrones s'exécutent correctement

---

## Phase 7 : ML Engine - RAG et LLM

**Objectif** : Implémenter le moteur ML avec RAG (Retrieval Augmented Generation).

**Durée estimée** : 7-10 jours

### Tâches

#### 7.1 Base de données - ML
- [ ] Mettre à jour `BotConfiguration`
  - [ ] Ajouter `ml_enabled`
  - [ ] Ajouter `ml_provider` (OPENAI, ANTHROPIC, OLLAMA)
  - [ ] Ajouter `ml_model`
  - [ ] Ajouter `ml_temperature`
  - [ ] Ajouter `ml_max_tokens`
  - [ ] Ajouter `fallback_strategy` (ML_TO_NATIVE, NATIVE_TO_ML, PARALLEL)
  - [ ] Ajouter `confidence_threshold`
- [ ] Définir le modèle `MLModel`
  - [ ] name
  - [ ] model_type (RAG, CLASSIFIER, RERANKER)
  - [ ] provider
  - [ ] model_name
  - [ ] version
  - [ ] metrics (JSONB)
  - [ ] is_active
- [ ] Migrations Alembic

#### 7.2 Repository Layer ML
- [ ] Créer `MLModelRepository`
- [ ] Tests unitaires

#### 7.3 Service Layer - LLM Providers
- [ ] Créer l'interface `LLMProvider`
  - [ ] Méthode `generate_response()`
  - [ ] Méthode `generate_stream()`
- [ ] Créer `OpenAIProvider`
- [ ] Créer `AnthropicProvider`
- [ ] Créer `OllamaProvider`
- [ ] Créer `LLMProviderFactory`
- [ ] Tests unitaires

#### 7.4 Service Layer - RAG
- [ ] Créer `RAGRetriever`
  - [ ] Méthode `retrieve()`
  - [ ] Méthode `hybrid_search()` (keyword + semantic)
  - [ ] Méthode `rerank()`
- [ ] Créer `ContextBuilder`
  - [ ] Méthode `build_context()`
  - [ ] Ajout de l'historique de conversation
  - [ ] Ajout des connaissances récupérées
  - [ ] Ajout du contexte entreprise
- [ ] Créer `PromptBuilder`
  - [ ] Méthode `build_system_prompt()`
  - [ ] Méthode `build_user_prompt()`
  - [ ] Templates de prompts
- [ ] Tests unitaires

#### 7.5 Service Layer - ML Bot Engine
- [ ] Créer `MLBotEngine`
  - [ ] Méthode `process_message()`
  - [ ] Méthode `get_response()`
  - [ ] Intégration RAG + LLM
  - [ ] Gestion de la confiance
- [ ] Créer `DecisionEngine`
  - [ ] Méthode `route_to_native_or_ml()`
  - [ ] Implémentation des stratégies de fallback
  - [ ] A/B testing
- [ ] Tests unitaires

#### 7.6 Service Layer - ML Training
- [ ] Créer `MLTrainingService`
  - [ ] Méthode `train_intent_classifier()`
  - [ ] Méthode `fine_tune_llm()`
  - [ ] Méthode `evaluate_model()`
- [ ] Intégration MLflow (optionnel pour phase 1)
- [ ] Tests unitaires

#### 7.7 Controllers
- [ ] Mettre à jour `BotConfigurationController`
  - [ ] Ajouter les endpoints ML
- [ ] Créer `MLController`
  - [ ] POST `/api/v1/companies/{id}/ml/train`
  - [ ] GET `/api/v1/companies/{id}/ml/jobs/{id}`
  - [ ] GET `/api/v1/companies/{id}/ml/models`
  - [ ] POST `/api/v1/companies/{id}/ml/models/{id}/deploy`
- [ ] Tests d'intégration

#### 7.8 Frontend - ML Configuration
- [ ] Mettre à jour le composant BotConfigForm
  - [ ] Configuration ML (provider, modèle, température)
  - [ ] Stratégie de fallback
  - [ ] Seuil de confiance
- [ ] Créer le composant MLPerformanceDashboard
  - [ ] Métriques ML vs Natif
  - [ ] Graphiques de performance
- [ ] Créer le service API ML
- [ ] Créer le hook useML

#### 7.9 Intégration avec Conversations
- [ ] Intégrer MLBotEngine dans MessageService
- [ ] Router selon la configuration (NATIVE, ML, HYBRIDE)
- [ ] Gérer les fallbacks
- [ ] Logger les décisions pour analytics

**Livrables**
- Moteur ML avec RAG fonctionnel
- Intégration multi-fournisseurs LLM
- Decision Engine avec fallback
- Interface de configuration ML
- Dashboard de performance ML

**Critères de validation**
- Le RAG récupère les connaissances pertinentes
- Les réponses LLM sont cohérentes avec le contexte
- Le fallback vers le bot natif fonctionne
- Les différents fournisseurs LLM fonctionnent
- Les métriques de performance sont collectées

---

## Phase 8 : Analytics et Dashboard

**Objectif** : Implémenter le système d'analytics et les tableaux de bord.

**Durée estimée** : 5-7 jours

### Tâches

#### 8.1 Base de données - Analytics
- [ ] Définir le modèle `AnalyticsMetric`
  - [ ] metric_name
  - [ ] metric_value
  - [ ] dimensions (JSONB)
  - [ ] timestamp
- [ ] Définir le modèle `AnalyticsReport`
  - [ ] report_name
  - [ ] report_type (DAILY, WEEKLY, MONTHLY)
  - [ ] data (JSONB)
  - [ ] generated_at
- [ ] Créer des vues materialisées pour les agrégations
- [ ] Migrations Alembic

#### 8.2 Service Layer - Analytics
- [ ] Créer `AnalyticsService`
  - [ ] Méthode `track_metric()`
  - [ ] Méthode `get_conversation_stats()`
  - [ ] Méthode `get_message_stats()`
  - [ ] Méthode `get_agent_performance()`
  - [ ] Méthode `get_ml_performance()`
  - [ ] Méthode `get_response_time_stats()`
  - [ ] Méthode `generate_report()`
- [ ] Créer `DashboardService`
  - [ ] Méthode `get_company_dashboard()`
  - [ ] Méthode `get_super_admin_dashboard()`
- [ ] Tests unitaires

#### 8.3 Event Tracking
- [ ] Créer des event handlers pour analytics
  - [ ] Track message sent
  - [ ] Track message received
  - [ ] Track conversation created
  - [ ] Track conversation assigned
  - [ ] Track bot response
  - [ ] Track agent response
- [ ] Agréger les metrics en temps réel

#### 8.4 Controllers
- [ ] Créer `AnalyticsController`
  - [ ] GET `/api/v1/companies/{id}/analytics/conversations`
  - [ ] GET `/api/v1/companies/{id}/analytics/messages`
  - [ ] GET `/api/v1/companies/{id}/analytics/agents`
  - [ ] GET `/api/v1/companies/{id}/analytics/ml`
  - [ ] GET `/api/v1/companies/{id}/analytics/response-time`
  - [ ] GET `/api/v1/companies/{id}/analytics/reports`
- [ ] Créer `DashboardController`
  - [ ] GET `/api/v1/companies/{id}/dashboard`
  - [ ] GET `/api/v1/super-admin/dashboard`
- [ ] Tests d'intégration

#### 8.5 Frontend - Dashboard Entreprise
- [ ] Créer la page Dashboard Entreprise
- [ ] Créer le composant KPI Cards
  - [ ] Conversations aujourd'hui
  - [ ] Messages envoyés
  - [ ] Temps moyen de réponse
  - [ ] Nouveaux clients
  - [ ] IA activée
  - [ ] Agents connectés
- [ ] Créer le composant ConversationChart
- [ ] Créer le composant MessageChart
- [ ] Créer le composant ResponseTimeChart
- [ ] Créer le service API analytics
- [ ] Créer le hook useAnalytics

#### 8.6 Frontend - Dashboard Super Admin
- [ ] Créer la page Dashboard Super Admin
- [ ] Créer le composant GlobalStats
  - [ ] Total entreprises
  - [ ] Total utilisateurs
  - [ ] Total conversations
  - [ ] Utilisation plateforme
- [ ] Créer le composant CompanyList
- [ ] Créer le composant CompanyGrowthChart

#### 8.7 Frontend - Analytics détaillés
- [ ] Créer la page Analytics
- [ ] Créer le composant AnalyticsFilters (période, filtres)
- [ ] Créer le composant AgentPerformanceTable
- [ ] Créer le composant MLvsNativeComparison
- [ ] Export des rapports (Excel, PDF)

**Livrables**
- Système d'analytics complet
- Dashboard entreprise fonctionnel
- Dashboard super admin fonctionnel
- Rapports exportables
- Graphiques et visualisations

**Critères de validation**
- Les metrics sont correctement trackés
- Les agrégations sont performantes
- Les dashboards affichent les bonnes données
- Les exports fonctionnent
- Les données sont isolées par entreprise

---

## Phase 9 : Notifications

**Objectif** : Implémenter le système de notifications internes.

**Durée estimée** : 3-4 jours

### Tâches

#### 9.1 Base de données - Notifications
- [ ] Définir le modèle `Notification`
  - [ ] user_id
  - [ ] type (NEW_CONVERSATION, MENTION, RESERVATION, PAYMENT, etc.)
  - [ ] title
  - [ ] message
  - [ ] data (JSONB)
  - [ ] is_read
  - [ ] read_at
  - [ ] created_at
- [ ] Définir le modèle `NotificationPreference`
  - [ ] user_id
  - [ ] notification_type
  - [ ] enabled
  - [ ] channel (IN_APP, EMAIL, SMS)
- [ ] Migrations Alembic

#### 9.2 Repository Layer
- [ ] Créer `NotificationRepository`
- [ ] Créer `NotificationPreferenceRepository`
- [ ] Tests unitaires

#### 9.3 Service Layer
- [ ] Créer `NotificationService`
  - [ ] Méthode `create_notification()`
  - [ ] Méthode `send_to_user()`
  - [ ] Méthode `send_to_role()`
  - [ ] Méthode `mark_as_read()`
  - [ ] Méthode `get_user_notifications()`
- [ ] Créer les event handlers pour notifications
  - [ ] Nouvelle conversation → notifier agents
  - [ ] Mention d'un agent → notifier l'agent
  - [ ] Réservation créée → notifier admin
- [ ] Tests unitaires

#### 9.4 Real-time Notifications
- [ ] Implémenter WebSocket pour les notifications en temps réel
- [ ] Créer le endpoint `/ws/notifications`
- [ ] Gestion des connexions WebSocket
- [ ] Broadcast des notifications

#### 9.5 Controllers
- [ ] Créer `NotificationsController`
  - [ ] GET `/api/v1/notifications`
  - [ ] PUT `/api/v1/notifications/{id}/read`
  - [ ] PUT `/api/v1/notifications/read-all`
  - [ ] GET `/api/v1/notifications/preferences`
  - [ ] PUT `/api/v1/notifications/preferences`
- [ ] Tests d'intégration

#### 9.6 Frontend - Notifications
- [ ] Créer le composant NotificationBell
- [ ] Créer le composant NotificationList
- [ ] Créer le composant NotificationPreferences
- [ ] Créer le hook useNotifications
- [ ] Intégration WebSocket
- [ ] Son de notification
- [ ] Badge de compteur

**Livrables**
- Système de notifications fonctionnel
- Notifications en temps réel via WebSocket
- Préférences de notification
- Interface de notifications

**Critères de validation**
- Les notifications sont créées automatiquement
- Les notifications sont reçues en temps réel
- Les préférences sont respectées
- Le marquage comme lu fonctionne

---

## Phase 10 : Catalogue Produits (Optionnel)

**Objectif** : Implémenter le module catalogue pour les entreprises e-commerce.

**Durée estimée** : 5-7 jours

### Tâches

#### 10.1 Base de données - Catalogue
- [ ] Définir le modèle `Product`
  - [ ] name
  - [ ] description
  - [ ] price
  - [ ] currency
  - [ ] stock
  - [ ] images (JSONB)
  - [ ] category_id
  - [ ] is_active
  - [ ] metadata (JSONB)
- [ ] Définir le modèle `ProductCategory`
  - [ ] name
  - [ ] parent_id
- [ ] Migrations Alembic

#### 10.2 Repository Layer
- [ ] Créer `ProductRepository`
- [ ] Créer `ProductCategoryRepository`
- [ ] Tests unitaires

#### 10.3 Service Layer
- [ ] Créer `ProductService`
  - [ ] Méthode `create_product()`
  - [ ] Méthode `update_product()`
  - [ ] Méthode `delete_product()`
  - [ ] Méthode `search_products()`
- [ ] Tests unitaires

#### 10.4 Controllers
- [ ] Créer `ProductsController`
  - [ ] GET `/api/v1/companies/{id}/products`
  - [ ] POST `/api/v1/companies/{id}/products`
  - [ ] PUT `/api/v1/companies/{id}/products/{id}`
  - [ ] DELETE `/api/v1/companies/{id}/products/{id}`
- [ ] Tests d'intégration

#### 10.5 Frontend - Catalogue
- [ ] Créer la page Products
- [ ] Créer le composant ProductList
- [ ] Créer le composant ProductForm
- [ ] Créer le service API products
- [ ] Créer le hook useProducts

#### 10.6 Intégration avec Bot
- [ ] Intégrer la recherche produits dans le bot
- [ ] Le bot peut envoyer des fiches produits
- [ ] Templates de messages produits

**Livrables**
- Module catalogue fonctionnel
- Interface de gestion des produits
- Intégration avec le bot

**Critères de validation**
- Les produits sont correctement gérés
- La recherche fonctionne
- Le bot peut présenter les produits

---

## Phase 11 : Système de Réservations (Optionnel)

**Objectif** : Implémenter le module de réservations pour les services.

**Durée estimée** : 5-7 jours

### Tâches

#### 11.1 Base de données - Réservations
- [ ] Définir le modèle `Service`
  - [ ] name
  - [ ] description
  - [ ] duration (minutes)
  - [ ] price
- [ ] Définir le modèle `AvailabilitySlot`
  - [ ] service_id
  - [ ] start_time
  - [ ] end_time
  - [ ] is_available
- [ ] Définir le modèle `Reservation`
  - [ ] customer_id
  - [ ] service_id
  - [ ] slot_id
  - [ ] status (PENDING, CONFIRMED, CANCELLED)
  - [ ] notes
- [ ] Migrations Alembic

#### 11.2 Repository Layer
- [ ] Créer `ServiceRepository`
- [ ] Créer `AvailabilitySlotRepository`
- [ ] Créer `ReservationRepository`
- [ ] Tests unitaires

#### 11.3 Service Layer
- [ ] Créer `ReservationService`
  - [ ] Méthode `create_reservation()`
  - [ ] Méthode `confirm_reservation()`
  - [ ] Méthode `cancel_reservation()`
  - [ ] Méthode `get_available_slots()`
- [ ] Tests unitaires

#### 11.4 Controllers
- [ ] Créer `ReservationsController`
  - [ ] POST `/api/v1/companies/{id}/reservations`
  - [ ] GET `/api/v1/companies/{id}/reservations`
  - [ ] PUT `/api/v1/companies/{id}/reservations/{id}/confirm`
  - [ ] PUT `/api/v1/companies/{id}/reservations/{id}/cancel`
- [ ] Tests d'intégration

#### 11.5 Frontend - Réservations
- [ ] Créer la page Reservations
- [ ] Créer le composant ReservationCalendar
- [ ] Créer le composant ReservationList
- [ ] Créer le service API reservations
- [ ] Créer le hook useReservations

#### 11.6 Intégration avec Bot
- [ ] Le bot peut proposer une réservation
- [ ] Le bot peut vérifier les disponibilités
- [ ] Confirmation automatique

**Livrables**
- Module réservations fonctionnel
- Interface de gestion des réservations
- Intégration avec le bot

**Critères de validation**
- Les créneaux sont correctement gérés
- Les réservations sont créées correctement
- Le bot peut gérer les réservations

---

## Phase 12 : Infrastructure de Production

**Objectif** : Préparer l'application pour le déploiement en production.

**Durée estimée** : 5-7 jours

### Tâches

#### 12.1 Dockerisation
- [ ] Créer Dockerfile pour le backend
- [ ] Créer Dockerfile pour le frontend
- [ ] Optimiser les images (multi-stage build)
- [ ] Créer docker-compose.prod.yml
- [ ] Tests des conteneurs

#### 12.2 Configuration Production
- [ ] Configurer les variables d'environnement production
- [ ] Configurer CORS pour les domaines production
- [ ] Configurer les secrets management
- [ ] Configurer les limites de ressources

#### 12.3 Base de données Production
- [ ] Configurer PostgreSQL pour la production
- [ ] Configurer les backups automatiques
- [ ] Configurer la réplication (read replicas)
- [ ] Optimiser les index
- [ ] Configurer le connection pooling

#### 12.4 Cache et Queue
- [ ] Configurer Redis en production
- [ ] Configurer la persistance Redis
- [ ] Configurer Celery avec supervision
- [ ] Configurer RabbitMQ pour la production

#### 12.5 Monitoring
- [ ] Configurer Prometheus
- [ ] Configurer Grafana dashboards
- [ ] Configurer les alertes
- [ ] Configurer les logs structurés
- [ ] Configurer OpenTelemetry tracing

#### 12.6 Sécurité Production
- [ ] Configurer HTTPS/TLS
- [ ] Configurer le firewall
- [ ] Configurer rate limiting
- [ ] Configurer WAF (Web Application Firewall)
- [ ] Scanner de vulnérabilités

#### 12.7 CI/CD
- [ ] Configurer GitHub Actions ou GitLab CI
- [ ] Pipeline de tests automatiques
- [ ] Pipeline de build
- [ ] Pipeline de déploiement
- [ ] Rollback automatique

#### 12.8 Documentation Déploiement
- [ ] Guide de déploiement
- [ ] Guide de configuration
- [ ] Guide de monitoring
- [ ] Guide de troubleshooting

**Livrables**
- Application dockerisée
- Configuration production prête
- Infrastructure monitoring
- Pipeline CI/CD
- Documentation déploiement

**Critères de validation**
- L'application se déploie sans erreur
- Le monitoring fonctionne
- Les backups sont automatiques
- Le CI/CD fonctionne

---

## Phase 13 : Tests et QA

**Objectif** : Effectuer des tests complets et corriger les bugs.

**Durée estimée** : 5-7 jours

### Tâches

#### 13.1 Tests Unitaires
- [ ] Vérifier la couverture de tests (>80%)
- [ ] Ajouter les tests manquants
- [ ] Corriger les tests échouants

#### 13.2 Tests d'Intégration
- [ ] Tester tous les flux end-to-end
- [ ] Tester l'intégration entre modules
- [ ] Tester les webhooks
- [ ] Tester les événements

#### 13.3 Tests de Performance
- [ ] Tests de charge (Locust ou k6)
- [ ] Optimiser les requêtes lentes
- [ ] Optimiser les index
- [ ] Tests de stress

#### 13.4 Tests de Sécurité
- [ ] Tests de pénétration
- [ ] Vérification RLS multi-tenant
- [ ] Tests d'injection SQL
- [ ] Tests XSS
- [ ] Tests CSRF
- [ ] Scanner de dépendances

#### 13.5 Tests UX
- [ ] Tests utilisateurs
- [ ] Corriger l'ergonomie
- [ ] Optimiser les performances frontend
- [ ] Tests accessibilité

#### 13.6 Bug Fixes
- [ ] Corriger tous les bugs identifiés
- [ ] Re-tester après corrections
- [ ] Documenter les bugs résolus

**Livrables**
- Suite de tests complète
- Rapport de tests
- Bugs corrigés
- Performance optimisée

**Critères de validation**
- Tous les tests passent
- Couverture de tests >80%
- Aucune vulnérabilité critique
- Performance acceptable

---

## Phase 14 : Documentation Finale

**Objectif** : Produire la documentation complète du projet.

**Durée estimée** : 3-4 jours

### Tâches

#### 14.1 Documentation Technique
- [ ] Architecture complète
- [ ] Diagrammes de séquence
- [ ] Diagrammes de composants
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Schéma de base de données
- [ ] Guide des modules

#### 14.2 Documentation Utilisateur
- [ ] Guide Super Admin
- [ ] Guide Admin Entreprise
- [ ] Guide Agent
- [ ] Guide FAQ
- [ ] Vidéos de démonstration (optionnel)

#### 14.3 Documentation Développeur
- [ ] Guide de contribution
- [ ] Guide de développement local
- [ ] Guide des tests
- [ ] Guide de déploiement
- [ ] Code comments

#### 14.4 Documentation Opérationnelle
- [ ] Guide de monitoring
- [ ] Guide de backup
- [ ] Guide de scaling
- [ ] Guide de troubleshooting
- [ ] Runbooks

**Livrables**
- Documentation technique complète
- Documentation utilisateur complète
- Documentation développeur complète
- Documentation opérationnelle

**Critères de validation**
- Toute la documentation est à jour
- Les exemples fonctionnent
- Les diagrammes sont clairs

---

## Phase 14 : Livraison et Formation

**Objectif** : Livrer le projet et former les utilisateurs.

**Durée estimée** : 2-3 jours

### Tâches

#### 14.1 Livraison
- [ ] Déploiement en production
- [ ] Vérification post-déploiement
- [ ] Migration des données (si nécessaire)
- [ ] Configuration initiale

#### 14.2 Formation
- [ ] Formation Super Admin
- [ ] Formation Admin Entreprise
- [ ] Formation Agents
- [ ] Session Q&A

#### 14.3 Support Initial
- [ ] Période de support (2 semaines)
- [ ] Corrections bugs mineurs
- [ ] Ajustements UX

#### 14.4 Clôture
- [ ] Documenter les leçons apprises
- [ ] Planifier les améliorations futures
- [ ] Handoff officiel

**Livrables**
- Application en production
- Utilisateurs formés
- Support initial
- Rapport de clôture

**Critères de validation**
- L'application fonctionne en production
- Les utilisateurs sont autonomes
- Les bugs critiques sont résolus

---

## Ordre Recommandé des Phases

### MVP Minimum (Phases 1-4)
1. Phase 0 : Initialisation
2. Phase 1 : Authentification et Multi-tenancy
3. Phase 2 : Abstraction Channel et WhatsApp
4. Phase 3 : Clients et Conversations
5. Phase 4 : Bot Engine Natif

### MVP avec ML (Phases 5-7)
6. Phase 5 : Base de Connaissances
7. Phase 6 : Infrastructure ML
8. Phase 7 : ML Engine - RAG et LLM

### Application Complète (Phases 8-11)
9. Phase 8 : Analytics et Dashboard
10. Phase 9 : Notifications
11. Phase 10 : Catalogue Produits (optionnel)
12. Phase 11 : Système de Réservations (optionnel)

### Production (Phases 12-14)
13. Phase 12 : Infrastructure de Production
14. Phase 13 : Tests et QA
15. Phase 14 : Documentation Finale
16. Phase 15 : Livraison et Formation

---

## Notes Importantes

1. **Indépendance des phases** : Chaque phase doit pouvoir être validée indépendamment avant de passer à la suivante.
2. **Tests obligatoires** : Aucune phase n'est considérée terminée sans tests validés.
3. **Documentation continue** : La documentation doit être mise à jour à chaque phase.
4. **Flexibilité** : L'ordre peut être ajusté selon les priorités du business.
5. **Backlog** : Les fonctionnalités optionnelles (Catalogue, Réservations) peuvent être déplacées dans un backlog futur.

---

## Estimation Totale

- **MVP Minimum** : 19-27 jours
- **MVP avec ML** : 33-47 jours
- **Application Complète** : 43-64 jours
- **Production Ready** : 58-85 jours

*Note : Ces estimations sont basées sur un développeur senior travaillant à temps plein. Ajuster selon l'équipe disponible.*
