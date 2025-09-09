# Tutoriel 3 : Créer un pipeline de données avec BigQuery et Dataform

Ce tutoriel explique comment construire un pipeline de données simple pour charger un fichier CSV depuis Google Cloud Storage (GCS) vers une table BigQuery en utilisant une table externe comme couche de staging (STG) et Dataform pour orchestrer le chargement dans la couche ODS (Operational Data Store).

## Objectif

L'objectif est de mettre en place le pipeline suivant :

1.  **Fichier CSV dans GCS** : Notre source de données brute.
2.  **Table Externe BigQuery (STG)** : Une table qui pointe directement vers le fichier CSV dans GCS, sans ingérer les données.
3.  **Table BigQuery (ODS)** : La table finale, gérée et peuplée par Dataform, contenant les données propres.

## Prérequis

*   Un projet Google Cloud avec BigQuery et Cloud Storage activés.
*   Un bucket GCS. Pour ce tutoriel, nous utiliserons un bucket nommé `gs://votre-bucket-unique/`.
*   Un fichier `employees.csv` téléversé à la racine de votre bucket.
*   Un repository Dataform connecté à votre projet GCP.

## Étape 1 : Créer la table externe (Couche STG)

La première étape consiste à créer une table externe dans BigQuery qui référence notre fichier `employees.csv` stocké sur GCS. Cela nous permet d'interroger les données du fichier sans avoir à les charger au préalable.

1.  **Créez un ensemble de données (dataset)** dans BigQuery nommé `stg_employees`.
2.  Utilisez le script SQL suivant pour créer la table externe. Ce script doit être exécuté directement dans l'éditeur de requêtes BigQuery.

    **Script : `create_external_table_employees.sql`**
    ```sql
    CREATE OR REPLACE EXTERNAL TABLE `stg_employees.employees`
    (
      employee_id INT64,
      first_name STRING,
      last_name STRING,
      email STRING,
      hire_date DATE
    )
    OPTIONS (
      format = 'CSV',
      uris = ['gs://votre-bucket-unique/employees.csv'], -- Remplacez par le chemin de votre bucket
      skip_leading_rows = 1
    );
    ```

3.  **Explication du script :**
    *   `CREATE OR REPLACE EXTERNAL TABLE` : Crée une nouvelle table externe ou la remplace si elle existe déjà.
    *   `stg_employees.employees` : Le nom complet de notre table dans la couche de staging.
    *   `OPTIONS(...)` :
        *   `format = 'CSV'` : Spécifie que le fichier source est au format CSV.
        *   `uris = ['...']` : Indique l'emplacement du fichier source dans GCS. **N'oubliez pas de remplacer `votre-bucket-unique` par le nom de votre bucket.**
        *   `skip_leading_rows = 1` : Ignore la première ligne du fichier CSV, qui est généralement l'en-tête.

Après l'exécution, vous pouvez interroger `stg_employees.employees` comme n'importe quelle autre table BigQuery.

## Étape 2 : Charger les données dans l'ODS avec Dataform

Maintenant que nos données sources sont accessibles via la table externe, nous allons utiliser Dataform pour les charger dans une table matérialisée dans notre couche ODS.

1.  **Créez un ensemble de données (dataset)** dans BigQuery nommé `ods_employees`.
2.  Dans votre repository Dataform, créez un nouveau fichier SQLX dans le répertoire `definitions/` nommé `load_employees.sqlx`.
3.  Copiez le contenu suivant dans votre fichier.

    **Script : `load_employees.sqlx`**
    ```sqlx
    -- Fichier : definitions/load_employees.sqlx

    -- Configuration pour créer une table dans le schéma "ods_employees"
    config {
      type: "table",
      schema: "ods_employees",
      name: "employees"
    }

    -- Sélectionne les données depuis la table externe de staging
    SELECT
        employee_id,
        first_name,
        last_name,
        email,
        hire_date
    FROM
        ${ref("stg_employees", "employees")}

    ```

4.  **Explication du script :**
    *   `config { ... }` : Le bloc de configuration Dataform.
        *   `type: "table"` : Indique à Dataform de matérialiser le résultat de la requête dans une table BigQuery.
        *   `schema: "ods_employees"` : Spécifie que la table doit être créée dans le dataset `ods_employees`.
        *   `name: "employees"` : Définit le nom de la table de destination.
    *   `${ref("stg_employees", "employees")}` : La fonction `ref()` est cruciale. Elle indique à Dataform que ce script dépend de la table `employees` dans le dataset `stg_employees`. Dataform utilisera cette information pour construire le graphe de dépendances (DAG) de votre pipeline.

## Étape 3 : Exécuter le pipeline Dataform

1.  Allez dans votre espace de travail Dataform dans la console Google Cloud.
2.  Cliquez sur **"Démarrer l'exécution"** et sélectionnez **"Exécuter toutes les actions"**.
3.  Dataform va :
    *   Analyser les dépendances.
    *   Exécuter la requête définie dans `load_employees.sqlx`.
    *   Créer (ou remplacer) la table `ods_employees.employees` avec les données provenant de la table externe `stg_employees.employees`.

## Conclusion

Félicitations ! Vous avez créé un pipeline ELT (Extract, Load, Transform) simple et reproductible.

*   **Extraction (Extract)** : Les données sont disponibles dans GCS.
*   **Chargement (Load)** : La table externe `stg_employees.employees` rend les données accessibles à BigQuery instantanément.
*   **Transformation (Transform)** : Dataform orchestre le chargement final de la couche STG vers la couche ODS, où des transformations plus complexes pourraient être ajoutées à l'avenir.

Cette approche sépare clairement la source de données brute (GCS), la couche d'accès (table externe STG) et la couche de données structurées (table ODS), tout en bénéficiant de la gestion des dépendances et de l'orchestration offertes par Dataform.