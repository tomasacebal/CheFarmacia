# --- START OF FILE scrapers/sources.py ---

import os
import json
from datetime import datetime
from .base import BaseScraper

class SourcesScraper(BaseScraper):
    """
    Un scraper especial que no accede a una web, sino que lee datos de
    archivos JSON pre-procesados en el directorio /sources.
    
    Busca archivos .json en la carpeta /sources, y para cada uno, extrae
    la información de las farmacias de turno correspondientes al mes actual.
    """
    SOURCES_DIR = "sources"
    
    # Mapeo de meses para buscar la clave correcta en los JSON
    MESES_ES = {
        'january': 'enero', 'february': 'febrero', 'march': 'marzo',
        'april': 'abril', 'may': 'mayo', 'june': 'junio',
        'july': 'julio', 'august': 'agosto', 'september': 'septiembre',
        'october': 'octubre', 'november': 'noviembre', 'december': 'diciembre'
    }

    def fetch(self) -> list[dict]:
        farmacias_del_mes = []
        
        # Determinar el mes actual en español para buscar en los JSON
        current_month_en = datetime.now().strftime("%B").lower()
        current_month_es = self.MESES_ES.get(current_month_en)

        if not current_month_es:
            print(f"[ERROR] No se pudo encontrar la traducción para el mes: {current_month_en}")
            return []

        if not os.path.isdir(self.SOURCES_DIR):
            print(f"[ADVERTENCIA] El directorio '{self.SOURCES_DIR}' no existe. No se cargarán farmacias desde archivos locales.")
            return []

        print(f"[INFO] Buscando farmacias de '{current_month_es}' en el directorio '{self.SOURCES_DIR}'...")

        # Recorrer todos los archivos en el directorio /sources
        for filename in os.listdir(self.SOURCES_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(self.SOURCES_DIR, filename)
                print(f"  -> Procesando archivo: {filename}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"    [ERROR] No se pudo leer o procesar el archivo JSON {filename}: {e}")
                    continue

                # Buscar datos para el mes actual
                if current_month_es in data:
                    # Iterar sobre cada localidad dentro del mes
                    for localidad, info in data[current_month_es].items():
                        fuente = info.get("fuente", "Fuente no especificada")
                        confianza = info.get("confianza", 1)
                        dias = info.get("dias", {})

                        # Iterar sobre cada día y sus farmacias
                        for dia, farmacias_en_dia in dias.items():
                            for farmacia_data in farmacias_en_dia:
                                # Construir el diccionario en el formato esperado por el sistema principal
                                farmacia_formateada = {
                                    "nombre": farmacia_data.get("nombre"),
                                    "direccion": farmacia_data.get("direccion"),
                                    "telefono": farmacia_data.get("telefono", ""),
                                    "mapa": farmacia_data.get("mapa"),
                                    "fecha": str(dia),  # El día del mes
                                    "localidad": localidad,
                                    "fuente": fuente,
                                    "nivel_confianza": confianza
                                }
                                farmacias_del_mes.append(farmacia_formateada)

        print(f"Scraping de fuentes locales finalizado. Farmacias encontradas: {len(farmacias_del_mes)}")
        return farmacias_del_mes