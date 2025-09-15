# Cas d'Usage : Alimentation Lakehouse Conséquent

Cette documentation présente l'architecture et l'implémentation pratique du framework GCP Data Lakehouse pour des cas d'usage d'alimentation de données conséquents.

## Vue d'Ensemble Architecture

![Architecture Pipeline Data](Architecture-pipline-data.png)

*Architecture générale du framework GCP Data Lakehouse avec les 3 couches : RAW → STG → ODS*

## Composants de l'Architecture

### 1. Couche RAW (Cloud Storage)
- **Rôle** : Stockage des fichiers bruts
- **Formats supportés** : CSV, JSON, Parquet
- **Avantages** :
  - Stockage illimité et économique
  - Durabilité et disponibilité élevées
  - Support natif GCP

### 2. Couche STG (01_STG - Tables Externes BigQuery)
- **Rôle** : Interface d'accès aux données raw sans ingestion
- **Technologie** : Tables externes BigQuery
- **Avantages** :
  - Pas de duplication de données
  - Accès SQL direct aux fichiers
  - Intégration native avec Dataform

### 3. Couche ODS (02_ODS - Tables BigQuery)
- **Rôle** : Données nettoyées, transformées et enrichies
- **Technologie** : Tables BigQuery matérialisées
- **Métadonnées automatiques** : `ingestion_date`, `source_file`

## Exemple Concret : Pattern 1 Ingestion CSV

![Exemple Implementation Pattern 1](Architecture-pipline-data-exemple-implementation.png)

*Implémentation détaillée du Pattern 1 avec l'exemple employees (CSV → STG → ODS)*

### Flux de Données Détaillé

1. **Upload CSV vers GCS**
   - Fichier : `employees.csv` (jusqu'à 5GB)
   - Bucket : `gs://lakehouse-bucket-20250903/`
   - Validation : Schéma et format

2. **Table Externe STG**
   - `01_STG.employees` : Accès direct au CSV
   - Configuration : Délimiteur, headers, types
   - Pas d'ingestion : Économique et performant

3. **Transformation ELT avec Dataform**
   - Script : `load_stg_to_ods_employees.sqlx`
   - Orchestration : Gestion des dépendances
   - Enrichissement : Métadonnées d'ingestion

4. **Table ODS finale**
   - `02_ODS.employees` : Données nettoyées
   - Types BigQuery : INT64, FLOAT64, STRING, TIMESTAMP
   - Prêt pour analytics et reporting

## Avantages du Pattern

### Performance
- **Full BigQuery** : Traitement natif sans infrastructure externe
- **Tables externes** : Pas de duplication de stockage
- **Optimisations** : Partitioning et clustering automatiques

### Observabilité
- **Lineage complet** : De la source aux données finales
- **Métadonnées** : Traçabilité des transformations
- **Monitoring** : Logs et métriques intégrés GCP

### Scalabilité
- **Volumes conséquents** : Support multi-GB sans limite
- **Parallélisation** : Processing automatique BigQuery
- **Élasticité** : Ressources à la demande

## Cas d'Usage Supportés

### Volumes de Données
- ✅ **5MB** : Tests et développement
- ✅ **1GB** : Datasets moyens, analytics
- ✅ **5GB** : Volumes conséquents, production
- ✅ **>5GB** : Possibilité de splitting ou autre pattern

### Types de Sources
- **CSV** : Delimiter configurables (`;`, `,`, `|`)
- **JSON** : Structure imbriquée supportée
- **Parquet** : Format optimisé pour analytics
- **Multi-formats** : Pattern extensible

### Fréquences d'Ingestion
- **Batch quotidien** : Pattern standard recommandé
- **Intraday** : Multiple fois par jour possible
- **Near real-time** : Avec Cloud Functions et événements GCS

## Prochaines Évolutions

### Pattern 2 : Orchestration Avancée
- Intégration Cloud Composer (Airflow)
- Workflows conditionnels
- Gestion d'erreurs sophistiquée

### Pattern 3 : Streaming
- Cloud Pub/Sub → Dataflow → BigQuery
- Ingestion temps réel
- Fenêtrage et agrégations

### Pattern 4 : Multi-Sources
- Connecteurs natifs (Salesforce, SAP, etc.)
- APIs REST avec Cloud Functions
- CDC (Change Data Capture)

## Conformité Framework

Cette documentation respecte strictement les standards définis dans [`framework.md`](../framework.md) :

- ✅ Stack technique GCP uniquement
- ✅ Architecture 3-couches RAW → STG → ODS
- ✅ Conventions de nommage respectées
- ✅ Templates employees comme référence
- ✅ Métadonnées d'ingestion obligatoires
- ✅ Documentation des patterns évolutifs