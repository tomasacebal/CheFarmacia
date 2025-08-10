import requests
import html
import re
import json
from datetime import datetime
from .base import BaseScraper
from unidecode import unidecode
from urllib.parse import quote

class ZarateScraper(BaseScraper):
    URL = "https://www.colfarmazarate.com/administracion-de-turnos/index.js"
    LOCALIDAD = "Zarate"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def js_to_json(self, js_text):
        # Elimina comentarios simples
        js_text = re.sub(r"//.*", "", js_text)
        # Reemplaza comillas simples por dobles si no hay comillas internas
        js_text = re.sub(r"'", '"', js_text)
        # Quita comas colgantes
        js_text = re.sub(r",\s*([\]}])", r"\1", js_text)
        return js_text

    def extract_json_objects(self, js_text, variable_name):
        # Encuentra el inicio de la variable
        start = js_text.find(f"const {variable_name} = ")
        if start == -1:
            raise ValueError(f"No se encontró la variable {variable_name}")

        # Detecta si es objeto o array
        first_char = js_text[start:].split("=", 1)[1].strip()[0]
        if first_char == "[":
            open_char, close_char = "[", "]"
        elif first_char == "{":
            open_char, close_char = "{", "}"
        else:
            raise ValueError(f"Formato inesperado para la variable {variable_name}")

        # Extrae el bloque balanceado
        count = 0
        in_string = False
        escaped = False
        end = None

        for i, c in enumerate(js_text[start:]):
            if c == '"' and not escaped:
                in_string = not in_string
            if not in_string:
                if c == open_char:
                    count += 1
                elif c == close_char:
                    count -= 1
                    if count == 0:
                        end = start + i + 1
                        break
            escaped = (c == "\\" and not escaped)

        if end is None:
            raise ValueError(f"No se pudo encontrar el cierre del bloque para {variable_name}")

        json_str = js_text[start: end].split("=", 1)[1].strip().rstrip(";")
        json_str = self.js_to_json(json_str)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Fallo al parsear JSON para {variable_name}: {e}")
            print(json_str[:500])
            raise


    def fetch(self):
        response = requests.get(self.URL)
        js_text = response.text

        turnos = self.extract_json_objects(js_text, "turnos")
        farmacias = self.extract_json_objects(js_text, "farmacias")

        resultados = []
        ahora = datetime.now()

        for turno in turnos:
            dia_str = unidecode(turno["dia"]).strip()
            dia_match = re.search(r"(\d{1,2})", dia_str)
            if not dia_match:
                continue
            fecha = dia_match.group(1)

            for localidad, nombres in turno["farmacias"].items():
                if isinstance(nombres, str):
                    nombres = [nombres]

                for nombre in nombres:
                    nombre_norm = unidecode(nombre.strip())
                    detalles_lista = farmacias.get(localidad, [])
                    detalles = next((f for f in detalles_lista if unidecode(f.get("farmacia", "")).strip() == nombre_norm), None)

                    if detalles:
                        direccion = detalles.get("dirección", "").strip()
                        telefono = detalles.get("teléfono", "").strip()
                        nombre_farmacia = detalles.get("farmacia", "").strip()

                        if nombre_farmacia and direccion:
                            direccion_completa = f"{direccion}, {self.LOCALIDAD}"
                            url_mapa = f"https://www.google.com/maps/search/{quote(direccion_completa)}"

                            resultados.append({
                                "fecha": fecha,
                                "nombre": nombre_farmacia,
                                "direccion": direccion_completa,
                                "telefono": telefono,
                                "localidad": self.LOCALIDAD,
                                "fuente": self.URL,
                                "nivel_confianza": self.CONFIANZA,
                                "mapa": url_mapa
                            })

        print(f"[ZÁRATE] Farmacias encontradas: {len(resultados)}")
        return resultados
