# Dashboard — Tickets de support informatique

Application interactive construite avec **Streamlit, pandas et Matplotlib** pour analyser le classeur `01_Technologie_IT.xlsx` et répondre aux six questions de la feuille **Mode d'emploi**.

## Fichiers

- `app.py` : application Streamlit.
- `requirements.txt` : dépendances Python (une copie `requirement.txt` est également fournie).
- `01_Technologie_IT.xlsx` : données source.

## Questions couvertes

1. Quels types de demandes représentent le plus de tickets ?
2. Quel service reçoit le plus de tickets et quel est son délai médian de résolution ?
3. Quelle part des tickets résolus dépasse l’objectif SLA ? Comparaison par priorité.
4. Les canaux d’entrée diffèrent-ils en temps de première réponse ?
5. Comment le volume de tickets et les dépassements SLA évoluent-ils par mois ?
6. Quelle action concrète proposer au responsable du support ?

## Installation sous Windows avec VS Code

Ouvrez le dossier du projet dans VS Code, puis ouvrez **Terminal → New Terminal**.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Si PowerShell empêche l'activation de l'environnement, utilisez l'invite de commandes (`cmd`) :

```bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Ouvrez ensuite l'URL affichée dans le terminal, généralement `http://localhost:8501`.

## Utiliser les données

Par défaut, l'application recherche `01_Technologie_IT.xlsx` dans le même dossier que `app.py`. Le fichier fourni dans ce projet est déjà renommé ainsi. Vous pouvez également charger un classeur `.xlsx` depuis la barre latérale.

Le classeur doit contenir une feuille `Données` et les colonnes utilisées dans le fichier source.

## Méthode de calcul SLA

Un ticket est considéré comme hors SLA si sa durée de résolution est strictement supérieure à l'objectif SLA. Le taux est calculé seulement sur les tickets résolus avec durée de résolution et objectif SLA renseignés. Les tickets en cours ne sont pas comptés comme des dépassements.

## Dépannage

- **`streamlit` n'est pas reconnu** : activez l'environnement virtuel et essayez `python -m streamlit run app.py`.
- **Erreur de fichier Excel** : vérifiez que le classeur est dans le dossier de `app.py` et que la feuille s'appelle `Données`.
- **Aucun résultat affiché** : réinitialisez ou élargissez les filtres dans la barre latérale.
