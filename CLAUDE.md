# Claude Code Configuration

## Git Commit Rules

Pour éviter d'ajouter Claude comme co-auteur automatiquement dans les commits, utilisez des messages de commit simples sans les lignes :

```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Commandes recommandées

```bash
# Commit simple sans co-auteur
git commit -m "Your commit message here"

# Vérification avant commit
git status
git diff --name-only

# Push vers le repo
git push origin main
```

## Notes
- Ce fichier CLAUDE.md sert de référence pour les règles de commit
- Les commits peuvent être faits avec ou sans co-auteur selon les préférences
- Le workflow reste inchangé pour le développement