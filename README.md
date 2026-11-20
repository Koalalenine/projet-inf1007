# Projet 2 INF1007 : popularité des commandants Magic (Scryfall + otags)

> **Statut : volet 1 (jeu de données) terminé.** Les volets 2 (modèle) et 3 (interface) restent à faire.

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

## Installation et lancement

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python -m src.main collecter     # télécharge, construit donnees/commandants_top1000.csv
python -m src.main verifier      # vérifie les critères de la section 2
pytest                           # tests (hors ligne)
coverage run -m pytest && coverage report -m
```

La collecte fait environ 150 à 400 requêtes (quelques minutes) ; les résultats sont mis en
cache dans `donnees/cache_*.json` (ignorés par Git). Un tag qui ne renvoie aucun résultat est
signalé : corrigez-le dans `TAGS_PAR_DEFAUT` (`src/donnees.py`) ou avec `--tags a,b,c`.

## Structure

```
src/exceptions.py   exceptions personnalisées (DonneeInvalideError, ScryfallError)
src/donnees.py      appels API, cache JSON, construction du DataFrame, vérification des critères
src/main.py         point d'entrée (ligne de commande)
tests/              tests pytest (API simulée, aucun accès réseau)
donnees/            CSV (généré, non versionné) et graphique d'exploration
modeles/            modèle sauvegardé + métadonnées JSON (volet 2)
```

## Outils du chapitre 7

- **Décorateur** `@chronometre` : affiche la durée des étapes de collecte.
- **Générateur** `lire_csv_par_blocs` : lit le CSV par blocs de lignes.

## Couverture de tests

Résultat de `python -m coverage run -m pytest` puis `python -m coverage report` (18 tests, tous réussis) :

| Module | Couverture |
|---|---|
| `src/donnees.py` | 76 % |
| `src/exceptions.py` | 100 % |
| **Total (fichiers de tests inclus)** | **86 %** |

Les lignes non couvertes de `donnees.py` sont les fonctions qui font de vrais appels réseau
(`_get`, `collecter_*`) et la production du graphique. `src/main.py` n'est pas mesuré tant qu'aucun
test ne l'importe. À mettre à jour après les volets 2 et 3.

## Documentation consultée

- pandas : « 10 minutes to pandas » (https://pandas.pydata.org/docs/user_guide/10min.html) et
  `pandas.read_csv`, paramètre `chunksize` (https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- scikit-learn : _à compléter au volet 2_
- Technologie d'interface : _à compléter au volet 3_
- API Scryfall : https://scryfall.com/docs/api et syntaxe de recherche (`order:`, `otag:`) :
  https://scryfall.com/docs/syntax
