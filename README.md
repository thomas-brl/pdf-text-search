# Recherche PDF

Une application ([Flask](https://flask.palletsprojects.com/) + [pywebview](https://pywebview.flowrl.com/)) qui recherche une entrée dans tous les PDF d'un dossier (y compris les sous-dossiers), affiche les documents correspondants, et ouvre un PDF directement à la bonne page.

## Fonctionnalités

- Recherche de texte dans tous les PDF d'un dossier, de manière récursive.
- Résultats regroupés par document, avec la liste des pages contenant le mot recherché.
- Ouvre un document directement dans l'application, à la page correspondante.

## Prérequis

- Python 3.9+
- Flask
- PDFplumber
- PyWebView
