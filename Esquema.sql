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