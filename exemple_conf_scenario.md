# SICG — Configuration Complète du Chatbot WhatsApp

## Entreprise

| Champ | Valeur |
|---|---|
| Nom | SICG (Société Industrielle de Commerce Général) |
| Secteur | Fabrication mousses, matelas, éponges, transformation tôles |
| Adresse | Zone Industrielle de Bonabéri, Douala, Cameroun |
| Téléphone | +1 555-955-0644 |
| Horaires | Lun-Ven 7h-17h, Sam 7h-12h |

---

## 1. Configuration Bot

| Champ | Valeur |
|---|---|
| Nom bot | SICG Bot |
| Langue | Français |
| Fuseau | Africa/Douala |

### Horaires d'ouverture (business_hours)

Le champ `business_hours` est un JSON stocké dans la configuration du bot.
Il définit les jours et heures d'ouverture. Hors de ces plages, le bot envoie automatiquement le **message d'absence** (`away_message`) au lieu de traiter les messages via le moteur de scénarios.

**Format :**
```json
{
  "monday":    {"open": "07:00", "close": "17:00"},
  "tuesday":   {"open": "07:00", "close": "17:00"},
  "wednesday": {"open": "07:00", "close": "17:00"},
  "thursday":  {"open": "07:00", "close": "17:00"},
  "friday":    {"open": "07:00", "close": "17:00"},
  "saturday":  {"open": "07:00", "close": "12:00"},
  "sunday":    null
}
```

**Règles :**
- Chaque clé est un jour en anglais minuscule (`monday` à `sunday`)
- Valeur `{"open": "HH:MM", "close": "HH:MM"}` = ouvert ce jour aux heures indiquées
- Valeur `null` ou clé absente = fermé ce jour
- Si `business_hours` est `null` ou vide → bot actif 24h/24
- Le fuseau horaire (`timezone`) de la config est utilisé pour calculer l'heure locale
- L'heure est comparée en format 24h (ex: `"17:00"` = 17h00)

**Comportement :**
1. Nouveau contact hors horaires → envoie `away_message` (pas le `welcome_message`)
2. Contact existant hors horaires → envoie `away_message` (pas de traitement scénario)
3. Contact pendant les horaires → comportement normal (welcome + scénarios)

**Configuration via l'UI :**
- Page Bot → Configuration → Modifier → Section "🕐 Horaires d'ouverture"
- Cocher/décocher chaque jour
- Définir les heures avec les champs time

### Message de bienvenue
```
Bienvenue chez *SICG* (Société Industrielle de Commerce Général) ! 🏭

Nous sommes spécialisés dans la fabrication de mousses, matelas, éponges et la transformation de tôles.

📍 Bonabéri, Zone Industrielle — Douala
📞 +1 555-955-0644
🕐 Lun-Ven 7h-17h | Sam 7h-12h

Tapez *MENU* pour découvrir nos services.
```

### Message inconnu (fallback)
```
Désolé, je n'ai pas compris votre demande. Tapez *MENU* pour voir les options disponibles, ou *AGENT* pour parler à un conseiller.
```

### Message d'absence (hors horaires)
```
Nos bureaux sont actuellement fermés. 🕐

Horaires : Lun-Ven 7h00-17h00 | Sam 7h00-12h00

Nous vous répondrons dès la reprise. En attendant, tapez *CATALOGUE* pour consulter nos produits.
```

### Message de fermeture
```
Merci d'avoir contacté SICG ! À bientôt 🙏
```

---

## 2. Catégories de Produits

### Catégorie 1 : Matelas
| Produit | Prix | Devise | Stock | Description |
|---|---|---|---|---|
| Matelas 1 place 190x90 | 25000 | XAF | 120 | Matelas mousse HD densité 25, épaisseur 15cm. Confort ferme, idéal chambres d'enfants. |
| Matelas 2 places 190x140 | 45000 | XAF | 85 | Matelas mousse HD densité 28, épaisseur 18cm. Confort médium, housse lavable incluse. |
| Matelas King Size 200x180 | 75000 | XAF | 40 | Matelas mousse premium densité 30, épaisseur 22cm. Confort supérieur, housse matelassée. |
| Matelas Orthopédique 190x140 | 95000 | XAF | 25 | Mousse haute résilience D35 + couche mémoire de forme. Soutien optimal du dos. |
| Matelas Bébé 120x60 | 12000 | XAF | 60 | Mousse hypoallergénique densité 20, épaisseur 10cm. Certifié sans substances nocives. |

### Catégorie 2 : Mousses
| Produit | Prix | Devise | Stock | Description |
|---|---|---|---|---|
| Mousse HD D25 (par m²) | 8000 | XAF | 500 | Mousse haute densité 25 kg/m³, épaisseur 10cm. Usage : assises, coussins. |
| Mousse HD D30 (par m²) | 12000 | XAF | 300 | Mousse haute densité 30 kg/m³, épaisseur 10cm. Usage : matelas, canapés haut de gamme. |
| Mousse rebondée (par m²) | 5000 | XAF | 800 | Mousse reconstituée économique. Usage : sous-couche, isolation, rembourrage basique. |
| Mousse D35 Premium (par m²) | 18000 | XAF | 150 | Mousse ultra-dense pour usage professionnel. Durabilité supérieure. |
| Mousse découpe sur-mesure | 0 | XAF | 999 | Découpe à vos dimensions exactes. Prix sur devis. Contactez un conseiller. |

### Catégorie 3 : Éponges
| Produit | Prix | Devise | Stock | Description |
|---|---|---|---|---|
| Éponge ménage standard | 500 | XAF | 5000 | Éponge double face (mousse + grattant). Format classique cuisine/salle de bain. |
| Éponge grattante pro | 800 | XAF | 3000 | Face grattante renforcée pour nettoyage intensif. Restaurants, hôtels, industries. |
| Lot 10 éponges ménage | 4000 | XAF | 1200 | Pack économique de 10 éponges standard. Idéal familles et petits commerces. |
| Éponge industrielle grande | 2500 | XAF | 800 | Format XL (20x12cm) pour nettoyage grandes surfaces, véhicules, équipements. |
| Éponge naturelle bain | 1500 | XAF | 400 | Éponge douce pour soins corporels. Texture fine, longue durée. |

### Catégorie 4 : Tôles
| Produit | Prix | Devise | Stock | Description |
|---|---|---|---|---|
| Tôle BG 28 (feuille 2m) | 4500 | XAF | 2000 | Tôle bac galvanisée calibre 28. Couverture économique, durée de vie 10-15 ans. |
| Tôle BG 32 (feuille 2m) | 5500 | XAF | 1500 | Tôle bac galvanisée calibre 32, plus épaisse. Résistance accrue aux intempéries. |
| Tôle nervurée (feuille 2m) | 7000 | XAF | 1000 | Profil nervuré pour grandes portées. Idéal hangars, entrepôts, bâtiments industriels. |
| Tôle aluzinc (feuille 2m) | 9500 | XAF | 600 | Revêtement aluminium-zinc anti-corrosion. Durée de vie 25+ ans, aspect moderne. |
| Faîtière galvanisée | 3000 | XAF | 800 | Pièce de finition pour jonction de toiture. Longueur 1m, galvanisée. |

### Catégorie 5 : Habillages
| Produit | Prix | Devise | Stock | Description |
|---|---|---|---|---|
| Housse matelas 1 place | 5000 | XAF | 200 | Housse zippée lavable en tissu coton-polyester. Protection anti-acariens. |
| Housse matelas 2 places | 8000 | XAF | 150 | Housse zippée grande taille, tissu épais résistant. Lavable en machine. |
| Tissu d'ameublement (par m) | 3500 | XAF | 1000 | Tissu décoratif pour canapés, fauteuils. Choix de coloris sur place. |
| Rembourrage coussin (pièce) | 2000 | XAF | 500 | Coussin pré-rembourré mousse souple 40x40cm. Pour canapés et décoration. |
| Protège-matelas imperméable | 6000 | XAF | 180 | Protection anti-liquide, surface coton respirant. Taille 2 places. |

---

## 3. Mots-clés (Réponses directes)

### MENU
```
📋 *Menu SICG :*

1️⃣ Tapez *CATALOGUE* — Voir nos produits
2️⃣ Tapez *COMMANDER* — Passer commande
3️⃣ Tapez *DEVIS* — Demander un devis personnalisé
4️⃣ Tapez *LIVRAISON* — Infos livraison
5️⃣ Tapez *HORAIRES* — Nos horaires
6️⃣ Tapez *LOCALISATION* — Notre adresse
7️⃣ Tapez *PROMO* — Promotions en cours
8️⃣ Tapez *AGENT* — Parler à un conseiller
9️⃣ Tapez *RECLAMATION* — Faire une réclamation
```

### HORAIRES
```
🕐 *Horaires d'ouverture SICG :*

• Lundi – Vendredi : 7h00 à 17h00
• Samedi : 7h00 à 12h00
• Dimanche & Jours fériés : Fermé

📞 +1 555-955-0644
```

### LOCALISATION
```
📍 *SICG — Société Industrielle de Commerce Général*

Zone Industrielle de Bonabéri
Douala, Cameroun

🚗 Repère : après le carrefour Bonabéri, direction zone industrielle, à 200m sur la droite.

📞 +1 555-955-0644
```

### PROMO
```
🎉 *Promotions en cours chez SICG :*

🔥 -15% sur tous les matelas 2 places jusqu'au 31/07
🔥 Lot 10 éponges à 3 500 XAF au lieu de 4 000
🔥 Livraison gratuite sur Douala pour commande > 50 000 XAF
🔥 -10% sur les tôles aluzinc (commande > 20 feuilles)

Tapez *COMMANDER* pour en profiter !
```

### LIVRAISON
```
🚚 *Informations livraison SICG :*

• *Douala ville* : 2 000 XAF (gratuit si commande > 50 000 XAF)
• *Yaoundé* : 5 000 XAF
• *Bafoussam / Bamenda* : 7 000 XAF
• *Autres villes Cameroun* : 8 000 – 15 000 XAF selon zone

⏱️ *Délais :*
• Douala : 24h
• Yaoundé : 48h
• Autres : 48-72h

📦 *Minimum commande :*
• Particulier : 10 000 XAF
• Grossiste : 50 000 XAF

Tapez *COMMANDER* pour passer commande.
```

### MERCI
```
De rien ! N'hésitez pas à revenir vers nous. Tapez *MENU* à tout moment. 🙏
```

### BONJOUR
```
Bonjour ! 👋 Comment puis-je vous aider aujourd'hui ?

Tapez *MENU* pour voir nos services.
```

### SALUT
```
Salut ! 👋 Bienvenue chez SICG.

Tapez *MENU* pour découvrir nos produits et services.
```

### PRIX
```
💰 *Nos gammes de prix :*

• Éponges : à partir de 500 XAF
• Mousses : à partir de 5 000 XAF/m²
• Matelas : à partir de 12 000 XAF
• Tôles : à partir de 4 500 XAF/feuille
• Habillages : à partir de 2 000 XAF

Tapez *CATALOGUE* pour voir le détail par catégorie.
```

### CONTACT
```
📞 *Nous contacter :*

📱 WhatsApp : +1 555-955-0644
📍 Zone Industrielle de Bonabéri, Douala
🕐 Lun-Ven 7h-17h | Sam 7h-12h

Tapez *AGENT* pour parler directement à un conseiller.
```

---

## 4. Scénarios

---

### Scénario 1 : COMMANDER
**Trigger :** `COMMANDER`
**Nom :** Passer une commande
**Fonctionnalités testées :** choice, text, condition, catalogue (via interpolation), handoff, interpolation variables

```json
[
  {
    "step": 1,
    "type": "choice",
    "message": "🛒 *Passer une commande*\n\nVous êtes :\n\n1️⃣ *Particulier*\n2️⃣ *Grossiste / Entreprise*\n\nTapez 1 ou 2.",
    "choices": {
      "1": "Parfait ! Commande particulier (minimum 10 000 XAF).",
      "2": "Commande grossiste enregistrée (minimum 50 000 XAF).",
      "PARTICULIER": "Parfait ! Commande particulier (minimum 10 000 XAF).",
      "GROSSISTE": "Commande grossiste enregistrée (minimum 50 000 XAF).",
      "DEFAULT": "❌ Veuillez taper *1* (Particulier) ou *2* (Grossiste)."
    }
  },
  {
    "step": 2,
    "type": "choice",
    "message": "📦 Quelle catégorie de produit vous intéresse ?\n\n1️⃣ Matelas\n2️⃣ Mousses\n3️⃣ Éponges\n4️⃣ Tôles\n5️⃣ Habillages\n\nTapez le numéro ou le nom de la catégorie.",
    "choices": {
      "1": "{catalogue:Matelas}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "2": "{catalogue:Mousses}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "3": "{catalogue:Éponges}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "4": "{catalogue:Tôles}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "5": "{catalogue:Habillages}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "MATELAS": "{catalogue:Matelas}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "MOUSSES": "{catalogue:Mousses}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "EPONGES": "{catalogue:Éponges}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "TOLES": "{catalogue:Tôles}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "HABILLAGES": "{catalogue:Habillages}\n\nIndiquez le produit et la quantité à l'étape suivante.",
      "DEFAULT": "❌ Catégorie non reconnue. Tapez un numéro de 1 à 5."
    }
  },
  {
    "step": 3,
    "type": "text",
    "message": "Quel produit souhaitez-vous commander ? Indiquez le *nom exact* et la *quantité*.\n\nExemple : _Matelas 2 places x3_ ou _Tôle BG 28 x50 feuilles_"
  },
  {
    "step": 4,
    "type": "text",
    "message": "📝 Votre nom complet ?"
  },
  {
    "step": 5,
    "type": "text",
    "message": "📱 Votre numéro de téléphone (si différent de celui-ci) ?\n\n_(Tapez MEME si c'est ce numéro)_"
  },
  {
    "step": 6,
    "type": "choice",
    "message": "🚚 Mode de livraison :\n\n1️⃣ *Livraison à domicile* (frais selon zone)\n2️⃣ *Retrait en usine* (gratuit) — Bonabéri, Zone Industrielle\n\nTapez 1 ou 2.",
    "choices": {
      "1": "Livraison à domicile sélectionnée. Indiquez votre adresse à l'étape suivante.",
      "2": "Retrait en usine sélectionné.\n📍 Adresse : Zone Industrielle de Bonabéri, Douala.\n🕐 Retrait possible : Lun-Ven 7h-17h, Sam 7h-12h.",
      "DEFAULT": "❌ Tapez *1* (Livraison) ou *2* (Retrait en usine)."
    }
  },
  {
    "step": 7,
    "type": "condition",
    "message": "📍 Indiquez votre *ville et quartier* de livraison.\n\n_(Si vous avez choisi retrait en usine, tapez USINE)_",
    "conditions": [
      {
        "if": "equals",
        "value": "USINE",
        "reply": "✅ Retrait confirmé à l'usine SICG — Bonabéri, Zone Industrielle."
      },
      {
        "if": "default",
        "value": "",
        "reply": "📍 Adresse de livraison notée."
      }
    ]
  },
  {
    "step": 8,
    "type": "handoff",
    "message": "✅ *Récapitulatif de votre commande SICG :*\n\n👤 Client : {step_4_answer}\n📱 Tél : {step_5_answer}\n📦 Type : {step_1_answer}\n🛒 Produit(s) : {step_3_answer}\n🚚 Livraison : {step_6_answer}\n📍 Adresse : {step_7_answer}\n📅 Date : {date} à {time}\n\nUn conseiller SICG va finaliser votre commande et vous confirmer le montant total. Merci de patienter ! 🙏"
  }
]
```

---

### Scénario 2 : DEVIS
**Trigger :** `DEVIS`
**Nom :** Demande de devis personnalisé
**Fonctionnalités testées :** text (collecte libre), choice, handoff, interpolation {date}, {step_N_answer}

```json
[
  {
    "step": 1,
    "type": "text",
    "message": "📐 *Demande de devis personnalisé SICG*\n\nDécrivez votre besoin en détail :\n• Type de produit (mousse, matelas, tôle, éponge…)\n• Dimensions souhaitées\n• Quantité\n• Usage prévu\n\nExemple : _Mousse HD D30, 200x150x10cm, 50 pièces, pour canapés restaurant_"
  },
  {
    "step": 2,
    "type": "choice",
    "message": "⏰ Quel est votre délai souhaité ?\n\n1️⃣ Urgent (< 1 semaine)\n2️⃣ Normal (1-2 semaines)\n3️⃣ Flexible (> 2 semaines)\n\nTapez 1, 2 ou 3.",
    "choices": {
      "1": "⚡ Demande urgente notée — supplément possible.",
      "2": "📅 Délai normal (1-2 semaines).",
      "3": "🕐 Délai flexible — meilleur tarif possible.",
      "URGENT": "⚡ Demande urgente notée.",
      "NORMAL": "📅 Délai normal.",
      "FLEXIBLE": "🕐 Délai flexible.",
      "DEFAULT": "❌ Tapez *1* (Urgent), *2* (Normal) ou *3* (Flexible)."
    }
  },
  {
    "step": 3,
    "type": "text",
    "message": "🏢 Nom de votre entreprise (ou votre nom complet si particulier) ?"
  },
  {
    "step": 4,
    "type": "text",
    "message": "📧 Votre adresse email (pour recevoir le devis en PDF) ?\n\n_(Tapez WHATSAPP si vous préférez recevoir le devis ici)_"
  },
  {
    "step": 5,
    "type": "text",
    "message": "📱 Numéro de téléphone de contact ?\n\n_(Tapez MEME si c'est ce numéro WhatsApp)_"
  },
  {
    "step": 6,
    "type": "handoff",
    "message": "✅ *Demande de devis enregistrée !*\n\n📋 *Besoin :* {step_1_answer}\n⏰ *Délai :* {step_2_answer}\n👤 *Client :* {step_3_answer}\n📧 *Email :* {step_4_answer}\n📱 *Tél :* {step_5_answer}\n📅 *Date demande :* {date}\n\nNotre équipe commerciale vous contactera sous 24h avec votre devis détaillé. Un conseiller prend le relais. 🙏"
  }
]
```

---

### Scénario 3 : CATALOGUE
**Trigger :** `CATALOGUE`
**Nom :** Consultation du catalogue
**Fonctionnalités testées :** choice avec {catalogue:Catégorie} dans les reply, DEFAULT re-ask

```json
[
  {
    "step": 1,
    "type": "choice",
    "message": "🛍️ *Catalogue SICG*\n\nChoisissez une catégorie :\n\n1️⃣ Matelas\n2️⃣ Mousses\n3️⃣ Éponges\n4️⃣ Tôles\n5️⃣ Habillages\n6️⃣ Tout voir\n\nTapez le numéro.",
    "choices": {
      "1": "{catalogue:Matelas}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "2": "{catalogue:Mousses}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "3": "{catalogue:Éponges}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "4": "{catalogue:Tôles}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "5": "{catalogue:Habillages}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "6": "{catalogue}\n\n👉 Tapez *COMMANDER* pour passer commande ou *MENU* pour revenir au menu.",
      "MATELAS": "{catalogue:Matelas}\n\n👉 Tapez *COMMANDER* pour passer commande.",
      "MOUSSES": "{catalogue:Mousses}\n\n👉 Tapez *COMMANDER* pour passer commande.",
      "EPONGES": "{catalogue:Éponges}\n\n👉 Tapez *COMMANDER* pour passer commande.",
      "TOLES": "{catalogue:Tôles}\n\n👉 Tapez *COMMANDER* pour passer commande.",
      "HABILLAGES": "{catalogue:Habillages}\n\n👉 Tapez *COMMANDER* pour passer commande.",
      "DEFAULT": "❌ Catégorie non reconnue. Tapez un numéro de *1* à *6*."
    },
    "end_message": "Merci d'avoir consulté notre catalogue ! 🛍️"
  }
]
```

---

### Scénario 4 : RECLAMATION
**Trigger :** `RECLAMATION`
**Nom :** Service réclamation
**Fonctionnalités testées :** choice, text (multi-étape collecte), handoff, {date}, {time}

```json
[
  {
    "step": 1,
    "type": "choice",
    "message": "⚠️ *Service Réclamation SICG*\n\nQuel type de problème rencontrez-vous ?\n\n1️⃣ Produit défectueux / qualité\n2️⃣ Retard de livraison\n3️⃣ Erreur de commande\n4️⃣ Facturation incorrecte\n5️⃣ Autre problème\n\nTapez le numéro.",
    "choices": {
      "1": "🔧 Produit défectueux — nous sommes désolés.",
      "2": "🚚 Retard de livraison — nous allons vérifier.",
      "3": "📦 Erreur de commande — nous corrigeons.",
      "4": "💰 Problème de facturation — noté.",
      "5": "📝 Autre problème — décrivez-le.",
      "DEFAULT": "❌ Tapez un numéro de *1* à *5*."
    }
  },
  {
    "step": 2,
    "type": "text",
    "message": "📝 Décrivez votre problème en détail.\n\nSi vous avez un *numéro de commande*, merci de l'indiquer."
  },
  {
    "step": 3,
    "type": "text",
    "message": "📅 Date approximative de votre achat ou commande ?"
  },
  {
    "step": 4,
    "type": "text",
    "message": "👤 Votre nom complet ?"
  },
  {
    "step": 5,
    "type": "handoff",
    "message": "✅ *Réclamation enregistrée avec succès*\n\n⚠️ *Type :* {step_1_answer}\n📝 *Détail :* {step_2_answer}\n📅 *Date achat :* {step_3_answer}\n👤 *Client :* {step_4_answer}\n\n🕐 *Enregistrée le :* {date} à {time}\n\nUn responsable qualité SICG va traiter votre réclamation sous 24-48h. Vous recevrez un retour sur ce même numéro. Merci de votre patience. 🙏"
  }
]
```

---

### Scénario 5 : AGENT
**Trigger :** `AGENT`
**Nom :** Parler à un conseiller
**Fonctionnalités testées :** text + handoff (transfert rapide)

```json
[
  {
    "step": 1,
    "type": "text",
    "message": "👤 *Mise en relation avec un conseiller SICG*\n\nPour mieux vous orienter, décrivez brièvement l'objet de votre demande :"
  },
  {
    "step": 2,
    "type": "handoff",
    "message": "✅ Merci ! Un conseiller SICG va vous répondre dans les prochaines minutes.\n\n🕐 Temps d'attente estimé : < 5 min (heures ouvrables)\n📅 Heures ouvrables : Lun-Ven 7h-17h | Sam 7h-12h\n\n_Si nous sommes en dehors des heures d'ouverture, nous vous répondrons dès la reprise._\n\n📋 Votre demande : _{step_1_answer}_"
  }
]
```

---

## 5. Résumé des fonctionnalités couvertes

| Fonctionnalité Bot | Où elle est testée |
|---|---|
| **Step type : text** | COMMANDER (3,4,5), DEVIS (1,3,4,5), RECLAMATION (2,3,4), AGENT (1) |
| **Step type : choice** | COMMANDER (1,2,6), DEVIS (2), CATALOGUE (1), RECLAMATION (1) |
| **Step type : condition** | COMMANDER (7) — if equals "USINE" + default |
| **Step type : catalogue** | Via `{catalogue:X}` dans reply des choices (COMMANDER 2, CATALOGUE 1) |
| **Step type : handoff** | COMMANDER (8), DEVIS (6), RECLAMATION (5), AGENT (2) |
| **Interpolation {step_N_answer}** | Récapitulatifs dans tous les handoff |
| **Variables {date}, {time}** | DEVIS (6), RECLAMATION (5) |
| **{catalogue:Catégorie}** | COMMANDER (2), CATALOGUE (1) |
| **{catalogue} (tout)** | CATALOGUE (1) — choix "6" |
| **DEFAULT (re-ask invalide)** | Tous les choice steps |
| **Mots-clés simples** | MENU, HORAIRES, LOCALISATION, PROMO, LIVRAISON, MERCI, BONJOUR, SALUT, PRIX, CONTACT |
| **Message bienvenue** | Premier contact automatique |
| **Message inconnu (fallback)** | Tout message non reconnu |
| **Message absence** | Hors horaires |

---

## 6. Parcours de test recommandés

### Test 1 — Commande complète (particulier + livraison)
```
Client : MENU
Bot : [affiche menu]
Client : COMMANDER
Bot : Vous êtes : 1 Particulier / 2 Grossiste
Client : 1
Bot : Parfait ! [...] Quelle catégorie ?
Client : 1
Bot : [affiche catalogue Matelas] Indiquez produit...
Client : Matelas 2 places x2
Bot : Votre nom complet ?
Client : Jean Kamga
Bot : Numéro de téléphone ?
Client : MEME
Bot : Mode livraison ?
Client : 1
Bot : Ville et quartier ?
Client : Douala Akwa
Bot : [HANDOFF] Récapitulatif + transfert agent
```

### Test 2 — Commande (retrait usine)
```
Client : COMMANDER
[...mêmes étapes...]
Client : 2 (retrait)
Bot : Retrait en usine sélectionné [...]
Client : USINE
Bot : ✅ Retrait confirmé [...]
Bot : [HANDOFF] Récapitulatif
```

### Test 3 — Devis personnalisé
```
Client : DEVIS
Bot : Décrivez votre besoin...
Client : Mousse D30, 300x200x15cm, 100 pièces pour hôtel
Bot : Délai ?
Client : 2
Bot : Nom entreprise ?
Client : Hôtel Palm Beach
Bot : Email ?
Client : palm@hotel.cm
Bot : Téléphone ?
Client : MEME
Bot : [HANDOFF] Devis enregistré + récapitulatif
```

### Test 4 — Réclamation
```
Client : RECLAMATION
Bot : Type de problème ? 1-5
Client : 1
Bot : Décrivez...
Client : Matelas reçu avec tache et déchirure sur le côté
Bot : Date achat ?
Client : 25 juin 2026
Bot : Nom ?
Client : Marie Fouda
Bot : [HANDOFF] Réclamation enregistrée
```

### Test 5 — Catalogue + mot-clé
```
Client : CATALOGUE
Bot : Catégorie 1-6 ?
Client : 4
Bot : [catalogue Tôles affiché]
[Scénario terminé]
Client : PROMO
Bot : [promos en cours]
Client : HORAIRES
Bot : [horaires]
```

### Test 6 — Fallback + agent
```
Client : abc123xyz
Bot : Désolé, je n'ai pas compris... Tapez MENU ou AGENT.
Client : AGENT
Bot : Décrivez votre demande...
Client : Je veux un partenariat commercial
Bot : [HANDOFF] Transfert + objet noté
```

### Test 7 — Re-ask (saisie invalide)
```
Client : COMMANDER
Bot : Vous êtes : 1/2
Client : 7
Bot : ❌ Veuillez taper 1 ou 2. [reste sur même étape]
Client : 1
Bot : [avance normalement]
```
