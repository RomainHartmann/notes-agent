# Instructions projet

## Langue

- Toujours communiquer en français avec l'utilisateur
- Le code reste en anglais
- Pas de commentaires dans le code
- Un fichier = une responsabilité

## Git

- Commits : `type(scope): description` (ex: `feat(auth): add JWT refresh`)
- Types : feat, fix, refactor, test, chore, docs
- Un commit par changement logique, pas par fichier
- Quand l'utilisateur valide une feature ("ok", "c'est bon", "valide", "push", "ship it"), faire `git add . && git commit && git push` immédiatement sans demander confirmation
- Ne jamais laisser du travail non commité après validation
- Ne jamais discard/revert du code (git checkout, git reset, etc.) sans demander confirmation

## Co-Authored-By

- Ajouter `Co-Authored-By: Claude <noreply@anthropic.com>` uniquement quand Claude a réellement contribué au code (logique, architecture, implémentation)
- Ne pas l'ajouter sur les commits triviaux (renommage de variable, formatage, déplacement de fichier)

## Known Gotchas

_Ajouter ici les problèmes rencontrés. Format :_

- _[date] description du problème et règle pour l'éviter_

## Lessons Learned

_Quand l'utilisateur me corrige ou que je fais une erreur, ajouter une règle ici. Court et actionnable. Nettoyer régulièrement les doublons et règles obsolètes._
