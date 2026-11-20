"""Tests du prédicteur (petit modèle entraîné à la volée, aucun accès réseau)."""
import json

import pytest

from src.exceptions import DonneeInvalideError, SaisieInvalideError
from src.predicteur import Prediction, Predicteur, ordinal


def test_predire_cas_usuel(predicteur, saisies_valides):
    p = predicteur.predire(saisies_valides)
    assert 1 <= p.borne_basse <= p.position <= p.borne_haute <= predicteur.taille
    assert p.entrees["tag_ramp"] == 1


def test_nb_tags_calcule_automatiquement(predicteur, saisies_valides):
    saisies_valides["tag_draw"] = "1"
    assert predicteur.valider(saisies_valides)["nb_tags"] == 2


def test_predire_est_deterministe(predicteur, saisies_valides):
    assert predicteur.predire(saisies_valides) == predicteur.predire(saisies_valides)


def test_validation_rapporte_toutes_les_erreurs(predicteur):
    with pytest.raises(SaisieInvalideError) as info:
        predicteur.predire({"cmc": "abc", "annee": "1800"})
    message = str(info.value)
    assert "Coût de mana" in message and "Année" in message and "Identité" in message


def test_saisie_hors_intervalle_refusee(predicteur, saisies_valides):
    saisies_valides["cmc"] = "99"
    with pytest.raises(SaisieInvalideError, match="entre"):
        predicteur.predire(saisies_valides)


def test_fichiers_absents(tmp_path):
    with pytest.raises(DonneeInvalideError, match="introuvable"):
        Predicteur(str(tmp_path / "x.joblib"), str(tmp_path / "x.json"))


def test_modele_illisible(predicteur, tmp_path):
    faux = tmp_path / "faux.joblib"
    faux.write_text("pas un modele", encoding="utf-8")
    meta = tmp_path / "m2.json"
    meta.write_text(json.dumps(predicteur.metadonnees), encoding="utf-8")
    with pytest.raises(DonneeInvalideError):
        Predicteur(str(faux), str(meta))


def test_importances_triees_et_somme_a_un(predicteur):
    toutes = predicteur.importances(n=100)
    valeurs = [v for _, v in toutes]
    assert valeurs == sorted(valeurs, reverse=True)
    assert sum(valeurs) == pytest.approx(1.0)
    assert len(predicteur.importances(n=3)) == 3


@pytest.mark.parametrize("n, attendu", [(1, "1er"), (2, "2e"), (250, "250e")])
def test_ordinal(n, attendu):
    assert ordinal(n) == attendu


def test_niveau_confiance_et_description(predicteur):
    assert predicteur.niveau_confiance() in {"faible", "moyenne", "bonne"}
    texte = predicteur.decrire(Prediction(10, 5, 20))
    assert "10e" in texte and "Confiance" in texte
