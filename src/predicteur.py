"""Chargement du modèle sauvegardé et prédiction à partir de saisies validées."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import joblib
import numpy as np
import pandas as pd

from src.donnees import charger_json
from src.exceptions import DonneeInvalideError, SaisieInvalideError
from src.variables import COLONNE_NB_TAGS, LIBELLES, Variable, VariableBinaire, construire_variables

PERCENTILES_FOURCHETTE = (10, 90)  # 80 % des arbres de la forêt sont dans la fourchette


@dataclass(frozen=True)
class Prediction:
    """Résultat d'une prédiction : position estimée, fourchette et saisies utilisées."""

    position: int
    borne_basse: int
    borne_haute: int
    entrees: dict = field(default_factory=dict)


def ordinal(n: int) -> str:
    """Retourne l'ordinal français abrégé : 1 -> « 1er », 12 -> « 12e »."""
    return "1er" if n == 1 else f"{n}e"


class Predicteur:
    """Charge le pipeline joblib et ses métadonnées, valide les saisies et prédit.

    Contient (composition) la liste des variables construites depuis les métadonnées.
    Le modèle n'est jamais ré-entraîné.
    """

    def __init__(self, chemin_modele: str, chemin_metadonnees: str) -> None:
        for chemin in (chemin_modele, chemin_metadonnees):
            if not os.path.isfile(chemin):
                raise DonneeInvalideError(
                    f"Fichier introuvable : {chemin}. Lancez « python -m src.main entrainer ».")
        self._metadonnees = charger_json(chemin_metadonnees)
        try:
            self._modele = joblib.load(chemin_modele)
        except (OSError, EOFError, ValueError, AttributeError, ImportError) as erreur:
            raise DonneeInvalideError(
                f"Modèle illisible ({chemin_modele}) : {erreur}. Relancez « entrainer ».") from erreur
        self._variables = construire_variables(self._metadonnees)
        self._libelles = {v.nom: v.libelle for v in self._variables} | LIBELLES

    @property
    def variables(self) -> list[Variable]:
        return list(self._variables)

    @property
    def metadonnees(self) -> dict:
        return self._metadonnees

    @property
    def taille(self) -> int:
        """Nombre de positions possibles (taille du jeu d'entraînement)."""
        return int(self._metadonnees["taille_jeu_de_donnees"])

    def valider(self, saisies: dict[str, str]) -> dict[str, float | int | str]:
        """Valide toutes les saisies et calcule `nb_tags`.

        Lève SaisieInvalideError avec un message par champ fautif (un champ absent compte comme vide).
        """
        valeurs: dict[str, float | int | str] = {}
        erreurs: list[str] = []
        for variable in self._variables:
            try:
                valeurs[variable.nom] = variable.valider(saisies.get(variable.nom, ""))
            except SaisieInvalideError as erreur:
                erreurs.append(str(erreur))
        if erreurs:
            raise SaisieInvalideError("\n".join(erreurs))
        if COLONNE_NB_TAGS in self._metadonnees["colonnes_entree"]:
            valeurs[COLONNE_NB_TAGS] = sum(
                valeurs[v.nom] for v in self._variables if isinstance(v, VariableBinaire))
        return valeurs

    def predire(self, saisies: dict[str, str]) -> Prediction:
        """Prédit la position d'un commandant ; la fourchette vient de la dispersion des arbres."""
        valeurs = self.valider(saisies)
        ligne = pd.DataFrame([valeurs], columns=self._metadonnees["colonnes_entree"])
        try:
            matrice = self._modele.named_steps["preparation"].transform(ligne)
            arbres = np.array([a.predict(matrice)[0] for a in self._modele.named_steps["regression"].estimators_])
        except (KeyError, AttributeError, ValueError) as erreur:
            raise DonneeInvalideError(f"Le modèle sauvegardé n'a pas la forme attendue : {erreur}") from erreur
        bas, haut = np.percentile(arbres, PERCENTILES_FOURCHETTE)
        limiter = lambda x: int(min(max(round(float(x)), 1), self.taille))  # noqa: E731
        return Prediction(limiter(arbres.mean()), limiter(bas), limiter(haut), valeurs)

    def niveau_confiance(self) -> str:
        """Compare l'erreur du modèle à celle de la référence : « faible », « moyenne » ou « bonne »."""
        metriques = self._metadonnees["metriques"]
        rapport = metriques["mae_modele"] / metriques["mae_reference_moyenne"]
        return "faible" if rapport >= 0.95 else "moyenne" if rapport >= 0.8 else "bonne"

    def decrire(self, prediction: Prediction) -> str:
        """Résume la prédiction pour un non-informaticien."""
        metriques = self._metadonnees["metriques"]
        return (
            f"Estimation : environ le {ordinal(prediction.position)} commandant le plus populaire "
            f"sur {self.taille}.\n"
            f"Fourchette (80 % des arbres de la forêt) : de la {ordinal(prediction.borne_basse)} "
            f"à la {ordinal(prediction.borne_haute)} position.\n"
            f"Confiance : {self.niveau_confiance()}. Sur des cartes jamais vues, le modèle se trompe "
            f"en moyenne de {metriques['mae_modele']:.0f} positions "
            f"(deviner la moyenne se trompe de {metriques['mae_reference_moyenne']:.0f})."
        )

    def importances(self, n: int = 10) -> list[tuple[str, float]]:
        """Retourne les `n` variables les plus importantes (colonnes encodées regroupées par variable)."""
        pipeline = self._modele
        noms = pipeline.named_steps["preparation"].get_feature_names_out()
        poids = pipeline.named_steps["regression"].feature_importances_
        categories = list(self._metadonnees["variables_categorielles"])
        totaux: dict[str, float] = {}
        for nom, poids_colonne in zip(noms, poids):
            brut = nom.split("__", 1)[-1]
            origine = next((c for c in categories if brut.startswith(c + "_")), brut)
            totaux[origine] = totaux.get(origine, 0.0) + float(poids_colonne)
        classement = sorted(totaux.items(), key=lambda paire: paire[1], reverse=True)[:n]
        return [(self._libelles.get(nom, nom), valeur) for nom, valeur in classement]
