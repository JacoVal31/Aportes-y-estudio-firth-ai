import requests
import os
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DEFINITIVA v15 ---

TOTAL_PAGES = 204
BASE_DIR = "SUNAT"
V15_DIR = os.path.join(BASE_DIR, "v15")
LOG_DIR = os.path.join(V15_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V15_DIR, "PDF descargados")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# Las dos URLs, ambas son necesarias en el flujo correcto.
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

# --- FUNCIONES ---

def flush_log_buffer_to_file(force_flush=False):
    """Escribe el contenido del búfer de logs en el archivo."""
    if len(log_buffer) >= 50 or (force_flush and log_buffer):
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
            f.write("\n".join(log_buffer) + "\n")
        log_buffer.clear()

def parse_page_for_metadata(html_content, page_num):
    """Analiza el HTML y extrae los metadatos de los archivos de esa página."""
    soup = BeautifulSoup(html_content, 'html.parser')
    files_on_page = []
    download_links = soup.find_all('a', onclick=lambda x: x and 'jsDescargarArchivo' in x)
    
    if not download_links:
        error_path = os.path.join(LOG_DIR, f"error_pagina_{page_num}.html")
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\nADVERTENCIA: No se encontraron enlaces en la página {page_num}. El HTML se guardó en '{error_path}' para revisión.")

    for link in download_links:
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", link.get('onclick', ''))
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            params = {'cod_tipclas': cod_tipclas, 'num_resclas': num_resclas, 'fano_resclas': fano_resclas}
            files_on_page.append({'params': params, 'page_num': page_num})
    return files_on_page

def download_file(session, file_info):
    """Descarga un único archivo. La sesión ya debe estar en el estado correcto."""
    global processed_files_count
    
    params = file_info['params']
    page_num = file_info['page_num']
    
    params['num_resclas'] = str(params['num_resclas']).zfill(6)
    
    year = str(params['fano_resclas'])
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    processed_files_count += 1
    print(f"Progreso: Archivo #{processed_files_count} | Página {page_num} | Procesando: {filename}", end='\r')

    if os.path.exists(filepath):
        return

    payload = {'accion': 'descargarArchivo', **params}
    
    try:
        # La descarga siempre se pide a la URL de acción/búsqueda
        response = session.post(SEARCH_URL, data=payload, timeout=60)
        
        if response.status_code == 200 and response.headers.get('Content-Type', '').strip().lower() == 'application/pdf':
            with open(filepath, 'wb') as f:
                f.write(response.content)
            log_buffer.append(f"[Página {page_num}] [Descarga Exitosa] Archivo: {filename}")
        else:
            log_buffer.append(f"[Página {page_num}] [Error Descarga] Archivo: {filename} | Estado: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log_buffer.append(f"[Página {page_num}] [Error Red] Archivo: {filename} | Error: {e}")
    
    flush_log_buffer_to_file()

def main():
    """Orquesta el proceso completo con la lógica de navegación y payload correctos."""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v15' verificada.")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Origin': 'http://www.aduanet.gob.pe'
        })

        try:
            # --- PÁGINA 1 ---
            print("\n--- Estableciendo sesión y procesando Página 1 ---")
            session.headers.update({'Referer': SEARCH_URL})
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            response = session.post(SEARCH_URL, data=initial_payload, timeout=60)
            response.raise_for_status()
            
            files_on_page = parse_page_for_metadata(response.text, 1)
            print(f"Encontrados {len(files_on_page)} archivos. Descargando...")
            for file_info in files_on_page:
                download_file(session, file_info)
            
            # --- PÁGINAS 2 HASTA EL FINAL ---
            for page_num in range(2, TOTAL_PAGES + 1):
                print(f"\n--- Navegando a Página {page_num} ---")
                
                # La lógica de navegación que descubrimos juntos:
                # 1. El Referer es la URL de paginación.
                # 2. El payload es con 'pagina' y 'tamanioPagina'.
                # 3. La petición se envía a la URL de paginación.
                session.headers.update({'Referer': PAGINATION_URL})
                pagination_payload = {
                    'pagina': str(page_num - 1),
                    'tamanioPagina': '30'
                }
                page_response = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
                page_response.raise_for_status()

                files_on_page = parse_page_for_metadata(page_response.text, page_num)
                if not files_on_page:
                    print(f"ADVERTENCIA: No se encontraron archivos en la página {page_num}. Finalizando.")
                    break
                
                print(f"Encontrados {len(files_on_page)} archivos. Descargando...")
                for file_info in files_on_page:
                    download_file(session, file_info)
        
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error crítico de red. El proceso se ha detenido. Error: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Proceso interrumpido por el usuario.")

    flush_log_buffer_to_file(force_flush=True)
    print("\n\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()