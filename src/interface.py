"""Interface graphique Tkinter. Elle appelle la logique (Predicteur, Historique) sans la contenir."""
from __future__ import annotations

import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src import graphiques
from src.exceptions import DonneeInvalideError, SaisieInvalideError
from src.historique import Historique
from src.predicteur import Predicteur
from src.variables import Variable, VariableCategorielle, VariableNumerique

AVERTISSEMENT = ("Exercice pédagogique (INF1007) : cet outil n'est pas une aide à la décision. "
                 "Projet étudiant non officiel, non approuvé par Wizards of the Coast ni par Scryfall.")


class Application:
    """Fenêtre principale : contient le prédicteur, l'historique et les champs de saisie (composition)."""

    def __init__(self, predicteur: Predicteur, historique: Historique) -> None:
        self._predicteur = predicteur
        self._historique = historique
        self._champs: dict[str, tk.Variable] = {}
        self._derniere = None
        self._racine = tk.Tk()
        self._racine.title("Popularité des commandants Magic")
        self._racine.minsize(1100, 720)
        self._racine.report_callback_exception = self._erreur_inattendue
        self._construire_fenetre()

    # ------------------------------------------------------------ construction
    def _construire_fenetre(self) -> None:
        ttk.Label(self._racine, text="Quelle popularité pour ce commandant ?",
                  font=("TkDefaultFont", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        ttk.Label(self._racine, text=AVERTISSEMENT, foreground="#8a4b00", wraplength=980,
                  justify="left").pack(anchor="w", padx=12, pady=(2, 8))

        corps = ttk.Frame(self._racine)
        corps.pack(fill="both", expand=True, padx=12)
        gauche = ttk.Frame(corps)
        gauche.pack(side="left", fill="y")
        droite = ttk.Frame(corps)
        droite.pack(side="left", fill="both", expand=True, padx=(12, 0))

        variables = self._predicteur.variables
        generales = [v for v in variables if v.TYPE_CHAMP != "case"]
        roles = [v for v in variables if v.TYPE_CHAMP == "case"]
        cadre = ttk.LabelFrame(gauche, text="Caractéristiques de la carte", padding=8)
        cadre.pack(fill="x")
        for ligne, variable in enumerate(generales):
            self._creer_champ(cadre, variable, ligne)
        cadre_roles = ttk.LabelFrame(gauche, text="Rôles de la carte (cochez ceux qui s'appliquent)", padding=8)
        cadre_roles.pack(fill="x", pady=(8, 0))
        for i, variable in enumerate(roles):
            case = tk.IntVar(value=0)
            self._champs[variable.nom] = case
            ttk.Checkbutton(cadre_roles, text=variable.libelle, variable=case).grid(
                row=i // 3, column=i % 3, sticky="w", padx=4, pady=1)

        boutons = ttk.Frame(gauche)
        boutons.pack(fill="x", pady=8)
        ttk.Button(boutons, text="Prédire", command=self._predire).pack(side="left")
        ttk.Button(boutons, text="Réinitialiser", command=self._reinitialiser).pack(side="left", padx=6)
        ttk.Button(boutons, text="Historique", command=self._afficher_historique).pack(side="left")
        self._racine.bind("<Return>", lambda _evenement: self._predire())

        self._statut = tk.StringVar()
        ttk.Label(gauche, textvariable=self._statut, foreground="#b00020", wraplength=480,
                  justify="left").pack(anchor="w")

        resultat = ttk.LabelFrame(droite, text="Résultat", padding=8)
        resultat.pack(fill="x")
        self._texte_resultat = tk.StringVar(value="Remplissez le formulaire puis cliquez sur « Prédire ».")
        ttk.Label(resultat, textvariable=self._texte_resultat, wraplength=440, justify="left").pack(anchor="w")

        self._figure = Figure(figsize=(5.6, 6.2), dpi=72)
        self._toile = FigureCanvasTkAgg(self._figure, master=droite)
        self._toile.get_tk_widget().pack(fill="both", expand=True, pady=(8, 0))
        self._redessiner()

    def _creer_champ(self, parent: ttk.Frame, variable: Variable, ligne: int) -> None:
        """Crée le widget adapté au type de variable (liste déroulante ou champ numérique)."""
        ttk.Label(parent, text=variable.libelle).grid(row=ligne, column=0, sticky="w", pady=2)
        valeur = tk.StringVar()
        self._champs[variable.nom] = valeur
        if isinstance(variable, VariableCategorielle):
            ttk.Combobox(parent, textvariable=valeur, values=variable.valeurs, state="readonly",
                         width=30).grid(row=ligne, column=1, padx=8, pady=2)
        else:
            ttk.Entry(parent, textvariable=valeur, width=32).grid(row=ligne, column=1, padx=8, pady=2)
            if isinstance(variable, VariableNumerique):
                ttk.Label(parent, text=f"{variable.minimum:g} à {variable.maximum:g}",
                          foreground="gray").grid(row=ligne, column=2, sticky="w")

    # ------------------------------------------------------------------ actions
    def _saisies(self) -> dict[str, str]:
        return {nom: str(champ.get()) for nom, champ in self._champs.items()}

    def _predire(self) -> None:
        """Valide, prédit, enregistre dans l'historique et affiche le résultat ; jamais de traceback."""
        try:
            prediction = self._predicteur.predire(self._saisies())
            self._historique.ajouter(prediction)
        except SaisieInvalideError as erreur:
            self._statut.set(str(erreur))
            messagebox.showwarning("Saisie invalide", str(erreur), parent=self._racine)
            return
        except DonneeInvalideError as erreur:
            messagebox.showerror("Erreur", str(erreur), parent=self._racine)
            return
        self._statut.set("")
        self._derniere = prediction
        self._texte_resultat.set(self._predicteur.decrire(prediction))
        self._redessiner()

    def _redessiner(self) -> None:
        graphiques.dessiner(self._figure, self._predicteur.importances(), self._predicteur.taille, self._derniere)
        self._toile.draw()

    def _reinitialiser(self) -> None:
        for nom, champ in self._champs.items():
            champ.set(0 if isinstance(champ, tk.IntVar) else "")
        self._statut.set("")
        self._derniere = None
        self._texte_resultat.set("Remplissez le formulaire puis cliquez sur « Prédire ».")
        self._redessiner()

    def _afficher_historique(self) -> None:
        try:
            lignes = self._historique.lire()
        except DonneeInvalideError as erreur:
            messagebox.showerror("Historique", str(erreur), parent=self._racine)
            return
        if not lignes:
            messagebox.showinfo("Historique", "Aucune prédiction enregistrée.", parent=self._racine)
            return
        fenetre = tk.Toplevel(self._racine)
        fenetre.title(f"Historique ({len(lignes)} prédictions)")
        colonnes = list(lignes[0])
        tableau = ttk.Treeview(fenetre, columns=colonnes, show="headings", height=14)
        for colonne in colonnes:
            tableau.heading(colonne, text=colonne)
            tableau.column(colonne, width=170 if colonne in ("roles", "type_principal") else 95)
        for ligne in sorted(lignes, key=lambda l: l["date"], reverse=True):
            tableau.insert("", "end", values=[ligne[c] for c in colonnes])
        tableau.pack(fill="both", expand=True, padx=8, pady=8)

    def _erreur_inattendue(self, type_erreur, valeur, trace) -> None:
        """Dernier filet : affiche un message simple et garde la trace dans la console."""
        traceback.print_exception(type_erreur, valeur, trace)
        messagebox.showerror("Erreur inattendue", "Une erreur est survenue. L'application reste ouverte.",
                             parent=self._racine)

    def lancer(self) -> None:
        """Démarre la boucle d'événements."""
        self._racine.mainloop()
