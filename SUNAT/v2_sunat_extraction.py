import requests
import os
import re
import time
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---

# ¡Importante! Define cuántas páginas quieres procesar.
# La web indica un total de 204 páginas.
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

    # Si el archivo ya existe, no lo volvemos a descargar.
    if os.path.exists(filepath):
        print(f"☑️  Ya existe: {filename}")
        return

    payload = {
        'accion': 'descargarArchivo',
        **params
    }
    
    try:
        response = session.post(SEARCH_URL, data=payload, timeout=30)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ Descarga completa: {filename}")
        else:
            print(f"❌ Error al descargar {filename}. Estado: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ocurrió un error de red al intentar descargar {filename}: {e}")


def process_page(session, html_content):
    """Analiza el HTML de una página, extrae los datos y manda a descargar los archivos."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    download_links = soup.find_all(
        'a',
        onclick=lambda x: x and x.startswith("jsDescargarArchivo")
    )
    
    if not download_links:
        print("No se encontraron enlaces de descarga en la página actual.")
        return

    print(f"Se encontraron {len(download_links)} resoluciones en esta página.")

    for link in download_links:
        onclick_attr = link.get('onclick', '')
        match = re.search(r"jsDescargarArchivo\('([^']*)','([^']*)','([^']*)'\)", onclick_attr)
        
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            file_params = {
                'cod_tipclas': cod_tipclas,
                'num_resclas': num_resclas,
                'fano_resclas': fano_resclas
            }
            download_file(session, file_params)
            time.sleep(0.5) # Pequeña pausa para no saturar el servidor.

def main():
    """Función principal que controla la sesión, paginación y el proceso de descarga."""
    print("Iniciando el proceso de descarga masiva...")
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Directorio '{DOWNLOAD_DIR}' creado.")

    # Usamos una sesión para mantener las cookies de la búsqueda inicial.
    with requests.Session() as session:
        # Añadimos un User-Agent para simular un navegador real.
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 1. Realizar la búsqueda inicial para obtener la página 1.
        print("Realizando búsqueda inicial para obtener la primera página...")
        initial_payload = {
            'accion': 'cargarSubpartidas',
            'cmbCriterio': '0', # '0' es para 'Todos'
            'txtValor': '',
            'cmbOrderBy': '0'
        }
        try:
            response = session.post(SEARCH_URL, data=initial_payload)
            response.raise_for_status() # Lanza un error si la solicitud falla
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la búsqueda inicial: {e}")
            return
            
        print("\n--- Procesando Página 1 ---")
        process_page(session, response.text)

        # 2. Iterar por el resto de las páginas.
        for page_num in range(2, TOTAL_PAGES + 1):
            print(f"\n--- Solicitando Página {page_num} de {TOTAL_PAGES} ---")
            
            # El parámetro 'pagina' es el índice, que es el número de página - 1.
            pagination_payload = {
                'tamanioPagina': '30',
                'pagina': str(page_num - 1)
            }
            
            try:
                response = session.post(PAGINATION_URL, data=pagination_payload, timeout=30)
                response.raise_for_status()
                process_page(session, response.text)
                
                # Pausa entre solicitudes de página para ser respetuoso con el servidor.
                time.sleep(2) 
            except requests.exceptions.RequestException as e:
                print(f"No se pudo cargar la página {page_num}. Error: {e}")
                # Se puede decidir continuar con la siguiente o detener el script.
                continue

    print("\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")


if __name__ == "__main__":
    main()