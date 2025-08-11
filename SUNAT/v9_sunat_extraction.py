import pandas as pd
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN v8 ---

BASE_DIR = "SUNAT"
V8_DIR = os.path.join(BASE_DIR, "v8")
LOG_DIR = os.path.join(V8_DIR, "logs")
DOWNLOAD_ROOT_DIR = os.path.join(V8_DIR, "PDF descargados")

EXCEL_FILE_PATH = os.path.join(V8_DIR, "nombres_identificados.xlsx")
LOG_FILE_PATH = os.path.join(LOG_DIR, "logs.txt")

SEARCH_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"
PAGINATION_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/CAConsultaSubpartidasInter.jsp"

# --- RECURSOS GLOBALES ---
log_buffer = []
processed_files_count = 0

# --- FUNCIONES ---

def flush_log_buffer_to_file(force_flush=False):
    if len(log_buffer) >= 100 or (force_flush and log_buffer):
        print(f"\n📝 Escribiendo un lote de {len(log_buffer)} registros en {LOG_FILE_PATH}...\n")
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n--- INICIO DEL LOTE DE LOGS: {timestamp} ---\n")
            f.write("\n".join(log_buffer))
            f.write(f"\n--- FIN DEL LOTE ---\n")
        log_buffer.clear()

def download_file(session, file_info, total_files):
    global processed_files_count
    
    numero_formateado = str(file_info['Numero']).zfill(6)
    
    params = {
        'cod_tipclas': file_info['Tipo'],
        'num_resclas': numero_formateado,
        'fano_resclas': str(file_info['Año'])
    }
    
    year = str(file_info['Año'])
    page_num = file_info['Pagina_Encontrada']
    filename = f"{params['cod_tipclas']}-{params['num_resclas']}-{year}.pdf"
    
    year_dir = os.path.join(DOWNLOAD_ROOT_DIR, year)
    os.makedirs(year_dir, exist_ok=True)
    filepath = os.path.join(year_dir, filename)

    processed_files_count += 1
    progress = (processed_files_count / total_files) * 100
    print(f"Progreso Total: [{processed_files_count}/{total_files}] {progress:.2f}% | Procesando: {filename}", end='\r')

    if os.path.exists(filepath):
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

def main():
    global processed_files_count
    processed_files_count = 0
    
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_ROOT_DIR, exist_ok=True)
    print("🚀 Estructura de carpetas 'v8' verificada.")

    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"❌ ERROR: No se encontró el archivo de entrada en '{EXCEL_FILE_PATH}'.")
        print("Por favor, asegúrate de que 'nombres_identificados.xlsx' esté en la carpeta 'SUNAT/v8/'.")
        return
        
    print(f"📊 Leyendo la lista de archivos desde '{EXCEL_FILE_PATH}'...")
    df = pd.read_excel(EXCEL_FILE_PATH)
    total_files = len(df)
    
    if total_files == 0:
        print("El archivo Excel no contiene archivos para descargar.")
        return
        
    print(f"Se encontraron {total_files} archivos para procesar.")

    # Agrupar los archivos por la página en la que fueron encontrados.
    grouped_by_page = df.sort_values(by='Pagina_Encontrada').groupby('Pagina_Encontrada')

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': SEARCH_URL
        })

        # Iterar sobre cada grupo de página.
        for page_num, group_df in grouped_by_page:
            print(f"\n\n---  navegando a la página {page_num} para establecer el estado de la sesión ---")
            
            try:
                # Actualizar el estado de la sesión para la página actual.
                if page_num == 1:
                    # Para la página 1, hacemos la búsqueda inicial.
                    initial_payload = {'accion': 'cargarSubpartidas', 'cmbCriterio': '0', 'cmbOrderBy': '4'}
                    session.post(SEARCH_URL, data=initial_payload, timeout=60)
                    print(f"✅ Sesión establecida en Página 1.")
                else:
                    # Para las demás páginas, hacemos la paginación.
                    pagination_payload = {'currPage': str(page_num - 1), 'Action': 'next', 'tamanioPagina': '30'}
                    session.post(PAGINATION_URL, data=pagination_payload, timeout=60)
                    print(f"✅ Sesión establecida en Página {page_num}.")
                
                # Una vez en la página correcta, descargar todos los archivos de ese grupo.
                print(f"--- comenzando la descarga de {len(group_df)} archivos de la página {page_num} ---")
                files_in_group = group_df.to_dict('records')
                for file_info in files_in_group:
                    download_file(session, file_info, total_files)

            except requests.exceptions.RequestException as e:
                print(f"\n❌ Error al navegar a la página {page_num}. Saltando este grupo. Error: {e}")
                processed_files_count += len(group_df) # Ajustar contador para no afectar el % de progreso.
                continue

    flush_log_buffer_to_file(force_flush=True)
    print("\n\n🎉 ¡Proceso de descarga masiva finalizado! 🎉")

if __name__ == "__main__":
    main()