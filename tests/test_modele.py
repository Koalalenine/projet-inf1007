"""Tests hors ligne du modèle de régression."""
import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline

from src.exceptions import DonneeInvalideError
from src.modele import (
    calculer_mae_numpy,
    entrainer_et_evaluer,
    entrainer_depuis_csv,
    sauvegarder_artifacts,
    sauvegarder_graphique,
)


@pytest.fixture
def jeu_test() -> pd.DataFrame:
    """Construit un petit jeu déterministe avec variables numériques et catégorielles."""
    nombre = 40
    return pd.DataFrame({
        "nom": [f"Commandant {i}" for i in range(nombre)],
        "position": np.arange(1, nombre + 1),
        "cmc": np.tile([2.0, 3.0, 4.0, 5.0], 10),
        "annee": np.tile([2020, 2021, 2022, 2023], 10),
        "identite_couleur": np.tile(["W", "U", "B", "R", "G"], 8),
        "type_principal": np.tile(["Legendary Creature", "Legendary Artifact Creature"], 20),
        "tag_ramp": np.arange(nombre) % 2,
        "nb_tags": np.arange(nombre) % 4,
    })


def test_calculer_mae_numpy_correspond_a_sklearn():
    reel = np.array([10.0, 20.0, 30.0])
    prevu = np.array([12.0, 18.0, 33.0])
    assert calculer_mae_numpy(reel, prevu) == pytest.approx(mean_absolute_error(reel, prevu))


def test_calculer_mae_numpy_refuse_des_vecteurs_incompatibles():
    with pytest.raises(DonneeInvalideError):
        calculer_mae_numpy([1.0, 2.0], [1.0])


def test_entrainer_et_evaluer_produit_scores_et_metadonnees(jeu_test):
    resultat = entrainer_et_evaluer(jeu_test, taille_test=0.25, graine=7)

    assert len(resultat.valeurs_reelles) == 10
    assert resultat.metriques["mae_modele"] >= 0
    assert resultat.metriques["mae_reference_moyenne"] >= 0
    assert "nom" not in resultat.metadonnees["colonnes_entree"]
    assert resultat.metadonnees["cible"] == "position"
    assert "W" in resultat.metadonnees["variables_categorielles"]["identite_couleur"]


def test_entrainer_et_evaluer_est_reproductible(jeu_test):
    premier = entrainer_et_evaluer(jeu_test, taille_test=0.25, graine=12)
    deuxieme = entrainer_et_evaluer(jeu_test, taille_test=0.25, graine=12)

    assert premier.metriques["mae_modele"] == pytest.approx(deuxieme.metriques["mae_modele"])
    assert premier.valeurs_reelles.tolist() == deuxieme.valeurs_reelles.tolist()


def test_entrainer_et_evaluer_refuse_cible_absente(jeu_test):
    with pytest.raises(DonneeInvalideError, match="Colonne cible"):
        entrainer_et_evaluer(jeu_test.drop(columns=["position"]))


def test_entrainer_et_evaluer_refuse_valeurs_manquantes(jeu_test):
    jeu_test.loc[0, "cmc"] = np.nan
    with pytest.raises(DonneeInvalideError, match="valeurs manquantes"):
        entrainer_et_evaluer(jeu_test)


def test_entrainer_et_evaluer_refuse_taille_test_invalide(jeu_test):
    with pytest.raises(DonneeInvalideError, match="proportion de test"):
        entrainer_et_evaluer(jeu_test, taille_test=1.0)


def test_sauvegarder_artifacts_et_graphique(jeu_test, tmp_path):
    resultat = entrainer_et_evaluer(jeu_test)
    chemin_modele = tmp_path / "modeles" / "modele.joblib"
    chemin_json = tmp_path / "modeles" / "metadata.json"
    chemin_graphique = tmp_path / "modeles" / "evaluation.png"

    sauvegarder_artifacts(resultat, str(chemin_modele), str(chemin_json))
    sauvegarder_graphique(resultat, str(chemin_graphique))

    modele_sauvegarde = joblib.load(chemin_modele)
    with chemin_json.open(encoding="utf-8") as fichier:
        metadonnees = json.load(fichier)
    assert isinstance(modele_sauvegarde, Pipeline)
    assert metadonnees["metriques"]["mae_modele"] == pytest.approx(resultat.metriques["mae_modele"])
    assert chemin_graphique.stat().st_size > 0


def test_entrainer_depuis_csv_refuse_un_fichier_absent(tmp_path):
    with pytest.raises(DonneeInvalideError, match="Fichier introuvable"):
        entrainer_depuis_csv(
            str(tmp_path / "absent.csv"),
            str(tmp_path / "modele.joblib"),
            str(tmp_path / "metadata.json"),
            str(tmp_path / "evaluation.png"),
        )
