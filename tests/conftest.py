"""Fixtures partagées : un petit modèle entraîné et sauvegardé dans un dossier temporaire."""
import numpy as np
import pandas as pd
import pytest

from src.modele import entrainer_et_evaluer, sauvegarder_artifacts
from src.predicteur import Predicteur


@pytest.fixture
def jeu_reduit() -> pd.DataFrame:
    n = 60
    tags = {"tag_ramp": np.arange(n) % 2, "tag_draw": (np.arange(n) // 2) % 2}
    return pd.DataFrame({
        "nom": [f"C{i}" for i in range(n)], "position": np.arange(1, n + 1),
        "cmc": np.tile([2.0, 3.0, 4.0, 5.0], 15), "annee": np.tile([2018, 2020, 2022, 2024], 15),
        "identite_couleur": np.tile(["W", "U", "B", "R", "G"], 12),
        "type_principal": np.tile(["Legendary Creature", "Legendary Artifact"], 30),
        **tags, "nb_tags": tags["tag_ramp"] + tags["tag_draw"],
    })


@pytest.fixture
def predicteur(jeu_reduit, tmp_path) -> Predicteur:
    resultat = entrainer_et_evaluer(jeu_reduit, taille_test=0.25, graine=1)
    chemin_modele, chemin_meta = str(tmp_path / "m.joblib"), str(tmp_path / "m.json")
    sauvegarder_artifacts(resultat, chemin_modele, chemin_meta)
    return Predicteur(chemin_modele, chemin_meta)


@pytest.fixture
def saisies_valides() -> dict[str, str]:
    return {"cmc": "3", "annee": "2022", "identite_couleur": "U",
            "type_principal": "Legendary Creature", "tag_ramp": "1", "tag_draw": "0"}
