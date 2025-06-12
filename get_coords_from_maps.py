import json
import os
import time
import urllib.parse
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path  # pip install chromedriver-py

CACHE_FILE = "coordenadas_cache.json"
FARMACIAS_24H_JSON = "data/farmacias_24_horas.json"

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def crear_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-3d-apis")

    service = Service(executable_path=binary_path)
    return webdriver.Chrome(service=service, options=chrome_options)

def extraer_coordenadas_desde_url(url):
    try:
        # Patrón 1: /@LAT,LNG
        if "/@" in url:
            at_index = url.find("/@")
            partes = url[at_index + 2:].split(",")
            lat = float(partes[0])
            lng = float(partes[1])
            return {"lat": lat, "lng": lng}

        # Patrón 2: destination=LAT,LNG
        match_dest = re.search(r"[?&]destination=(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match_dest:
            lat = float(match_dest.group(1))
            lng = float(match_dest.group(2))
            return {"lat": lat, "lng": lng}

        # Patrón 3: cualquier LAT,LNG suelto (último recurso, puede dar falsos positivos)
        match = re.search(r"(-3?\d+\.\d+),(-5?\d+\.\d+)", url)
        if match:
            lat = float(match.group(1))
            lng = float(match.group(2))
            return {"lat": lat, "lng": lng}

        return None
    except Exception as e:
        print(f"[ERROR] No se pudo extraer coordenadas: {e}")
        return None



def obtener_coordenadas(direccion, delay=5):
    """Usa un WebDriver para buscar la dirección en Google Maps y devuelve coordenadas."""
    print(f"[BUSCANDO] {direccion}")
    query = urllib.parse.quote(direccion)
    url = f"https://www.google.com/maps/search/?api=1&query={query}"

    driver = crear_driver()
    try:
        driver.get(url)
        time.sleep(delay)
        final_url = driver.current_url
        coords = extraer_coordenadas_desde_url(final_url)
        if coords:
            print(f"[✓] Coordenadas: {coords}")
            return coords
        else:
            print("[✗] No se encontraron coordenadas")
            return {"lat": None, "lng": None}
    finally:
        driver.quit()

def consultar_coordenadas(direccion, mapa_url):
    """Consulta coordenadas de una dirección, primero desde la URL si contiene @lat,lng, si no, recurre a Selenium."""
    cache = cargar_cache()

    if direccion in cache:
        print(f"[CACHE] Coordenadas ya guardadas para: {direccion}")
        return cache[direccion]

    # Paso 1: Intentar extraer coordenadas directamente de la URL
    if mapa_url:
        coords = extraer_coordenadas_desde_url(mapa_url)
        if coords and coords["lat"] is not None and coords["lng"] is not None:
            print(f"[✓] Coordenadas extraídas desde mapa_url: {coords}")
            cache[direccion] = coords
            guardar_cache(cache)
            return coords

    # Paso 2: Usar Selenium si no se pudo extraer
    coords = obtener_coordenadas(direccion)
    cache[direccion] = coords
    guardar_cache(cache)
    return coords

def añadir_coordenadas_a_farmacias_24h():
    """Agrega coordenadas a cada farmacia del archivo 24h usando el campo 'mapa' con Selenium."""
    if not os.path.exists(FARMACIAS_24H_JSON):
        print(f"[ERROR] Archivo no encontrado: {FARMACIAS_24H_JSON}")
        return

    with open(FARMACIAS_24H_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    cambios = False
    cache = cargar_cache()

    for localidad, farmacias in data.items():
        for farmacia in farmacias:
            direccion = farmacia.get("direccion")
            mapa_url = farmacia.get("mapa")

            if not mapa_url:
                print(f"[ADVERTENCIA] No hay URL de mapa para: {direccion}")
                continue

            if direccion in cache:
                print(f"[CACHE] Coordenadas ya guardadas para: {direccion}")
                farmacia["coordenadas"] = cache[direccion]
                continue

            coords = extraer_coordenadas_desde_url(mapa_url)
            if coords:
                farmacia["coordenadas"] = coords
                cache[direccion] = coords
                cambios = True

    if cambios:
        with open(FARMACIAS_24H_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        guardar_cache(cache)
        print("[✓] Archivo actualizado con nuevas coordenadas.")
    else:
        print("[INFO] No había coordenadas por agregar.")


def obtener_coordenadas_desde_url_directa(mapa_url, delay=3):
    """Abre el link de Google Maps directamente y extrae coordenadas usando Selenium."""
    print(f"[MAPA] Ingresando a: {mapa_url}")
    driver = crear_driver()
    try:
        driver.get(mapa_url)
        time.sleep(delay)
        final_url = driver.current_url
        coords = extraer_coordenadas_desde_url(final_url)
        if coords:
            print(f"[✓] Coordenadas: {coords}")
            return coords
        else:
            print("[✗] No se encontraron coordenadas")
            return {"lat": None, "lng": None}
    finally:
        driver.quit()


if __name__ == "__main__":
    # Solo para pruebas rápidas
    # direccion = "Vélez Sársfield 4164, B1605BQB Vicente López, Provincia de Buenos Aires"
    # coords = consultar_coordenadas(direccion)
    # print(coords)

    # También podés ejecutar directamente la función de actualización del archivo 24h
    # añadir_coordenadas_a_farmacias_24h()

    print(extraer_coordenadas_desde_url("https://www.google.com/maps/place/-34.417152,-58.597868"))
