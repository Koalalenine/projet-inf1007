"""Variables d'entrée du modèle : classe abstraite et trois classes enfants (polymorphisme).

Chaque variable sait valider une saisie textuelle à sa façon. L'interface ne contient
aucune règle de validation : elle appelle simplement `valider`.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod

from src.exceptions import DonneeInvalideError, SaisieInvalideError

COLONNE_NB_TAGS = "nb_tags"  # calculée automatiquement : somme des cases cochées
LIBELLES = {
    "cmc": "Coût de mana converti",
    "annee": "Année de sortie",
    "identite_couleur": "Identité de couleur",
    "type_principal": "Type principal",
    COLONNE_NB_TAGS: "Nombre de rôles",
}


class Variable(ABC):
    """Une variable d'entrée : un nom de colonne, un libellé lisible et une règle de validation."""

    TYPE_CHAMP = "nombre"  # type de champ proposé par l'interface : nombre, liste ou case

    def __init__(self, nom: str, libelle: str | None = None) -> None:
        self._nom = nom
        self._libelle = libelle or LIBELLES.get(nom, nom.removeprefix("tag_").replace("-", " "))

    @property
    def nom(self) -> str:
        """Nom de la colonne dans le jeu de données."""
        return self._nom

    @property
    def libelle(self) -> str:
        """Texte affiché à l'utilisateur."""
        return self._libelle

    @abstractmethod
    def valider(self, saisie: str) -> float | int | str:
        """Convertit la saisie en valeur utilisable ; lève SaisieInvalideError si elle est refusée."""

    def _refuser(self, raison: str) -> SaisieInvalideError:
        return SaisieInvalideError(f"« {self._libelle} » : {raison}")

    def __str__(self) -> str:
        return self._libelle

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._nom!r})"

    def __eq__(self, autre: object) -> bool:
        return type(self) is type(autre) and self.__dict__ == autre.__dict__

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._nom))


class VariableNumerique(Variable):
    """Nombre compris entre `minimum` et `maximum` (accepte la virgule décimale)."""

    TYPE_CHAMP = "nombre"

    def __init__(self, nom: str, minimum: float, maximum: float, entier: bool = False,
                 libelle: str | None = None) -> None:
        super().__init__(nom, libelle)
        if minimum > maximum:
            raise DonneeInvalideError(f"Intervalle invalide pour {nom} : {minimum} > {maximum}.")
        self._minimum = minimum
        self._maximum = maximum
        self._entier = entier

    @property
    def minimum(self) -> float:
        return self._minimum

    @property
    def maximum(self) -> float:
        return self._maximum

    def valider(self, saisie: str) -> float | int:
        texte = str(saisie).strip().replace(",", ".")
        if not texte:
            raise self._refuser("ce champ est vide.")
        try:
            valeur = float(texte)
        except ValueError:
            raise self._refuser(f"« {saisie} » n'est pas un nombre.") from None
        if not math.isfinite(valeur):
            raise self._refuser("la valeur doit être un nombre fini.")
        if not self._minimum <= valeur <= self._maximum:
            raise self._refuser(f"la valeur doit être entre {self._minimum:g} et {self._maximum:g}.")
        if self._entier:
            if not valeur.is_integer():
                raise self._refuser("la valeur doit être un nombre entier.")
            return int(valeur)
        return valeur


class VariableCategorielle(Variable):
    """Choix parmi une liste de valeurs connues du modèle."""

    TYPE_CHAMP = "liste"

    def __init__(self, nom: str, valeurs: list[str], libelle: str | None = None) -> None:
        super().__init__(nom, libelle)
        if not valeurs:
            raise DonneeInvalideError(f"Aucune valeur possible pour {nom}.")
        self._valeurs = list(valeurs)

    @property
    def valeurs(self) -> list[str]:
        return list(self._valeurs)

    def valider(self, saisie: str) -> str:
        texte = str(saisie).strip()
        if not texte:
            raise self._refuser("aucun choix sélectionné.")
        if texte not in self._valeurs:
            raise self._refuser(f"« {texte} » n'est pas un choix possible.")
        return texte


class VariableBinaire(Variable):
    """Case à cocher : 0/1 ou non/oui."""

    TYPE_CHAMP = "case"
    _VALEURS = {"0": 0, "non": 0, "1": 1, "oui": 1}

    def valider(self, saisie: str) -> int:
        texte = str(saisie).strip().lower()
        if texte not in self._VALEURS:
            raise self._refuser("la valeur doit être 0 ou 1 (non ou oui).")
        return self._VALEURS[texte]


def construire_variables(metadonnees: dict) -> list[Variable]:
    """Construit les variables à saisir à partir des métadonnées JSON du modèle.

    La colonne `nb_tags` est exclue : le prédicteur la calcule. Lève DonneeInvalideError
    si une clé attendue manque dans les métadonnées.
    """
    try:
        colonnes = metadonnees["colonnes_entree"]
        categories = metadonnees["variables_categorielles"]
        nombres = metadonnees["variables_numeriques"]
    except KeyError as erreur:
        raise DonneeInvalideError(f"Métadonnées incomplètes : clé {erreur} absente.") from erreur

    variables: list[Variable] = []
    for nom in colonnes:
        if nom == COLONNE_NB_TAGS:
            continue
        if nom in categories:
            variables.append(VariableCategorielle(nom, categories[nom]))
        elif nom in nombres:
            bornes = nombres[nom]
            if nom.startswith("tag_") and bornes["minimum"] == 0 and bornes["maximum"] == 1:
                variables.append(VariableBinaire(nom))
            else:
                variables.append(VariableNumerique(
                    nom, bornes["minimum"], bornes["maximum"], entier=(nom == "annee")))
        else:
            raise DonneeInvalideError(f"Colonne « {nom} » absente des métadonnées.")
    return variables
