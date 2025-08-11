# --- START OF FILE scrapers/san_fernando.py ---

import requests
from bs4 import BeautifulSoup
import re
from .base import BaseScraper
from utils import generar_link_mapa # Importamos la utilidad para generar links de mapa

class SanFernandoScraper(BaseScraper):
    URL = "https://colfarmasanfdo.org.ar/turnero.html"
    LOCALIDAD = "San Fernando"
    CONFIANZA = 3

    def fetch(self) -> list[dict]:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()  # Lanza un error si la petición falla
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener la página de San Fernando: {e}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        farmacias = []
        
        # Este diccionario mapeará el índice de una columna (0, 1, 2...) al día del mes.
        # Se reinicia cada vez que encontramos una fila de fecha.
        column_to_day_map = {}

        # Seleccionamos todas las filas de la tabla
        rows = soup.select("table tr")

        for row in rows:
            # Si la fila tiene la clase "fecha", procesamos las fechas
            if "fecha" in row.get("class", []):
                column_to_day_map = {}  # Reseteamos el mapeo para la nueva semana/grupo de días
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    # Buscamos el número del día en el texto (ej: "Viernes 01:")
                    match = re.search(r'(\d+)', cell.text)
                    if match:
                        # Extraemos el número, lo convertimos a entero para quitar ceros a la izquierda
                        # y lo guardamos en nuestro mapa.
                        day_number = int(match.group(1))
                        column_to_day_map[i] = day_number
            
            # Si no es una fila de fecha, es una fila de farmacias
            else:
                # Si no hemos procesado ninguna fecha aún, saltamos esta fila
                if not column_to_day_map:
                    continue

                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    # Obtenemos el día correspondiente a esta columna
                    day = column_to_day_map.get(i)
                    raw_text = cell.text.strip()

                    # Si hay un día asociado y la celda tiene texto, la procesamos
                    if day and raw_text:
                        parts = [p.strip() for p in raw_text.split(':', 1)]
                        
                        if len(parts) == 2:
                            nombre = parts[0]
                            direccion_raw = parts[1]
                        else:
                            # Si no hay ':', asumimos que todo es el nombre y la dirección no está clara
                            nombre = raw_text
                            direccion_raw = ""
                            print(f"[ADVERTENCIA] Formato inesperado en San Fernando: '{raw_text}'")

                        # Limpiamos y estandarizamos la dirección para mejorar el geocoding
                        direccion_limpia = direccion_raw.replace("San Fdo.", "San Fernando").replace("Virr.", "Virreyes").replace("Vict.", "Victoria").replace("S. F.", "San Fernando")
                        # Agregamos la localidad y provincia para mayor precisión en el mapa
                        if "San Fernando" not in direccion_limpia and "Virreyes" not in direccion_limpia and "Victoria" not in direccion_limpia:
                            direccion_completa = f"{direccion_limpia}, {self.LOCALIDAD}, Provincia de Buenos Aires"
                        else:
                            direccion_completa = f"{direccion_limpia}, Provincia de Buenos Aires"


                        farmacias.append({
                            "fecha": str(day),  # Guardamos el día como string sin ceros
                            "nombre": nombre,
                            "direccion": direccion_completa.strip(),
                            "telefono": "",  # No hay teléfono en la fuente
                            "localidad": self.LOCALIDAD,
                            "fuente": self.URL,
                            "nivel_confianza": self.CONFIANZA,
                            "mapa": generar_link_mapa(direccion_completa)
                        })

        print(f"Scraping de San Fernando finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias