# Quick Start - Airflow sur Kubernetes

## 🚀 Démarrage rapide (3 étapes)

### 1. Prérequis
- Docker Desktop avec Kubernetes activé
- kubectl installé

### 2. Vérifier l'environnement (optionnel)

```cmd
scripts\check-env.bat
```

### 3. Lancer le déploiement

```cmd
scripts\deploy-clean.bat
```

**Note** : Les scripts se placent automatiquement dans le bon répertoire, vous pouvez les lancer depuis n'importe où.

### 4. Accéder à Airflow

- **Interface Web** : http://localhost:32794
- **Username** : admin
- **Password** : admin123

## 🔧 Scripts disponibles

| Script | Description |
|--------|-------------|
| `deploy-clean.bat` | Déploiement complet Airflow (avec corrections) |
| `redeploy-clean.bat` | Redéploiement complet (suppression + redéploiement) |
| `fix-dags.bat` | Corriger le problème des DAGs qui n'apparaissent pas |
| `status-clean.bat` | Vérifier le statut des services |
| `stop-clean.bat` | Arrêter tous les services |
| `logs-clean.bat [service]` | Voir les logs d'un service |
| `add-dag-clean.bat [fichier]` | Ajouter un nouveau DAG |
| `check-env.bat` | Vérifier l'environnement |

## 📊 Monitoring

- **Flower (Celery)** : http://localhost:31847
- **Username** : admin
- **Password** : flower123

## 🛠️ Commandes utiles

```cmd
# Voir les pods
kubectl get pods -n airflow

# Voir les services  
kubectl get services -n airflow

# Logs en temps réel
kubectl logs -n airflow deployment/airflow-webserver -f

# Redémarrer un service
kubectl rollout restart deployment/airflow-webserver -n airflow
```

## 🆘 En cas de problème

1. Vérifiez que Docker Desktop est démarré
2. Vérifiez que Kubernetes est activé dans Docker Desktop
3. Lancez `scripts\status-clean.bat` pour diagnostiquer
4. Consultez les logs avec `scripts\logs-clean.bat webserver`

## 🔒 Ports utilisés

- **32794** : Interface Web Airflow (port sécurisé)
- **31847** : Interface Flower (port sécurisé)

Ces ports sont volontairement non-standards pour plus de sécurité.