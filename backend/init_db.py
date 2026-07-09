"""
Script d'initialisation de la base de données.

Crée :
  1. L'entreprise système  (slug: system)
  2. Le super administrateur
  3. Une entreprise de démonstration  (slug: demo)     [optionnel]
  4. Un administrateur pour la démo                    [optionnel]

Usage :
  # Initialisation minimale (system + superadmin uniquement)
  python init_db.py

  # Avec entreprise de démonstration
  python init_db.py --demo

  # Personnaliser les identifiants
  python init_db.py --email admin@monsite.com --password MonMotDePasse123

  # Simulation — aucune écriture en base
  python init_db.py --dry-run
  python init_db.py --dry-run --demo
"""

import asyncio
import argparse
import sys
from datetime import datetime
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.users.models import User, UserRoleEnum
from app.users.repositories import UserRepository
from app.companies.models import Company, CompanySettings
from app.companies.repositories import CompanyRepository, CompanySettingsRepository

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return pwd_context.hash(password)


async def _get_or_create_company(
    db,
    slug: str,
    name: str,
    description: str,
    email: str | None = None,
    timezone: str = "UTC",
    language: str = "fr",
    currency: str = "XAF",
) -> Company:
    repo = CompanyRepository(db)
    company = await repo.get_by_slug(slug)
    if company:
        print(f"  [OK] Entreprise existante  : {name!r}  (id={company.id})")
        return company

    company = Company(
        id=uuid4(),
        name=name,
        slug=slug,
        description=description,
        email=email,
        is_active=True,
        is_suspended=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    company = await repo.create(company)

    # Paramètres de l'entreprise
    settings_repo = CompanySettingsRepository(db)
    existing_settings = await settings_repo.get_by_company_id(company.id)
    if not existing_settings:
        settings = CompanySettings(
            id=uuid4(),
            company_id=company.id,
            timezone=timezone,
            language=language,
            currency=currency,
            theme_color="#25D366",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await settings_repo.create(settings)

    print(f"  [CRÉE] Entreprise           : {name!r}  (id={company.id})")
    return company


async def _get_or_create_user(
    db,
    company_id,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRoleEnum,
) -> User:
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if user:
        # Mise à jour du mot de passe et du rôle si l'utilisateur existe déjà
        user.password_hash = _hash(password)
        user.role = role
        user.is_active = True
        user.company_id = company_id
        await repo.update(user)
        print(f"  [OK] Utilisateur existant  : {email}  (id={user.id})")
        return user

    user = User(
        id=uuid4(),
        company_id=company_id,
        email=email,
        password_hash=_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user = await repo.create(user)
    print(f"  [CRÉE] Utilisateur          : {email}  (id={user.id})")
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Vérification connexion BDD
# ─────────────────────────────────────────────────────────────────────────────

async def check_db_connection() -> bool:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"\n  [ERREUR] Impossible de se connecter à la base de données :\n  {e}")
        print("\n  Vérifiez DATABASE_URL dans backend/.env et que PostgreSQL est démarré.\n")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Dry-run (lecture seule)
# ─────────────────────────────────────────────────────────────────────────────

async def _dry_check_company(db, slug: str, name: str) -> None:
    repo = CompanyRepository(db)
    company = await repo.get_by_slug(slug)
    if company:
        print(f"  [EXISTE]  Entreprise {name!r} (slug={slug!r}, id={company.id})")
        settings_repo = CompanySettingsRepository(db)
        settings = await settings_repo.get_by_company_id(company.id)
        if settings:
            print(f"            ↳ CompanySettings : timezone={settings.timezone}, "
                  f"language={settings.language}, currency={settings.currency}")
        else:
            print(f"            ↳ CompanySettings : ABSENTS — seraient créés")
    else:
        print(f"  [CRÉER]   Entreprise {name!r} (slug={slug!r}) — n'existe pas encore")
        print(f"            ↳ CompanySettings seraient créés")


async def _dry_check_user(db, email: str, role: UserRoleEnum) -> None:
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if user:
        role_change = " — rôle inchangé" if user.role == role else f" — rôle mis à jour : {user.role} → {role}"
        active_label = "actif" if user.is_active else "INACTIF — serait réactivé"
        print(f"  [EXISTE]  Utilisateur {email!r} (id={user.id}, {active_label}){role_change}")
        print(f"            ↳ Mot de passe serait mis à jour")
    else:
        print(f"  [CRÉER]   Utilisateur {email!r} (rôle={role.value}) — n'existe pas encore")


async def dry_run(
    superadmin_email: str,
    superadmin_password: str,
    with_demo: bool,
    demo_email: str,
    demo_password: str,
) -> None:
    print("\n" + "═" * 60)
    print("  DRY-RUN — simulation (aucune écriture en base)")
    print("═" * 60)

    if not await check_db_connection():
        sys.exit(1)

    async with AsyncSessionLocal() as db:

        print("\n▶ Entreprise système")
        await _dry_check_company(db, slug="system", name="System")

        print("\n▶ Super administrateur")
        await _dry_check_user(db, email=superadmin_email, role=UserRoleEnum.SUPER_ADMIN)

        if with_demo:
            print("\n▶ Entreprise de démonstration")
            await _dry_check_company(db, slug="demo", name="Entreprise Démo")

            print("\n▶ Administrateur démo")
            await _dry_check_user(db, email=demo_email, role=UserRoleEnum.COMPANY_ADMIN)

    print("\n" + "═" * 60)
    print("  Fin du dry-run — rien n'a été écrit en base.")
    print("  Relancez sans --dry-run pour appliquer les changements.")
    print("═" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation principale
# ─────────────────────────────────────────────────────────────────────────────

async def init(
    superadmin_email: str,
    superadmin_password: str,
    with_demo: bool,
    demo_email: str,
    demo_password: str,
):
    print("\n" + "═" * 60)
    print("  Initialisation de la base de données")
    print("═" * 60)

    if not await check_db_connection():
        sys.exit(1)


    async with AsyncSessionLocal() as db:

        # ── 1. Entreprise système ────────────────────────────────────────────
        print("\n▶ Entreprise système")
        system_company = await _get_or_create_company(
            db,
            slug="system",
            name="System",
            description="Entreprise interne — réservée au super administrateur.",
            timezone="UTC",
            language="fr",
            currency="USD",
        )

        # ── 2. Super administrateur ──────────────────────────────────────────
        print("\n▶ Super administrateur")
        superadmin = await _get_or_create_user(
            db,
            company_id=system_company.id,
            email=superadmin_email,
            password=superadmin_password,
            first_name="Super",
            last_name="Admin",
            role=UserRoleEnum.SUPER_ADMIN,
        )

        # ── 3. Entreprise de démonstration (optionnel) ───────────────────────
        if with_demo:
            print("\n▶ Entreprise de démonstration")
            demo_company = await _get_or_create_company(
                db,
                slug="demo",
                name="Entreprise Démo",
                description="Entreprise de démonstration — peut être supprimée.",
                email="contact@demo.local",
                timezone="Africa/Douala",
                language="fr",
                currency="XAF",
            )

            print("\n▶ Administrateur démo")
            await _get_or_create_user(
                db,
                company_id=demo_company.id,
                email=demo_email,
                password=demo_password,
                first_name="Admin",
                last_name="Démo",
                role=UserRoleEnum.COMPANY_ADMIN,
            )

    # ── Récapitulatif ────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  Initialisation terminée ✅")
    print("═" * 60)
    print(f"\n  Super Admin")
    print(f"    Email    : {superadmin_email}")
    print(f"    Mot de passe : {superadmin_password}")
    print(f"    URL      : http://localhost:3000/auth/login")

    if with_demo:
        print(f"\n  Admin Démo")
        print(f"    Email    : {demo_email}")
        print(f"    Mot de passe : {demo_password}")

    print("\n  ⚠️  Changez les mots de passe en production !\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialise la base de données avec les données de démarrage."
    )
    parser.add_argument(
        "--email",
        default="superadmin@system.com",
        help="Email du super administrateur (défaut: superadmin@system.com)",
    )
    parser.add_argument(
        "--password",
        default="superadmin123",
        help="Mot de passe du super administrateur (défaut: superadmin123)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Créer aussi une entreprise et un admin de démonstration",
    )
    parser.add_argument(
        "--demo-email",
        default="admin@demo.local",
        help="Email de l'admin démo (défaut: admin@demo.local)",
    )
    parser.add_argument(
        "--demo-password",
        default="demo1234",
        help="Mot de passe de l'admin démo (défaut: demo1234)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulation : vérifie ce qui existe et affiche ce qui serait créé, sans rien écrire",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.dry_run:
        asyncio.run(
            dry_run(
                superadmin_email=args.email,
                superadmin_password=args.password,
                with_demo=args.demo,
                demo_email=args.demo_email,
                demo_password=args.demo_password,
            )
        )
    else:
        asyncio.run(
            init(
                superadmin_email=args.email,
                superadmin_password=args.password,
                with_demo=args.demo,
                demo_email=args.demo_email,
                demo_password=args.demo_password,
            )
        )
