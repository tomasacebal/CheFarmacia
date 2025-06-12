import os
import json
from pygit2 import Repository, Signature, RemoteCallbacks, UserPass
import requests
import datetime
import re
import urllib.parse

from get_coords_from_maps import consultar_coordenadas  # función que busca coordenadas con cache


# ... [importaciones y funciones sin cambios] ...


def merge_data(existing, new):
    for mes, contenido in new.items():
        if mes not in existing:
            existing[mes] = contenido
        else:
            for dia, nuevas_farmacias in contenido["dias"].items():
                if dia not in existing[mes]["dias"]:
                    existing[mes]["dias"][dia] = nuevas_farmacias
                else:
                    direcciones_existentes = {
                        f["direccion"]: idx for idx, f in enumerate(existing[mes]["dias"][dia])
                    }

                    for f in nuevas_farmacias:
                        dir_nueva = f["direccion"]
                        if dir_nueva in direcciones_existentes:
                            # Reemplaza la farmacia existente por la nueva (actualiza coordenadas)
                            idx = direcciones_existentes[dir_nueva]
                            existing[mes]["dias"][dia][idx] = f
                        else:
                            # Agrega si no existe
                            existing[mes]["dias"][dia].append(f)
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

    for f in farmacias:
        mes = 'junio'
        localidad = f["localidad"]
        fuente = f["fuente"]
        confianza = f["nivel_confianza"]
        dia = f["fecha"]
        mapa = f["mapa"]

        if mes not in data:
            data[mes] = {
                "localidad": localidad,
                "fuente": fuente,
                "confianza": confianza,
                "dias": {}
            }

        if dia not in data[mes]["dias"]:
            data[mes]["dias"][dia] = []

        direccionMaps = f"{f["direccion"]}, {f["localidad"]}"
        direccion = f["direccion"]
        telefono = limpiar_telefono(f["telefono"])
        mapa = mapa
        coords = consultar_coordenadas(direccion, mapa) # ← usa cache o consulta a Maps

        data[mes]["dias"][dia].append({
            "nombre": f["nombre"],
            "direccion": direccion,
            "telefono": telefono,
            "mapa": mapa,
            "coordenadas": coords
        })

    return data


def commit_and_push(repo_path, file_path, message="Update JSON file"):
    repo = Repository(repo_path)
    index = repo.index
    index.add(file_path)
    index.write()
    tree = index.write_tree()

    author = Signature("AutoScraper by HIGHER®", "atomasacebal@gmail.com")
    committer = author
    parent = repo.head.peel().id

    oid = repo.create_commit(
        "refs/heads/main",
        author,
        committer,
        message,
        tree,
        [parent]
    )

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
