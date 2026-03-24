# notes-watcher — Plan du projet

## Objectif

Construire un outil d'automatisation personnel, propre et maintenable, qui tourne en arrière-plan sur un Mac mini M4. Il surveille un dossier dans Apple Notes (iCloud), analyse chaque note via l'API Claude, et agit en conséquence : ouvre Claude Code dans un Terminal sur le bon repo, ou écrit une réponse directement dans la note.

Ce projet est destiné à être public sur GitHub. Le code, l'architecture, le README et les messages de commit doivent tous refléter un niveau de qualité professionnel.

---

## Standards attendus

- Code sobre, lisible, sans commentaires inutiles
- Chaque fonction fait une seule chose
- Aucune valeur en dur dans le code : tout passe par `config.json`
- Gestion d'erreur explicite partout (API, AppleScript, fichiers)
- Logs structurés avec timestamp dans `watcher.log`
- Zéro dépendance externe : uniquement la stdlib Python
- Messages de commit descriptifs et précis
- README soigné, pensé pour un visiteur GitHub qui découvre le projet

---

## Structure des fichiers

```
notes-watcher/
├── watcher.py
├── config.json
├── config.example.json
├── install.sh
├── .gitignore
└── README.md
```

---

## Fichiers à créer ou finaliser

### `watcher.py`

Script principal. Exécuté toutes les minutes par launchd.

Flux d'exécution :

1. Charger `config.json`
2. Interroger Notes.app via AppleScript pour lister les notes sans tag de traitement dans le dossier configuré
3. Pour chaque note : extraire titre + corps via fichier temporaire
4. Envoyer à l'API Claude pour analyse
5. Agir selon le résultat (voir logique métier ci-dessous)
6. Taguer la note
7. Logger le résultat

Règles importantes :

- Une note peut contenir plusieurs éléments indépendants. Claude retourne un tableau `"items"`, chaque item est traité séparément.
- Note avec corps vide : Claude déduit depuis le titre uniquement
- Note avec titre et corps vides : ignorée, loguée
- Deux tâches simultanées ouvrent deux Terminals indépendants (pas de séquencement, chaque tâche a sa propre branche git)

### `config.json` (non commité)

```json
{
  "notes_folder": "MonProjet",
  "processed_tag": "claude-done",
  "exists_tag": "claude-exists",
  "frontend_path": "/chemin/vers/repo-flutter",
  "backend_path": "/chemin/vers/repo-backend",
  "dev_branch": "dev",
  "anthropic_api_key": "sk-ant-...",
  "pushover_app_token": "...",
  "pushover_user_key": "..."
}
```

### `config.example.json` (commité)

Même structure que `config.json` mais avec toutes les valeurs remplacées par des chaînes vides ou des placeholders explicites. C'est ce fichier que le visiteur GitHub voit.

### `install.sh`

Génère et charge un agent launchd dans `~/Library/LaunchAgents/`. Doit :

- Décharger l'ancien agent s'il existe avant de recharger
- Afficher le chemin du log à la fin

### `.gitignore`

Doit contenir au minimum :

```
config.json
watcher.log
__pycache__/
*.pyc
```

### `README.md`

Voir section dédiée ci-dessous.

---

## Logique métier

### Détection des notes non traitées

Une note est considérée non traitée si son corps ne contient ni `#claude-done` ni `#claude-exists`.

### Appel API Claude

Modèle : `claude-sonnet-4-20250514`

Le prompt demande à Claude de retourner uniquement un JSON valide (pas de markdown, pas de backticks) avec un tableau `"items"`. Chaque item a un `"type"` qui est soit `"task"` soit `"reflection"`.

En cas d'ambiguïté sur le type d'un item, Claude choisit le type dominant.

Structure attendue :

```json
{
  "items": [
    {
      "type": "task",
      "target": "frontend",
      "branch_name": "feat/nom-de-la-feature",
      "task_description": "description courte de la tâche"
    },
    {
      "type": "reflection",
      "response": "réponse structurée en texte brut, dans la même langue que la note",
      "pushover_summary": "résumé court max 100 caractères"
    }
  ]
}
```

Règles de déduction pour `target` :

- `frontend` : Flutter, widget, screen, UI, style, layout, animation, page, composant
- `backend` : API, base de données, serveur, route, endpoint, modèle, auth, requête, migration, cron

### Traitement d'un item `task`

1. Taguer immédiatement la note avec `#claude-done` (évite le double-traitement si Claude Code prend du temps)
2. Construire le prompt complet pour Claude Code (voir ci-dessous)
3. Écrire le prompt dans un fichier temporaire
4. Créer un script shell temporaire qui `cd` dans le bon repo et lance `claude "$TASK"`
5. Ouvrir un Terminal via AppleScript et exécuter ce script
6. Envoyer une notification Pushover : `🛠 Tâche lancée : [titre de la note]` / `[frontend ou backend] - [branch_name]`

Contenu du prompt envoyé à Claude Code :

```
Tu es Claude Code. Voici ta mission :

1. Analyse le contenu du projet pour comprendre la base de code existante.

2. Vérifie si la fonctionnalité ou le correctif demandé existe déjà dans le code.

3a. Si ça EXISTE DÉJÀ sans modification nécessaire :
    - Ne crée pas de branche, ne fais aucun commit.
    - Exécute cette commande osascript pour remplacer #claude-done par #claude-exists dans la note.
    - Explique brièvement ce que tu as trouvé.

3b. Si ça N'EXISTE PAS encore :
    - git checkout [dev_branch] && git pull
    - git checkout -b [branch_name]
    - Implémente les modifications nécessaires.
    - git add -A && git commit -m "message descriptif expliquant ce qui a changé et pourquoi"
    - git checkout [dev_branch] && git merge [branch_name]

Demande : [task_description]
```

### Traitement d'un item `reflection`

1. Écrire la réponse dans la note sous un séparateur `---`
2. Envoyer une notification Pushover : `💡 [titre de la note]` / `[pushover_summary]`
3. Taguer la note avec `#claude-done`

### Tags

- `#claude-done` : note traitée (tâche lancée ou réflexion répondue)
- `#claude-exists` : tâche détectée par Claude Code comme déjà existante dans le code, posé par Claude Code lui-même via osascript en remplacement de `#claude-done`
- Pas de Pushover pour `#claude-exists`

---

## README.md

Le README doit être sobre, bien structuré, et immédiatement compréhensible pour un visiteur qui ne connaît pas le projet.

Structure attendue :

```
# notes-watcher

[phrase d'accroche] : "J'écris une note sur mon iPhone → l'IA code la feature et merge automatiquement."

[section philosophie — 3 à 5 lignes, ton direct, pas de jargon]

L'idée ici est que la qualité de ce qu'on construit n'est plus limitée par le temps passé à coder,
mais par la qualité des idées qu'on a. Une pensée dans le métro, une idée sous la douche, une
question à 23h : au lieu de disparaître, elles deviennent des commits. Il n'y a plus besoin d'avoir
la tête dans le code pour chaque impulsion. L'idée devient le projet.

Ce n'est pas toujours parfait. Claude Code fait un premier jet, parfois il faut reprendre. Mais le
cap est franchi : l'intention suffit à déclencher le travail.

## Comment ça marche
Schéma du workflow en texte ou ASCII art (Note iPhone → iCloud → Mac mini → watcher.py → Claude API → Claude Code / Réponse dans la note)

## Fonctionnalités
Liste concise

## Prérequis
- macOS (Mac mini recommandé, toujours allumé)
- Python 3
- Claude Code CLI installé
- Clé API Anthropic
- Compte Pushover

## Installation
Étapes numérotées, commandes copiables

## Configuration
Description de chaque champ de config.example.json

## Stack
Python · AppleScript · launchd · Anthropic API · Claude Code CLI · Pushover · Git
```

Le README ne doit pas être sur-documenté. Chaque section doit être courte et directe.
La section philosophie est la seule qui peut être un peu plus longue : c'est ce qui donne du sens au projet pour un visiteur GitHub.

---

## Ce qui n'est PAS dans ce projet (pour l'instant)

- Workflow GitHub Actions (TestFlight + Google Play) : prévu, sera dans un fichier séparé
- Interface graphique
- Support multi-dossiers
- Support Windows ou Linux
