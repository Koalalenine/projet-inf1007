"""Tests de l'historique CSV."""
import pytest

from src.exceptions import DonneeInvalideError
from src.historique import COLONNES, Historique
from src.predicteur import Prediction


def une_prediction(position: int = 100) -> Prediction:
    return Prediction(position, position - 10, position + 10,
                      {"identite_couleur": "U", "type_principal": "Legendary Creature", "cmc": 3.0,
                       "annee": 2022, "tag_ramp": 1, "tag_draw": 0, "tag_mana-rock": 1})


def test_ajouter_puis_lire(tmp_path):
    h = Historique(str(tmp_path / "dossier" / "h.csv"))
    h.ajouter(une_prediction(120), horodatage="2026-11-20T10:00:00")
    ligne = h.lire()[0]
    assert ligne["position"] == "120" and ligne["roles"] == "ramp;mana-rock"
    assert ligne["date"] == "2026-11-20T10:00:00"


def test_en_tete_ecrit_une_seule_fois(tmp_path):
    h = Historique(str(tmp_path / "h.csv"))
    for i in range(3):
        h.ajouter(une_prediction(i + 1))
    assert len(h) == 3
    assert (tmp_path / "h.csv").read_text(encoding="utf-8").count("date,") == 1


def test_lire_fichier_absent_donne_liste_vide(tmp_path):
    assert Historique(str(tmp_path / "absent.csv")).lire() == []


def test_lire_colonnes_inattendues(tmp_path):
    chemin = tmp_path / "h.csv"
    chemin.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DonneeInvalideError):
        Historique(str(chemin)).lire()


def test_ajouter_dans_un_chemin_impossible(tmp_path):
    fichier = tmp_path / "fichier"
    fichier.write_text("x", encoding="utf-8")
    with pytest.raises(DonneeInvalideError):
        Historique(str(fichier / "h.csv")).ajouter(une_prediction())


def test_colonnes_attendues_stables():
    assert COLONNES[0] == "date" and "position" in COLONNES
