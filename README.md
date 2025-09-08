# GCP LakeHouse - Tutoriel BigQuery

Ce repository contient un tutoriel complet pour importer des fichiers CSV depuis Google Cloud Storage vers BigQuery dans un environnement d'entreprise.

## 📋 Contenu

- **[tutoriel_import_csv_gcs_bigquery.md](./tutoriel_import_csv_gcs_bigquery.md)** - Guide complet d'import CSV vers BigQuery avec orchestration Airflow

## 🎯 Public cible

- Data Engineers
- Data Analysts
- Équipes travaillant sur la stack GCP BigQuery

## 🏢 Contexte entreprise

- **Environnement** : GCP Console (DEV)
- **Orchestrateur** : Apache Airflow
- **Stack** : BigQuery full stack
- **Objectif** : Pipeline de données automatisé et schedulé

## 🚀 Utilisation

1. Suivez le tutoriel étape par étape dans [tutoriel_import_csv_gcs_bigquery.md](./tutoriel_import_csv_gcs_bigquery.md)
2. Adaptez les configurations à votre environnement
3. Implémentez le pipeline Airflow selon vos besoins

## 📊 Exemple de données

Le tutoriel utilise un fichier CSV d'exemple avec des données d'employés contenant :
- Informations personnelles (nom, prénom, email, âge)
- Données géographiques (ville, coordonnées)
- Informations professionnelles (salaire, département, statut)

## 🔧 Prérequis

- Accès à la GCP Console
- Fichier CSV dans Google Cloud Storage
- Permissions BigQuery et GCS appropriées
- Apache Airflow configuré (Cloud Composer recommandé)

## 📚 Ressources

- [Bonnes pratiques pour charger, transformer et exporter des données BigQuery](https://cloud.google.com/bigquery/docs/load-transform-export-intro?hl=fr)
- [Documentation BigQuery](https://cloud.google.com/bigquery/docs)
- [Documentation Apache Airflow](https://airflow.apache.org/docs/)
- [Google Cloud Composer](https://cloud.google.com/composer/docs)