import os
import datetime
import requests
import json
import re
import base64
import argparse
from pathlib import Path

class TimeLogger:
    def __init__(self, verbose=False):
        self.verbose = verbose
        # Cargar configuración desde archivo
        self.config = self.load_config()
        
        # Configuración de Jira y Tempo desde el archivo config.json
        self.jira_url = self.config['jira']['url']
        self.tempo_api_token = self.config['tempo']['api_token']
        self.jira_email = self.config['jira']['email']
        self.jira_api_token = self.config['jira']['api_token']
        self.account_id = self.config['jira']['account_id']

        # Crear token de autenticación para Jira
        credentials = f"{self.jira_email}:{self.jira_api_token}"
        self.jira_auth = base64.b64encode(credentials.encode()).decode()

        # Verificar credenciales de Jira
        self.verify_jira_credentials()

        # Almacenamiento local para respaldo
        self.home_dir = str(Path.home())
        self.log_dir = os.path.join(self.home_dir, "time_logs")
        self.log_file = os.path.join(self.log_dir, "time_entries.json")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_message(self, message, is_verbose=False, is_error=False):
        """Imprimir mensaje según el modo verbose"""
        if is_error or not is_verbose or (is_verbose and self.verbose):
            print(message)

    def verify_jira_credentials(self):
        """Verificar que las credenciales de Jira sean válidas"""
        url = f"{self.jira_url}/rest/api/3/myself"
        headers = {
            "Authorization": f"Basic {self.jira_auth}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self.log_message("✅ Conexión con Jira establecida correctamente", is_verbose=True)
        except requests.exceptions.RequestException as e:
            self.log_message("\n❌ Error al conectar con Jira", is_error=True)
            if response.status_code == 401:
                self.log_message("Las credenciales de Jira son inválidas. Por favor, verifica tu email y API token en config.json", is_error=True)
            elif response.status_code == 404:
                self.log_message("La URL de Jira es incorrecta. Por favor, verifica la URL en config.json", is_error=True)
            else:
                self.log_message(f"Error de conexión: {str(e)}", is_error=True)
            raise SystemExit(1)

    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        example_config_path = os.path.join(os.path.dirname(__file__), 'config.example.json')
        
        if not os.path.exists(config_path):
            if os.path.exists(example_config_path):
                print(f"\n⚠️  No se encontró el archivo config.json")
                print(f"ℹ️  Por favor, crea un archivo config.json basado en config.example.json")
                print(f"📝 Copia config.example.json a config.json y actualiza los valores con tus credenciales")
            else:
                print(f"\n❌ No se encontraron archivos de configuración")
                print(f"Por favor, contacta al administrador del sistema")
            raise FileNotFoundError("Archivo de configuración no encontrado")
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"\n❌ Error al leer el archivo de configuración")
            print(f"Por favor, verifica que config.json tiene un formato JSON válido")
            raise

    def validate_jira_issue_id(self, issue_id):
        """Validar que el ID del issue coincida con el formato de Jira (ej: PROJ-123 o INT0012-92)"""
        pattern = r'^[A-Z0-9]+-\d+$'
        if not re.match(pattern, issue_id):
            raise ValueError("Formato de ID de Jira inválido. Formato esperado: PROJ-123 o INT0012-92")
        return issue_id

    def validate_effort(self, effort):
        """Validar que el esfuerzo sea un número positivo"""
        try:
            effort_float = float(effort)
            if effort_float <= 0:
                raise ValueError
            return effort_float
        except ValueError:
            raise ValueError("El esfuerzo debe ser un número positivo")

    def get_jira_issue_id(self, issue_key):
        """Obtener el ID numérico del issue de Jira usando la clave"""
        url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
        headers = {
            "Authorization": f"Basic {self.jira_auth}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 404:
                print(f"\n❌ El issue {issue_key} no existe o no tienes permiso para verlo")
                print("Por favor verifica:")
                print("1. Que el ID del issue sea correcto")
                print("2. Que tengas permisos para ver este issue")
                print("3. Que el proyecto exista y tengas acceso a él")
                raise ValueError(f"Issue {issue_key} no encontrado o sin acceso")
            
            response.raise_for_status()
            data = response.json()
            return data['id']
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error al obtener ID de Jira: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    print("Las credenciales de Jira son inválidas")
                elif e.response.status_code == 403:
                    print("No tienes permisos suficientes para acceder a este issue")
                print(f"Detalles de la respuesta: {e.response.text}")
            raise ValueError(f"No se pudo obtener el ID para {issue_key}")

    def validate_date(self, date_str):
        """Validar que la fecha esté en formato YYYY-MM-DD y no sea muy antigua"""
        if not date_str:
            # Si no se proporciona fecha, usar la fecha actual
            return datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            # Verificar que la fecha no sea más de 30 días en el pasado
            days_ago = (datetime.datetime.now() - date).days
            if days_ago > 30:
                raise ValueError("La fecha no puede ser más de 30 días en el pasado")
            return date.strftime("%Y-%m-%d")  # Asegurar formato consistente
        except ValueError as e:
            if "más de 30 días" in str(e):
                raise e
            raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")

    def validate_billable(self, value):
        """Validar entrada de facturable (y/n)"""
        value = value.lower()
        if value not in ['y', 'n']:
            raise ValueError("Por favor ingrese 'y' para facturable o 'n' para no facturable")
        return value == 'y'

    def get_input(self, prompt, required=True, validator=None):
        """Función auxiliar para obtener entrada del usuario con validación"""
        while True:
            value = input(prompt).strip()
            if not value and not required:
                return value
            if not value and required:
                print("¡Este campo es requerido!")
                continue
            
            if validator:
                try:
                    return validator(value)
                except ValueError as e:
                    print(f"Error: {str(e)}")
                continue
            return value

    def get_work_attributes(self):
        """Obtener atributos de trabajo disponibles de la API de Tempo"""
        url = "https://api.tempo.io/4/work-attributes"
        headers = {
            "Authorization": f"Bearer {self.tempo_api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Imprimir atributos disponibles y sus valores
            self.log_message("\nAtributos de Trabajo Disponibles:", is_verbose=True)
            for attr in data.get('results', []):
                self.log_message(f"\nAtributo: {attr['name']} (Clave: {attr['key']})", is_verbose=True)
                if attr.get('type') == 'STATIC_LIST' and 'values' in attr:
                    self.log_message(f"Valores válidos: {', '.join(attr['values'])}", is_verbose=True)
            
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            self.log_message(f"Error al obtener atributos de trabajo: {e}", is_error=True)
            if hasattr(e.response, 'text'):
                self.log_message(f"Detalles de la respuesta: {e.response.text}", is_error=True)
            return []

    def log_time(self):
        """Función principal para registrar una entrada de tiempo"""
        self.log_message("\n=== Nueva Entrada de Tiempo ===", is_verbose=True)
        
        try:
            # Obtener atributos de trabajo primero
            self.log_message("\nObteniendo atributos de trabajo...", is_verbose=True)
            attributes = self.get_work_attributes()
            billable_attr = next((attr for attr in attributes if '_Billable_' in attr['key']), None)
            
            if not billable_attr:
                self.log_message("\nAdvertencia: No se encontró la configuración del atributo Facturable. Usando valores por defecto.", is_verbose=True)
                billable_values = {'Yes': 'Yes', 'No': 'No'}
            else:
                billable_values = {val: val for val in billable_attr.get('values', ['Yes', 'No'])}
                self.log_message(f"\nValores válidos para facturable: {', '.join(billable_values.keys())}", is_verbose=True)
            
            # Inicializar fecha actual
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Recolectar y validar información requerida
            issue_key = self.get_input("Ingrese ID del Issue de Jira (ej: PROJ-123): ", validator=self.validate_jira_issue_id)
            effort = self.get_input("Ingrese esfuerzo en horas (ej: 2.5): ", validator=self.validate_effort)
            description = self.get_input("Ingrese descripción: ")
            billable = self.get_input("¿Es facturable? (y/n): ", validator=self.validate_billable)
            date = self.get_input(f"Ingrese fecha (YYYY-MM-DD) o presione Enter para hoy ({today}): ", required=False, validator=self.validate_date) or today
            
            # Obtener el ID numérico del issue de Jira
            issue_id = self.get_jira_issue_id(issue_key)
            
            # Convertir esfuerzo a segundos
            time_spent_seconds = int(float(effort) * 3600)

            # Mapear y/n a valores reales de Tempo
            billable_value = list(billable_values.keys())[0] if billable else list(billable_values.keys())[-1]

            # Preparar payload para la API de Tempo
            payload = {
                "issueId": int(issue_id),
                "timeSpentSeconds": time_spent_seconds,
                "billableSeconds": time_spent_seconds if billable else 0,
                "description": description,
                "authorAccountId": self.account_id,
                "startDate": date,
                "startTime": "09:00:00",
                "attributes": [
                    {
                        "key": "_Billable_",
                        "value": billable_value
                    }
                ]
            }

            # Debug: Imprimir el payload
            self.log_message("\nEnviando payload a la API de Tempo:", is_verbose=True)
            self.log_message(json.dumps(payload, indent=2), is_verbose=True)

            # Enviar a la API de Tempo
            success = self.send_to_tempo(payload)
            
            if success:
                self.log_message("\n✅ Entrada de tiempo registrada exitosamente")
                self.log_message(f"Issue: {issue_key}", is_verbose=True)
                self.log_message(f"Esfuerzo: {effort} horas", is_verbose=True)
                self.log_message(f"Descripción: {description}", is_verbose=True)
                self.log_message(f"Fecha: {date}", is_verbose=True)
            else:
                self.log_message("\n❌ Falló el registro en Tempo. Guardando localmente como respaldo.", is_error=True)
                self.save_entry_locally(payload)

        except ValueError as e:
            self.log_message(f"\n❌ Error: {str(e)}", is_error=True)
            return False
        except Exception as e:
            self.log_message(f"\n❌ Error inesperado: {str(e)}", is_error=True)
            return False

        return True

    def send_to_tempo(self, payload):
        """Enviar entrada de tiempo a la API de Tempo"""
        url = "https://api.tempo.io/4/worklogs"
        headers = {
            "Authorization": f"Bearer {self.tempo_api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Debug: Imprimir la solicitud completa
            self.log_message("\nEnviando solicitud a: " + url, is_verbose=True)
            self.log_message("Headers: " + str({k: v for k, v in headers.items() if k != "Authorization"}), is_verbose=True)
            
            response = requests.post(url, json=payload, headers=headers)
            self.log_message(f"\nCódigo de estado de la respuesta: {response.status_code}", is_verbose=True)
            
            if response.status_code in [200, 201]:
                return True
            else:
                self.log_message(f"Error en la respuesta de la API de Tempo: {response.text}", is_error=True)
                response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            self.log_message(f"Error al registrar en Tempo: {e}", is_error=True)
            if hasattr(e.response, 'text'):
                self.log_message(f"Detalles de la respuesta: {e.response.text}", is_error=True)
            return False

    def save_entry_locally(self, entry):
        """Guardar entrada en archivo JSON local como respaldo"""
        entries = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []
        
        entries.append(entry)
        with open(self.log_file, 'w') as f:
            json.dump(entries, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Registrador de tiempo para Jira/Tempo')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar información detallada')
    args = parser.parse_args()
    
    logger = TimeLogger(verbose=args.verbose)
    
    while True:
        logger.log_time()
        
        # Preguntar si el usuario quiere registrar otra entrada
        another = input("\n¿Registrar otra entrada? (y/n): ").lower()
        if another != 'y':
            print("¡Hasta luego!")
            break

if __name__ == "__main__":
    main() 