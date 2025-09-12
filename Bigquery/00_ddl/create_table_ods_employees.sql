-- Création de la table employees avec schéma typé
CREATE TABLE `lake-471013.02_ODS.employees` (
  id INT64 NOT NULL,
  nom STRING,
  prenom STRING,
  email STRING,
  age INT64,
  ville STRING,
  code_postal STRING,
  telephone STRING,
  salaire FLOAT64,
  departement STRING,
  date_embauche DATE,
  statut STRING,
  score FLOAT64,
  latitude FLOAT64,
  longitude FLOAT64,
  commentaire STRING,
  reference STRING,
  niveau STRING,
  categorie STRING,
  timestamp TIMESTAMP,
  -- Métadonnées d'ingestion
  ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);