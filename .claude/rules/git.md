# Git Conventions

- Commit format: `type(scope): description` (e.g. `feat(tasks): add PR mode`)
- Types: feat, fix, refactor, test, chore, docs
- Scope: the module name (`tasks`, `analysis`, `notes`, `config`, `state`, `notifications`)
- One commit per logical change, not per file
- When user validates ("ok", "c'est bon", "valide", "push", "ship it") → commit and push immediately
- Never leave uncommitted work after validation
- Never discard/revert code (`git checkout`, `git reset`, etc.) without asking
- Co-Authored-By: `Claude <noreply@anthropic.com>` only on genuine code contributions, not trivial changes
- Git worktrees are used for parallel isolated task execution — never modify worktree logic without understanding the full flow in tasks.py
