import pandas as pd
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN v6 ---

# Nombres de las carpetas para la nueva estructura.
BASE_DIR = "SUNAT"
V6_DIR = os.path.join(BASE_DIR, "v6")
LOG_DIR = os.path.join(V6_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V6_DIR, "PDF descargados")

# Ruta al archivo Excel y al archivo de logs.
EXCEL_FILE_PATH = os.path.join(V6_DIR, "nombres_identificados.xlsx")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# URLs del servidor.
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"

# --- RECURSOS GLOBALES ---
log_buffer = []
downloaded_files_count = 0

# --- FUNCIONES ---

def flush_log_buffer_to_file(force_flush=False):
    """Escribe el contenido del búfer de logs en el archivo logs.txt."""
    if len(log_buffer) >= 100 or (force_flush and log_buffer):
        print(f"\n📝 Escribiendo un lote de {len(log_buffer)} registros en {LOG_FILE_PATH}...\n")
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
            f.write("\n".join(log_buffer))
            f.write(f"\n--- FIN DEL LOTE ---\n")
        log_buffer.clear()

def download_file(session, file_info, total_files):
    """Descarga un único archivo de forma secuencial."""
    global downloaded_files_count
    
    # Construir parámetros desde la información del archivo.
    params = {
        'cod_tipclas': file_info['Tipo'],
        'num_resclas': file_info['Numero'],
        'fano_resclas': str(file_info['Año'])
    }
    year = str(file_info['Año'])
    page_num = file_info['Pagina_Encontrada']
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    # Actualizar progreso.
    downloaded_files_count += 1
    progress = (downloaded_files_count / total_files) * 100
    print(f"Progreso: [{downloaded_files_count}/{total_files}] {progress:.2f}% | Procesando: {filename}", end='\r')

    if os.path.exists(filepath):
        return

    payload = {'accion': 'descargarArchivo', **params}
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=60)
        
        # Condición de éxito corregida y más específica.
        if response.status_code == 200 and response.headers.get('Content-Type', '').strip().lower() == 'application/pdf':
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_log_entry = f"[Página {page_num}] [Descarga Exitosa] Archivo: {filename} | Ruta: {filepath}"
            log_buffer.append(file_log_entry)
        else:
            # Log de error mejorado para ver el Content-Type que devuelve el servidor.
            content_type = response.headers.get('Content-Type', 'N/A')
            error_log_entry = f"[Página {page_num}] [Error de Descarga] Archivo: {filename} | Estado: {response.status_code} | Content-Type Recibido: {content_type}"
            log_buffer.append(error_log_entry)

    except requests.exceptions.RequestException as e:
        error_log_entry = f"[Página {page_num}] [Error de Red] Archivo: {filename} | Error: {e}"
        log_buffer.append(error_log_entry)
    
    flush_log_buffer_to_file()

def main():
    """Función principal que prepara la sesión, lee el Excel y orquesta la descarga secuencial."""
    global downloaded_files_count
    downloaded_files_count = 0
    
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v6' verificada.")

    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"❌ ERROR: No se encontró el archivo de entrada en '{EXCEL_FILE_PATH}'.")
        print("Por favor, asegúrate de que 'nombres_identificados.xlsx' esté en la carpeta 'SUNAT/v6/'.")
        return
        
    print(f"📊 Leyendo la lista de archivos desde '{EXCEL_FILE_PATH}'...")
    df = pd.read_excel(EXCEL_FILE_PATH)
    files_to_download = df.to_dict('records')
    total_files = len(files_to_download)
    
    if total_files == 0:
        print("El archivo Excel no contiene archivos para descargar.")
        return
        
    print(f"Se encontraron {total_files} archivos para procesar.")

    with requests.Session() as session:
        # --- PASO CRÍTICO: PREPARAR LA SESIÓN ---
        print("\n🔑 Iniciando y preparando la sesión con el servidor...")
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': SEARCH_URL
        })
        initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
        try:
            session.post(SEARCH_URL, data=initial_payload, timeout=60)
            print("✅ Sesión preparada exitosamente. Las cookies necesarias han sido establecidas.")
        except requests.exceptions.RequestException as e:
            print(f"❌ No se pudo preparar la sesión. Error: {e}. Abortando.")
            return

        # --- FASE 2: DESCARGA SECUENCIAL ---
        print(f"\n--- Iniciando descarga masiva secuencial ---\n")
        
        for file_info in files_to_download:
            download_file(session, file_info, total_files)

    flush_log_buffer_to_file(force_flush=True)
    print("\n\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()