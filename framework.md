Stack technique :
Les developements du projets sont etrictement limités à ces srvices GCP
 - Bigquery
 - Dataform
 - Cloud Composer
 - Cloud Function
 - Dataproc
 - Cloud run
 
 
Patterns
 description
 - ingection d'un fichier csv
 - raw : csv fine -> Stagig : table externe Bigquery -> ODS : integration Dataform
  
 avantages :
 - Traitement full Bigquery
 - Pas d'autre brique processing engagée
 - Garentie un linéage et une observabilité de bout en bout
 
 template d'implementation :
  - sql\01_stg_map\create_external_table_employees.sql
  - sql\02_ods_load\load_employees.sqlx
  - 
  
 tutoriels : 
 - tuto3_pipeline_dataform.md 