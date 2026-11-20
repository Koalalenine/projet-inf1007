"""Graphique Matplotlib de l'interface (dessiné sur une Figure fournie, sans pyplot)."""
from __future__ import annotations

from matplotlib.figure import Figure

from src.predicteur import Prediction


def dessiner(figure: Figure, importances: list[tuple[str, float]], taille: int,
             prediction: Prediction | None = None) -> None:
    """Efface `figure` puis dessine l'importance des variables et la position prédite."""
    figure.clear()
    haut, bas = figure.subplots(2, 1, gridspec_kw={"height_ratios": [3, 1.4]})

    libelles = [nom for nom, _ in reversed(importances)]
    valeurs = [100 * v for _, v in reversed(importances)]
    haut.barh(libelles, valeurs, color="#4a7fb5", label="Part de l'importance")
    haut.set_title("Variables les plus influentes du modèle", fontsize=11)
    haut.set_xlabel("Importance (% de la décision de la forêt)")
    haut.tick_params(axis="y", labelsize=8)

    bas.set_xlim(1, taille)
    bas.set_yticks([])
    bas.set_xlabel("Position (1 = le plus populaire)")
    bas.set_title("Position prédite", fontsize=11)
    if prediction is None:
        bas.text(0.5, 0.5, "Lancez une prédiction", ha="center", va="center", transform=bas.transAxes)
    else:
        bas.axvspan(prediction.borne_basse, prediction.borne_haute, alpha=0.3, color="#4a7fb5",
                    label="Fourchette (80 % des arbres)")
        bas.axvline(prediction.position, color="crimson", linewidth=2,
                    label=f"Prédiction : {prediction.position}")
        bas.legend(loc="upper center", bbox_to_anchor=(0.5, -0.55), ncol=2, fontsize=8, frameon=False)
    figure.tight_layout()
