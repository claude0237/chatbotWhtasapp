# Guide Admin Entreprise

## Rôle

L'**Admin** gère son entreprise : configuration du bot, agents, intégrations, analytics.

## Configuration du Bot

### Activer le bot
1. **Bot** → **Configuration** → toggle **Activer le bot**
2. Choisir le type : **Natif** (règles), **ML** (IA), ou **Hybride**

### Messages personnalisés
- **Message de bienvenue** : affiché à chaque nouvelle conversation
- **Message d'absence** : affiché en dehors des heures d'ouverture
- **Message inconnu** : affiché si le bot ne comprend pas

### Configurer les mots-clés
1. **Bot** → **Mots-clés** → **Ajouter**
2. Saisir le mot-clé déclencheur (ex: "prix")
3. Saisir la réponse automatique
4. Sauvegarder

### Configurer les scénarios
1. **Bot** → **Scénarios** → **Nouveau scénario**
2. Définir le mot-clé déclencheur
3. Ajouter des étapes (messages, questions, actions)
4. Activer le scénario

## Base de Connaissances

1. **Connaissances** → **Ajouter une entrée**
2. Titre + contenu (le bot utilisera ce contenu pour répondre)
3. Pour les fichiers : **Importer** (PDF, DOCX, TXT)

## Gestion des Agents

1. **Équipe** → **Inviter un agent**
2. Saisir l'email → **Envoyer l'invitation**
3. L'agent reçoit un email avec un lien d'activation

### Désactiver un agent
**Équipe** → agent → toggle **Actif**

## Catalogue Produits

1. **Produits** → **Nouveau produit**
2. Remplir : Nom, Description, Prix, Stock, Catégorie
3. Ajouter des images (URL)
4. **Créer**

Le bot présentera automatiquement les produits pertinents.

## Réservations

1. **Réservations** → **Services** → **Nouveau service**
2. Nom, Durée (minutes), Prix (optionnel)
3. Ajouter des créneaux dans **Disponibilités**

## Analytics

- **Dashboard** : vue synthétique (conversations, temps de réponse, satisfaction)
- **Rapports** : exporter CSV par période
- **Performance agents** : voir les stats individuelles

## Notifications

**Paramètres** → **Notifications** pour activer/désactiver chaque type :
- Nouvelle conversation
- Mention
- Réservation
- Paiement
