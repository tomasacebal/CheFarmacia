import os
import json
from pygit2 import Repository, Signature, RemoteCallbacks, UserPass
import requests
import datetime
import re
import urllib.parse
import datetime as d
import telegram
import asyncio

from get_coords_from_maps import consultar_coordenadas  # función que busca coordenadas con cache


# ... [importaciones y funciones sin cambios] ...


def merge_data(existing, new):
    for mes, localidades in new.items():
        if mes not in existing:
            existing[mes] = localidades
        else:
            for localidad, contenido in localidades.items():
                if localidad not in existing[mes]:
                    existing[mes][localidad] = contenido
                else:
                    for dia, nuevas_farmacias in contenido["dias"].items():
                        if dia not in existing[mes][localidad]["dias"]:
                            existing[mes][localidad]["dias"][dia] = nuevas_farmacias
                        else:
                            direcciones_existentes = {
                                f["direccion"]: idx for idx, f in enumerate(existing[mes][localidad]["dias"][dia])
                            }

                            for f in nuevas_farmacias:
                                dir_nueva = f["direccion"]
                                if dir_nueva in direcciones_existentes:
                                    idx = direcciones_existentes[dir_nueva]
                                    existing[mes][localidad]["dias"][dia][idx] = f
                                else:
                                    existing[mes][localidad]["dias"][dia].append(f)
    return existing


def save_to_json(new_data):
    json_path = os.getenv("JSON_PATH")
    print(f"Guardando archivo en: {json_path}")

    if not json_path:
        raise ValueError("La variable JSON_PATH no está definida en el .env")

    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Cargar data existente si existe
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ JSON corrupto o vacío. Se reemplazará completamente.")
                existing_data = {}
    else:
        existing_data = {}

    merged_data = merge_data(existing_data, new_data)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)



def limpiar_telefono(raw):
    return re.sub(r"[^\d+]", "", raw)


def generar_link_mapa(direccion):
    query = urllib.parse.quote(direccion)
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def format_data_for_json(farmacias):
    data = {}

    meses = {
    'january': 'enero',
    'february': 'febrero',
    'march': 'marzo',
    'april': 'abril',
    'may': 'mayo',
    'june': 'junio',
    'july': 'julio',
    'august': 'agosto',
    'september': 'septiembre',
    'october': 'octubre',
    'november': 'noviembre',
    'diciembre': 'diciembre'
    }
    mes = meses[d.datetime.now().strftime("%B").lower()]  # Podrías hacerlo dinámico con datetime.now().strftime("%B").lower()

    for f in farmacias:
        localidad = f["localidad"]
        fuente = f["fuente"]
        confianza = f["nivel_confianza"]
        dia = f["fecha"]
        mapa = f["mapa"]

        if mes not in data:
            data[mes] = {}

        if localidad not in data[mes]:
            data[mes][localidad] = {
                "fuente": fuente,
                "confianza": confianza,
                "dias": {}
            }

        if dia not in data[mes][localidad]["dias"]:
            data[mes][localidad]["dias"][dia] = []

        direccion = f["direccion"]
        telefono = limpiar_telefono(f["telefono"])
        coords = consultar_coordenadas(direccion, mapa)

        data[mes][localidad]["dias"][dia].append({
            "nombre": f["nombre"],
            "direccion": direccion,
            "telefono": telefono,
            "mapa": mapa,
            "coordenadas": coords
        })

    return data

def commit_and_push(repo_path, message="Automatic project update"):
    """
    Añade TODOS los cambios del proyecto (nuevos, modificados, eliminados),
    hace commit y push. No crea un commit si no hay cambios.
    """
    repo = Repository(repo_path)
    index = repo.index

    index.add_all()
    index.write()
    tree = index.write_tree()

    try:
        # --- ESTA ES LA LÓGICA CORREGIDA Y MÁS ROBUSTA ---
        # 1. Obtener la referencia a la rama 'main' explícitamente.
        main_ref = repo.references.get("refs/heads/main")

        if not main_ref:
            # Si la rama 'main' no existe, es el primer commit.
            print("[INFO] Rama 'main' no encontrada. Creando primer commit.")
            parents = []
            parent_tree = None
        else:
            # 2. Obtener el commit al que apunta la referencia de 'main'.
            parent_commit = repo.get(main_ref.target)
            if not parent_commit:
                 raise Exception("No se pudo encontrar el commit padre de main.")
            parent_tree = parent_commit.tree
            parents = [parent_commit.id]
        
        # 3. Comprobar si hay cambios reales.
        if parent_tree and tree.id == parent_tree.id:
            print("[INFO] No se detectaron cambios en el repositorio. No se realizará el commit.")
            return

    except KeyError:
        # Manejo de error por si la referencia no existe (aunque .get() lo previene)
        print("[INFO] Creando primer commit (KeyError).")
        parents = []


    # El resto del proceso es el mismo
    author = Signature("AutoScraper by HIGHER®", "atomasacebal@gmail.com")
    committer = author

    oid = repo.create_commit(
        "refs/heads/main",  # La referencia a actualizar
        author,
        committer,
        message,
        tree,
        parents  # La lista de padres correcta
    )
    print(f"[INFO] Commit creado con éxito: {oid.hex}")

    remote = repo.remotes["origin"]
    remote_url = os.getenv("GITHUB_REMOTE")
    match = re.match(r'https://([^:@]+):?([^@]*)@', remote_url)
    if match:
        username = match.group(1)
        password = match.group(2)
    else:
        username = ""
        password = ""

    callbacks = RemoteCallbacks(credentials=UserPass(username, password))
    remote.push(["refs/heads/main"], callbacks=callbacks)
    print("[INFO] Push a 'origin/main' realizado con éxito.")

def generate_localities_list(input_json_path, output_json_path):
    """
    Actualiza el archivo de localidades. Lee el archivo existente, lo compara con las
    localidades actuales del scraper y añade solo las que no existen, conservando
    los datos existentes (como las coordenadas).
    """
    print(f"Actualizando lista de localidades desde: {input_json_path}")

    # 1. Obtener la lista completa de localidades desde el scraping actual
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        scraped_localities_set = set()
        for month_data in scraped_data.values():
            # .keys() devuelve los nombres de las localidades para ese mes
            scraped_localities_set.update(month_data.keys())
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] No se pudo leer el archivo de entrada '{input_json_path}'. No se puede actualizar la lista de localidades.")
        return

    # 2. Leer el archivo de localidades.json existente o crear una estructura por defecto
    try:
        with open(output_json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si el archivo no existe o está corrupto, empezamos de cero
        existing_data = {"Buenos Aires": []}
    
    # Asegurarnos de que la clave de la provincia exista
    if "Buenos Aires" not in existing_data:
        existing_data["Buenos Aires"] = []

    # 3. Obtener un set de los nombres de las localidades ya registradas para una búsqueda rápida
    existing_names_set = {loc['nombre'] for loc in existing_data["Buenos Aires"]}

    # 4. Encontrar las localidades que son nuevas
    new_localities_names = scraped_localities_set - existing_names_set

    # 5. Si hay localidades nuevas, añadirlas a la estructura
    if new_localities_names:
        print(f"[INFO] Se encontraron {len(new_localities_names)} localidades nuevas: {', '.join(sorted(list(new_localities_names)))}")
        for name in sorted(list(new_localities_names)):
            new_locality_obj = {
                "nombre": name,
                "coordenadas": {
                    "lat": None,
                    "lng": None
                }
            }
            existing_data["Buenos Aires"].append(new_locality_obj)
        
        # 6. Re-ordenar la lista completa alfabéticamente por nombre
        existing_data["Buenos Aires"].sort(key=lambda x: x['nombre'])
        
    else:
        print("[INFO] No se encontraron nuevas localidades. El archivo está actualizado.")
        # No es necesario hacer nada más si no hay cambios, pero igual guardaremos por consistencia.

    # 7. Guardar la estructura de datos (actualizada o no) de vuelta en el archivo
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    total_localities = len(existing_data["Buenos Aires"])
    print(f"[INFO] Archivo de localidades actualizado con éxito. Total: {total_localities} localidades.")

async def send_telegram_notification(message):
    """
    Envía un mensaje a un chat de Telegram usando las credenciales del .env.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[ADVERTENCIA] No se configuraron las credenciales de Telegram. No se enviará notificación.")
        return

    try:
        bot = telegram.Bot(token=bot_token)
        # Usamos MarkdownV2 para formatear el texto. Los caracteres especiales deben ser escapados.
        # Para mensajes simples como este, no suele ser un problema.
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="MarkdownV2"
        )
        print("[INFO] Notificación de Telegram enviada con éxito.")
    except Exception as e:
        print(f"[ERROR] Falló al enviar la notificación de Telegram: {e}")