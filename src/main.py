"""Point d'entrée : collecte, vérification, entraînement et interface graphique.

Usage (depuis la racine du dépôt) :
    python -m src.main collecter [--nombre 1000] [--tags ramp,removal,...]
    python -m src.main verifier
    python -m src.main entrainer
    python -m src.main interface
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from src import donnees, modele
from src.historique import Historique
from src.predicteur import Predicteur
from src.exceptions import DonneeInvalideError, ScryfallError

DOSSIER = "donnees"
CSV = os.path.join(DOSSIER, "commandants_top1000.csv")
CACHE_TOP = os.path.join(DOSSIER, "cache_top.json")
CACHE_TAGS = os.path.join(DOSSIER, "cache_otags.json")
GRAPHIQUE = os.path.join(DOSSIER, "identites_couleur.png")
DOSSIER_MODELES = "modeles"
FICHIER_MODELE = os.path.join(DOSSIER_MODELES, "commandants_random_forest.joblib")
METADONNEES_MODELE = os.path.join(DOSSIER_MODELES, "commandants_metadata.json")
GRAPHIQUE_EVALUATION = os.path.join(DOSSIER_MODELES, "predit_contre_reel.png")
FICHIER_HISTORIQUE = os.path.join(DOSSIER, "historique_predictions.csv")


def commande_collecter(nombre: int, tags: list[str]) -> None:
    """Télécharge le top, interroge les otags, écrit le CSV et le graphique."""
    top = donnees.collecter_top_commandants(nombre, CACHE_TOP)
    par_tag = donnees.collecter_otags({c["id"] for c in top}, tags, CACHE_TAGS)
    df = donnees.construire_dataframe(top, par_tag)
    donnees.sauvegarder_csv(df, CSV)
    donnees.graphique_identites(df, GRAPHIQUE)
    print(f"{len(df)} lignes écrites dans {CSV}")


def commande_verifier() -> None:
    """Affiche forme, types, valeurs manquantes et bilan des critères."""
    if not os.path.exists(CSV):
        raise DonneeInvalideError(
            f"{CSV} introuvable : lancez d'abord « python -m src.main collecter ».")
    df = pd.read_csv(CSV)
    print("Forme :", df.shape)
    print(df.dtypes.to_string())
    print("Valeurs manquantes :", int(df.isna().sum().sum()))
    for critere, ok in donnees.verifier_criteres(df).items():
        print(f"[{'OK' if ok else 'ÉCHEC'}] {critere}")


def commande_entrainer() -> None:
    """Entraîne et évalue le modèle, puis enregistre ses fichiers."""
    resultat = modele.entrainer_depuis_csv(
        CSV,
        FICHIER_MODELE,
        METADONNEES_MODELE,
        GRAPHIQUE_EVALUATION,
    )
    print(f"MAE du modèle : {resultat.metriques['mae_modele']:.1f} positions")
    print(f"MAE de la référence moyenne : {resultat.metriques['mae_reference_moyenne']:.1f} positions")
    print(f"R² du modèle : {resultat.metriques['r2_modele']:.3f}")
    print(f"Modèle enregistré dans {FICHIER_MODELE}")
    print(f"Métadonnées enregistrées dans {METADONNEES_MODELE}")
    print(f"Graphique enregistré dans {GRAPHIQUE_EVALUATION}")


def commande_interface() -> None:
    """Charge le modèle sauvegardé (sans le ré-entraîner) et ouvre la fenêtre."""
    predicteur = Predicteur(FICHIER_MODELE, METADONNEES_MODELE)
    try:
        from src.interface import Application  # import tardif : Tkinter n'est pas requis pour les tests
    except ImportError as erreur:
        raise DonneeInvalideError(
            f"Tkinter est introuvable ({erreur}). Sous Linux : sudo apt install python3-tk.") from erreur
    Application(predicteur, Historique(FICHIER_HISTORIQUE)).lancer()


def main() -> None:
    """Analyse les arguments et exécute la commande demandée."""
    parseur = argparse.ArgumentParser(description="Projet 2 INF1007 : commandants et otags")
    sous = parseur.add_subparsers(dest="commande", required=True)
    collecte = sous.add_parser("collecter", help="télécharger et construire le CSV")
    collecte.add_argument("--nombre", type=int, default=1000)
    collecte.add_argument("--tags", default=",".join(donnees.TAGS_PAR_DEFAUT),
                          help="otags séparés par des virgules")
    sous.add_parser("verifier", help="vérifier les critères du jeu de données")
    sous.add_parser("entrainer", help="entraîner, évaluer et sauvegarder le modèle")
    sous.add_parser("interface", help="ouvrir l'interface graphique")
    args = parseur.parse_args()

    try:
        if args.commande == "collecter":
            commande_collecter(args.nombre, [t.strip() for t in args.tags.split(",") if t.strip()])
        elif args.commande == "verifier":
            commande_verifier()
        elif args.commande == "interface":
            commande_interface()
        else:
            commande_entrainer()
    except (ScryfallError, DonneeInvalideError) as erreur:
        print(f"Erreur : {erreur}")


if __name__ == "__main__":
    main()
