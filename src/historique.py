"""Historique des prédictions dans un fichier CSV."""
from __future__ import annotations

import csv
import os
from datetime import datetime

from src.exceptions import DonneeInvalideError
from src.predicteur import Prediction

COLONNES = ["date", "identite_couleur", "type_principal", "cmc", "annee", "roles",
            "position", "borne_basse", "borne_haute"]


class Historique:
    """Ajoute et relit les prédictions d'un fichier CSV (une ligne par prédiction)."""

    def __init__(self, chemin: str) -> None:
        self._chemin = chemin

    @property
    def chemin(self) -> str:
        return self._chemin

    def ajouter(self, prediction: Prediction, horodatage: str | None = None) -> None:
        """Ajoute une ligne ; écrit l'en-tête si le fichier n'existe pas encore."""
        entrees = prediction.entrees
        ligne = {
            "date": horodatage or datetime.now().isoformat(timespec="seconds"),
            "identite_couleur": entrees.get("identite_couleur", ""),
            "type_principal": entrees.get("type_principal", ""),
            "cmc": entrees.get("cmc", ""),
            "annee": entrees.get("annee", ""),
            "roles": ";".join(nom.removeprefix("tag_") for nom, v in entrees.items()
                              if nom.startswith("tag_") and v == 1),
            "position": prediction.position,
            "borne_basse": prediction.borne_basse,
            "borne_haute": prediction.borne_haute,
        }
        nouveau = not os.path.isfile(self._chemin)
        try:
            dossier = os.path.dirname(self._chemin)
            if dossier:
                os.makedirs(dossier, exist_ok=True)
            with open(self._chemin, "a", newline="", encoding="utf-8") as fichier:
                ecrivain = csv.DictWriter(fichier, fieldnames=COLONNES)
                if nouveau:
                    ecrivain.writeheader()
                ecrivain.writerow(ligne)
        except OSError as erreur:
            raise DonneeInvalideError(f"Impossible d'écrire l'historique : {erreur}") from erreur

    def lire(self) -> list[dict[str, str]]:
        """Retourne les lignes enregistrées ([] si le fichier n'existe pas).

        Lève DonneeInvalideError si le fichier est illisible ou n'a pas les bonnes colonnes.
        """
        if not os.path.isfile(self._chemin):
            return []
        try:
            with open(self._chemin, newline="", encoding="utf-8") as fichier:
                lecteur = csv.DictReader(fichier)
                if lecteur.fieldnames != COLONNES:
                    raise DonneeInvalideError(f"Colonnes inattendues dans {self._chemin}.")
                return list(lecteur)
        except (OSError, UnicodeDecodeError, csv.Error) as erreur:
            raise DonneeInvalideError(f"Historique illisible : {erreur}") from erreur

    def __len__(self) -> int:
        return len(self.lire())
