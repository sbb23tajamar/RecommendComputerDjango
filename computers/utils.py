from openai import AzureOpenAI  
import os
from dotenv import load_dotenv
import pyodbc
import os
import re
import mysql.connector
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from computer_manager.settings import DOC_INT_ENDPOINT, DOC_INT_KEY, DOC_INT_MODEL, AI_ENDPOINT, AI_KEY, AI_MODEL, DATABASES
 
document_intelligence_endpoint = DOC_INT_ENDPOINT
document_intelligence_key = DOC_INT_KEY
document_intelligence_model_id = DOC_INT_MODEL  # ID del modelo personalizado
 
openai_endpoint = AI_ENDPOINT
openai_api_key = AI_KEY

server = DATABASES['default']['HOST']
database = DATABASES['default']['NAME']
username = DATABASES['default']['USER']
password = DATABASES['default']['PASSWORD']
##driver = DATABASES['default']['OPTIONS']['driver']

# Configuración de Azure OpenAI
client = AzureOpenAI(  
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,  
    api_version="2024-05-01-preview",  
)  

#ChatBot Method
def detect_language(text):
    """Detecta el idioma del texto usando Azure OpenAI."""
    prompt = f"Detecta el idioma del siguiente texto y responde solo con el código del idioma (es, en, fr, zh, ru):\n\n{text}"

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "system", "content": "Eres un asistente de detección de idiomas."},
                      {"role": "user", "content": prompt}],
            max_tokens=5
        )

        detected_language = response.choices[0].message.content.strip()
        return detected_language if detected_language in ["es", "en", "fr", "zh", "ru"] else "es"  # Default a español

    except Exception as e:
        return "es"  # Default en caso de error


def clean_sql_query(sql_query):
    """Limpia la consulta SQL eliminando errores de formato y asegurando que los valores numéricos sean correctos."""
    sql_query = re.sub(r"```sql|```", "", sql_query).strip()
    sql_query = re.sub(r"ram\s*=\s*'(\d+)\s*gb'", r"ram = \1", sql_query)
    sql_query = re.sub(r"precio\s*=\s*'(\d+)'", r"precio = \1", sql_query)
    sql_query = re.sub(r"disco_duro\s*=\s*'(\d+)\s*gb'", r"disco_duro = \1", sql_query)
    return sql_query


def generate_query(user_input):
    """Convierte la consulta del usuario en una búsqueda SQL válida para SQL Server."""
    prompt = f"""
    Eres un asistente que genera consultas SQL válidas para SQL Server.
    Extrae los requisitos del usuario y genera SOLO la consulta SQL, sin texto adicional.

    BASE DE DATOS: Tabla 'computers'
    Columnas: marca, modelo, procesador, ram, gpu, disco_duro, sistema_operativo, precio

    🔹 REGLAS IMPORTANTES:
    - ❌ NO uses `LIMIT`, usa `TOP` en su lugar.
    - ❌ NO uses tildes invertidas (`).
    - ✅ Usa `LIKE '%valor%'` para búsquedas parciales en `procesador`, `gpu`, `sistema_operativo` y `marca`.
    - ✅ Usa `ORDER BY` para ordenar resultados.
    - ✅ Asegura que los valores numéricos **NO** tengan comillas ('16 gb' ❌ → `16` ✅).
    - ✅ Para relación calidad-precio usa `ORDER BY (precio / ram) ASC`.

        🔹 EJEMPLOS:
    Usuario: "¿Qué ordenadores tienen 16GB de RAM?"
    SQL: SELECT * FROM computers WHERE ram = 16;

    Usuario: "¿Cuál es el ordenador con mejor relación calidad-precio?"
    SQL: SELECT TOP 1 * FROM computers ORDER BY (precio / ram) ASC;

    Usuario: "¿Cuántos ordenadores tienen más de 512GB de disco?"
    SQL: SELECT COUNT(*) FROM computers WHERE disco_duro > 512;

    Usuario: "¿Qué ordenadores tienen procesador Intel i5?"
    SQL: SELECT * FROM computers WHERE LOWER(procesador) LIKE '%intel%' AND LOWER(procesador) LIKE '%i5%';

    Usuario: "{user_input}"
    """

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "system", "content": "Eres un experto en SQL Server."},
                      {"role": "user", "content": prompt}],
            max_tokens=100
        )

        sql_query = response.choices[0].message.content.strip()
        sql_query = clean_sql_query(sql_query)

        if not sql_query.lower().startswith("select"):
            return "⚠️ Error: la consulta SQL generada no es válida."

        print(f"✅ Consulta generada: {sql_query}")
        return sql_query

    except Exception as e:
        return f"⚠️ Error generando la consulta SQL: {str(e)}"


def chatbot_response(user_input):
    """Genera la respuesta del chatbot en el idioma del usuario."""
    user_language = detect_language(user_input)
    sql_query = generate_query(user_input)

    if "Error generando la consulta" in sql_query:
        return sql_query

    try:
        results = search_computers(sql_query)

        if not results:
            return {
                "es": "🔍 No encontré ningún equipo con esas características. ¿Quieres intentar otra búsqueda? 😊",
                "en": "🔍 I couldn't find any computers with those specifications. Would you like to try another search? 😊",
                "fr": "🔍 Je n'ai trouvé aucun ordinateur avec ces spécifications. Voulez-vous essayer une autre recherche ? 😊",
                "zh": "🔍 我找不到符合这些规格的计算机。你想尝试另一个搜索吗？😊",
                "ru": "🔍 Я не нашел компьютеров с такими характеристиками. Хотите попробовать другой поиск? 😊"
            }.get(user_language, "🔍 No encontré ningún equipo con esas características. 😊")

        formatted_results = "\n".join([
            f"{row['marca']} {row['modelo']} - {row['procesador']} | RAM: {row['ram']}GB | GPU: {row['gpu']} | Disco: {row['disco_duro']}GB | {row['sistema_operativo']} - 💰 {row['precio']}€"
            for row in results
        ])

        prompt = f"""
        Eres un asistente experto en informática y hardware de computadoras.
        Un usuario ha solicitado información sobre ordenadores en nuestra base de datos.

        🔹 **Consulta del usuario:** "{user_input}"
        🔹 **Resultados de la base de datos:** 
        {formatted_results}

        📌 **Tu tarea:** 
        - Explica los resultados de manera clara y profesional.
        - Destaca las diferencias entre los modelos (si hay más de uno).
        - Recomienda una opción si es posible.
        - Usa un tono amigable pero técnico.
        - Responde en este idioma: {user_language}
        """

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "system", "content": f"Eres un experto en hardware y debes responder en {user_language}."},
                      {"role": "user", "content": prompt}],
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return {
            "es": f"❌ Hubo un problema al buscar en la base de datos: {str(e)}",
            "en": f"❌ There was a problem searching the database: {str(e)}",
            "fr": f"❌ Un problème est survenu lors de la recherche dans la base de données : {str(e)}",
            "zh": f"❌ 查询数据库时出现问题：{str(e)}",
            "ru": f"❌ Произошла ошибка при поиске в базе данных: {str(e)}"
        }.get(user_language, f"❌ Hubo un problema al buscar en la base de datos: {str(e)}")

#extrarct_pdf method
def extract_data_from_pdf(pdf_path):
    """Extracts data from a PDF using Azure Document Intelligence."""
    endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    api_key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    model_id = os.getenv("AZURE_MODEL_ID")

    # Connect to Azure
    document_analysis_client = DocumentAnalysisClient(endpoint, AzureKeyCredential(api_key))

    with open(pdf_path, "rb") as pdf_file:
        poller = document_analysis_client.begin_analyze_document(model_id, document=pdf_file)
        result = poller.result()

    # Extract and structure the data
    extracted_data = {}
    for field_name, field_value in result.documents[0].fields.items():
        extracted_data[field_name] = field_value.value if field_value else None

    return extracted_data

#validate_data method
def validate_data(data):
    """Checks that the extracted data is correct and complete, and normalizes key names."""

    # Mapeo de claves para que coincidan con la base de datos
    key_mapping = {
        "SO": "sistema_operativo",
        "marca": "marca",
        "modelo": "modelo",
        "procesador": "procesador",
        "ram": "ram",
        "gpu": "gpu",
        "disco duro": "disco_duro",
        "precio": "precio"
    }

    # Normalizar claves
    normalized_data = {key_mapping.get(k, k): v for k, v in data.items()}

    # Lista de campos requeridos en la base de datos
    required_fields = ["marca", "modelo", "procesador", "ram", "gpu", "disco_duro", "sistema_operativo", "precio"]

    for field in required_fields:
        if not normalized_data.get(field):
            print(f"⚠️ Warning: The field '{field}' is empty or was not detected correctly.")

    # Formatear precio
    if "precio" in normalized_data:
        normalized_data["precio"] = convert_price_to_float(normalized_data["precio"])

    # Formatear RAM y Disco Duro
    if "ram" in normalized_data:
        normalized_data["ram"] = convert_storage_to_float(normalized_data["ram"])

    if "disco_duro" in normalized_data:
        normalized_data["disco_duro"] = convert_storage_to_float(normalized_data["disco_duro"])

    return normalized_data

def convert_price_to_float(price):
    """Converts a price string from European format (e.g., '2.130,00€') to float (e.g., 2130.00)."""
    if not price:
        return None
    price = price.replace("€", "").strip()
    price = price.replace(".", "").replace(",", ".")  # Convertir formato europeo a estándar
    try:
        return round(float(price), 2)
    except ValueError:
        print(f"⚠️ Warning: Invalid price format. Original value: {price}")
        return None  # Evitar errores en la BD

def convert_storage_to_float(storage):
    """Converts a storage value from European format (e.g., '1.024,00 GB') to float (e.g., 1024.00)."""
    if not storage:
        return None
    storage = storage.replace(".", "").replace(",", ".").strip()  # Convertir formato europeo a estándar
    match = re.search(r"(\d+(\.\d+)?)\s*(GB|TB)", storage, re.IGNORECASE)
    if match:
        number = float(match.group(1))
        unit = match.group(3).upper()
        return round(number * 1024, 2) if unit == "TB" else round(number, 2)  # Convertir TB a GB
    try:
        return round(float(storage), 2)
    except ValueError:
        print(f"⚠️ Warning: Invalid storage format. Original value: {storage}")
        return None

#database method
def get_db_connection():
    """Establishes a connection to the Azure SQL Database."""
    ##DRIVER={driver} Necesario solo enm local no para subirlo en Render
    try:
        conn = mysql.connector.connect(
             host=server,
             user=username,
             password=password,
             database=database
        )
        return conn
    except pyodbc.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def create_table():
    """Creates the 'computers' table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='computers' AND xtype='U')
        CREATE TABLE computers (
            id INT IDENTITY(1,1) PRIMARY KEY,
            marca NVARCHAR(50),
            modelo NVARCHAR(50),
            procesador NVARCHAR(100),
            ram DECIMAL(10,2),
            gpu NVARCHAR(100),
            disco_duro DECIMAL(10,2),
            sistema_operativo NVARCHAR(50),
            precio DECIMAL(10,2)
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Table 'computers' is ready.")

def check_duplicate(computer_data):
    """Checks if a computer with the same specs already exists in the database."""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM computers 
        WHERE marca = ? AND modelo = ? AND procesador = ? 
        AND ram = ? AND gpu = ? AND disco_duro = ? 
        AND sistema_operativo = ? AND precio = ?
    """, (
        computer_data["marca"], computer_data["modelo"], computer_data["procesador"],
        computer_data["ram"], computer_data["gpu"], computer_data["disco_duro"],
        computer_data["sistema_operativo"], computer_data["precio"]
    ))

    count = cursor.fetchone()[0]
    conn.close()
    return count > 0  # True si ya existe, False si no

def insert_computer(computer_data):
    """Inserts a new computer into the database if it does not already exist."""
    if check_duplicate(computer_data):
        print("⚠️ This computer already exists in the database. Skipping insertion.")
        return

    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO computers (marca, modelo, procesador, ram, gpu, disco_duro, sistema_operativo, precio) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        computer_data["marca"], computer_data["modelo"], computer_data["procesador"],
        computer_data["ram"], computer_data["gpu"], computer_data["disco_duro"],
        computer_data["sistema_operativo"], computer_data["precio"]
    ))

    conn.commit()
    conn.close()
    print("✅ New computer inserted successfully.")

def search_computers(query):
    """Ejecuta la consulta SQL generada por OpenAI."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"❌ Error al ejecutar la consulta SQL: {e}")
        return []
