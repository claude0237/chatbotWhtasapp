# Guide Complet : Configuration Meta Embedded Signup en Production

## Table des matières
1. [Pré-requis](#pré-requis)
2. [Configuration de l'App Meta](#configuration-de-lapp-meta)
3. [Configuration du Domaine en Production](#configuration-du-domaine-en-production)
4. [Pré-requis pour les Clients](#pré-requis-pour-les-clients)
5. [Processus d'Intégration Client](#processus-dintégration-client)
6. [Dépannage](#dépannage)

---

## Pré-requis

### Pour toi (SaaS Provider)
- Un compte Facebook Business Manager
- Un VPS avec IP publique
- Un nom de domaine (ex: `omera.com`)
- Accès administrateur au portail Meta Developers

### Pour le client
- Un compte Facebook Business Manager
- Un WhatsApp Business Account (WABA) existant
- Un numéro WhatsApp Business actif
- Accès administrateur à son compte Meta

---

## Configuration de l'App Meta

### Étape 1 : Créer l'App

1. Allez sur [https://developers.facebook.com](https://developers.facebook.com)
2. Cliquez sur **Démarrer** → **Créer une application**
3. Choisissez le type **Business** (pour Embedded Signup)
4. Nommez l'application (ex: "OmeraWeb SaaS")
5. Cliquez sur **Créer une application**

### Étape 2 : Configurer les Paramètres de Base

1. Dans le menu de gauche, allez dans **Paramètres de base**
2. Remplissez les informations :
   - **Domaines de l'application** : Ajoute ton domaine de production
     - En développement : `villas-midwest-field-physics.trycloudflare.com`
     - En production : `api.omera.com`, `app.omera.com`, etc.
   - **URL de confidentialité** : `https://omera.com/privacy`
   - **URL des conditions d'utilisation** : `https://omera.com/terms`
   - **Catégorie de l'application** : Business
   - **Contact email** : ton email professionnel
3. Cliquez sur **Enregistrer les modifications**

### Étape 3 : Activer WhatsApp Product

1. Dans le menu de gauche, cliquez sur **Ajouter un produit**
2. Cliquez sur **WhatsApp** → **Configurer**
3. Acceptez les conditions d'utilisation
4. Sélectionnez le numéro de téléphone pour recevoir des SMS de vérification

### Étape 4 : Configurer WhatsApp

1. Dans **WhatsApp → Configuration**, vous verrez :
   - **Phone Number ID** : Notez-le (ex: `123456789012345`)
   - **WABA ID** : Notez-le (ex: `987654321098765`)
   - **Access Token** : Générez un token temporaire (durée 60 jours)

### Étape 5 : Configurer Embedded Signup

1. Allez dans **WhatsApp → Embedded Signup**
2. Cliquez sur **Gérer les configurations**
3. Cliquez sur **Créer une nouvelle configuration**
4. Remplissez les champs :
   - **Nom de la configuration** : "OmeraWeb Production"
   - **Redirect URI** : `https://app.omera.com/` (ton domaine de production - IMPORTANT : le slash final compte)
   - **Domaines autorisés** : `app.omera.com`
   - **Mode** : Sélectionnez les fonctionnalités nécessaires :
     - ✅ `whatsapp_business_management`
     - ✅ `whatsapp_business_messaging`
     - ✅ `whatsapp_business_phone_number`
5. Cliquez sur **Créer**
6. **Notez le Configuration ID** (ex: `1248075927303592`)

**IMPORTANT :** Avec Embedded Signup + config_id, le redirect_uri est géré par Meta en interne. Vous n'avez PAS besoin de le configurer dans le code backend ou frontend. Il est uniquement configuré dans le portail Meta.

### Étape 6 : Configurer Facebook Login

1. Allez dans **Produits → Facebook Login → Paramètres**
2. Activez **Connexion OAuth Web**
3. Activez **Se connecter avec le SDK JavaScript**
4. Dans **Domaines autorisés pour le SDK Javascript**, ajoute :
   - `app.omera.com`
5. Dans **URI de redirection OAuth valides**, ajoute :
   - `https://app.omera.com/`
6. Activez **Imposer le HTTPS** (recommandé)
7. Cliquez sur **Enregistrer les modifications**

### Étape 7 : Passer en Mode Production

**Important :** Le mode développement bloque Embedded Signup pour les utilisateurs externes.

1. Allez dans **Paramètres de base → Mode**
2. Cliquez sur **Passer en mode en direct**
3. Remplissez le formulaire de vérification :
   - **Utilisation de l'app** : Décrivez comment ton app utilise WhatsApp (ex: "SaaS de gestion de conversations WhatsApp pour entreprises")
   - **URL de l'app** : `https://app.omera.com`
   - **Capture d'écran de l'app** : Uploade une capture
   - **Vidéo de démonstration** (optionnel) : Uploade une vidéo
4. Cliquez sur **Envoyer pour vérification**
5. **Attendez l'approbation** (environ 2 jours ouvrés)

---

## Configuration du Domaine en Production

### Étape 1 : Acheter un Domaine

1. Achetez un domaine chez un registrar (Namecheap, GoDaddy, OVH, etc.)
   - Ex: `omera.com`
2. Configurez les DNS pour pointer vers ton VPS

### Étape 2 : Configurer DNS

Dans ton panneau de contrôle du registrar :

```
Type    Nom                Valeur                    TTL
A       api                123.45.67.89              3600
A       app                123.45.67.89              3600
CNAME   www                omera.com                 3600
```

Remplace `123.45.67.89` par l'IP publique de ton VPS.

### Étape 3 : Configurer SSL sur le VPS

Sur ton VPS (Ubuntu/Debian) :

```bash
# Installer Nginx
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y

# Configurer Nginx pour le frontend
sudo nano /etc/nginx/sites-available/app.omera.com
```

Contenu de la configuration :

```nginx
server {
    listen 80;
    server_name app.omera.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/app.omera.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtenir un certificat SSL gratuit avec Let's Encrypt
sudo certbot --nginx -d app.omera.com
```

Faites de même pour `api.omera.com` (proxy vers port 8000).

### Étape 4 : Configurer le Backend

Dans `backend/.env` :

```env
# CORS Origins
CORS_ORIGINS=https://app.omera.com,https://api.omera.com

# Meta App Configuration
NEXT_PUBLIC_META_APP_ID=123456789012345
META_APP_SECRET=abc123def456ghi789
NEXT_PUBLIC_META_CONFIG_ID=1248075927303592
```

**NOTE :** Vous n'avez PAS besoin de configurer `redirect_uri` dans le backend. Avec Embedded Signup + config_id, Meta gère le redirect_uri en interne via la configuration du portail Meta. Le code backend (`backend/app/whatsapp/controllers/__init__.py`) n'envoie pas de redirect_uri lors de l'échange du token.

Dans `frontend/.env.local` :

```env
NEXT_PUBLIC_API_URL=https://api.omera.com
NEXT_PUBLIC_META_APP_ID=123456789012345
NEXT_PUBLIC_META_CONFIG_ID=1248075927303592
```

### Étape 5 : Mettre à jour la Configuration Meta

Une fois le domaine configuré et SSL activé :

1. Allez dans **Paramètres de base → Domaines de l'application**
   - Supprime les URLs de développement
   - Ajoute : `app.omera.com`, `api.omera.com`

2. Allez dans **WhatsApp → Embedded Signup → Gérer les configurations**
   - Modifie la configuration
   - **Redirect URI** : `https://app.omera.com/`
   - **Domaines autorisés** : `app.omera.com`

3. Allez dans **Produits → Facebook Login → Paramètres**
   - **Domaines autorisés** : `app.omera.com`
   - **URI de redirection** : `https://app.omera.com/`

---

## Pré-requis pour les Clients

### Ce que le client doit avoir AVANT l'intégration

1. **Compte Facebook Business Manager**
   - Le client doit avoir un compte Business Manager actif
   - Il doit être administrateur de son compte

2. **WhatsApp Business Account (WABA)**
   - Le client doit avoir un WABA existant
   - Le WABA doit être en mode production (pas en sandbox)
   - Le WABA doit avoir au moins un numéro WhatsApp Business actif

3. **Numéro WhatsApp Business**
   - Le numéro doit être vérifié (SMS reçu)
   - Le numéro doit être actif et utilisé
   - Le numéro ne doit pas être bloqué par Meta

4. **Accès Administrateur**
   - Le client doit avoir les droits administrateur sur son WABA
   - Il doit pouvoir autoriser des apps tierces

### Ce que le client doit faire PENDANT l'intégration

1. **Autoriser l'App Meta**
   - Cliquer sur le bouton "Connecter WhatsApp" dans ton SaaS
   - Se connecter avec son compte Facebook Business
   - Sélectionner son WABA dans la liste
   - Sélectionner son numéro WhatsApp
   - Autoriser l'accès aux fonctionnalités requises

2. **Confirmer la Configuration**
   - Vérifier que le numéro apparaît dans ton SaaS
   - Tester l'envoi d'un message test
   - Confirmer que le webhook fonctionne

---

## Processus d'Intégration Client

### Étape 1 : Onboarding Client

1. Le client s'inscrit sur ta plateforme SaaS
2. Il crée son entreprise/organisation
3. Il accède à la page "Intégration WhatsApp"

### Étape 2 : Vérification des Pré-requis

Dans ton interface, affiche un checklist :

```
✅ Compte Facebook Business Manager actif
✅ WhatsApp Business Account existant
✅ Numéro WhatsApp Business actif
⬜ App Meta autorisée
⬜ Webhook configuré
⬜ Test d'envoi réussi
```

### Étape 3 : Connexion via Embedded Signup

1. Le client clique sur "Connecter WhatsApp"
2. La popup Meta s'ouvre avec ton `config_id`
3. Le client se connecte à son compte Facebook Business
4. Meta affiche la liste de ses WABAs
5. Le client sélectionne son WABA
6. Le client sélectionne son numéro WhatsApp
7. Le client autorise les permissions (whatsapp_business_messaging, etc.)
8. Meta redirige vers ton app avec un code
9. Ton backend échange le code contre un token
10. Ton backend sauvegarde les credentials

### Étape 4 : Configuration du Webhook

Ton backend doit automatiquement :

1. Abonner le WABA au webhook de ton app
2. Configurer les champs du webhook (messages, status, etc.)
3. Vérifier que le webhook est actif

### Étape 5 : Test de Fonctionnement

1. Envoie un message test depuis le numéro du client
2. Vérifie que le message arrive dans ton SaaS
3. Envoie une réponse depuis ton SaaS
4. Vérifie que le message est reçu sur WhatsApp

### Étape 6 : Confirmation

Affiche un message de succès :

```
🎉 Intégration WhatsApp réussie !

Numéro connecté : +237 6 41 70 16 29
WABA ID : 987654321098765
Statut webhook : ✅ Actif

Vous pouvez maintenant envoyer et recevoir des messages WhatsApp.
```

---

## Dépannage

### Erreur 191 : Domaine non autorisé

**Cause** : Le domaine n'est pas configuré dans les paramètres de l'app Meta.

**Solution** :
1. Allez dans **Paramètres de base → Domaines de l'application**
2. Ajoutez le domaine exact (ex: `app.omera.com`)
3. Sauvegardez les modifications

### Erreur 36008 : Redirect URI mismatch

**Cause** : L'URI de redirection ne correspond pas à celle configurée.

**Solution** :
1. Allez dans **Produits → Facebook Login → Paramètres**
2. Vérifiez que l'URI exacte est dans **URI de redirection OAuth valides**
3. Vérifiez que l'URI exacte est dans **WhatsApp → Embedded Signup → Redirect URI**
4. Le slash final compte : `https://app.omera.com/` ≠ `https://app.omera.com`

### Popup Meta bloquée / chargement infini

**Cause** : L'app est en mode développement et le client n'est pas testeur.

**Solution** :
1. Vérifiez que l'app est en **mode production**
2. Si en développement, ajoutez le client comme **testeur** dans **Rôles → Testeurs**
3. Attendez que Meta approuve l'app pour le mode production

### Webhook non reçu

**Cause** : Le webhook n'est pas configuré ou le port est bloqué.

**Solution** :
1. Vérifiez que le port 8000 est ouvert sur le VPS (`sudo ufw allow 8000`)
2. Vérifiez que le webhook URL est accessible publiquement
3. Vérifiez les logs backend pour les erreurs webhook

### Token expiré

**Cause** : Le token d'accès a expiré (durée 60 jours par défaut).

**Solution** :
1. Implémentez un système de rafraîchissement de token
2. Utilisez les webhooks de Meta pour détecter les expirations
3. Demandez au client de reconnecter son compte

---

## Checklist de Mise en Production

### Avant de lancer

- [ ] App Meta créée et configurée
- [ ] WhatsApp product activé
- [ ] Embedded Signup configuré avec config_id
- [ ] Facebook Login configuré
- [ ] Domaine acheté et configuré
- [ ] SSL installé sur le VPS
- [ ] Nginx configuré et fonctionnel
- [ ] Backend déployé sur le VPS
- [ ] Frontend déployé sur le VPS
- [ ] CORS configuré correctement
- [ ] App Meta en mode production (approuvée)
- [ ] Webhook endpoint accessible publiquement
- [ ] Tests effectués avec un compte test

### Après le lancement

- [ ] Surveillance des logs webhook
- [ ] Monitoring des erreurs OAuth
- [ ] Alertes pour les tokens expirés
- [ ] Documentation client disponible
- [ ] Support technique configuré

---

## Ressources Utiles

- [Meta Developers Documentation](https://developers.facebook.com/docs/)
- [WhatsApp Embedded Signup Guide](https://developers.facebook.com/docs/whatsapp/embedded-signup)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login)
- [Meta App Review Guidelines](https://developers.facebook.com/docs/app-review)

---

## Support

En cas de problème :
1. Vérifiez les logs backend (`/api/logs`)
2. Vérifiez la console browser (F12)
3. Consultez le portail Meta pour les erreurs
4. Contactez le support Meta Developers

---

**Dernière mise à jour** : 10 juillet 2026
**Version** : 1.0
