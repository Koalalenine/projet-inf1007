"""Entraînement, évaluation et sauvegarde du modèle de régression."""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import date

import joblib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from numpy.typing import ArrayLike
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.exceptions import DonneeInvalideError

CIBLE = "position"
GRAINE_ALEATOIRE = 42
PROPORTION_TEST = 0.2


@dataclass
class ResultatEntrainement:
    """Regroupe le modèle entraîné, ses scores, les prédictions de test et ses métadonnées."""

    modele: Pipeline
    metriques: dict[str, float]
    valeurs_reelles: np.ndarray
    predictions: np.ndarray
    metadonnees: dict[str, object]


def calculer_mae_numpy(valeurs_reelles: ArrayLike, predictions: ArrayLike) -> float:
    """Calcule l'erreur absolue moyenne avec NumPy; refuse les tableaux vides ou incompatibles."""
    reel = np.asarray(valeurs_reelles, dtype=float)
    prevu = np.asarray(predictions, dtype=float)
    if reel.ndim != 1 or prevu.ndim != 1 or reel.shape != prevu.shape or reel.size == 0:
        raise DonneeInvalideError("Les valeurs réelles et prédites doivent être deux vecteurs non vides de même taille.")
    return float(np.mean(np.abs(reel - prevu)))


def entrainer_et_evaluer(
    df: pd.DataFrame,
    taille_test: float = PROPORTION_TEST,
    graine: int = GRAINE_ALEATOIRE,
) -> ResultatEntrainement:
    """Sépare les données, entraîne la référence et la forêt, puis évalue sur le test uniquement."""
    if df.empty:
        raise DonneeInvalideError("Le jeu de données est vide.")
    if CIBLE not in df.columns:
        raise DonneeInvalideError(f"Colonne cible introuvable : {CIBLE}.")
    if not pd.api.types.is_numeric_dtype(df[CIBLE]):
        raise DonneeInvalideError(f"La cible « {CIBLE} » doit être numérique.")
    if df.isna().any().any():
        raise DonneeInvalideError("Le jeu de données contient des valeurs manquantes.")
    if not 0 < taille_test < 1:
        raise DonneeInvalideError("La proportion de test doit être entre 0 et 1.")
    if len(df) < 4 or math.ceil(len(df) * taille_test) < 2:
        raise DonneeInvalideError("Il faut assez de lignes pour créer des ensembles d'entraînement et de test.")

    colonnes_a_retirer = [colonne for colonne in ("nom", CIBLE) if colonne in df.columns]
    entrees = df.drop(columns=colonnes_a_retirer)
    if entrees.empty:
        raise DonneeInvalideError("Aucune variable d'entrée disponible pour entraîner le modèle.")

    colonnes_numeriques = entrees.select_dtypes(include="number").columns.tolist()
    colonnes_categorielles = [colonne for colonne in entrees.columns if colonne not in colonnes_numeriques]
    transformations = []
    if colonnes_numeriques:
        transformations.append(("numeriques", "passthrough", colonnes_numeriques))
    if colonnes_categorielles:
        transformations.append((
            "categories",
            OneHotEncoder(handle_unknown="ignore"),
            colonnes_categorielles,
        ))

    preprocesseur = ColumnTransformer(transformations)
    pipeline = Pipeline([
        ("preparation", preprocesseur),
        ("regression", RandomForestRegressor(
            n_estimators=100,
            random_state=graine,
            n_jobs=1,
        )),
    ])

    cible = df[CIBLE]
    x_train, x_test, y_train, y_test = train_test_split(
        entrees,
        cible,
        test_size=taille_test,
        random_state=graine,
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    reference = DummyRegressor(strategy="mean")
    reference.fit(np.zeros((len(y_train), 1)), y_train)
    predictions_reference = reference.predict(np.zeros((len(y_test), 1)))

    valeurs_reelles = y_test.to_numpy(dtype=float)
    metriques = {
        "mae_modele": calculer_mae_numpy(valeurs_reelles, predictions),
        "mae_reference_moyenne": calculer_mae_numpy(valeurs_reelles, predictions_reference),
        "r2_modele": float(r2_score(valeurs_reelles, predictions)),
    }

    variables_categorielles = {
        colonne: sorted(str(valeur) for valeur in entrees[colonne].unique())
        for colonne in colonnes_categorielles
    }
    variables_numeriques = {
        colonne: {
            "minimum": float(entrees[colonne].min()),
            "maximum": float(entrees[colonne].max()),
        }
        for colonne in colonnes_numeriques
    }
    metadonnees: dict[str, object] = {
        "date_entrainement": date.today().isoformat(),
        "cible": CIBLE,
        "type_probleme": "regression",
        "modele": "RandomForestRegressor",
        "metrique_principale": "MAE",
        "metriques": metriques,
        "colonnes_entree": entrees.columns.tolist(),
        "variables_categorielles": variables_categorielles,
        "variables_numeriques": variables_numeriques,
        "taille_jeu_de_donnees": len(df),
        "taille_test": taille_test,
        "graine_aleatoire": graine,
    }
    return ResultatEntrainement(
        modele=pipeline,
        metriques=metriques,
        valeurs_reelles=valeurs_reelles,
        predictions=np.asarray(predictions, dtype=float),
        metadonnees=metadonnees,
    )


def sauvegarder_artifacts(
    resultat: ResultatEntrainement,
    chemin_modele: str,
    chemin_metadonnees: str,
) -> None:
    """Enregistre le pipeline avec joblib et les informations destinées à l'interface en JSON."""
    for chemin in (chemin_modele, chemin_metadonnees):
        dossier = os.path.dirname(chemin)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
    joblib.dump(resultat.modele, chemin_modele)
    with open(chemin_metadonnees, "w", encoding="utf-8") as fichier:
        json.dump(resultat.metadonnees, fichier, ensure_ascii=False, indent=2)


def sauvegarder_graphique(
    resultat: ResultatEntrainement,
    chemin: str,
) -> None:
    """Enregistre un graphique des positions prédites contre les positions réelles du test."""
    dossier = os.path.dirname(chemin)
    if dossier:
        os.makedirs(dossier, exist_ok=True)

    minimum = float(min(resultat.valeurs_reelles.min(), resultat.predictions.min()))
    maximum = float(max(resultat.valeurs_reelles.max(), resultat.predictions.max()))
    figure = Figure(figsize=(7, 6))
    axe = figure.subplots()
    canvas = FigureCanvasAgg(figure)
    axe.scatter(resultat.valeurs_reelles, resultat.predictions, alpha=0.65, label="Commandants du test")
    axe.plot([minimum, maximum], [minimum, maximum], "r--", label="Prédiction parfaite")
    axe.set_title("Positions prédites contre réelles")
    axe.set_xlabel("Position réelle")
    axe.set_ylabel("Position prédite")
    axe.legend()
    figure.tight_layout()
    canvas.print_png(chemin)


def entrainer_depuis_csv(
    chemin_csv: str,
    chemin_modele: str,
    chemin_metadonnees: str,
    chemin_graphique: str,
) -> ResultatEntrainement:
    """Charge le CSV, entraîne le modèle, puis sauvegarde les artefacts et le graphique."""
    if not os.path.isfile(chemin_csv):
        raise DonneeInvalideError(f"Fichier introuvable : {chemin_csv}")
    try:
        df = pd.read_csv(chemin_csv)
    except (OSError, UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as erreur:
        raise DonneeInvalideError(f"Impossible de lire le jeu de données {chemin_csv} : {erreur}") from erreur

    resultat = entrainer_et_evaluer(df)
    sauvegarder_artifacts(resultat, chemin_modele, chemin_metadonnees)
    sauvegarder_graphique(resultat, chemin_graphique)
    return resultat
