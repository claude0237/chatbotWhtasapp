# FAQ - Questions Fréquentes

## Général

**Q : Le bot répond-il en dehors des heures de travail ?**
Oui. En dehors des heures configurées, le bot envoie le **message d'absence** et peut quand même répondre aux questions simples via les mots-clés.

**Q : Combien de conversations simultanées le système peut-il gérer ?**
En configuration standard (2 réplicas backend), environ 500 conversations simultanées. Scalable horizontalement sans limite théorique.

**Q : Les données sont-elles isolées entre entreprises ?**
Oui. Chaque entreprise n'a accès qu'à ses propres données. L'isolation est vérifiée à chaque requête via le `company_id`.

**Q : Peut-on utiliser plusieurs canaux (WhatsApp + email) ?**
L'architecture est multi-canal. WhatsApp est pleinement intégré. D'autres canaux peuvent être ajoutés via le module `channels`.

## Bot et IA

**Q : Quelle est la différence entre le bot Natif et le bot ML ?**
- **Natif** : répond uniquement aux mots-clés et scénarios configurés. Prévisible, rapide, gratuit.
- **ML** : utilise un LLM (GPT-4, Claude, etc.) avec RAG sur la base de connaissances. Plus intelligent, coût par token.
- **Hybride** : essaie le natif d'abord, puis le ML si aucune règle ne correspond.

**Q : Le bot peut-il apprendre des conversations passées ?**
Pas d'apprentissage automatique en temps réel. Il utilise la base de connaissances que vous alimentez manuellement.

**Q : Comment améliorer la précision du bot ML ?**
1. Enrichir la base de connaissances avec des entrées spécifiques
2. Augmenter le `similarity_threshold` si les réponses sont trop génériques
3. Utiliser GPT-4 plutôt que GPT-3.5 pour des réponses plus précises

## Réservations

**Q : Le bot peut-il réserver automatiquement sans intervention humaine ?**
Oui. Si l'utilisateur confirme ("oui", "ok"), la réservation est créée et confirmée automatiquement.

**Q : Que se passe-t-il si deux clients essaient de réserver le même créneau ?**
Le premier à confirmer obtient le créneau. Le slot est immédiatement marqué `is_available=false` à la création de la réservation.

## Sécurité

**Q : Les tokens JWT sont-ils stockés côté client ?**
Oui, dans le `localStorage`. Le `refresh_token` a une durée de vie de 7 jours et est renouvelé automatiquement.

**Q : Comment révoquer l'accès d'un utilisateur immédiatement ?**
Désactiver l'utilisateur dans **Équipe** → toggle **Actif**. Le token actuel sera rejeté à la prochaine vérification (max 30 minutes).

## Technique

**Q : Comment voir les logs en temps réel ?**
```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

**Q : Comment ajouter une migration Alembic ?**
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Q : Comment vider le cache Redis ?**
```bash
redis-cli -a $REDIS_PASSWORD FLUSHDB  # Vider la DB actuelle seulement
```
