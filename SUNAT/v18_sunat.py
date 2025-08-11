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

# --- CONFIGURACIÓN DEFINITIVA v19 ---
TOTAL_PAGES_TO_PROCESS = 204
BASE_DIR = "SUNAT"
V19_DIR = os.path.join(BASE_DIR, "v19")
DOWNLOAD_ROOT_DIR = os.path.join(V19_DIR, "PDF descargados")
LOG_DIR = os.path.join(V19_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# Las dos URLs clave para el flujo de 3 pasos
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
RESULTS_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

def flush_log_buffer_to_file(force_flush=False):
    if len(log_buffer) >= 50 or (force_flush and log_buffer):
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(log_buffer) + "\n")
        log_buffer.clear()

def parse_and_download(session, page_source, page_num):
    global processed_files_count
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a', onclick=lambda x: x and 'jsDescargarArchivo' in x)
    
    if not links:
        print(f"ADVERTENCIA: No se encontraron enlaces en la página {page_num}.")
        return 0

    print(f"Página {page_num}: Encontrados {len(links)} archivos. Descargando...")
    
    for link in links:
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", link.get('onclick', ''))
        if not match: continue
            
        cod_tipclas, num_resclas, fano_resclas = match.groups()
        num_resclas = str(num_resclas).zfill(6)
        year = str(fano_resclas)
        filename = f"{cod_tipclas}-{num_resclas}-{year}.pdf"
        
        year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
        os.makedirs(year_dir, exist_ok=True)
        filepath = os.path.join(year_dir, filename)

        processed_files_count += 1
        print(f"Progreso: Archivo #{processed_files_count} | {filename}", end='\r')

        if os.path.exists(filepath): continue

        payload = {'accion': 'descargarArchivo', 'cod_tipclas': cod_tipclas, 'num_resclas': num_resclas, 'fano_resclas': fano_resclas}
        
        try:
            response = session.post(SEARCH_URL, data=payload, timeout=60)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                log_buffer.append(f"[Página {page_num}] [Descarga Exitosa] {filename}")
            else:
                log_buffer.append(f"[Página {page_num}] [Error Descarga] {filename} | Estado: {response.status_code}")
        except requests.exceptions.RequestException:
            log_buffer.append(f"[Página {page_num}] [Error Red] {filename}")
        
        flush_log_buffer_to_file()
    return len(links)

def navigate_to_page(driver, wait, page_num):
    try:
        next_page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_num))))
        driver.execute_script("arguments[0].click();", next_page_link)
        start_item_indicator = f"{(page_num - 1) * 30 + 1}"
        wait.until(EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{start_item_indicator}') and contains(text(), 'a ')]")))
        return True
    except (TimeoutException, NoSuchElementException):
        return False

def main():
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v19' verificada.")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # --- PASO 1: INICIAR SESIÓN ---
        driver.get(SEARCH_URL)
        print("🖥️  Navegador Chrome iniciado.")
        wait.until(EC.element_to_be_clickable((By.NAME, "submit"))).click()
        print("PASO 1: Sesión iniciada.")

        # --- PASO 2: IR A LA PÁGINA DE RESULTADOS (INACTIVA) ---
        driver.get(RESULTS_URL)
        print("PASO 2: Navegando a la página de resultados.")

        # --- PASO 3: ACTIVAR LA TABLA Y PAGINACIÓN ---
        # ¡¡EL TRUCO QUE DESCUBRISTE!!
        print("PASO 3: Realizando búsqueda en la página de resultados para activar la tabla...")
        # Selector robusto para el botón "Buscar" del formulario de búsqueda en esta página
        second_search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//form[@name='frmBusqueda']//input[@value=' Buscar ']")))
        second_search_button.click()
        
        # Esperar a que la paginación sea visible como confirmación de que la tabla está activa.
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "2")))
        print("✅ ¡Tabla de resultados y paginación activadas!")
        
        with requests.Session() as session:
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Procesar página 1 (ya está cargada)
            parse_and_download(session, driver.page_source, 1)

            # Procesar páginas restantes
            for page_num in range(2, TOTAL_PAGES_TO_PROCESS + 1):
                print(f"\n--- Navegando a Página {page_num} ---")
                
                if navigate_to_page(driver, wait, page_num):
                    for cookie in driver.get_cookies():
                        session.cookies.set(cookie['name'], cookie['value'])
                    parse_and_download(session, driver.page_source, page_num)
                else:
                    print(f"\nNo se pudo navegar a la página {page_num}. Finalizando.")
                    break
    
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
    finally:
        driver.quit()
        flush_log_buffer_to_file(force_flush=True)
        print("\n\n🖥️  Navegador cerrado.")
        print("🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()