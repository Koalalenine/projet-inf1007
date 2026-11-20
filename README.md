# Projet 2 INF1007 : popularité des commandants Magic (Scryfall + otags)

> **Statut : volet 1 terminé.** Le modèle du volet 2 est entraîné et évalué; la validation C n'a pas été présentée faute de temps. Le volet 3 reste à faire.

## Description

Prédire la **position** (1 = le plus populaire) d'un commandant de Magic: The Gathering
parmi les 1000 commandants les plus populaires, à partir de ses *otags* (Oracle Tags de
Scryfall Tagger : `ramp`, `removal`, `draw`, etc.) et de quelques caractéristiques de la carte.
Problème de **régression**.

## Jeu de données

- **Source** : API Scryfall (https://scryfall.com/docs/api). L'ordre de popularité vient de
  `order:edhrec` (données EDHREC reprises par Scryfall). Les otags viennent de Scryfall Tagger
  (tags de la communauté), interrogés via le filtre de recherche `otag:`.
- **Date de collecte** : 2026-11-19
  (le classement EDHREC change avec le temps ; la date permet de situer les résultats).
- **Licence / conditions d'utilisation** : pas de licence de type CC. Scryfall fournit ses données
  gratuitement, dans le cadre de la *Wizards of the Coast Fan Content Policy*, « pour créer des logiciels
  Magic, faire de la recherche ou créer du contenu communautaire » (https://scryfall.com/docs/api).
  Notre usage (projet pédagogique, recherche, application gratuite) entre dans ce cadre. Conditions à respecter :
  ne pas faire payer l'accès aux données, ne pas simplement republier ou redistribuer les données de
  Scryfall (le logiciel doit apporter une valeur ajoutée), ne pas utiliser le nom ou les logos de Scryfall
  comme si Scryfall approuvait le projet, et ajouter un délai de 200 ms avant chaque requête (fait dans
  `PAUSE_ENTRE_REQUETES`).
- **Redistribution du CSV** : par prudence, le CSV **n'est pas versionné** dans ce dépôt public (voir
  `.gitignore`) : chaque utilisateur le régénère avec `python -m src.main collecter`. Le graphique
  d'exploration (`donnees/identites_couleur.png`) est versionné.
- **Mention** : projet étudiant non officiel, non produit, non approuvé ni soutenu par Wizards of the Coast
  ni par Scryfall. Magic: The Gathering est une marque de Wizards of the Coast, LLC.
- **Colonnes** : `nom`, `position` (cible), `cmc`, `annee`, `identite_couleur`,
  `type_principal`, `nb_tags`, et une colonne `tag_<nom>` (0/1) par otag.
- Aucune donnée personnelle.

## Exploration et préparation initiale

Le CSV final contient 1 000 lignes et 34 colonnes, sans valeur manquante. Les bornes IQR signalent
17 valeurs de `cmc`, 32 années et 5 valeurs de `nb_tags` éloignées du reste. Elles restent plausibles
pour des cartes Magic (cartes anciennes, coût élevé ou nombreuses fonctions) ; aucune ligne n'a donc
été supprimée. Les tags qui ne renvoyaient aucun commandant ont été vérifiés : quatre ont été remplacés
par des tags plus précis et trois retirés. Les choix et les nombres de résultats sont détaillés dans
`DECISIONS.md`. Le graphique exploratoire est `donnees/identites_couleur.png`.

## Installation et lancement

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python -m src.main collecter     # télécharge, construit donnees/commandants_top1000.csv
python -m src.main verifier      # vérifie les critères de la section 2
python -m src.main entrainer     # entraîne, évalue et sauvegarde le modèle
pytest                           # tests (hors ligne)
python -m coverage run -m pytest
python -m coverage report -m
```

La collecte fait environ 150 à 400 requêtes (quelques minutes) ; les résultats sont mis en
cache dans `donnees/cache_*.json` (ignorés par Git). Un tag qui ne renvoie aucun résultat est
signalé : corrigez-le dans `TAGS_PAR_DEFAUT` (`src/donnees.py`) ou avec `--tags a,b,c`.

## Structure

```
src/exceptions.py   exceptions personnalisées (DonneeInvalideError, ScryfallError)
src/donnees.py      appels API, cache JSON, construction du DataFrame, vérification des critères
src/modele.py       séparation, référence, entraînement, évaluation et sauvegarde du modèle
src/main.py         point d'entrée (ligne de commande)
tests/              tests pytest (API simulée et logique du modèle, aucun accès réseau)
donnees/            CSV (généré, non versionné) et graphique d'exploration
modeles/            pipeline .joblib, métadonnées JSON et graphique d'évaluation
```

## Modèle et résultats

La cible est `position`. Les données sont séparées en 80 % entraînement et 20 % test avec la graine 42.
Les variables catégorielles sont encodées par `OneHotEncoder`. Le `RandomForestRegressor` est comparé à
une référence `DummyRegressor` qui prédit la moyenne des rangs d'entraînement. Sur le test, le modèle
obtient une MAE de **247,3 positions**, contre **248,8** pour la référence, et un R² de **-0,077**.
Le gain de MAE est très faible et le R² négatif indique que le modèle explique mal la variation des rangs;
ces résultats modestes ne justifient pas de présenter les prédictions comme fiables.

Le pipeline est sauvegardé dans `modeles/commandants_random_forest.joblib`, ses métadonnées pour l'interface
dans `modeles/commandants_metadata.json`, et le graphique prédit/réel dans `modeles/predit_contre_reel.png`.
Le modèle n'est pas réentraîné au lancement de l'interface.

## Outils du chapitre 7

- **Décorateur** `@chronometre` : affiche la durée des étapes de collecte.
- **Générateur** `lire_csv_par_blocs` : lit le CSV par blocs de lignes.
- La MAE est calculée de façon vectorisée avec NumPy et comparée à scikit-learn dans un test.

## Couverture de tests

Résultat de `python -m coverage run -m pytest` puis `python -m coverage report` (27 tests, tous réussis) :

| Module | Couverture |
|---|---|
| `src/donnees.py` | 76 % |
| `src/modele.py` | 89 % |
| `src/exceptions.py` | 100 % |
| **Total (fichiers de tests inclus)** | **89 %** |

Les lignes non couvertes de `donnees.py` sont les fonctions qui font de vrais appels réseau
(`_get`, `collecter_*`) et la production du graphique. `src/main.py` n'est pas mesuré tant qu'aucun
test ne l'importe. À mettre à jour après les volets 2 et 3.

## Documentation consultée

- pandas : « 10 minutes to pandas » (https://pandas.pydata.org/docs/user_guide/10min.html) et
  `pandas.read_csv`, paramètre `chunksize` (https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- scikit-learn : `train_test_split` (https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html),
  `OneHotEncoder` (https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html),
  `RandomForestRegressor` (https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)
  et MAE (https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html)
- Technologie d'interface : _à compléter au volet 3_
- API Scryfall : https://scryfall.com/docs/api et syntaxe de recherche (`order:`, `otag:`) :
  https://scryfall.com/docs/syntax
