import os
import datetime
import requests
import json
import re
import base64
from pathlib import Path

class TimeLogger:
    def __init__(self):
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

        # Almacenamiento local para respaldo
        self.home_dir = str(Path.home())
        self.log_dir = os.path.join(self.home_dir, "time_logs")
        self.log_file = os.path.join(self.log_dir, "time_entries.json")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

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
            response.raise_for_status()
            data = response.json()
            return data['id']
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener ID de Jira: {e}")
            if hasattr(e.response, 'text'):
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
            print("\nAtributos de Trabajo Disponibles:")
            for attr in data.get('results', []):
                print(f"\nAtributo: {attr['name']} (Clave: {attr['key']})")
                if attr.get('type') == 'STATIC_LIST' and 'values' in attr:
                    print("Valores válidos:", ", ".join(attr['values']))
            
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener atributos de trabajo: {e}")
            if hasattr(e.response, 'text'):
                print(f"Detalles de la respuesta: {e.response.text}")
            return []

    def log_time(self):
        """Función principal para registrar una entrada de tiempo"""
        print("\n=== Nueva Entrada de Tiempo ===")
        
        try:
            # Obtener atributos de trabajo primero
            print("\nObteniendo atributos de trabajo...")
            attributes = self.get_work_attributes()
            billable_attr = next((attr for attr in attributes if '_Billable_' in attr['key']), None)
            
            if not billable_attr:
                print("\nAdvertencia: No se encontró la configuración del atributo Facturable. Usando valores por defecto.")
                billable_values = {'Yes': 'Yes', 'No': 'No'}
            else:
                billable_values = {val: val for val in billable_attr.get('values', ['Yes', 'No'])}
                print(f"\nValores válidos para facturable: {', '.join(billable_values.keys())}")
            
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
            
            # Convertir esfuerzo a segundos (Tempo espera tiempo en segundos)
            time_spent_seconds = int(float(effort) * 3600)

            # Mapear y/n a valores reales de Tempo
            billable_value = list(billable_values.keys())[0] if billable else list(billable_values.keys())[-1]

            # Preparar payload para la API de Tempo
            payload = {
                "issueId": int(issue_id),  # Asegurar que issueId sea entero
                "timeSpentSeconds": time_spent_seconds,
                "billableSeconds": time_spent_seconds if billable else 0,
                "description": description,
                "authorAccountId": self.account_id,
                "startDate": date,  # Fecha en formato YYYY-MM-DD
                "startTime": "09:00:00",  # Hora en formato HH:mm:ss
                "attributes": [
                    {
                        "key": "_Billable_",
                        "value": billable_value
                    }
                ]
            }

            # Debug: Imprimir el payload
            print("\nEnviando payload a la API de Tempo:")
            print(json.dumps(payload, indent=2))

            # Enviar a la API de Tempo
            success = self.send_to_tempo(payload)
            
            if success:
                print("\n¡Entrada de tiempo registrada exitosamente en Tempo!")
                print(f"Issue: {issue_key}")
                print(f"Esfuerzo: {effort} horas")
                print(f"Descripción: {description}")
                print(f"Fecha: {date}")
            else:
                print("\nFalló el registro en Tempo. Guardando localmente como respaldo.")
                self.save_entry_locally(payload)

        except ValueError as e:
            print(f"\nError: {str(e)}")
            return False
        except Exception as e:
            print(f"\nError inesperado: {str(e)}")
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
            print("\nEnviando solicitud a:", url)
            print("Headers:", {k: v for k, v in headers.items() if k != "Authorization"})
            
            response = requests.post(url, json=payload, headers=headers)
            print(f"\nCódigo de estado de la respuesta: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("¡Entrada de tiempo registrada exitosamente!")
                return True
            else:
                print(f"Error en la respuesta de la API de Tempo: {response.text}")
                response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error al registrar en Tempo: {e}")
            if hasattr(e.response, 'text'):
                print(f"Detalles de la respuesta: {e.response.text}")
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
    logger = TimeLogger()
    
    while True:
        logger.log_time()
        
        # Preguntar si el usuario quiere registrar otra entrada
        another = input("\n¿Registrar otra entrada? (y/n): ").lower()
        if another != 'y':
            print("¡Hasta luego!")
            break

if __name__ == "__main__":
    main() 