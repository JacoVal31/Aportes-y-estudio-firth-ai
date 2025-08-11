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

# --- CONFIGURACIÓN DEFINITIVA v18 ---
TOTAL_PAGES_TO_PROCESS = 204
BASE_DIR = "SUNAT"
V18_DIR = os.path.join(BASE_DIR, "v18")
DOWNLOAD_ROOT_DIR = os.path.join(V18_DIR, "PDF descargados")
LOG_DIR = os.path.join(V18_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

# Las dos URLs, cada una con su propósito.
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
RESULTS_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

def flush_log_buffer_to_file(force_flush=False):
    """Escribe el contenido del búfer de logs en el archivo."""
    if len(log_buffer) >= 50 or (force_flush and log_buffer):
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(log_buffer) + "\n")
        log_buffer.clear()

def parse_and_download(session, page_source, page_num):
    """Analiza el HTML de la página actual y descarga los archivos."""
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
    """Función robusta para navegar a la página siguiente."""
    try:
        # El enlace de paginación es simplemente el número de la página.
        next_page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_num))))
        
        # Usar JavaScript para hacer clic, es más fiable.
        driver.execute_script("arguments[0].click();", next_page_link)
        
        # Confirmar que la página ha cargado esperando un elemento que debe cambiar.
        start_item_indicator = f"{(page_num - 1) * 30 + 1}"
        wait.until(EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{start_item_indicator}') and contains(text(), 'a ')]")))
        
        return True
    except (TimeoutException, NoSuchElementException):
        return False

def main():
    """Orquesta el proceso completo con el flujo de navegación de 2 pasos."""
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v18' verificada.")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # --- PASO 1: INICIAR BÚSQUEDA ---
        driver.get(SEARCH_URL)
        print("🖥️  Navegador Chrome iniciado.")
        
        search_button = wait.until(EC.element_to_be_clickable((By.NAME, "submit")))
        search_button.click()
        print("🔍 Búsqueda inicial enviada...")

        # --- PASO 2: NAVEGAR A LA PÁGINA DE RESULTADOS ---
        # ¡¡ESTA ES LA LÍNEA CLAVE QUE FALTABA!!
        print(f"🌐 Navegando a la página de resultados para ver la paginación...")
        driver.get(RESULTS_URL)

        # Ahora que estamos en la página correcta, podemos empezar a trabajar.
        print("✅ En la página de resultados. Procesando Página 1...")
        
        with requests.Session() as session:
            # Transferir las cookies del navegador a la sesión de requests
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Procesar página 1
            parse_and_download(session, driver.page_source, 1)

            # Procesar páginas restantes
            for page_num in range(2, TOTAL_PAGES_TO_PROCESS + 1):
                print(f"\n--- Navegando a Página {page_num} ---")
                
                if navigate_to_page(driver, wait, page_num):
                    # Es buena práctica actualizar las cookies por si cambian.
                    for cookie in driver.get_cookies():
                        session.cookies.set(cookie['name'], cookie['value'])
                    
                    parse_and_download(session, driver.page_source, page_num)
                else:
                    print(f"\nNo se pudo navegar a la página {page_num}. Finalizando el proceso.")
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