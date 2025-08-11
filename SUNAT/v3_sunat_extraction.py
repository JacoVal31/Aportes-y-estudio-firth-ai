import requests
import os
import re
import time
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---

# Define cuántas páginas quieres procesar.
TOTAL_PAGES = 204 

# Nombre de la carpeta donde se guardarán los PDFs.
DOWNLOAD_DIR = "resoluciones_sunat_full"

# URLs base del servidor de Aduanas.
BASE_URL = "http://www.aduanet.gob.pe"
SEARCH_URL = f"{BASE_URL}/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = f"{BASE_URL}/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- FIN DE LA CONFIGURACIÓN ---

def download_file(session, params):
    """Descarga un único archivo PDF usando la sesión activa."""
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{params['fano_resclas']}.pdf"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(filepath):
        print(f"☑️  Ya existe: {filename}")
        return

    payload = {
        'accion': 'descargarArchivo',
        **params
    }
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=45)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ Descarga completa: {filename}")
        else:
            print(f"❌ Error al descargar {filename}. Estado: {response.status_code}, Tipo: {response.headers.get('Content-Type')}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ocurrió un error de red al intentar descargar {filename}: {e}")

def process_page(session, html_content, page_num):
    """Analiza el HTML de una página, extrae los datos y manda a descargar los archivos."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    download_links = soup.find_all(
        'a',
        onclick=lambda x: x and x.strip().startswith("jsDescargarArchivo")
    )
    
    if not download_links:
        print(f"ADVERTENCIA: No se encontraron enlaces de descarga en la página {page_num}.")
        # Opcional: guardar el HTML para depuración
        # with open(f"debug_page_{page_num}.html", "w", encoding="utf-8") as f:
        #     f.write(html_content)
        return False

    print(f"Encontradas {len(download_links)} resoluciones en la página {page_num}.")

    for link in download_links:
        onclick_attr = link.get('onclick', '')
        match = re.search(r"jsDescargarArchivo\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", onclick_attr)
        
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            file_params = {
                'cod_tipclas': cod_tipclas,
                'num_resclas': num_resclas,
                'fano_resclas': fano_resclas
            }
            download_file(session, file_params)
            time.sleep(0.3) # Pausa mínima para no saturar el servidor.
    return True

def main():
    """Función principal que controla la sesión, paginación y el proceso de descarga."""
    print("Iniciando el proceso de descarga masiva...")
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Directorio '{DOWNLOAD_DIR}' creado.")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': SEARCH_URL
        })

        print("Realizando búsqueda inicial para obtener la primera página...")
        initial_payload = {
            'accion': 'cargarSubpartidas',
            'cmbCriterio': '0',
            'txtValor': '',
            'cmbOrderBy': '4' # Ordenar por fecha de publicación (4) puede ser más estable
        }
        try:
            response = session.post(SEARCH_URL, data=initial_payload, timeout=45)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fatal al realizar la búsqueda inicial: {e}")
            return
            
        print("\n--- Procesando Página 1 ---")
        process_page(session, response.text, 1)

        # Iterar por el resto de las páginas
        for page_num in range(2, TOTAL_PAGES + 1):
            print(f"\n--- Solicitando Página {page_num} de {TOTAL_PAGES} ---")
            
            # *** CORRECCIÓN CLAVE ***
            # Este es el payload correcto para la paginación, imitando el formulario 'NavigFormNext'.
            pagination_payload = {
                'currPage': str(page_num - 1), # La página de la que venimos (índice base 1)
                'Action': 'next',
                'tamanioPagina': '30' # A menudo es bueno reenviar este dato
            }
            
            try:
                # La solicitud de paginación debe ir al mismo JSP que la procesa.
                response = session.post(PAGINATION_URL, data=pagination_payload, timeout=45)
                response.raise_for_status()
                
                if not process_page(session, response.text, page_num):
                    print("Deteniendo el script debido a una página sin enlaces. Puede que hayamos llegado al final.")
                    break # Detiene el bucle si una página falla

                time.sleep(1) # Pausa de 1 segundo entre cada página.
            except requests.exceptions.RequestException as e:
                print(f"No se pudo cargar la página {page_num}. Error: {e}")
                continue

    print("\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()