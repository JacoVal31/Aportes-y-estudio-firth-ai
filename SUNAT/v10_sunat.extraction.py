import requests
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN v9 ---

# Define cuántas páginas quieres procesar (máximo 204).
TOTAL_PAGES = 204

# Nombres de las carpetas para la nueva estructura.
BASE_DIR = "SUNAT"
V9_DIR = os.path.join(BASE_DIR, "v9")
LOG_DIR = os.path.join(V9_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V9_DIR, "PDF descargados")

# Ruta al archivo de logs.
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# URLs del servidor.
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

# --- FUNCIONES ---

def flush_log_buffer_to_file(force_flush=False):
    """Escribe el contenido del búfer de logs en el archivo logs.txt."""
    if len(log_buffer) >= 50 or (force_flush and log_buffer): # Escribimos más seguido
        print(f"\n📝 Escribiendo un lote de {len(log_buffer)} registros en {LOG_FILE_PATH}...\n")
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
            f.write("\n".join(log_buffer))
            f.write(f"\n--- FIN DEL LOTE ---\n")
        log_buffer.clear()

def download_file(session, file_info):
    """Descarga un único archivo de forma secuencial."""
    global processed_files_count
    
    params = file_info['params']
    page_num = file_info['page_num']
    
    # Aseguramos el formato correcto del número.
    params['num_resclas'] = str(params['num_resclas']).zfill(6)
    
    year = str(params['fano_resclas'])
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    processed_files_count += 1
    print(f"Progreso: [{processed_files_count}/~6120] | Procesando: {filename}", end='\r')

    if os.path.exists(filepath):
        log_buffer.append(f"[Página {page_num}] [Omitido - Ya Existe] Archivo: {filename}")
        return

    payload = {'accion': 'descargarArchivo', **params}
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=60)
        
        if response.status_code == 200 and response.headers.get('Content-Type', '').strip().lower() == 'application/pdf':
            with open(filepath, 'wb') as f:
                f.write(response.content)
            log_buffer.append(f"[Página {page_num}] [Descarga Exitosa] Archivo: {filename} | Ruta: {filepath}")
        else:
            content_type = response.headers.get('Content-Type', 'N/A')
            log_buffer.append(f"[Página {page_num}] [Error de Descarga] Archivo: {filename} | Estado: {response.status_code} | Content-Type: {content_type}")

    except requests.exceptions.RequestException as e:
        log_buffer.append(f"[Página {page_num}] [Error de Red] Archivo: {filename} | Error: {e}")
    
    flush_log_buffer_to_file()

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
    """Función principal que navega, analiza y descarga de forma secuencial página por página."""
    global processed_files_count
    processed_files_count = 0
    
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v9' verificada.")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': SEARCH_URL
        })

        try:
            # --- PÁGINA 1 ---
            print("\n--- Navegando y procesando Página 1 ---")
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            response = session.post(SEARCH_URL, data=initial_payload, timeout=60)
            response.raise_for_status()
            
            files_to_download = parse_page_for_metadata(response.text, 1)
            print(f"Encontrados {len(files_to_download)} archivos. Comenzando descarga...")
            for file_info in files_to_download:
                download_file(session, file_info)
            
            # --- PÁGINAS 2 HASTA EL FINAL ---
            for page_num in range(2, TOTAL_PAGES + 1):
                print(f"\n--- Navegando y procesando Página {page_num} ---")
                pagination_payload = {'currPage': str(page_num - 1), 'Action': 'next', 'tamanioPagina': '30'}
                page_response = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
                page_response.raise_for_status()

                files_to_download = parse_page_for_metadata(page_response.text, page_num)
                if not files_to_download:
                    print(f"ADVERTENCIA: No se encontraron archivos en la página {page_num}. Finalizando.")
                    break
                
                print(f"Encontrados {len(files_to_download)} archivos. Comenzando descarga...")
                for file_info in files_to_download:
                    download_file(session, file_info)
        
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error crítico de red. El proceso se ha detenido. Error: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Proceso interrumpido por el usuario.")

    flush_log_buffer_to_file(force_flush=True)
    print("\n\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()