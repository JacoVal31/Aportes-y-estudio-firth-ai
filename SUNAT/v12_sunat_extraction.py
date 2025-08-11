import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURACIÓN DE LA PRUEBA ---

# El único objetivo es probar la transición de la página 1 a la 2.
# Las URLs que sabemos que son relevantes.
SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# Directorio para guardar los resultados de la prueba.
TEST_DIR = "test_paginacion"

# --- FUNCIONES DE LA PRUEBA ---

def get_resolution_codes_from_html(html_content):
    """Función simple para extraer los códigos de resolución de un HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    codes = set() # Usamos un set para que el orden no importe en la comparación.
    links = soup.find_all('a', onclick=lambda x: x and 'jsDescargarArchivo' in x)
    for link in links:
        code = link.get_text(strip=True)
        if code:
            codes.add(code)
    return codes

def run_test():
    """Ejecuta la prueba de obtener la página 1 y luego la página 2."""
    
    os.makedirs(TEST_DIR, exist_ok=True)
    print(f"🔬 Iniciando prueba de diagnóstico. Los resultados se guardarán en la carpeta '{TEST_DIR}'.")

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        try:
            # --- PASO 1: OBTENER PÁGINA 1 ---
            print("\n--- PASO 1: Solicitando Página 1 ---")
            session.headers.update({'Referer': SEARCH_URL})
            initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
            
            response_p1 = session.post(SEARCH_URL, data=initial_payload, timeout=60)
            response_p1.raise_for_status()
            
            path_p1 = os.path.join(TEST_DIR, "pagina_1_real.html")
            with open(path_p1, "w", encoding="utf-8") as f:
                f.write(response_p1.text)
            print(f"✅ Página 1 obtenida y guardada en '{path_p1}'.")

            # --- PASO 2: INTENTAR OBTENER PÁGINA 2 ---
            print("\n--- PASO 2: Solicitando Página 2 ---")
            # Usamos la URL y el Referer que funcionaban en el script de mapeo.
            session.headers.update({'Referer': PAGINATION_URL})
            pagination_payload = {'currPage': '1', 'Action': 'next', 'tamanioPagina': '30'}
            
            response_p2 = session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
            response_p2.raise_for_status()

            path_p2 = os.path.join(TEST_DIR, "pagina_2_intento.html")
            with open(path_p2, "w", encoding="utf-8") as f:
                f.write(response_p2.text)
            print(f"✅ Página 2 obtenida y guardada en '{path_p2}'.")

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error crítico durante la prueba: {e}")
            return

    # --- PASO 3: ANÁLISIS Y VEREDICTO ---
    print("\n--- PASO 3: Analizando los resultados ---")
    
    codes_p1 = get_resolution_codes_from_html(response_p1.text)
    codes_p2 = get_resolution_codes_from_html(response_p2.text)

    print(f"Códigos muestra de Página 1: {list(codes_p1)[:3]}...")
    print(f"Códigos muestra de Página 2: {list(codes_p2)[:3]}...")

    print("\n--- VEREDICTO ---")
    if not codes_p1 or not codes_p2:
        print("🟡 No se pudieron extraer códigos de uno o ambos archivos. Revisa los HTML manualmente.")
    elif codes_p1 == codes_p2:
        print("❌ FALLO: El contenido de la Página 2 es IDÉNTICO al de la Página 1.")
        print("Esto confirma que la petición de paginación no está funcionando como se espera.")
    else:
        print("✅ ÉXITO: ¡El contenido de la Página 2 es DIFERENTE del de la Página 1!")
        print("Esto significa que la lógica de navegación es correcta y el problema debe estar en otro lado.")

if __name__ == "__main__":
    run_test()