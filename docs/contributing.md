# Guide de Contribution

## Prérequis

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- Git

## Installation locale

### 1. Cloner le dépôt

```bash
git clone https://github.com/your-org/chatbot.git
cd chatbot
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env
# Éditer .env avec vos valeurs locales
```

Démarrer PostgreSQL et Redis :

```bash
docker compose up -d db redis
```

Appliquer les migrations :

```bash
alembic upgrade head
```

Lancer le serveur :

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

L'application est accessible sur `http://localhost:3000`.

## Workflow Git

```
main          ← Production stable
  └── develop ← Intégration
        ├── feature/nom-feature
        ├── fix/nom-bug
        └── chore/nom-tache
```

### Créer une branche

```bash
git checkout develop
git pull
git checkout -b feature/ma-feature
```

### Soumettre une PR

1. Pousser la branche : `git push origin feature/ma-feature`
2. Ouvrir une Pull Request vers `develop`
3. Remplir le template de PR
4. Attendre la revue de code

### Conventions de commit (Conventional Commits)

```
feat: ajouter la recherche de produits dans le bot
fix: corriger la validation du token WhatsApp
docs: mettre à jour le guide de déploiement
test: ajouter tests unitaires pour ReservationService
chore: mettre à jour les dépendances
refactor: simplifier la logique de NativeBotEngine
```

## Standards de Code

### Python
- Formatter : **ruff format**
- Linter : **ruff check** + **mypy**
- Docstrings : style Google

```bash
ruff format app/
ruff check app/
mypy app/ --ignore-missing-imports
```

### TypeScript/React
- Formatter : **Prettier**
- Linter : **ESLint**

```bash
npm run lint
npm run format
```

## Tests

### Backend

```bash
pytest                    # Tous les tests
pytest app/notifications/ # Module spécifique
pytest -k "test_create"   # Par nom
pytest --cov=app          # Avec couverture
```

Couverture minimale requise : **80%**

### Frontend

```bash
npm test                  # Mode watch
npm test -- --coverage    # Avec couverture
```

## Structure des modules backend

Chaque module suit la même structure :

```
app/mon_module/
├── __init__.py
├── models/
│   └── __init__.py      # SQLAlchemy models
├── repositories/
│   └── __init__.py      # Data access layer
├── services/
│   └── __init__.py      # Business logic
├── controllers/
│   └── __init__.py      # FastAPI router
└── tests/
    ├── __init__.py
    └── test_*.py
```

## API Documentation

FastAPI génère automatiquement la documentation :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`
- OpenAPI JSON : `http://localhost:8000/openapi.json`
