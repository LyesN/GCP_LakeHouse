Stack technique :
Les developements du projets sont etrictement limités à ces srvices GCP
 - Bigquery
 - Dataform
 - Cloud Composer
 - Cloud Function
 - Dataproc
 - Cloud run
 
 
Patterns 1
 
  description
 - ingection d'un fichier csv
 - raw : csv file -> Stagig : table externe Bigquery -> ODS : integration Dataform
  
 avantages :
 - Traitement full Bigquery
 - Pas d'autre brique processing engagée
 - Garentie un linéage et une observabilité de bout en bout
 
 template des livrables :
  - bigquery\00_ddl\create_external_table_stg_employees.sql
  - bigquery\00_ddl\create_table_ods_employees.sql
  - Dataform\02_ods\load_stg_to_ods_employees.sqlx
  
 tutoriels : 
 - tuto1_bases_ingestion_sql.md
 - tuto3_pipeline_dataform.md