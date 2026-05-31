import os
import requests
import pandas as pd
import re
import time

max_datos = 500

API = "http://104.225.223.220:8003/api/"

r = requests.get(f"{API}usuarios/random?cantidad={max_datos}")
todos = r.json()["data"]

df_usuarios = pd.DataFrame(todos)
#se crea el dataframe de los 500 usuarios



"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++   USUARIOS   ++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""



print(f"Usuarios descargados: {len(df_usuarios)}")
print("Campos vacíos por columna:")
print(df_usuarios.isnull().sum())
print()

# Mirar cuales son los campos vacíos

COLUMNAS  = ["nombre", "apellido", "email", "telefono", "ciudad", "edad", "genero"]

#axis=0: Operaciones hacia abajo (por filas) y axis=1: Operaciones hacia los lados (por columnas).
datos_incompletos = df_usuarios[COLUMNAS].isnull().any(axis=1) 
ids_incompletos = df_usuarios.loc[datos_incompletos, "usuario_id"].tolist() #lista los ids de los usuarios que tengan campos vácios

print(f"Usuarios con al menos un campo vacío: {len(ids_incompletos)}")


# Obtener los datos de las llamadas
def parsear_transcripcion(texto: str) -> dict:
    """
    Extrae los datos de la llamada.
    El agente pregunta estos datos al cliente, así que buscamos la respuesta del cliente justo después de cada pregunta.

    Estrategia: leer el texto línea a línea y capturar lo que dice el Cliente
    cuando responde a preguntas de datos personales.
    """
    resultado = {
        "nombre_llamada": None, #ya
        "apellido_llamada":None,#ya
        "email_llamada": None,#ya
        "telefono_llamada": None,#listo 
        "ciudad_llamada": None,
        "edad_llamada": None,#ya
        "genero_llamada": None,#listo
    }

    if not texto:
        return resultado

    lineas = texto.strip().split("\n")

    for i, linea in enumerate(lineas):
        linea_lower = linea.lower()

        # Para telefono
        # Buscar en líneas del Cliente que parezcan un número de teléfono
        if linea.startswith("Cliente:"):
            contenido = linea.replace("Cliente:", "").strip()

            encontrado = re.search(
                r"(?:número es|teléfono es|es el|es)\s*([\+\d\s.\-\(\)]+)", #Guarda el número con todo y simbolos y espacios
                contenido,
                re.IGNORECASE,
            )
            
            if encontrado:
                telefono = encontrado.group(1)
                # limpiar formato visual
                telefono = re.sub(r"[.\-\s()\[\]]", "", telefono)  #se elimina todo menos el + (si es que el numero ya lo tenía desde un principio)
                
                # validar teléfono y si tiene entre 7 y 15 digitos
                if re.fullmatch(r"\+?\d{7,15}", telefono):
                    resultado["telefono_llamada"] = telefono
                    continue

        # para la edad
        if linea.startswith("Cliente:"):
            encontrado = re.search(r"[Tt]engo\s+(\d{1,3})\s+años", linea)
            if encontrado:
                resultado["edad_llamada"] = int(encontrado.group(1))
                continue

        # Género
        if linea.startswith("Cliente:"):
            encontrado = re.search(r"\b(femenino|masculino|mujer|hombre|no binario|otro)\b", linea, re.IGNORECASE)
            if encontrado:
                resultado["genero_llamada"] = encontrado.group(1).capitalize()
                continue
            
        if linea.startswith("Cliente:"):
            encontrado = re.search(r"\b(femenino|masculino|mujer|hombre|f|m|no binario|nobinario|no-binario|otro)\b",
            linea,
            re.IGNORECASE,
            )

            if encontrado:
                genero_detectado = encontrado.group(1).lower()
                
                otro = {
                    "no binario": "Otro",
                    "nobinario": "Otro",
                    "no-binario": "Otro",
                    "otro": "Otro",
                }

                resultado["genero_llamada"] = otro.get(genero_detectado)
                continue

        #Nombre y apellido
        if linea.startswith("Cliente:"):
            encontrado = re.search(
                r"(?:me llamo|soy|con|habla)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)",
                linea,
                re.IGNORECASE,
            )
            if encontrado:
                nombre_completo = encontrado.group(1).strip()
                partes = nombre_completo.split()
                resultado["nombre_llamada"] = partes[0]
                
                if len(partes) > 1:
                    resultado["apellido_llamada"] = " ".join(partes[1:])
                continue
        
        #para el correo
        if linea.startswith("Cliente:"):
            encontrado = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',linea)
            
            if encontrado:
                resultado["email_llamada"] = encontrado.group(1).lower()
                continue
        
        #para la ciudad de la llamada 
        if linea.startswith("Cliente:"):
            encontrado = re.search(
                r"(?:soy de|vivo en|ciudad es|resido en)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)*)",
                linea,
                re.IGNORECASE,
            )

            if encontrado:
                resultado["ciudad_llamada"] = encontrado.group(1).title()
                continue
            
    return resultado



datos_completos = []

print(f"\nConsultando /api/llamadas/usuario/{{id}} para {len(ids_incompletos)} usuarios...")

for idx, uid in enumerate(ids_incompletos): 
    try:
        resp = requests.get(f"{API}llamadas/usuario/{uid}", timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"  Error en usuario {uid}: {e}")
        continue

    llamadas = payload.get("data", [])
    if not llamadas:
        continue

    # Usar la primera llamada (la más reciente debería tener más info)
    transcripcion = llamadas[0].get("transcripcion", "")
    extraido = parsear_transcripcion(transcripcion)
    extraido["usuario_id"] = uid
    datos_completos.append(extraido)

    # Pequeña pausa para no saturar la API
    if idx % 50 == 0:
        print(f"  Procesados: {idx}/{len(ids_incompletos)}")
        time.sleep(0.2)

print(f"\nRegistros con datos extraídos de llamadas: {len(datos_completos)}")

#se hace un merge de ambos dataframes (el de usuarios y el de las llamadas )
df_llamadas = pd.DataFrame(datos_completos) #dataframe de las llamadas

if df_llamadas.empty:
    print("No se extrajeron datos de llamadas.")
    df_final = df_usuarios.copy() #devuelve solo los datos obtenidos de la dataframe usuarios
else:
    df_final = df_usuarios.merge(df_llamadas, on="usuario_id", how="left") #Se hace el merge de ambos dataframes entonces: Conserva todas las filas de la tabla izquierda (df_usuarios) Aunque no existan en df_llamadas.

    # Para cada campo objetivo, rellenar el vacío con el valor de la llamada
    columnas_a_completar  = {
        "nombre":   "nombre_llamada",
        "apellido": "apellido_llamada",
        "telefono": "telefono_llamada",
        "edad":     "edad_llamada",
        "genero":   "genero_llamada",
        "email": "email_llamada",
        "ciudad": "ciudad_llamada"
    }

    for campo_original, campo_llamada in columnas_a_completar.items():
        if campo_llamada in df_final.columns:
            df_final[campo_original] = df_final[campo_original].fillna(df_final[campo_llamada]) #Si está vacío la columna campo_original se llena con campo_llamada

    # Quitar columnas temporales de la llamada
    df_final.drop(columns=list(columnas_a_completar.values()), inplace=True, errors="ignore")


# Verificar si aun quedan campos nulos: 
usuarios_incompletos = df_final[
    df_final[COLUMNAS].isnull().any(axis=1)
]

print(
    usuarios_incompletos[
        ["usuario_id", "nombre", "apellido", "telefono", "edad", "genero"]
    ].to_string(index=False)
)

#Limpiar toda la tabla antes de exportarla:

def limpiar_texto():
    for columna in COLUMNAS:
        if columna in df_final.columns:
            df_final[columna] = df_final[columna].apply(
                lambda x: re.sub(r"\s+", " ", x).strip()
                if isinstance(x, str)
                else x
            )

def normalizar_email():
    if "email" in df_final.columns:
        df_final["email"] = df_final["email"].apply(
            lambda x: x.lower().strip()
            if isinstance(x, str)
            else x
        )

def normalizar_genero():
    normalizacion_genero = {
        "F": "Femenino",
        "f": "Femenino",
        "Mujer": "Femenino",
        "mujer": "Femenino",

        "M": "Masculino",
        "m": "Masculino",
        "Hombre": "Masculino",
        "hombre": "Masculino",

        "No binario": "Otro",
        "no binario": "Otro",
        "Otro": "Otro",
        "otro": "Otro"
    }

    if "genero" in df_final.columns:
        df_final["genero"] = df_final["genero"].replace(normalizacion_genero)

#telefono:
def normalizar_telefono(tel, pais_nombre=None):
    if pd.isna(tel) or str(tel).strip() == "":
        return None

    tel = str(tel).strip()
    # Eliminar extensiones
    tel = re.sub(r"[xX]\d+$", "", tel).strip()
    tel = re.sub(r"(?:ext\.?|extension)\s*\d+$", "", tel, flags=re.IGNORECASE).strip()

    # Limpiar todo símbolo visual incluyendo paréntesis, conservar + inicial
    tiene_plus = tel.lstrip().startswith("+")
    solo_digitos = re.sub(r"\D", "", tel)

    if not (7 <= len(solo_digitos) <= 15):
        return None

    return solo_digitos

def normalizar_telefonos(df=None):
    if df is None:
        try:
            df = df_final
        except NameError:
            return None

    if "telefono" not in df.columns:
        return df

    for idx, fila in df.iterrows():
        pais = fila["pais"] if "pais" in df.columns else None
        df.at[idx, "telefono"] = normalizar_telefono(fila["telefono"], pais)

    return df

def normalizar_nombre():
    df_final["nombre"] = df_final["nombre"].str.title()
    
def normalizar_apellido():
    df_final["apellido"] = df_final["apellido"].str.title()
    
def normalizar_ciudad():
    df_final["ciudad"] = df_final["ciudad"].str.title()


#  Exportar el CSV final ya limpio
limpiar_texto()
normalizar_email()
normalizar_genero()
normalizar_telefonos()
normalizar_nombre()
normalizar_apellido()
normalizar_ciudad()

os.makedirs("csv", exist_ok=True)
df_final.to_csv("csv/usuarios.csv", index=False)
print("\nArchivo guardado: usuarios.csv")






"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++   PEDIDOS   +++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""



ids_todos      = df_final["usuario_id"].tolist()
pedidos_por_usuario = 2 # 2 pedidos por usuario

print(f"\nConsultando pedidos para {len(ids_todos)} usuarios ({pedidos_por_usuario} pedidos por usuario)...")

todos_los_pedidos = []

for idx, uid in enumerate(ids_todos):
    if len(todos_los_pedidos) >= max_datos:
        break

    try:
        url = f"{API}pedidos/usuario/{uid}?limit={pedidos_por_usuario}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        pedidos = resp.json().get("data", [])
    except Exception as e:
        print(f"  Error en usuario {uid}: {e}")
        continue

    todos_los_pedidos.extend(pedidos)

    if idx % 50 == 0:
        print(f"  Procesados: {idx}/{len(ids_todos)} — Pedidos acumulados: {len(todos_los_pedidos)}")
        time.sleep(0.2)

# Recortar exactamente a 500 por si el último usuario empujó por encima
df_pedidos = pd.DataFrame(todos_los_pedidos[:max_datos])

print(f"\nPedidos obtenidos: {len(df_pedidos)}")

df_pedidos.to_csv("csv/pedidos.csv", index=False)
print("\nArchivo guardado: csv/pedidos.csv")






"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++   DETALLES PEDIDOS   +++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""



ids_pedidos = df_pedidos["pedido_id"].tolist()
max_det_pedido = 2

print(f"\nConsultando detalles para {len(ids_pedidos)} pedidos (máx. {max_det_pedido} por pedido, tope {max_datos})...")

todos_los_detalles = []

for idx, pid in enumerate(ids_pedidos):
    if len(todos_los_detalles) >= max_datos:
        break

    try:
        url = f"{API}detalle_pedido/pedido/{pid}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        detalles = resp.json().get("data", [])
    except Exception as e:
        print(f"  Error en pedido {pid}: {e}")
        continue

    todos_los_detalles.extend(detalles)

    if idx % 50 == 0:
        print(f"  Procesados: {idx}/{len(ids_pedidos)} — Detalles acumulados: {len(todos_los_detalles)}")
        time.sleep(0.2)

df_detalles = pd.DataFrame(todos_los_detalles[:max_datos])

print(f"\nDetalles obtenidos: {len(df_detalles)}")

df_detalles.to_csv("csv/detalle_pedido.csv", index=False)
print("\nArchivo guardado: csv/detalle_pedido.csv")