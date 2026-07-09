# Guide Agent

## Rôle

L'**Agent** gère les conversations avec les clients, répond aux messages et escalade si nécessaire.

## Interface Conversations

### Vue principale
- **Liste des conversations** à gauche (triées par activité récente)
- **Fil de discussion** au centre
- **Infos client** à droite

### Statuts des conversations
- 🟡 **En attente** : nouveau message, non assigné
- 🟢 **Actif** : assigné à un agent
- ⚫ **Fermé** : conversation terminée

### Prendre en charge une conversation
1. Cliquer sur une conversation **En attente**
2. Cliquer **M'assigner**
3. Répondre au client

### Transférer une conversation
1. Bouton **Transférer** → sélectionner un autre agent
2. Ajouter une note interne (optionnel)
3. Confirmer

### Fermer une conversation
- Bouton **Fermer** → confirmer
- La conversation passe en statut **Fermé**

## Répondre aux Messages

1. Zone de texte en bas → taper le message
2. Utiliser les **Réponses rapides** (icône ⚡) pour les réponses fréquentes
3. Joindre une image/fichier via l'icône 📎
4. Appuyer sur **Entrée** ou cliquer **Envoyer**

## Notifications

Le badge cloche 🔔 indique les nouvelles notifications :
- Nouveau message dans une conversation assignée
- Mention par un collègue (`@votre_nom`)
- Nouvelle conversation assignée

Cliquer sur **Tout marquer comme lu** pour effacer le badge.

## Profil

**Icône profil** (en haut à droite) → **Mon profil** :
- Modifier nom, avatar
- Changer mot de passe
- Configurer les préférences de notification

## FAQ Agent

**Q : Le bot n'a pas compris le client, que faire ?**
Le bot passe automatiquement en mode agent si il ne trouve pas de réponse. La conversation apparaît en **En attente**.

**Q : Comment ajouter une note interne ?**
Dans la conversation → icône 📝 → la note est visible uniquement par l'équipe.

**Q : Puis-je voir l'historique d'un client ?**
Oui : panneau droit → onglet **Historique** → toutes les conversations passées.
