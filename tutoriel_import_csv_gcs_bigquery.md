# Tutoriel : Importer un fichier CSV depuis Google Cloud Storage vers BigQuery

## Référence des bonnes pratiques
📚 [Bonnes pratiques pour charger, transformer et exporter des données BigQuery](https://cloud.google.com/bigquery/docs/load-transform-export-intro?hl=fr)

## Contexte
- **Public cible** : Data Engineers, Data Analysts
- **Environnement** : GCP Console (environnement DEV)
- **Stack** : BigQuery
- **Objectif** : Créer un pipeline de données automatisé

## Paramètres du projet
- **Projet GCP** : `LakeHouse`
- **BigQuery name** : `lake-471013`
- **Dataset BigQuery** : `lakehouse_employee_data`
- **Bucket GCS** : `lakehouse-bucket-20250903`
- **Fichier CSV** : `employees_5mb.csv`
- **Chemin complet** : `gs://lakehouse-bucket-20250903/employees_5mb.csv`

## Prérequis
- Permissions appropriées sur BigQuery et GCS

## Plan du tutoriel

1. **[Étape 1](#étape-1--vérification-du-fichier-csv-dans-gcs)** : Vérification du fichier CSV dans GCS
2. **[Étape 2](#étape-2--développement-sur-console-gcp)** : Développement sur Console GCP
   - Création du dataset BigQuery
   - Définition de la table et du schéma
   - Développement du flux d'ingestion en SQL
3. **[Étape 3](#étape-3--test-et-validation-du-flux)** : Test et validation du flux d'ingestion
4. **[Étape 4](#étape-4--intégration-airflow-comme-orchestrateur)** : Intégration Airflow comme orchestrateur
   - Architecture du trigger Airflow
   - Configuration des connexions GCP
   - Monitoring et alertes
5. **[Étape 5](#étape-5--déploiement-et-monitoring-de-production)** : Déploiement et monitoring de production
6. **[Étape 6](#étape-6--optimisations-pour-lentreprise)** : Optimisations pour l'entreprise
   - Partitioning et clustering
   - Gestion des données sensibles
7. **[Bonnes pratiques](#bonnes-pratiques)** et **[Dépannage](#dépannage)**

## Structure du fichier CSV exemple
Le fichier contient les colonnes suivantes avec séparateur `;` :
```
id;nom;prenom;email;age;ville;code_postal;telephone;salaire;departement;date_embauche;statut;score;latitude;longitude;commentaire;reference;niveau;categorie;timestamp
```

## Étape 1 : Préparation et vérification du fichier CSV dans GCS

### 1.1 Création du bucket GCS

1. Accédez à la **GCP Console**
2. Naviguez vers **Cloud Storage**
3. Cliquez sur **Créer un bucket**
4. Configurez le bucket :
   - **Nom du bucket** : `lakehouse-bucket-20250903`
   - **Type d'emplacement** : Région
   - **Région** : `us-east1` (us pour le Free Tier)
   - **Classe de stockage** : Par défaut (Standard)
   - **Contrôle d'accès** : Par défaut
   - **Protection** : Pas de protection
5. Cliquez sur **Créer**

### 1.2 Upload du fichier CSV

1. Sélectionnez le bucket `lakehouse-bucket-20250903` créé
2. Cliquez sur **Importer des fichiers**
3. Sélectionnez votre fichier `employees_5mb.csv` depuis votre système local
4. Attendez la fin de l'upload
5. Vérifiez que le fichier apparaît dans la liste avec la taille attendue (~5MB)

### 1.3 Vérification du fichier uploadé

1. **Vérifier le fichier uploadé** :
   - Cliquez sur le fichier `employees_5mb.csv` pour voir ses détails
   - Notez le chemin complet : `gs://lakehouse-bucket-20250903/employees_5mb.csv`
   - Vérifiez que la taille est d'environ 5MB

## Étape 2 : Développement sur Console GCP

### Use Case : développement du flux d'ingestion dans la console BigQuery

### 2.1 Création du dataset BigQuery

1. Dans la **GCP Console**, accédez à **BigQuery**
2. Dans l'explorateur, cliquez sur votre projet `lake-471013`
3. Cliquez sur **Créer un dataset**
4. Configurez le dataset :
   - **ID du dataset** : `lakehouse_employee_data`
   - **Emplacement** : US (pour correspondre au bucket GCS)
   - **Expiration** : Par défaut ou selon votre politique d'entreprise
5. Cliquez sur **Créer un dataset**

### 2.1.1 Test d'accessibilité du fichier GCS

Une fois le dataset créé, vérifiez l'accessibilité du fichier CSV :

1. **Test d'accessibilité depuis BigQuery** :
   - Dans l'explorateur BigQuery, cliquez sur le dataset `lakehouse_employee_data` 
   - Cliquez sur **+ Créer une table**
   - **Source** : Google Cloud Storage
   - **Parcourir** : chercher le fichier dans le bucket `lakehouse-bucket-20250903`
   
2. **Validation des permissions** :
   - Si vous pouvez parcourir et sélectionner le fichier → Permissions OK
   - Si le fichier n'apparaît pas → Contactez votre administrateur GCP

2. **Quitter sans sauvegarder** :
   - "Annuler" tout en bas puis "Oui quitter"

### 2.2 Création de la table avec schéma défini

1. **Ouvrir l'éditeur SQL** :
   - Dans BigQuery, cliquez sur **+** (en haut du canvas)
   - Une nouvelle fenêtre d'éditeur SQL s'ouvre

2. **Saisir la requête de création de table** :

```sql
-- Création de la table employees avec schéma typé
CREATE TABLE `lake-471013.lakehouse_employee_data.employees` (
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
```

3. **Exécuter la requête** :
   - Cliquez sur **Exécuter** (bouton bleu) ou utilisez Ctrl+Enter
   - Vérifiez que la table apparaît dans l'explorateur sous `lakehouse_employee_data`
   - La table est maintenant créée et prête pour l'ingestion

### 2.3 Développement du flux d'ingestion en SQL

#### A. Requête de chargement depuis GCS

```sql
-- Flux d'ingestion principal depuis GCS avec schéma forcé
LOAD DATA INTO `lake-471013.lakehouse_employee_data.employees`
(id INT64, nom STRING, prenom STRING, email STRING, age INT64, ville STRING, 
 code_postal STRING, telephone STRING, salaire FLOAT64, departement STRING, 
 date_embauche DATE, statut STRING, score FLOAT64, latitude FLOAT64, 
 longitude FLOAT64, commentaire STRING, reference STRING, niveau STRING, 
 categorie STRING, timestamp TIMESTAMP)
FROM FILES (
  format = 'CSV',
  field_delimiter = ';',
  skip_leading_rows = 1,
  uris = ['gs://lakehouse-bucket-20250903/employees_5mb.csv']
);
```

**Avantages du schéma forcé** :
- **Évite les conflits** : BigQuery n'essaie pas de détecter automatiquement le schéma
- **Contrôle total** : Impose exactement les types de données souhaités
- **Robustesse** : Évite les erreurs "Field has changed mode/type"
- **Performance** : Pas de phase de détection automatique

## Étape 3 : Implémentation et orchestration du pipeline avec Dataform

### 3.1 Introduction à Dataform sur la Console GCP

**Dataform** est l'outil Google Cloud natif pour l'orchestration et la transformation des données dans BigQuery. Accessible directement depuis la Console GCP, il permet de :

- **Gestion de version** : Code SQL versionné et déployé comme du code
- **Orchestration native** : Déclenchement automatique des workflows
- **Tests intégrés** : Validation automatique de la qualité des données  
- **Documentation** : Documentation automatique des transformations
- **Dépendances** : Gestion automatique des dépendances entre tables

### 3.2 Création du projet Dataform dans la Console GCP

#### 3.2.1 Accès à Dataform

1. **Ouvrir la Console GCP** :
   - Connectez-vous à [console.cloud.google.com](https://console.cloud.google.com)
   - Sélectionnez votre projet `lake-471013`

2. **Naviguer vers Dataform** :
   - Dans le menu principal (☰), recherchez "Dataform"
   - Cliquez sur **Dataform** dans la section "Analytics"
   - Si c'est la première utilisation, activez l'API Dataform

#### 3.2.2 Création du repository Dataform

1. **Créer un nouveau repository** :
   - Cliquez sur **Créer un repository**
   - **Nom du repository** : `lakehouse-employees-pipeline`
   - **Région** : `us-east1` (pour correspondre à BigQuery et GCS)
   - **Service Account** : Utilisez le service account par défaut ou créez-en un dédié
   - Cliquez sur **Créer**

2. **Configuration des permissions** :
   - Vérifiez que le service account a les rôles :
     - `BigQuery Data Editor`
     - `BigQuery Job User` 
     - `Storage Object Viewer` (pour accéder aux fichiers GCS)

#### 3.2.3 Initialisation du workspace

1. **Créer un workspace de développement** :
   - Une fois le repository créé, cliquez sur **Créer un workspace de développement**
   - **Nom** : `dev-workspace`
   - Cliquez sur **Créer un workspace**

2. **Accéder à l'éditeur** :
   - Cliquez sur le workspace créé pour ouvrir l'éditeur Dataform intégré
   - Vous accédez maintenant à l'IDE Dataform dans le navigateur

### 3.3 Configuration du projet Dataform

#### 3.3.1 Fichier dataform.json

Dans l'éditeur Dataform, créez/modifiez le fichier `dataform.json` :

1. **Cliquer sur le fichier `dataform.json`** dans l'explorateur de fichiers à gauche
2. **Remplacer le contenu** par :

```json
{
  "defaultProject": "lake-471013",
  "defaultDataset": "lakehouse_employee_data",
  "defaultLocation": "US",
  "assertionSchema": "dataform_assertions",
  "warehouse": "bigquery",
  "defaultTags": ["lakehouse", "employees"],
  "vars": {
    "environment": "dev",
    "gcs_bucket": "lakehouse-bucket-20250903",
    "source_file": "employees_5mb.csv",
    "source_path": "gs://lakehouse-bucket-20250903/employees_5mb.csv"
  }
}
```

#### 3.3.2 Création des datasets requis

Avant de continuer, créer les datasets BigQuery nécessaires :

1. **Ouvrir BigQuery** dans un nouvel onglet
2. **Créer les datasets** suivants :
   - `lakehouse_employee_data_raw` (pour les données brutes)
   - `lakehouse_employee_data_staging` (pour les données nettoyées)
   - `lakehouse_employee_data` (pour les tables finales - déjà créé)
   - `dataform_assertions` (pour les tests qualité)

### 3.4 Création des transformations Dataform

#### 3.4.1 Table source - Ingestion depuis GCS

1. **Créer le dossier sources** :
   - Clic droit sur `definitions` → **Nouveau dossier** → `sources`

2. **Créer le fichier employees_raw.sqlx** :
   - Clic droit sur `sources` → **Nouveau fichier** → `employees_raw.sqlx`
   - **Contenu du fichier** :

```sql
config {
  type: "operations",
  name: "load_employees_raw",
  description: "Chargement des données employés depuis GCS vers BigQuery",
  tags: ["source", "raw", "employees"]
}

-- Créer la table avec schéma défini
CREATE OR REPLACE TABLE `${dataform.projectConfig.defaultProject}.lakehouse_employee_data_raw.employees_raw` (
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
  source_file STRING DEFAULT '${dataform.projectConfig.vars.source_path}'
);

-- Chargement depuis GCS avec schéma forcé
LOAD DATA INTO `${dataform.projectConfig.defaultProject}.lakehouse_employee_data_raw.employees_raw`
(id INT64, nom STRING, prenom STRING, email STRING, age INT64, ville STRING,
 code_postal STRING, telephone STRING, salaire FLOAT64, departement STRING,
 date_embauche DATE, statut STRING, score FLOAT64, latitude FLOAT64,
 longitude FLOAT64, commentaire STRING, reference STRING, niveau STRING,
 categorie STRING, timestamp TIMESTAMP)
FROM FILES (
  format = 'CSV',
  field_delimiter = ';',
  skip_leading_rows = 1,
  uris = ['${dataform.projectConfig.vars.source_path}']
);
```

#### 3.4.2 Table de staging - Nettoyage des données

1. **Créer le dossier staging** :
   - Clic droit sur `definitions` → **Nouveau dossier** → `staging`

2. **Créer le fichier employees_clean.sqlx** :
   - Clic droit sur `staging` → **Nouveau fichier** → `employees_clean.sqlx`
   - **Contenu du fichier** :

```sql
config {
  type: "table",
  schema: "lakehouse_employee_data_staging",
  name: "employees_clean",
  description: "Données employés nettoyées et validées",
  tags: ["staging", "clean", "employees"],
  dependencies: ["load_employees_raw"]
}

SELECT 
  -- Identifiants
  id,
  
  -- Noms normalisés
  TRIM(UPPER(nom)) as nom,
  TRIM(INITCAP(prenom)) as prenom,
  TRIM(LOWER(email)) as email,
  
  -- Validation des âges
  CASE 
    WHEN age BETWEEN 18 AND 65 THEN age 
    ELSE NULL 
  END as age,
  
  -- Données géographiques
  TRIM(INITCAP(ville)) as ville,
  TRIM(code_postal) as code_postal,
  REGEXP_REPLACE(telephone, r'[^\d+]', '') as telephone_clean,
  
  -- Informations professionnelles
  CASE 
    WHEN salaire > 0 THEN salaire 
    ELSE NULL 
  END as salaire,
  TRIM(UPPER(departement)) as departement,
  date_embauche,
  TRIM(UPPER(statut)) as statut,
  
  -- Scores et coordonnées
  CASE 
    WHEN score BETWEEN 0 AND 100 THEN score 
    ELSE NULL 
  END as score,
  CASE 
    WHEN latitude BETWEEN -90 AND 90 THEN latitude 
    ELSE NULL 
  END as latitude,
  CASE 
    WHEN longitude BETWEEN -180 AND 180 THEN longitude 
    ELSE NULL 
  END as longitude,
  
  -- Métadonnées
  commentaire,
  reference,
  niveau,
  categorie,
  timestamp,
  
  -- Métadonnées d'ingestion et transformation
  ingestion_date,
  source_file,
  CURRENT_TIMESTAMP() as transformation_date,
  
  -- Indicateurs qualité
  CASE 
    WHEN email LIKE '%@%.%' THEN TRUE 
    ELSE FALSE 
  END as email_valid,
  CASE 
    WHEN age IS NULL OR salaire IS NULL THEN TRUE 
    ELSE FALSE 
  END as has_missing_data

FROM `${dataform.projectConfig.defaultProject}.lakehouse_employee_data_raw.employees_raw`
WHERE id IS NOT NULL
  AND nom IS NOT NULL 
  AND prenom IS NOT NULL
```

#### 3.4.3 Tables métier (Data Marts)

1. **Créer le dossier marts** :
   - Clic droit sur `definitions` → **Nouveau dossier** → `marts`

2. **Créer dim_employees.sqlx** :
   - Clic droit sur `marts` → **Nouveau fichier** → `dim_employees.sqlx`

```sql
config {
  type: "table",
  schema: "lakehouse_employee_data",
  name: "dim_employees",
  description: "Dimension des employés pour les analyses métier",
  tags: ["marts", "dimension", "employees"],
  dependencies: ["employees_clean"]
}

SELECT 
  -- Clé primaire
  id as employee_id,
  
  -- Informations personnelles
  CONCAT(prenom, ' ', nom) as full_name,
  nom as last_name,
  prenom as first_name,
  email,
  age,
  
  -- Informations géographiques
  ville as city,
  code_postal as postal_code,
  telephone_clean as phone,
  latitude,
  longitude,
  
  -- Informations professionnelles
  departement as department,
  statut as status,
  niveau as level,
  categorie as category,
  date_embauche as hire_date,
  
  -- Calculs dérivés
  DATE_DIFF(CURRENT_DATE(), date_embauche, YEAR) as years_of_service,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), date_embauche, YEAR) >= 5 THEN 'Senior'
    WHEN DATE_DIFF(CURRENT_DATE(), date_embauche, YEAR) >= 2 THEN 'Confirmé'
    ELSE 'Junior'
  END as seniority_level,
  
  -- Indicateurs qualité
  email_valid,
  has_missing_data,
  
  -- Métadonnées
  transformation_date,
  CURRENT_TIMESTAMP() as dim_created_at

FROM ${ref("employees_clean")}
WHERE departement IS NOT NULL
  AND statut IN ('ACTIF', 'ACTIVE', 'EN_POSTE')
```

3. **Créer fact_salaries.sqlx** :

```sql
config {
  type: "table",
  schema: "lakehouse_employee_data",
  name: "fact_salaries",
  description: "Table de faits pour l'analyse des salaires",
  tags: ["marts", "fact", "salaries"],
  dependencies: ["employees_clean"]
}

SELECT 
  -- Clés
  id as employee_id,
  
  -- Mesures
  salaire as salary_amount,
  score as performance_score,
  
  -- Dimensions
  departement as department,
  niveau as level,
  age as employee_age,
  DATE_DIFF(CURRENT_DATE(), date_embauche, YEAR) as years_of_service,
  
  -- Calculs analytiques
  PERCENT_RANK() OVER (
    PARTITION BY departement 
    ORDER BY salaire
  ) * 100 as salary_percentile_dept,
  
  AVG(salaire) OVER (PARTITION BY departement) as avg_salary_dept,
  
  -- Classification salariale
  CASE 
    WHEN salaire >= 80000 THEN 'High'
    WHEN salaire >= 50000 THEN 'Medium' 
    ELSE 'Low'
  END as salary_band,
  
  -- Métadonnées
  transformation_date,
  CURRENT_TIMESTAMP() as fact_created_at

FROM ${ref("employees_clean")}
WHERE salaire IS NOT NULL 
  AND salaire > 0
  AND departement IS NOT NULL
```

### 3.5 Tests de qualité des données

1. **Créer le fichier tests/data_quality.sqlx** :
   - Créer le dossier `tests` dans `definitions`
   - Créer le fichier `data_quality.sqlx`

```sql
config {
  type: "assertion",
  name: "employees_data_quality_tests",
  description: "Tests de qualité sur les données employés",
  dependencies: ["employees_clean"]
}

-- Test: Pas de doublons sur les IDs
SELECT 
  COUNT(*) = 0 as test_passed
FROM (
  SELECT id, COUNT(*) as cnt
  FROM ${ref("employees_clean")}
  GROUP BY id
  HAVING COUNT(*) > 1
)
```

### 3.6 Compilation et exécution du pipeline

#### 3.6.1 Compilation du projet

1. **Compiler le projet** :
   - Cliquez sur **Compiler** en haut de l'éditeur
   - Vérifiez qu'il n'y a pas d'erreurs de syntaxe
   - Les dépendances sont automatiquement calculées

#### 3.6.2 Exécution du workflow

1. **Exécuter le workflow complet** :
   - Cliquez sur **Exécuter** → **Exécuter toutes les actions**
   - Sélectionnez les actions à exécuter dans l'ordre :
     1. `load_employees_raw`
     2. `employees_clean` 
     3. `employees_data_quality_tests`
     4. `dim_employees`
     5. `fact_salaries`

2. **Suivre l'exécution** :
   - L'interface affiche le statut en temps réel
   - Les logs détaillés sont disponibles pour chaque action
   - Les erreurs sont mises en évidence avec des détails

#### 3.6.3 Vérification des résultats

1. **Vérifier dans BigQuery** :
   - Ouvrir BigQuery dans un nouvel onglet
   - Vérifier que toutes les tables ont été créées
   - Contrôler le nombre de lignes dans chaque table

```sql
-- Vérification rapide
SELECT 'employees_raw' as table_name, COUNT(*) as row_count
FROM `lake-471013.lakehouse_employee_data_raw.employees_raw`
UNION ALL
SELECT 'employees_clean', COUNT(*)
FROM `lake-471013.lakehouse_employee_data_staging.employees_clean`
UNION ALL  
SELECT 'dim_employees', COUNT(*)
FROM `lake-471013.lakehouse_employee_data.dim_employees`
UNION ALL
SELECT 'fact_salaries', COUNT(*)
FROM `lake-471013.lakehouse_employee_data.fact_salaries`
```

### 3.7 Orchestration avec des workflows programmés

#### 3.7.1 Création d'un workflow release

1. **Créer une release** :
   - Dans Dataform, aller dans l'onglet **Releases**
   - Cliquez sur **Créer une release**
   - **Nom** : `v1.0-employees-pipeline`
   - **Configuration Git** : Branch `main`

2. **Configuration du workflow d'exécution** :
   - Aller dans **Workflow Configurations**
   - Cliquer sur **Créer une configuration de workflow**
   - **Nom** : `daily-employees-ingestion`
   - **Release** : Sélectionner `v1.0-employees-pipeline`
   - **Fréquence** : `0 2 * * *` (tous les jours à 2h du matin)

### 3.8 Monitoring et observabilité

#### 3.8.1 Dashboard d'exécution Dataform

Dans l'interface Dataform :

1. **Onglet "Workflow Invocations"** : 
   - Historique de toutes les exécutions
   - Durées et statuts des actions
   - Logs détaillés par action

2. **Graphique de dépendances** :
   - Visualisation du DAG des transformations
   - Identification des goulots d'étranglement

#### 3.8.2 Intégration avec Cloud Monitoring

```sql
-- Requête de monitoring dans BigQuery
SELECT 
  workflow_invocation_id,
  action_name,
  target,
  status,
  start_time,
  end_time,
  TIMESTAMP_DIFF(end_time, start_time, SECOND) as duration_seconds
FROM `lake-471013.dataform_monitoring.workflow_invocation_actions`
WHERE DATE(start_time) >= CURRENT_DATE() - 7
ORDER BY start_time DESC
```

### 3.9 Bonnes pratiques Dataform sur Console GCP

#### **Organisation du projet** :
- **Structure claire** : sources → staging → marts
- **Nommage cohérent** : Préfixes par couche (raw_, clean_, dim_, fact_)
- **Documentation** : Description détaillée dans les configs
- **Tags** : Étiquetage pour filtrer et organiser

#### **Gestion des environnements** :
- **Variables d'environnement** : Utiliser `dataform.json` vars
- **Workspaces séparés** : dev, staging, prod
- **Releases versionnées** : Git-based deployments

#### **Tests et qualité** :
- **Assertions obligatoires** : Tests sur chaque transformation
- **Validation des données** : Contrôles métier intégrés
- **Monitoring** : Surveillance des métriques de qualité

Cette implémentation via la Console GCP offre une interface graphique intuitive pour développer, tester et orchestrer votre pipeline de données BigQuery avec Dataform.