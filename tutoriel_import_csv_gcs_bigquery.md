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