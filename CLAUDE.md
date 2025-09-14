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

## Règles de Développement Data

### Consultation Obligatoire du Framework

**IMPORTANT** : Avant toute implémentation ou réponse concernant l'architecture data, Claude DOIT systématiquement consulter et appliquer les standards définis dans `framework.md`.

#### Règles strictes :

1. **Lecture préalable** : Toujours lire `framework.md` avant d'implémenter un cas d'usage

#### En cas de nouveau cas d'usage :

1. Identifier le pattern applicable depuis `framework.md`
2. Adapter le template du pattern choisi
3. Respecter toutes les conventions et standards
4. Proposer une évolution du framework si aucun pattern ne correspond

#### Exemples d'application :

- Pour ingestion CSV : utiliser Pattern 1 avec les templates associés
- Pour orchestration complexe : utiliser Pattern 2 avec Cloud Composer
- Toujours créer d'abord STG (table externe) puis ODS (table matérialisée)

## Notes
- Ce fichier CLAUDE.md sert de référence pour les règles de commit et de développement
- Les commits peuvent être faits avec ou sans co-auteur selon les préférences
- Le workflow reste inchangé pour le développement
- **Le framework.md est LA référence technique obligatoire pour tous les développements data**