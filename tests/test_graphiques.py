"""Tests du graphique de l'interface (Figure Matplotlib, sans fenêtre)."""
from matplotlib.figure import Figure

from src import graphiques
from src.predicteur import Prediction


def test_dessiner_sans_prediction(predicteur):
    figure = Figure()
    graphiques.dessiner(figure, predicteur.importances(), predicteur.taille)
    haut, bas = figure.axes
    assert haut.get_title() and "Lancez" in bas.texts[0].get_text()


def test_dessiner_avec_prediction_a_titre_axes_et_legende(predicteur):
    figure = Figure()
    graphiques.dessiner(figure, predicteur.importances(3), 1000, Prediction(500, 400, 600))
    haut, bas = figure.axes
    assert len(haut.patches) == 3
    assert bas.get_xlabel() and haut.get_xlabel()
    assert bas.lines[0].get_xdata()[0] == 500
    assert "Prédiction : 500" in [t.get_text() for t in bas.get_legend().get_texts()]


def test_dessiner_efface_le_dessin_precedent(predicteur):
    figure = Figure()
    for _ in range(2):
        graphiques.dessiner(figure, predicteur.importances(), predicteur.taille)
    assert len(figure.axes) == 2
