# Proyecto-base-de-datos

### Instala las dependencias

bash

```bash
pip install pandas psycopg2-binary requests
```

Eso instala:

* `pandas` — manejo de datos y DataFrames
* `psycopg2-binary` — conexión a PostgreSQL
* `requests` — consumo de la API REST



proyectoFinal/
│
├── extraer_usuarios.py      # Descarga usuarios desde la API y limpia datos con transcripciones
├── cargar.py                # Crea las tablas en Supabase e inserta todos los datos
├── .gitignore               # Excluye CSVs y archivos temporales
└── README.md                # Este archivo

## Posibles errores y soluciones


| Error                           | Solución                                                  |
| ------------------------------- | ---------------------------------------------------------- |
| `ModuleNotFoundError: psycopg2` | Correr`pip install psycopg2-binary`                        |
| `ModuleNotFoundError: pandas`   | Correr`pip install pandas`                                 |
| `connection refused`            | Verificar credenciales de Supabase                         |
| `ForeignKeyViolation`           | Ya manejado con filtros en el script                       |
| `UnicodeEncodeError`            | Agregar`sys.stdout.reconfigure(encoding='utf-8')`al inicio |
