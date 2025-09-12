-- Fichier : definitions/load_employees.sqlx

-- Configuration pour créer une table dans le schéma "02_ODS"
config {
  type: "table",
  schema: "02_ODS",
  name: "employees"
}

-- Sélectionne les données depuis la table externe de staging
SELECT
    id,
    nom,
    prenom,
    email,
    age,
    ville,
    code_postal,
    telephone,
    salaire,
    departement,
    date_embauche,
    statut,
    score,
    latitude,
    longitude,
    commentaire,
    reference,
    niveau,
    categorie,
    timestamp,
    -- Métadonnées d'ingestion
    CURRENT_TIMESTAMP() AS ingestion_date,
    'gs://lakehouse-bucket-20250903/employees.csv' AS source_file
FROM
    `01_STG.employees`