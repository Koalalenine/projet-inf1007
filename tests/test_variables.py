"""Tests des classes de variables et de leur validation (cas usuels, limites, erreurs)."""
import pytest

from src.exceptions import DonneeInvalideError, SaisieInvalideError
from src.variables import (Variable, VariableBinaire, VariableCategorielle, VariableNumerique,
                           construire_variables)


def test_numerique_valeur_usuelle_et_virgule():
    v = VariableNumerique("cmc", 0, 13)
    assert v.valider(" 4 ") == pytest.approx(4.0)
    assert v.valider("2,5") == pytest.approx(2.5)


def test_numerique_bornes_incluses():
    v = VariableNumerique("annee", 2000, 2026, entier=True)
    assert v.valider("2000") == 2000 and v.valider("2026") == 2026


@pytest.mark.parametrize("saisie", ["", "   ", "abc", "nan", "inf", "-1", "14"])
def test_numerique_refuse_saisies_invalides(saisie):
    with pytest.raises(SaisieInvalideError):
        VariableNumerique("cmc", 0, 13).valider(saisie)


def test_numerique_entier_refuse_decimal():
    with pytest.raises(SaisieInvalideError, match="entier"):
        VariableNumerique("annee", 2000, 2026, entier=True).valider("2020.5")


def test_numerique_intervalle_inverse_leve_erreur():
    with pytest.raises(DonneeInvalideError):
        VariableNumerique("x", 5, 1)


def test_categorielle_choix_valide_et_invalide():
    v = VariableCategorielle("identite_couleur", ["W", "U"])
    assert v.valider(" U ") == "U"
    with pytest.raises(SaisieInvalideError):
        v.valider("Z")
    with pytest.raises(SaisieInvalideError):
        v.valider("")


def test_categorielle_sans_valeur_leve_erreur():
    with pytest.raises(DonneeInvalideError):
        VariableCategorielle("x", [])


@pytest.mark.parametrize("saisie, attendu", [("1", 1), ("0", 0), ("Oui", 1), ("non", 0)])
def test_binaire_valeurs_acceptees(saisie, attendu):
    assert VariableBinaire("tag_ramp").valider(saisie) == attendu


def test_binaire_refuse_autre_valeur():
    with pytest.raises(SaisieInvalideError):
        VariableBinaire("tag_ramp").valider("2")


def test_polymorphisme_meme_methode_trois_comportements():
    variables: list[Variable] = [VariableNumerique("a", 0, 10), VariableCategorielle("b", ["x"]),
                                 VariableBinaire("tag_c")]
    assert [v.valider(s) for v, s in zip(variables, ["5", "x", "1"])] == [5, "x", 1]


def test_methodes_speciales():
    v = VariableNumerique("cmc", 0, 13)
    assert str(v) == "Coût de mana converti"
    assert repr(v) == "VariableNumerique('cmc')"
    assert v == VariableNumerique("cmc", 0, 13) and v != VariableNumerique("cmc", 0, 12)
    assert VariableBinaire("tag_a") != VariableCategorielle("tag_a", ["x"])


def test_libelle_de_tag_lisible():
    assert VariableBinaire("tag_mana-rock").libelle == "mana rock"


def test_construire_variables_depuis_metadonnees():
    meta = {"colonnes_entree": ["cmc", "identite_couleur", "tag_ramp", "nb_tags"],
            "variables_categorielles": {"identite_couleur": ["W"]},
            "variables_numeriques": {"cmc": {"minimum": 0.0, "maximum": 13.0},
                                     "tag_ramp": {"minimum": 0.0, "maximum": 1.0},
                                     "nb_tags": {"minimum": 0.0, "maximum": 8.0}}}
    types = [type(v).__name__ for v in construire_variables(meta)]
    assert types == ["VariableNumerique", "VariableCategorielle", "VariableBinaire"]  # nb_tags exclu


def test_construire_variables_metadonnees_incompletes():
    with pytest.raises(DonneeInvalideError, match="incomplètes"):
        construire_variables({"colonnes_entree": []})
