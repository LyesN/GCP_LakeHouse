import csv
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import os
import sys
import logging
from typing import List, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

fake = Faker('fr_FR')

# Constantes conformes au framework GCP Data Lakehouse
VILLES = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille']
DEPARTEMENTS = ['IT', 'RH', 'Marketing', 'Finance', 'Commercial', 'Production', 'Logistique', 'R&D']
STATUTS = ['actif', 'inactif']
NIVEAUX = ['junior', 'senior', 'expert']
CATEGORIES = ['A', 'B', 'C']

# Schéma conforme à create_table_ods_employees.sql (ordre et types respectés)
SCHEMA_ODS = {
    'id': {'type': 'INT64', 'required': True, 'min_val': 1},
    'nom': {'type': 'STRING', 'max_length': 50},
    'prenom': {'type': 'STRING', 'max_length': 50},
    'email': {'type': 'STRING', 'max_length': 100},
    'age': {'type': 'INT64', 'min_val': 16, 'max_val': 70},
    'ville': {'type': 'STRING', 'max_length': 50},
    'code_postal': {'type': 'STRING', 'max_length': 10},
    'telephone': {'type': 'STRING', 'max_length': 20},
    'salaire': {'type': 'FLOAT64', 'min_val': 20000.0, 'max_val': 150000.0},
    'departement': {'type': 'STRING', 'max_length': 50},
    'date_embauche': {'type': 'DATE', 'min_date': '2020-01-01', 'max_date': '2024-12-31'},
    'statut': {'type': 'STRING', 'max_length': 20},
    'score': {'type': 'FLOAT64', 'min_val': 0.0, 'max_val': 100.0},
    'latitude': {'type': 'FLOAT64', 'min_val': 42.0, 'max_val': 51.0},
    'longitude': {'type': 'FLOAT64', 'min_val': -5.0, 'max_val': 8.0},
    'commentaire': {'type': 'STRING', 'max_length': 200},
    'reference': {'type': 'STRING', 'max_length': 50},
    'niveau': {'type': 'STRING', 'max_length': 20},
    'categorie': {'type': 'STRING', 'max_length': 5},
    'timestamp': {'type': 'TIMESTAMP'}
}

def clean_field(value: Any, max_length: int = None) -> str:
    """
    Nettoie un champ pour éviter les problèmes avec le délimiteur CSV.
    Conforme aux standards du framework GCP Data Lakehouse.
    """
    if value is None:
        return ''

    if isinstance(value, str):
        # Nettoyer les caractères problématiques
        cleaned = value.replace(';', ',').replace('\n', ' ').replace('\r', ' ').strip()
        # Appliquer la limite de longueur si spécifiée
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        return cleaned

    return str(value)

def validate_field(field_name: str, value: Any) -> Any:
    """
    Valide un champ selon le schéma ODS défini.
    Conforme à create_table_ods_employees.sql
    """
    if field_name not in SCHEMA_ODS:
        logger.warning(f"Champ non reconnu dans le schéma ODS: {field_name}")
        return value

    schema = SCHEMA_ODS[field_name]
    field_type = schema.get('type')

    try:
        # Validation selon le type BigQuery
        if field_type == 'INT64':
            int_val = int(value)
            if 'min_val' in schema and int_val < schema['min_val']:
                int_val = schema['min_val']
            if 'max_val' in schema and int_val > schema['max_val']:
                int_val = schema['max_val']
            return int_val

        elif field_type == 'FLOAT64':
            float_val = float(value)
            if 'min_val' in schema and float_val < schema['min_val']:
                float_val = schema['min_val']
            if 'max_val' in schema and float_val > schema['max_val']:
                float_val = schema['max_val']
            return round(float_val, 6)

        elif field_type == 'STRING':
            max_length = schema.get('max_length')
            return clean_field(str(value), max_length)

        elif field_type in ['DATE', 'TIMESTAMP']:
            return str(value)

        else:
            return clean_field(str(value))

    except (ValueError, TypeError) as e:
        logger.error(f"Erreur de validation pour {field_name}: {e}")
        return None

def generate_row(row_id: int) -> List[Any]:
    """
    Génère une ligne de données CSV conforme au schéma ODS employees.
    Respecte exactement l'ordre des colonnes de create_table_ods_employees.sql
    """
    try:
        # Date d'embauche réaliste
        base_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 12, 31)
        random_days = random.randint(0, (end_date - base_date).days)
        date_embauche = base_date + timedelta(days=random_days)

        # Génération des données dans l'ordre exact du schéma ODS
        raw_data = {
            'id': row_id,
            'nom': fake.last_name(),
            'prenom': fake.first_name(),
            'email': fake.email(),
            'age': random.randint(18, 65),
            'ville': random.choice(VILLES),
            'code_postal': fake.postcode(),
            'telephone': fake.phone_number(),
            'salaire': round(random.uniform(25000, 120000), 2),
            'departement': random.choice(DEPARTEMENTS),
            'date_embauche': date_embauche.strftime('%Y-%m-%d'),
            'statut': random.choice(STATUTS),
            'score': round(random.uniform(0, 100), 2),
            'latitude': round(random.uniform(42.0, 51.0), 6),
            'longitude': round(random.uniform(-5.0, 8.0), 6),
            'commentaire': fake.text(max_nb_chars=150),
            'reference': str(uuid.uuid4())[:36],
            'niveau': random.choice(NIVEAUX),
            'categorie': random.choice(CATEGORIES),
            'timestamp': datetime.now().isoformat()
        }

        # Validation et nettoyage de chaque champ
        validated_row = []
        for field_name in SCHEMA_ODS.keys():
            validated_value = validate_field(field_name, raw_data[field_name])
            if validated_value is None:
                logger.error(f"Validation échouée pour {field_name} à la ligne {row_id}")
                validated_value = ''
            validated_row.append(validated_value)

        return validated_row

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la ligne {row_id}: {e}")
        # Ligne de fallback avec valeurs par défaut
        return [row_id, '', '', '', 25, '', '', '', 30000.0, '',
                '2023-01-01', 'actif', 50.0, 46.0, 2.0, '', '', 'junior', 'A',
                datetime.now().isoformat()]

def estimate_rows_needed(target_size_mb):
    """Estime le nombre de lignes nécessaires pour atteindre la taille cible"""
    sample_row = generate_row(1)
    sample_line = ';'.join(map(str, sample_row)) + '\n'
    avg_row_size = len(sample_line.encode('utf-8'))
    target_size_bytes = target_size_mb * 1024 * 1024
    estimated_rows = int(target_size_bytes / avg_row_size)
    print(f"Taille moyenne d'une ligne: {avg_row_size} bytes")
    print(f"Nombre estimé de lignes nécessaires: {estimated_rows:,}")
    return estimated_rows

def generate_csv_file(filename: str, target_size_mb: float, unit: str = 'MB') -> bool:
    """
    Génère un fichier CSV de la taille spécifiée.
    Conforme au framework GCP Data Lakehouse avec gestion d'erreurs robuste.

    Args:
        filename: Nom du fichier à générer
        target_size_mb: Taille cible (en MB ou GB selon unit)
        unit: 'MB' ou 'GB'

    Returns:
        bool: True si succès, False sinon
    """
    try:
        logger.info(f"🚀 Génération de {filename} ({target_size_mb}{unit}) - Framework GCP Data Lakehouse")

        if unit == 'GB':
            target_size_bytes = target_size_mb * 1024 * 1024 * 1024
            estimated_rows = estimate_rows_needed(target_size_mb * 1024)
        else:
            target_size_bytes = target_size_mb * 1024 * 1024
            estimated_rows = estimate_rows_needed(target_size_mb)

        # En-têtes conformes au schéma ODS (ordre exact)
        headers = list(SCHEMA_ODS.keys())

        # Validation des headers
        logger.info(f"📋 Schéma ODS: {len(headers)} colonnes conformes à create_table_ods_employees.sql")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)

            current_size = os.path.getsize(filename)
            row_id = 1
            error_count = 0

            while current_size < target_size_bytes:
                batch_size = min(10000, estimated_rows - row_id + 1)
                rows_batch = []

                for _ in range(batch_size):
                    try:
                        row_data = generate_row(row_id)
                        if row_data and len(row_data) == len(headers):
                            rows_batch.append(row_data)
                        else:
                            error_count += 1
                            logger.warning(f"⚠️ Ligne {row_id} invalide, ignorée")
                    except Exception as e:
                        error_count += 1
                        logger.error(f"❌ Erreur génération ligne {row_id}: {e}")

                    row_id += 1

                if rows_batch:
                    writer.writerows(rows_batch)
                    current_size = os.path.getsize(filename)

                # Progress reporting
                if row_id % 50000 == 0:
                    progress = (current_size / target_size_bytes) * 100
                    size_display = current_size / (1024*1024*1024) if unit == 'GB' else current_size / (1024*1024)
                    unit_display = 'GB' if unit == 'GB' else 'MB'

                    logger.info(f"⏳ Progression: {progress:.1f}% - {size_display:.2f}{unit_display} - {row_id:,} lignes - {error_count} erreurs")

        # Validation finale
        final_size = os.path.getsize(filename)
        final_size_display = final_size / (1024 * 1024 * 1024) if unit == 'GB' else final_size / (1024 * 1024)
        unit_display = 'GB' if unit == 'GB' else 'MB'

        logger.info(f"✅ Fichier {filename} généré avec succès:")
        logger.info(f"   📊 Taille: {final_size_display:.2f}{unit_display}")
        logger.info(f"   📈 Lignes: {row_id:,}")
        logger.info(f"   🔍 Erreurs: {error_count}")
        logger.info(f"   📋 Conforme au schéma ODS employees")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur critique lors de la génération de {filename}: {e}")
        return False

if __name__ == "__main__":
    logger.info("🏗️ Générateur CSV - Framework GCP Data Lakehouse")
    logger.info("📋 Conforme au schéma create_table_ods_employees.sql")

    if len(sys.argv) != 2:
        print("Usage: python generate_csv.py <1|5|5MB>")
        print("  1    = génère employees_1gb.csv (1GB)")
        print("  5    = génère employees_5gb.csv (5GB)")
        print("  5MB  = génère employees_5mb.csv (5MB)")
        print("\n🔍 Conformité Framework GCP Data Lakehouse:")
        print(f"  • Schéma: {len(SCHEMA_ODS)} colonnes ODS")
        print("  • Validation: Types BigQuery respectés")
        print("  • Nettoyage: Délimiteurs CSV sécurisés")
        print("  • Logging: Suivi des erreurs détaillé")
        sys.exit(1)

    # Créer le dossier data s'il n'existe pas
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"📁 Répertoire de sortie: {os.path.abspath(data_dir)}")

    arg = sys.argv[1]
    success = False

    if arg == "1":
        success = generate_csv_file('data/employees_1gb.csv', 1, 'GB')
    elif arg == "5":
        success = generate_csv_file('data/employees_5gb.csv', 5, 'GB')
    elif arg == "5MB":
        success = generate_csv_file('data/employees_5mb.csv', 5, 'MB')
    else:
        logger.error(f"❌ Taille non supportée: {arg}")
        logger.info("✅ Tailles supportées: 1, 5, 5MB")
        sys.exit(1)

    if success:
        logger.info("🎉 Génération terminée avec succès!")
        logger.info("📋 Fichier prêt pour ingestion BigQuery (Pattern 1)")
        sys.exit(0)
    else:
        logger.error("💥 Échec de la génération")
        sys.exit(1)