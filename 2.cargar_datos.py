import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

db = psycopg2.connect(
    host="aws-1-us-east-2.pooler.supabase.com",
    dbname="postgres",
    user="postgres.iegqjnfilnuugomzduvv",
    password="W!tpevrsDza44F@",
    port=5432,
    sslmode="require"
)
cur = db.cursor()
print("Conectado a Supabase")

cur.execute("""
CREATE TABLE IF NOT EXISTS categorias (
    categoria_id  INTEGER      PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL UNIQUE,
    descripcion   VARCHAR(100),
    activa        BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS productos (
    producto_id   INTEGER        PRIMARY KEY,
    nombre        VARCHAR(150)   NOT NULL,
    categoria_id  INTEGER        NOT NULL REFERENCES categorias(categoria_id),
    proveedor_id  INTEGER        NOT NULL,
    precio        NUMERIC(10,2)  NOT NULL CHECK (precio >= 0),
    costo         NUMERIC(10,2)  NOT NULL CHECK (costo >= 0),
    descripcion   VARCHAR(100),
    activo        BOOLEAN        NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id     INTEGER       PRIMARY KEY,
    nombre         VARCHAR(100)  NOT NULL,
    apellido       VARCHAR(100)  NOT NULL,
    email          VARCHAR(150)  NOT NULL UNIQUE,
    telefono       VARCHAR(20),
    fecha_registro DATE          NOT NULL,
    pais           VARCHAR(60),
    ciudad         VARCHAR(100),
    edad           INTEGER       CHECK (edad BETWEEN 0 AND 120),
    genero         VARCHAR(20),
    estado_cuenta  VARCHAR(20)   NOT NULL DEFAULT 'Activo'
);

CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id           INTEGER        PRIMARY KEY,
    usuario_id          INTEGER        NOT NULL REFERENCES usuarios(usuario_id),
    fecha_pedido        DATE           NOT NULL,
    estado              VARCHAR(50)    NOT NULL,
    subtotal            NUMERIC(10,2)  NOT NULL,
    descuento           NUMERIC(10,2)  NOT NULL DEFAULT 0,
    costo_envio         NUMERIC(10,2)  NOT NULL DEFAULT 0,
    total               NUMERIC(10,2)  NOT NULL,
    direccion_envio_id  INTEGER,
    sucursal_id         INTEGER,
    cupon_id            INTEGER,
    notas               TEXT
);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    detalle_id            INTEGER        PRIMARY KEY,
    pedido_id             INTEGER        NOT NULL REFERENCES pedidos(pedido_id),
    producto_id           INTEGER        NOT NULL REFERENCES productos(producto_id),
    cantidad              INTEGER        NOT NULL CHECK (cantidad > 0),
    precio_unitario       NUMERIC(10,2)  NOT NULL CHECK (precio_unitario >= 0),
    descuento_porcentaje  NUMERIC(5,2)   NOT NULL DEFAULT 0,
    subtotal              NUMERIC(10,2)  NOT NULL
);
""")
db.commit()
print("Tablas creadas")

# ── CARGAR CSVs ────────────────────────────────────────────────────────
df_usuarios   = pd.read_csv("csv/usuarios.csv")
df_pedidos    = pd.read_csv("csv/pedidos.csv")
df_detalle    = pd.read_csv("csv/detalle_pedido.csv")
df_productos  = pd.read_csv("csv/productos.csv")
df_categorias = pd.read_csv("csv/categorias.csv")

# Columnas que deben ser enteros en la BD
COLS_ENTERAS = {
    "categoria_id", "producto_id", "usuario_id", "pedido_id",
    "detalle_id", "proveedor_id", "cantidad",
    "direccion_envio_id", "sucursal_id", "cupon_id"
}

COLS_BOOL = {"activa", "activo"}

def limpiar_valor(val, col):
    """Convierte cada valor al tipo correcto según la columna."""
    if pd.isna(val):
        return None
    if col in COLS_BOOL:
        return bool(int(val))
    if col in COLS_ENTERAS:
        return int(float(val))
    # ← fix clave: convierte numpy floats/ints a tipos Python nativos
    if hasattr(val, 'item'):
        return val.item()
    return val

def cargar(tabla, df, columnas):
    df = df[columnas].copy()
    filas = [
        tuple(limpiar_valor(row[col], col) for col in columnas)
        for _, row in df.iterrows()
    ]
    sql = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cur, sql, filas)
    db.commit()
    print(f"  OK {tabla}: {len(filas)} registros")

print("\nInsertando datos...")
cargar("categorias", df_categorias, ["categoria_id", "nombre", "descripcion", "activa"])
cargar("productos",  df_productos,  ["producto_id", "nombre", "categoria_id", "proveedor_id", "precio", "costo", "descripcion", "activo"])
cargar("usuarios",   df_usuarios,   ["usuario_id", "nombre", "apellido", "email", "telefono", "fecha_registro", "pais", "ciudad", "edad", "genero", "estado_cuenta"])

usuarios_validos = set(df_usuarios["usuario_id"].astype(int))
df_pedidos_filtrado = df_pedidos[df_pedidos["usuario_id"].astype(int).isin(usuarios_validos)]
print(f"  Pedidos descartados por FK: {len(df_pedidos) - len(df_pedidos_filtrado)}")
cargar("pedidos", df_pedidos_filtrado, ["pedido_id", "usuario_id", "fecha_pedido", "estado", "subtotal", "descuento", "costo_envio", "total", "direccion_envio_id", "sucursal_id", "cupon_id", "notas"])

pedidos_validos = set(df_pedidos_filtrado["pedido_id"].astype(int))
productos_validos = set(df_productos["producto_id"].astype(int))  # ← nuevo

df_detalle_filtrado = df_detalle[
    df_detalle["pedido_id"].astype(int).isin(pedidos_validos) &
    df_detalle["producto_id"].astype(int).isin(productos_validos)  # ← nuevo
]
print(f"  Detalles descartados por FK: {len(df_detalle) - len(df_detalle_filtrado)}")
cargar("detalle_pedido", df_detalle_filtrado, ["detalle_id", "pedido_id", "producto_id", "cantidad", "precio_unitario", "descuento_porcentaje", "subtotal"])

print("\nVerificando integridad referencial...")
checks = [
    ("pedidos sin usuario válido",     "SELECT COUNT(*) FROM pedidos p LEFT JOIN usuarios u USING(usuario_id) WHERE u.usuario_id IS NULL"),
    ("detalle sin pedido válido",      "SELECT COUNT(*) FROM detalle_pedido d LEFT JOIN pedidos p USING(pedido_id) WHERE p.pedido_id IS NULL"),
    ("detalle sin producto válido",    "SELECT COUNT(*) FROM detalle_pedido d LEFT JOIN productos p USING(producto_id) WHERE p.producto_id IS NULL"),
    ("productos sin categoría válida", "SELECT COUNT(*) FROM productos p LEFT JOIN categorias c USING(categoria_id) WHERE c.categoria_id IS NULL"),
]
for descripcion, query in checks:
    cur.execute(query)
    n = cur.fetchone()[0]
    print(f"  {'OK' if n == 0 else f'✗ {n} huérfanos'} — {descripcion}")

cur.close()
db.close()
print("\nListo")