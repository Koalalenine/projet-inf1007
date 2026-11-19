# Journal d'utilisation de l'IA

Au moins 5 entrées sont exigées, dont une où la vérification a changé la décision (entrée 2).

> Avant la remise : refaites vous-mêmes les vérifications marquées « à reproduire » et ajoutez une ligne
> pour tout autre usage d'IA (volets 2 et 3 compris).

| Outil | Ce que vous avez demandé | Réponse reçue | Vérification faite | Décision |
|---|---|---|---|---|
| Claude | Comment utiliser l'API Scryfall pour le volet 1 ; code de collecte du top 1000 des commandants et de leurs otags | Code `src/donnees.py` ; l'IA a précisé que les otags ne sont pas dans le JSON des cartes et qu'il faut les interroger via `otag:` | Fonctionnement hors ligne vérifié par `pytest` (API simulée, 17 tests réussis). **À reproduire :** lancer `collecter` et lire les tags à 0 résultat ; relire la syntaxe `otag:` sur https://scryfall.com/docs/syntax | Gardé ; liste de tags à corriger après la collecte réelle |
| Claude | Le CSV peut-il être placé dans le dépôt GitHub public ? Quelle est la licence de Scryfall ? | Réponse de départ : données « libres d'utilisation ». | Lecture de https://scryfall.com/docs/api : l'accès est gratuit pour créer des logiciels, faire de la recherche ou du contenu communautaire, mais on ne doit pas « simplement republier » les données et ce n'est pas une licence ouverte de type CC | **Modifié :** CSV ajouté au `.gitignore`, non versionné ; README et DECISIONS corrigés pour expliquer la commande de collecte |
| Claude | Lancer les tests et mesurer la couverture, puis l'inscrire dans le README | 17 tests réussis, couverture totale de 79 % (`donnees.py` : 65 %) ; lignes manquantes = appels réseau et graphique | Résultat de `coverage run -m pytest` ; vérifié que les lignes manquantes correspondent bien aux fonctions réseau. **À reproduire** sur votre machine | Gardé ; chiffres à mettre à jour après les volets 2 et 3 |
| Claude | Vérifier que les noms d'otags de `TAGS_PAR_DEFAUT` existent réellement | L'IA ne peut pas interroger Scryfall depuis son environnement et ne peut donc pas confirmer les noms | Tentative impossible hors ligne ; la collecte affiche déjà « AUCUN RÉSULTAT » pour un tag inconnu | Rejeté : aucune liste n'est déclarée « vérifiée » ; vérification faite avec `collecter` sur notre machine |
| Claude | Lire l'énoncé et la structure du dépôt, lister les fichiers incomplets du volet 1 et donner les commandes Git | Liste des champs « à compléter » (README, DECISIONS, JOURNAL_IA) et séquence de commandes Git | Comparaison avec les sections 2, 5, 7 et l'annexe B de l'énoncé ; les dates de validation et de collecte ne sont pas inventées | Gardé ; dates de validation et de collecte à inscrire nous-mêmes |
