# Guide Super Admin

## Rôle et Responsabilités

Le **Super Admin** a accès à toutes les fonctionnalités de la plateforme. Il gère les entreprises clientes, les abonnements et la configuration globale.

## Connexion

1. Accéder à `https://yourdomain.com/login`
2. Saisir les identifiants Super Admin
3. Valider le 2FA si activé

## Gestion des Entreprises

### Créer une entreprise
1. Menu **Entreprises** → **Nouvelle entreprise**
2. Remplir : Nom, Email, Plan d'abonnement
3. Cliquer **Créer**
4. L'entreprise reçoit un email d'activation

### Suspendre / Activer une entreprise
- **Tableau des entreprises** → colonne **Statut** → toggle

### Modifier un abonnement
- **Entreprises** → cliquer sur l'entreprise → onglet **Abonnement**
- Sélectionner le nouveau plan → **Sauvegarder**

## Tableau de Bord Global

Le tableau de bord Super Admin affiche :
- Nombre total d'entreprises actives
- Conversations totales (toutes entreprises)
- Revenus mensuels
- Utilisation ML par entreprise

## Gestion des Utilisateurs

Super Admin peut voir et modifier tous les utilisateurs :
1. **Utilisateurs** → filtrer par entreprise
2. Actions disponibles : Activer, Désactiver, Changer le rôle, Réinitialiser le mot de passe

## API et Webhooks

Configurer les clés API globales dans **Paramètres** → **Intégrations** :
- WhatsApp Business API Token
- Clés OpenAI / Anthropic
- Clé SMTP

## Logs d'Audit

Tous les accès et modifications sont tracés :
1. **Audit** → filtrer par entreprise, utilisateur, action, date
2. Exporter en CSV si nécessaire
