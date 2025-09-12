-- Flux d'ingestion CSV vers BigQuery
-- Fichier source : employees
-- Table cible : employees.csv
-- Truncate avant bulk

TRUNCATE TABLE `lake-471013.02_ODS.employees`;

LOAD DATA INTO `lake-471013.02_ODS.employees`
(id INT64, nom STRING, prenom STRING, email STRING, age INT64, ville STRING, 
 code_postal STRING, telephone STRING, salaire FLOAT64, departement STRING, 
 date_embauche DATE, statut STRING, score FLOAT64, latitude FLOAT64, 
 longitude FLOAT64, commentaire STRING, reference STRING, niveau STRING, 
 categorie STRING, timestamp TIMESTAMP)
FROM FILES (
  format = 'CSV',
  field_delimiter = ';',
  skip_leading_rows = 1,
  uris = ['gs://lakehouse-bucket-20250903/employees.csv']
);