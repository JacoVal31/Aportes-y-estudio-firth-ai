import time
import os
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURACIÓN DEFINITIVA v16 ---
TOTAL_PAGES_TO_PROCESS = 204  # Total de páginas a procesar.
BASE_DIR = "SUNAT"
V16_DIR = os.path.join(BASE_DIR, "v16")
DOWNLOAD_ROOT_DIR = os.path.join(V16_DIR, "PDF descargados")
LOG_DIR = os.path.join(V16_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

def flush_log_buffer_to_file(force_flush=False):
    if len(log_buffer) >= 50 or (force_flush and log_buffer):
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(log_buffer) + "\n")
        log_buffer.clear()

def parse_and_download(session, page_source, page_num):
    """Analiza el HTML de la página actual y descarga los archivos correspondientes."""
    global processed_files_count
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a', onclick=lambda x: x and 'jsDescargarArchivo' in x)
    
    if not links:
        print(f"ADVERTENCIA: No se encontraron enlaces en la página {page_num}.")
        return 0

    print(f"Página {page_num}: Encontrados {len(links)} archivos. Descargando...")
    
    for link in links:
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", link.get('onclick', ''))
        if not match:
            continue
            
        cod_tipclas, num_resclas, fano_resclas = match.groups()
        num_resclas = str(num_resclas).zfill(6)
        year = str(fano_resclas)
        filename = f"{cod_tipclas}-{num_resclas}-{year}.pdf"
        
        year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
        os.makedirs(year_dir, exist_ok=True)
        filepath = os.path.join(year_dir, filename)

        processed_files_count += 1
        print(f"Progreso: Archivo #{processed_files_count} | {filename}", end='\r')

        if os.path.exists(filepath):
            continue

        payload = {'accion': 'descargarArchivo', 'cod_tipclas': cod_tipclas, 'num_resclas': num_resclas, 'fano_resclas': fano_resclas}
        
        try:
            response = session.post(SEARCH_URL, data=payload, timeout=60)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                log_buffer.append(f"[Página {page_num}] [Descarga Exitosa] {filename}")
            else:
                log_buffer.append(f"[Página {page_num}] [Error Descarga] {filename} | Estado: {response.status_code}")
        except requests.exceptions.RequestException as e:
            log_buffer.append(f"[Página {page_num}] [Error Red] {filename} | Error: {e}")
        
        flush_log_buffer_to_file()
    return len(links)

def main():
    """Orquesta el proceso completo usando Selenium para navegar y Requests para descargar."""
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v16' verificada.")

    # Iniciar el navegador Chrome con Selenium
    driver = webdriver.Chrome()
    driver.get(SEARCH_URL)
    print("🖥️ Navegador Chrome iniciado.")

    try:
        # Esperar a que el botón de búsqueda esté presente y hacer clic
        wait = WebDriverWait(driver, 20)
        search_button = wait.until(EC.element_to_be_clickable((By.NAME, "submit")))
        search_button.click()
        print("🔍 Búsqueda inicial realizada. Esperando resultados de la página 1...")

        # Crear una sesión de Requests para las descargas
        with requests.Session() as session:
            # Transferir cookies de Selenium a Requests para tener una sesión válida
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Procesar la primera página
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "beta"))) # Esperar a que la tabla cargue
            parse_and_download(session, driver.page_source, 1)

            # Iterar por el resto de las páginas
            for page_num in range(2, TOTAL_PAGES_TO_PROCESS + 1):
                print(f"\n--- Navegando a Página {page_num} ---")
                try:
                    # Encontrar el enlace de la página siguiente y hacerle clic
                    # Se busca un enlace que llame a paginacion() con el índice correcto.
                    next_page_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, 'paginacion(30,{page_num - 1})')]")))
                    next_page_link.click()
                    
                    # Esperar a que la nueva tabla cargue verificando un elemento que cambia
                    wait.until(EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), 'a {(page_num) * 30}')]")))
                    
                    # Analizar y descargar el contenido de la nueva página
                    parse_and_download(session, driver.page_source, page_num)

                except (TimeoutException, NoSuchElementException):
                    print(f"\nNo se pudo encontrar el enlace para la página {page_num}. Finalizando el proceso.")
                    break
    
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
    finally:
        # Cerrar el navegador al finalizar
        driver.quit()
        flush_log_buffer_to_file(force_flush=True)
        print("\n\n🖥️ Navegador cerrado.")
        print("🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()