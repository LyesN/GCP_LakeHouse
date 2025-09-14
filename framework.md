# Framework GCP Data Lakehouse

## Introduction

Ce framework définit les standards et patterns d'implémentation pour la construction de pipelines de données sur Google Cloud Platform. Il vise à assurer la cohérence, la maintenabilité et la scalabilité des solutions data.

## Stack Technique Autorisé

Les développements du projet sont **strictement limités** aux services GCP suivants :

| Service | Rôle | Usage |
|---------|------|-------|
| **BigQuery** | Data Warehouse | Stockage et requêtage des données structurées |
| **Dataform** | ELT/Orchestration | Transformations SQL et gestion des dépendances |
| **Cloud Storage** | Data Lake | Stockage des fichiers raw (CSV, JSON, Parquet) |
| **Cloud Composer** | Orchestration | Workflows complexes et scheduling |
| **Cloud Function** | Microservices | Fonctions serverless pour événements |
| **Dataproc** | Big Data Processing | Traitement Spark/Hadoop si nécessaire |
| **Cloud Run** | Services | Applications conteneurisées |

## Architecture en Couches

Le framework impose une architecture en **3 couches** :

```
RAW (Cloud Storage) → STG (01_STG) → ODS (02_ODS)
```

### Couche RAW
- **Stockage** : Cloud Storage buckets
- **Format** : Fichiers bruts (CSV, JSON, Parquet)
- **Naming** : `gs://{project}-bucket-{date}/`

### Couche STG (Staging - 01_STG)
- **Stockage** : Tables externes BigQuery
- **Rôle** : Accès direct aux fichiers raw sans ingestion
- **Schema** : `01_STG`
- **Convention** : `01_STG.{entity_name}`

### Couche ODS (Operational Data Store - 02_ODS)
- **Stockage** : Tables BigQuery matérialisées
- **Rôle** : Données nettoyées et transformées
- **Schema** : `02_ODS`
- **Convention** : `02_ODS.{entity_name}`
- **Métadonnées** : Ajout automatique de `ingestion_date` et `source_file`

## Patterns d'Implémentation

### Pattern 1 : Ingestion CSV Simple

**Use Case** : Ingestion d'un fichier CSV depuis GCS vers BigQuery

**Flux** :
```
Fichier CSV (GCS) → Table Externe (01_STG) → Table Matérialisée (02_ODS)
```

**Avantages** :
- ✅ Traitement full BigQuery
- ✅ Pas d'infrastructure processing supplémentaire
- ✅ Lineage et observabilité de bout en bout
- ✅ Performance optimale pour données structurées

**Template des livrables** :
```
bigquery/00_ddl/create_external_table_stg_{entity}.sql
bigquery/00_ddl/create_table_ods_{entity}.sql
Dataform/02_ods/load_stg_to_ods_{entity}.sqlx
```

**Contraintes** :
- Format source : CSV avec délimiteur défini
- Taille max recommandée : < 5GB par fichier
- Schema fixe et typé

### Pattern 2 : Ingestion avec Orchestration Airflow

**Use Case** : Pipeline complexe avec étapes conditionnelles

**Flux** :
```
GCS → STG → ODS (orchestré par Cloud Composer)
```

**Avantages** :
- ✅ Gestion des erreurs et reprises
- ✅ Workflows conditionnels
- ✅ Monitoring avancé
- ✅ Intégration avec systèmes externes

## Standards de Nommage

### Fichiers
- **DDL** : `create_{type}_{schema}_{entity}.sql`
- **Dataform** : `load_{source}_to_{target}_{entity}.sqlx`
- **Buckets** : `{project}-bucket-{yyyymmdd}`

### Tables
- **STG** : `01_STG.{entity_name}`
- **ODS** : `02_ODS.{entity_name}`

### Colonnes Métadonnées (Obligatoires en ODS)
```sql
ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
source_file STRING
```

## Standards de Développement

### Templates de Référence

Utiliser les fichiers de l'implémentation **employees** comme templates de référence pour tous les nouveaux cas d'usage :

**Fichiers Templates** :
- `bigquery/00_ddl/create_external_table_stg_employees.sql` - Table externe STG
- `bigquery/00_ddl/create_table_ods_employees.sql` - Table ODS
- `Dataform/02_ods/load_stg_to_ods_employees.sqlx` - Transformation ELT

**Règle** : Dupliquer ces templates et adapter pour la nouvelle entité en respectant les conventions de nommage.

## Bonnes Pratiques

### Performance
- Utiliser le partitioning sur les dates en ODS
- Privilégier les tables externes pour STG
- Optimiser les requêtes SELECT avec WHERE

### Monitoring
- Ajouter systématiquement les métadonnées d'ingestion
- Utiliser les vues Dataform pour le lineage


## Processus d'Implémentation

### 1. Analyse des Besoins
- Identifier le pattern applicable
- Définir l'entité et le schema
- Valider les contraintes techniques

### 2. Développement
- Suivre les templates du pattern choisi
- Respecter les conventions de nommage

### 3. Tests et Validation
- Vérifier le lineage de bout en bout
- Valider les types et contraintes
- Tester la performance

### 4. Déploiement
- Déployer STG puis ODS
- Vérifier les permissions
- Monitorer l'exécution

## Ressources et Références

### Documentation Technique
- [Bonnes pratiques BigQuery](https://cloud.google.com/bigquery/docs/load-transform-export-intro?hl=fr)
- [Guide Dataform](https://cloud.google.com/dataform/docs)

### Tutoriels du Projet
- `tutos/tuto1_bases_ingestion_sql.md` - Bases de l'ingestion CSV
- `tutos/tuto3_pipeline_dataform.md` - Pipeline avec tables externes

### Templates de Code
- `bigquery/00_ddl/` - Scripts DDL de création de tables
- `Dataform/02_ods/` - Transformations ELT

## Évolutions du Framework

Ce framework est évolutif. Les nouveaux patterns doivent :
1. Respecter l'architecture en couches
2. Utiliser uniquement la stack autorisée
3. Suivre les conventions de nommage
4. Être documentés avec un tutoriel associé