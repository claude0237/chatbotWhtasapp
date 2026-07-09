# Frontend — WhatsApp SaaS Platform

Interface web construite avec **Next.js 14** (App Router), **React 18**, **Tailwind CSS** et **TypeScript**.

---

## Démarrage Rapide

```bash
npm install

# Créer frontend/.env.local :
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

npm run dev
```

Accès : http://localhost:3000

---

## Structure

```
src/
├── app/                    # Pages Next.js (App Router)
│   ├── layout.tsx          # Layout racine (AuthProvider, polices)
│   ├── providers.tsx       # Providers React globaux
│   ├── page.tsx            # Redirection vers /dashboard
│   ├── auth/login/         # Page de connexion
│   ├── dashboard/          # Tableau de bord
│   ├── conversations/      # Conversations WhatsApp
│   ├── customers/          # Gestion des contacts
│   ├── bot/                # Configuration chatbot + simulation
│   ├── catalogue/          # Produits et catégories
│   ├── knowledge/          # Base de connaissances
│   ├── whatsapp/           # Connexion WhatsApp + messages
│   ├── companies/          # Panneau super admin
│   ├── users/              # Gestion utilisateurs
│   ├── documents/          # Upload documents ML
│   ├── ml-config/          # Configuration fournisseur IA
│   └── ml-performance/     # Performance pipeline ML
├── components/             # Composants réutilisables
│   ├── AppLayout.tsx       # Sidebar + navigation principale
│   ├── AuthenticatedLayout.tsx
│   ├── ProtectedRoute.tsx
│   ├── notifications/      # Cloche + liste notifications
│   ├── products/           # Formulaire + liste produits
│   └── reservations/       # Calendrier + liste réservations
├── contexts/
│   └── AuthContext.tsx     # Contexte Auth (user, login, logout)
├── hooks/                  # Hooks React personnalisés
│   ├── useAuth.ts          # Accès au contexte auth
│   ├── useHashTab.ts       # Tabs persistés dans l'URL (#hash)
│   ├── useConversations.ts
│   ├── useCustomers.ts
│   ├── useBotConfig.ts
│   ├── useKnowledge.ts
│   ├── useProducts.ts
│   ├── useML.ts
│   ├── useAnalytics.ts
│   └── useNotifications.ts
├── services/               # Couche API (appels axios)
│   ├── bot.ts
│   ├── conversations.ts
│   ├── customers.ts
│   ├── knowledge.ts
│   ├── ml.ts / mlService.ts
│   ├── products.ts
│   ├── reservations.ts
│   └── notifications.ts
└── lib/
    ├── api.ts              # Instance axios configurée
    └── utils.ts            # Utilitaires (cn, formatDate…)
```

---

## Configuration Environnement

Créer `frontend/.env.local` :

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

> En production, remplacer par l'URL publique du backend.

---

## `lib/api.ts` — Client HTTP

Instance **axios** centrale utilisée par toutes les pages et hooks.

**Comportement automatique :**
- Lit `localStorage.access_token` et l'injecte dans chaque requête (`Authorization: Bearer …`)
- Ajoute un `/` final à toutes les URLs (compatibilité FastAPI `redirect_slashes=False`)
- Sur erreur **401** : tente un refresh token automatique via `POST /auth/refresh/`
- Si le refresh échoue → vide le localStorage et redirige vers `/auth/login`

```typescript
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});
```

---

## `contexts/AuthContext.tsx` — Authentification

Context React qui expose dans toute l'app :

| Valeur | Type | Description |
|--------|------|-------------|
| `user` | `User \| null` | Utilisateur connecté (id, email, role, company_id) |
| `loading` | `boolean` | True pendant la vérification du token au démarrage |
| `login(email, password)` | `async` | POST /auth/login → stocke les tokens |
| `logout()` | `void` | Vide localStorage, remet user à null |
| `refreshAccessToken()` | `async` | Renouvelle le token manuellement |

**Au démarrage** : si un `access_token` existe en localStorage, `GET /auth/me` est appelé pour hydrater `user`. Sinon l'utilisateur reste `null` et sera redirigé vers login.

---

## `hooks/useHashTab.ts` — Navigation par onglets

Hook générique qui **persiste l'onglet actif dans l'URL** (`#hash`), permettant de revenir sur le bon onglet après un refresh.

```typescript
const [activeTab, setActiveTab] = useHashTab<'config' | 'scenarios' | 'keywords'>('config');
// URL : /bot#scenarios → activeTab = 'scenarios'
```

Utilisé dans : `bot/page.tsx`, `whatsapp/page.tsx`, `knowledge/page.tsx`, `catalogue/page.tsx`

---

## Pages

### `app/auth/login/page.tsx`
Formulaire de connexion email/mot de passe. Appelle `useAuth().login()`. Redirige vers `/dashboard` si succès.

---

### `app/dashboard/page.tsx`
Tableau de bord avec métriques clés :
- Conversations ouvertes / en attente
- Messages des 7 derniers jours
- Taux de résolution bot
- Nouveaux contacts

Appelle `GET /analytics/conversations`, `/analytics/messages`, `/analytics/customers`, `/analytics/bot`.

---

### `app/conversations/page.tsx`
Liste des conversations avec filtres par statut (`OPEN`, `WAITING`, `BOT`, `CLOSED`).

**Polling automatique** toutes les 5 secondes sur les conversations actives.

Fonctionnalités :
- Voir les messages d'une conversation
- Répondre en tant qu'agent
- Assigner à un collègue
- Fermer la conversation
- Voir l'état bot actif pour un contact

---

### `app/customers/page.tsx`
Gestion des contacts WhatsApp de l'entreprise.

- Recherche par nom ou numéro de téléphone
- Création / modification / suppression
- Affichage des tags et notes

---

### `app/bot/page.tsx`
Page centrale du chatbot — 4 onglets :

| Onglet | Description |
|--------|-------------|
| `⚙️ Configuration` | Messages d'accueil, fermeture, inconnu, timeout follow-up |
| `🎭 Scénarios` | Créer/modifier des scénarios avec leurs steps (text, choice, condition, catalogue, handoff) |
| `🔑 Mots-clés` | Réponses directes à des mots-clés |
| `🧪 Simulation` | Simuler une conversation avec le bot en local (sans WhatsApp) |

**Simulation locale (`simulateSend`)** : implémente en JS le même moteur que le backend (`BotEngine`) pour tester sans déployer. Gère tous les types de steps, l'interpolation de variables, et l'affichage du catalogue via l'API produits.

---

### `app/catalogue/page.tsx`
Gestion du catalogue produits — 2 onglets :

| Onglet | Description |
|--------|-------------|
| `📦 Produits` | CRUD produits (nom, prix, devise, stock, catégorie, description) |
| `🗂️ Catégories` | CRUD catégories de produits |

Les produits sont utilisés par le bot via `{catalogue:NomCategorie}` dans les messages.

---

### `app/knowledge/page.tsx`
Base de connaissances — 2 onglets :

| Onglet | Description |
|--------|-------------|
| `📄 Articles` | CRUD articles (titre, contenu, catégorie) |
| `🗂️ Catégories` | CRUD catégories |

Les articles sont indexés par le pipeline ML pour la recherche sémantique (RAG).

---

### `app/whatsapp/page.tsx`
Configuration WhatsApp — 3 onglets :

| Onglet | Description |
|--------|-------------|
| `🔗 Connexion` | Saisir Phone Number ID, Access Token, WABA ID |
| `💬 Messages` | Historique de tous les messages WhatsApp |
| `📋 Templates` | Templates Meta approuvés |

**Super Admin** voit en plus un panneau global avec l'URL du webhook et le verify token à configurer sur Meta for Developers.

---

### `app/companies/page.tsx`
Panneau **SUPER_ADMIN** uniquement.

- Liste toutes les entreprises
- Créer / modifier / supprimer une entreprise
- Activer / désactiver / suspendre

---

### `app/users/page.tsx`
Gestion des utilisateurs de l'entreprise courante.

- Liste avec rôles et statuts
- Créer un utilisateur (mot de passe obligatoire)
- Modifier un utilisateur (mot de passe optionnel — laisser vide = inchangé)
- Le **SUPER_ADMIN** voit en plus un sélecteur d'entreprise

---

### `app/documents/page.tsx`
Upload de documents (PDF, Word, CSV) pour alimenter le pipeline ML/RAG.

Appelle `POST /upload/` puis `POST /ml/ingest` pour déclencher l'ingestion.

---

### `app/ml-config/page.tsx`
Configuration du fournisseur IA : OpenAI / Anthropic / Ollama, choix du modèle, température, seuil de confiance.

---

### `app/ml-performance/page.tsx`
Métriques du pipeline ML : nombre de requêtes, taux de succès, temps de réponse moyen, distribution de confiance.

---

## `components/AppLayout.tsx` — Navigation

Sidebar responsive avec navigation adaptée au rôle :

| Rôle | Pages accessibles |
|------|------------------|
| `SUPER_ADMIN` | Dashboard, Entreprises, Utilisateurs, Webhook Meta |
| `COMPANY_ADMIN` | Dashboard, Conversations, Clients, Chatbot, Catalogue, Connaissances, Équipe, WhatsApp |
| `MANAGER` / `AGENT` | Dashboard, Conversations, Clients |

**Badge** sur Conversations : indique le nombre de conversations OPEN + WAITING, rafraîchi toutes les 30 secondes.

---

## Commandes

```bash
npm run dev          # Serveur de développement (http://localhost:3000)
npm run build        # Build de production
npm start            # Serveur de production
npm run lint         # ESLint
```
