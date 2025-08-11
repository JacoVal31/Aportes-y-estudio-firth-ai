import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURACIÓN DE LA PRUEBA FINAL ---

SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"
TEST_DIR = "test_paginacion_final"

# --- FUNCIONES DE LA PRUEBA ---

def get_resolution_codes_from_html(html_content):
    """Extrae los códigos de resolución de un HTML para compararlos."""
    soup = BeautifulSoup(html_content, 'html.parser')
    codes = set()
    links = soup.find_all('a', onclick=lambda x: x and 'jsDescargarArchivo' in x)
    for link in links:
        code = link.get_text(strip=True)
        if code:
            codes.add(code)
    return codes

def run_final_test():
    """Ejecuta la prueba definitiva para obtener la página 2."""
    
    os.makedirs(TEST_DIR, exist_ok=True)
    print(f"🔬 Iniciando prueba de diagnóstico final. Resultados en '{TEST_DIR}'.")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        try:
            # --- PASO 1: OBTENER PÁGINA 1 ---
            print("\n--- PASO 1: Estableciendo sesión con Página 1 ---")
            session.headers.update({'Referer': SEARCH_URL})
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            
            response_p1 = session.post(SEARCH_URL, data=initial_payload, timeout=60)
            response_p1.raise_for_status()
            
            path_p1 = os.path.join(TEST_DIR, "pagina_1_obtenida.html")
            with open(path_p1, "w", encoding="utf-8") as f:
                f.write(response_p1.text)
            print(f"✅ Página 1 guardada.")

            # --- PASO 2: INTENTAR OBTENER PÁGINA 2 CON EL PAYLOAD CORREGIDO ---
            print("\n--- PASO 2: Solicitando Página 2 con la lógica corregida ---")
            session.headers.update({'Referer': PAGINATION_URL})
            
            # LA CORRECCIÓN CLAVE Y DEFINITIVA: Usar los parámetros del formulario 'formPaginacion'.
            pagination_payload = {
                'pagina': '1', # Para la página 2, el índice es 1.
                'tamanioPagina': '30'
            }
            
            response_p2 = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
            response_p2.raise_for_status()

            path_p2 = os.path.join(TEST_DIR, "pagina_2_obtenida.html")
            with open(path_p2, "w", encoding="utf-8") as f:
                f.write(response_p2.text)
            print(f"✅ Respuesta para Página 2 obtenida y guardada.")

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error crítico durante la prueba: {e}")
            return

    # --- PASO 3: ANÁLISIS Y VEREDICTO FINAL ---
    print("\n--- PASO 3: Analizando los resultados ---")
    
    codes_p1 = get_resolution_codes_from_html(response_p1.text)
    codes_p2 = get_resolution_codes_from_html(response_p2.text)

    print(f"Muestra de códigos de Página 1: {list(codes_p1)[:3]}...")
    print(f"Muestra de códigos de Página 2: {list(codes_p2)[:3]}...")

    print("\n--- VEREDICTO FINAL ---")
    if not codes_p1 or not codes_p2:
        print("🟡 No se pudieron extraer códigos de uno o ambos archivos. Revisa los HTML manualmente.")
    elif codes_p1 == codes_p2:
        print("❌ FALLO PERSISTE: El contenido de la Página 2 sigue siendo IDÉNTICO al de la Página 1.")
        print("Esto indicaría un problema de sesión más complejo (posiblemente cookies de JS).")
    else:
        print("✅ ¡ÉXITO ROTUNDO! El contenido de la Página 2 es DIFERENTE.")
        print("Hemos encontrado la lógica correcta de paginación. Ahora podemos construir la solución final.")

if __name__ == "__main__":
    run_final_test()