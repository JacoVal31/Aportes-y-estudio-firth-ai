import requests
import os
import re
import time
import concurrent.futures
import threading
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURACIÓN ---

# Define cuántas páginas quieres procesar (máximo 204).
TOTAL_PAGES = 204

# Número de descargas en paralelo.
MAX_WORKERS = 20

# Nombres de las carpetas para la nueva estructura.
BASE_DIR = "SUNAT"
V2_DIR = os.path.join(BASE_DIR, "v2")
LOG_DIR = os.path.join(V2_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V2_DIR, "PDF descargados")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# URLs del servidor.
BASE_URL = "http://www.aduanet.gob.pe"
SEARCH_URL = f"{BASE_URL}/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = f"{BASE_URL}/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS COMPARTIDOS Y LOCKS ---

# Búfer para almacenar logs antes de escribirlos en el archivo.
log_buffer = []
# Lock para evitar que múltiples hilos escriban en el búfer al mismo tiempo.
log_lock = threading.Lock()

# --- FUNCIONES ---

def flush_log_buffer_to_file():
    """Escribe el contenido del búfer de logs en el archivo logs.txt."""
    with log_lock:
        if not log_buffer:
            return

        print(f"\n📝 Escribiendo un lote de {len(log_buffer)} registros en {LOG_FILE_PATH}...\n")
        
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
            for entry in log_buffer:
                f.write(entry + "\n")
            f.write(f"--- FIN DEL LOTE ---\n")
        
        log_buffer.clear()

def download_file(session, params, page_num):
    """Descarga un único archivo, gestionando la estructura de carpetas y el logging."""
    year = params['fano_resclas']
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    # Crear la estructura de carpetas por año.
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    if os.path.exists(filepath):
        console_log = f"☑️  Ya existe: {filename} en {year_dir}"
        print(console_log)
        return

    payload = {'accion': 'descargarArchivo', **params}
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=60)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Preparar logs detallados.
            console_log = f"✅ Descargado: {filename} -> Guardado en: {year_dir}"
            file_log_entry = f"[Página {page_num}] [Descarga Exitosa] Archivo: {filename} | Ruta: {filepath}"

            # Usar un lock para añadir logs al búfer de forma segura.
            with log_lock:
                print(console_log)
                log_buffer.append(file_log_entry)
                if len(log_buffer) >= 100:
                    flush_log_buffer_to_file()
        else:
            print(f"❌ Error al descargar {filename}. Estado: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ocurrió un error de red al intentar descargar {filename}: {e}")

def process_page(session, executor, html_content, page_num):
    """Analiza el HTML de una página y somete las tareas de descarga al executor concurrente."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    download_links = soup.find_all(
        'a',
        onclick=lambda x: x and x.strip().startswith("jsDescargarArchivo")
    )
    
    if not download_links:
        print(f"ADVERTENCIA: No se encontraron enlaces de descarga en la página {page_num}.")
        return False

    print(f"Encontradas {len(download_links)} resoluciones en página {page_num}. Enviando a la cola de descarga...")

    for link in download_links:
        onclick_attr = link.get('onclick', '')
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", onclick_attr)
        
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            file_params = {'cod_tipclas': cod_tipclas, 'num_resclas': num_resclas, 'fano_resclas': fano_resclas}
            # Someter la tarea de descarga para ejecución en paralelo.
            executor.submit(download_file, session, file_params, page_num)
    return True

def main():
    """Función principal que orquesta la sesión, la concurrencia y la paginación."""
    # 1. Crear toda la estructura de directorios necesaria.
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas verificada/creada.")
    
    # 2. Iniciar el gestor de hilos (ThreadPoolExecutor).
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': SEARCH_URL
            })

            print("📡 Realizando búsqueda inicial para obtener la primera página...")
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            
            try:
                response = session.post(SEARCH_URL, data=initial_payload, timeout=60)
                response.raise_for_status()
                
                print("\n--- Procesando Página 1 ---")
                process_page(session, executor, response.text, 1)

                # 3. Iterar por el resto de las páginas.
                for page_num in range(2, TOTAL_PAGES + 1):
                    print(f"\n--- Solicitando Página {page_num} de {TOTAL_PAGES} ---")
                    pagination_payload = {'currPage': str(page_num - 1), 'Action': 'next', 'tamanioPagina': '30'}
                    
                    page_response = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
                    page_response.raise_for_status()
                    
                    if not process_page(session, executor, page_response.text, page_num):
                        print("Deteniendo el script debido a una página sin enlaces. Puede que hayamos llegado al final.")
                        break
                    
                    time.sleep(1) # Pausa cortés entre la solicitud de cada PÁGINA.
                    
            except requests.exceptions.RequestException as e:
                print(f"Error crítico durante la paginación: {e}")
            except KeyboardInterrupt:
                print("\n🛑 Proceso interrumpido por el usuario.")

    # 4. Al finalizar, escribir cualquier log restante en el búfer.
    print("Descargas en cola finalizadas. Escribiendo logs restantes...")
    flush_log_buffer_to_file()

    print("\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()