import json
import os
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path  # pip install chromedriver-py

CACHE_FILE = "coordenadas_cache.json"


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
        at_index = url.find("/@")
        if at_index == -1:
            return None
        partes = url[at_index + 2:].split(",")
        lat = float(partes[0])
        lng = float(partes[1])
        return {"lat": lat, "lng": lng}
    except Exception as e:
        print(f"[ERROR] No se pudo extraer coordenadas: {e}")
        return None


def obtener_coordenadas(direccion, delay=2):
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


def consultar_coordenadas(direccion):
    """Consulta una dirección en caché. Si no existe, la busca y actualiza el caché."""
    cache = cargar_cache()

    if direccion in cache:
        print(f"[CACHE] Coordenadas ya guardadas para: {direccion}")
        return cache[direccion]

    coords = obtener_coordenadas(direccion)
    cache[direccion] = coords
    guardar_cache(cache)
    return coords

if __name__ == "__main__":
    direccion = "Av. Santa Fe 1234, Vicente López, Buenos Aires"
    coords = consultar_coordenadas(direccion)
    print(coords)
