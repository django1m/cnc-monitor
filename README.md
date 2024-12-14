# CNC Visualizer

Application web pour la surveillance et la gestion des routeurs CNC AXYZ équipés de contrôleurs A2MC.

## Fonctionnalités

- Tableau de bord des KPI pour chaque machine CNC
- Configuration des machines CNC (IP, horaires de travail)
- Collecte automatique des données via SMB
- Interface utilisateur moderne et responsive
- Gestion des utilisateurs avec différents niveaux d'accès

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Accès réseau aux machines CNC via SMB

## Installation

1. Cloner le dépôt :
```bash
git clone <url-du-depot>
cd cnc-visualizer
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancer l'application :
```bash
python app.py
```

L'application sera accessible à l'adresse : http://localhost:5000

## Configuration initiale

1. Connectez-vous avec les identifiants par défaut :
   - Utilisateur : admin
   - Mot de passe : admin

2. Allez dans les paramètres pour configurer vos machines CNC :
   - Ajoutez chaque machine avec son nom et son adresse IP
   - Configurez les horaires de travail pour chaque machine

## Structure du projet

- `app.py` : Application principale Flask
- `templates/` : Templates HTML
  - `base.html` : Template de base avec la navigation
  - `login.html` : Page de connexion
  - `dashboard.html` : Tableau de bord
  - `settings.html` : Page de configuration

## Sécurité

- Changez le mot de passe administrateur après la première connexion
- L'application utilise Flask-Login pour la gestion des sessions
- Les mots de passe sont stockés de manière sécurisée dans la base de données

## Maintenance

Les fichiers CSV sont collectés automatiquement toutes les heures et stockés dans le dossier `/tmp/CNC_X` où X est l'ID de la machine.

## Support

Pour toute question ou problème, veuillez créer une issue dans le dépôt GitHub.
