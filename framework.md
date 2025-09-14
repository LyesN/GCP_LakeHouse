# Framework GCP Data Lakehouse

## Stack Technique

Les développements du projet sont strictement limités à ces services GCP :

- **BigQuery** - Data Warehouse
- **Dataform** - Transformation et orchestration SQL
- **Cloud Composer** - Orchestration des workflows
- **Cloud Function** - Fonctions serverless
- **Dataproc** - Processing big data
- **Cloud Run** - Services conteneurisés

## Pattern 1 : Ingestion de fichiers CSV

### Description
Pipeline d'ingestion pour fichiers CSV avec les étapes suivantes :
- **Raw** : Fichier CSV → **Staging** : Table externe BigQuery → **ODS** : Intégration Dataform

### Avantages
- Traitement full BigQuery
- Pas d'autre brique processing engagée
- Garantie un lineage et une observabilité de bout en bout

### Template des livrables
```
bigquery/00_ddl/create_external_table_stg_employees.sql
bigquery/00_ddl/create_table_ods_employees.sql
Dataform/02_ods/load_stg_to_ods_employees.sqlx
```

### Tutoriels
- `tuto1_bases_ingestion_sql.md`
- `tuto3_pipeline_dataform.md`