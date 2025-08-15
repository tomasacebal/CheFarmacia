import os
from dotenv import load_dotenv
from tqdm import tqdm

from scrapers.san_isidro import SanIsidroScraper
from scrapers.tigre import TigreScraper
from scrapers.la_plata import LaPlataScraper
from scrapers.merlo import MerloScraper
from scrapers.zarate import ZarateScraper
from scrapers.florencio_varela import VarelaScraper
from scrapers.quilmes import QuilmesScraper
from scrapers.berazategui import BerazateguiScraper
from scrapers.lincoln import LincolnScraper
from scrapers.azul import AzulScraper
from scrapers.bolivar import BolivarScraper
from scrapers.coronel_suarez import CoronelSuarezScraper
from scrapers.las_toninas import LasToninasScraper
from scrapers.mar_de_ajo import MarDeAjoScraper
from scrapers.mar_del_tuyu import MarDelTuyuScraper
from scrapers.miramar import MiramarScraper
from scrapers.san_bernardo import SanBernardoScraper
from scrapers.san_clemente_del_tuyu import SanClementeScraper
from scrapers.santa_teresita import SantaTeresitaScraper
from scrapers.sources import SourcesScraper
from scrapers.san_fernando import SanFernandoScraper
from scrapers.mar_del_plata import MarDelPlataScraper

from utils import save_to_json, commit_and_push, format_data_for_json, merge_data, generate_localities_list

def run_all_scrapers():
    load_dotenv()

    # Lista de scrapers a ejecutar
    scrapers = [
        SourcesScraper(),

        SanIsidroScraper(),
        TigreScraper(),
        LaPlataScraper(),
        MerloScraper(),
        ZarateScraper(),
        QuilmesScraper(),
        BerazateguiScraper(),
        LincolnScraper(),
        AzulScraper(),
        BolivarScraper(),
        CoronelSuarezScraper(),
        LasToninasScraper(),
        MarDeAjoScraper(),
        MarDelTuyuScraper(),
        MiramarScraper(),
        SanBernardoScraper(),
        SanClementeScraper(),
        SantaTeresitaScraper(),
        SanFernandoScraper(),
        MarDelPlataScraper(),

        VarelaScraper(),
    ]

    datos_combinados = {}

    for scraper in tqdm(scrapers, desc="Ejecutando scrapers"):
        # El mensaje de info ahora es más genérico para el SourcesScraper
        localidad_info = getattr(scraper, 'LOCALIDAD', scraper.__class__.__name__)
        print(f"\n[INFO] Ejecutando scraper para: {localidad_info}")
        datos = scraper.fetch()
        datos_formateados = format_data_for_json(datos)
        datos_combinados = merge_data(datos_combinados, datos_formateados)


    # Guardar toda la info unificada
    MAIN_JSON_FILENAME = "data/farmacias_turno.json"
    save_to_json(datos_combinados)

    # Generar el archivo de localidades a partir del archivo principal recién guardado
    LOCALITIES_FILENAME = "data/localidades.json"
    generate_localities_list(input_json_path=MAIN_JSON_FILENAME, output_json_path=LOCALITIES_FILENAME)

    # Hacer commit y push
    repo_path = os.getenv("GITHUB_REPO_PATH")
    # Un mensaje más genérico ya que estamos subiendo todos los cambios del proyecto
    commit_message = "Actualización automática de datos y archivos del proyecto"

    if repo_path:
        # Simplemente llamamos a la función con la ruta y el mensaje.
        # Ya no necesitamos construir una lista de archivos.
        commit_and_push(repo_path, commit_message)
    else:
        print("[ADVERTENCIA] No se realizará commit y push. Falta la variable de entorno GITHUB_REPO_PATH.")

if __name__ == "__main__":
    run_all_scrapers()