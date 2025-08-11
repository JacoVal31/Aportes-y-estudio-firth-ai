import requests
import os
import re
import time
import concurrent.futures
import threading
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIGURACIÓN ---

# Define cuántas páginas quieres procesar (máximo 204).
TOTAL_PAGES = 204

# Número de descargas en paralelo.
MAX_WORKERS = 10

# Nombres de las carpetas para la nueva estructura v3.
BASE_DIR = "SUNAT"
V3_DIR = os.path.join(BASE_DIR, "v4")
LOG_DIR = os.path.join(V3_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V3_DIR, "PDF descargados")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")
EXCEL_FILE_PATH = os.path.join(V3_DIR, "nombres_identificados.xlsx")


# URLs del servidor.
BASE_URL = "http://www.aduanet.gob.pe"
SEARCH_URL = f"{BASE_URL}/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = f"{BASE_URL}/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS COMPARTIDOS Y LOCKS ---

log_buffer = []
log_lock = threading.Lock()
downloaded_files_count = 0
total_files_to_download = 0

# --- FUNCIONES ---

def flush_log_buffer_to_file(force_flush=False):
    """Escribe el contenido del búfer de logs en el archivo logs.txt."""
    with log_lock:
        if len(log_buffer) >= 100 or (force_flush and log_buffer):
            print(f"\n📝 Escribiendo un lote de {len(log_buffer)} registros en {LOG_FILE_PATH}...\n")
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
                f.write("\n".join(log_buffer))
                f.write(f"\n--- FIN DEL LOTE ---\n")
            log_buffer.clear()

def download_file(session, file_info):
    """Descarga un único archivo, gestionando la estructura de carpetas y el logging."""
    global downloaded_files_count
    params = file_info['params']
    page_num = file_info['page_num']
    
    year = params['fano_resclas']
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    if os.path.exists(filepath):
        with log_lock:
            downloaded_files_count += 1
            progress = (downloaded_files_count / total_files_to_download) * 100
            print(f"[{progress:6.2f}%] ☑️  Ya existe: {filename} en {year_dir}")
        return

    payload = {'accion': 'descargarArchivo', **params}
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=60)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            console_log = f"✅ Descargado: {filename} -> Guardado en: {year_dir}"
            file_log_entry = f"[Página {page_num}] [Descarga Exitosa] Archivo: {filename} | Ruta: {filepath}"

            with log_lock:
                downloaded_files_count += 1
                progress = (downloaded_files_count / total_files_to_download) * 100
                print(f"[{progress:6.2f}%] {console_log}")
                log_buffer.append(file_log_entry)
                flush_log_buffer_to_file()
        else:
            print(f"❌ Error al descargar {filename}. Estado: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ocurrió un error de red al intentar descargar {filename}: {e}")

def parse_page_for_metadata(html_content, page_num):
    """Analiza el HTML de una página y devuelve una lista con los metadatos de los archivos."""
    soup = BeautifulSoup(html_content, 'html.parser')
    files_on_page = []
    
    download_links = soup.find_all('a', onclick=lambda x: x and x.strip().startswith("jsDescargarArchivo"))
    
    for link in download_links:
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", link.get('onclick', ''))
        
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            file_params = {'cod_tipclas': cod_tipclas, 'num_resclas': num_resclas, 'fano_resclas': fano_resclas}
            files_on_page.append({'params': file_params, 'page_num': page_num})
            
    return files_on_page

def main():
    """Función principal que orquesta la recolección, exportación a Excel y descarga concurrente."""
    global total_files_to_download
    
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v3' verificada/creada.")
    
    files_to_download = []
    
    # --- FASE 1: RECOLECCIÓN SECUENCIAL DE METADATOS ---
    print("\n--- FASE 1: Iniciando recolección de metadatos de todas las páginas ---")
    
    try:
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': SEARCH_URL
            })
            
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            response = session.post(SEARCH_URL, data=initial_payload, timeout=60)
            response.raise_for_status()
            
            print("Página 1: Analizando...")
            files_to_download.extend(parse_page_for_metadata(response.text, 1))
            
            for page_num in range(2, TOTAL_PAGES + 1):
                print(f"Página {page_num}: Solicitando y analizando...")
                pagination_payload = {'currPage': str(page_num - 1), 'Action': 'next', 'tamanioPagina': '30'}
                page_response = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
                page_response.raise_for_status()
                
                files_on_page = parse_page_for_metadata(page_response.text, page_num)
                if not files_on_page:
                    print(f"ADVERTENCIA: No se encontraron archivos en la página {page_num}. Posible fin de los resultados.")
                    continue
                files_to_download.extend(files_on_page)
                time.sleep(0.5)
    except (requests.exceptions.RequestException, KeyboardInterrupt) as e:
        print(f"\n🛑 Proceso de recolección interrumpido o fallido: {e}")
        return

    total_files_to_download = len(files_to_download)
    print(f"\n--- FASE 1 COMPLETA: Se recolectaron metadatos de {total_files_to_download} archivos en total. ---")

    if not files_to_download:
        print("No se encontró ningún archivo para descargar. Saliendo.")
        return

    # --- EXPORTACIÓN A EXCEL ---
    print(f"\n📊 Creando archivo de Excel en: {EXCEL_FILE_PATH}")
    excel_data = []
    for item in files_to_download:
        params = item['params']
        full_code = f"{params['cod_tipclas']}-{params['num_resclas']}-{params['fano_resclas']}"
        excel_data.append({
            'Pagina_Encontrada': item['page_num'],
            'Codigo_Resolucion': full_code,
            'Año': params['fano_resclas'],
            'Tipo': params['cod_tipclas'],
            'Numero': params['num_resclas']
        })
    df = pd.DataFrame(excel_data)
    df.to_excel(EXCEL_FILE_PATH, index=False, engine='openpyxl')
    print("✅ Archivo de Excel 'nombres_identificados.xlsx' creado exitosamente.")

    # --- FASE 2: DESCARGA MASIVA CONCURRENTE ---
    print(f"\n--- FASE 2: Iniciando descarga masiva con {MAX_WORKERS} hilos ---")
    
    with requests.Session() as download_session:
        download_session.headers.update({'User-Agent': 'Mozilla/5.0'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(download_file, download_session, file_info) for file_info in files_to_download]
            concurrent.futures.wait(futures)

    flush_log_buffer_to_file(force_flush=True)
    print("\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()