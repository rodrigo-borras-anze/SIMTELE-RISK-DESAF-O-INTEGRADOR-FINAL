import os
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'simtele.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Crear las 6 tablas relacionales si no existen
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS caso_estudio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT
    );

    CREATE TABLE IF NOT EXISTS escenario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caso_id INTEGER,
        tipo TEXT NOT NULL,
        FOREIGN KEY (caso_id) REFERENCES caso_estudio(id)
    );

    CREATE TABLE IF NOT EXISTS simulacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        escenario_id INTEGER,
        fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usuario_equipo TEXT,
        estado TEXT DEFAULT 'EXITOSO',
        FOREIGN KEY (escenario_id) REFERENCES escenario(id)
    );

    CREATE TABLE IF NOT EXISTS ejecucion_metodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulacion_id INTEGER,
        metodo_nombre TEXT NOT NULL,
        tolerancia REAL,
        tiempo_ejecucion_ms REAL,
        convergio BOOLEAN,
        FOREIGN KEY (simulacion_id) REFERENCES simulacion(id)
    );

    CREATE TABLE IF NOT EXISTS iteracion_resultado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ejecucion_id INTEGER,
        numero_iteracion INTEGER,
        valor_aprox REAL,
        residuo REAL,
        error_abs REAL,
        error_rel REAL,
        FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id)
    );

    CREATE TABLE IF NOT EXISTS resultado_resumen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ejecucion_id INTEGER,
        clave TEXT NOT NULL,
        valor_json TEXT,
        FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id)
    );
    """)
    
    # 2. Insertar los casos de estudio y escenarios iniciales
    cursor.execute("SELECT COUNT(*) FROM caso_estudio")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO caso_estudio (id, nombre, descripcion) VALUES 
            (1, 'Detención de Emergencia', 'Búsqueda de raíces para v(t) = 0'),
            (2, 'Deterioro Mecánico', 'Cruce de umbral de inspección D(t)'),
            (3, 'Oscilaciones por Viento', 'Solución de EDO e Integración'),
            (4, 'Reconstrucción de Sensores', 'Interpolación de telemetría');

            INSERT INTO escenario (id, caso_id, tipo) VALUES 
            (1, 1, 'NORMAL'),
            (2, 2, 'NORMAL'),
            (3, 3, 'NORMAL'),
            (4, 4, 'NORMAL');
        """)
        
    conn.commit()
    conn.close()

def guardar_simulacion(caso_id, usuario_equipo, ejecuciones, escenario_tipo='NORMAL'):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    tipo = escenario_tipo.upper()
    cursor.execute(
        "SELECT id FROM escenario WHERE caso_id = ? AND tipo = ?",
        (caso_id, tipo)
    )
    fila = cursor.fetchone()
    if fila:
        escenario_id = fila[0]
    else:
        cursor.execute(
            "INSERT INTO escenario (caso_id, tipo) VALUES (?, ?)",
            (caso_id, tipo)
        )
        escenario_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO simulacion (escenario_id, usuario_equipo, estado) VALUES (?, ?, ?)",
        (escenario_id, usuario_equipo, 'EXITOSO')
    )
    simulacion_id = cursor.lastrowid

    for ej in ejecuciones:
        cursor.execute(
            "INSERT INTO ejecucion_metodo (simulacion_id, metodo_nombre, tolerancia, tiempo_ejecucion_ms, convergio) VALUES (?, ?, ?, ?, ?)",
            (simulacion_id, ej.get("metodo"), ej.get("tolerancia"), ej.get("tiempo_ms"), ej.get("convergio"))
        )
        ejecucion_id = cursor.lastrowid

        for it in ej.get("iteraciones", []):
            cursor.execute(
                "INSERT INTO iteracion_resultado (ejecucion_id, numero_iteracion, valor_aprox, residuo, error_abs, error_rel) VALUES (?, ?, ?, ?, ?, ?)",
                (ejecucion_id, it.get("k"), it.get("x"), it.get("residuo"), it.get("error_abs"), it.get("error_rel"))
            )

        val_final = ej.get("valor_final")
        if val_final:
            cursor.execute(
                "INSERT INTO resultado_resumen (ejecucion_id, clave, valor_json) VALUES (?, ?, ?)",
                (ejecucion_id, "valor_final", json.dumps(val_final))
            )

    conn.commit()
    conn.close()
    return simulacion_id

def obtener_historial_simulaciones(limit=50):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT s.id, c.nombre AS modulo, e.tipo AS escenario, s.fecha_ejecucion AS fecha, s.usuario_equipo, s.estado
    FROM simulacion s
    JOIN escenario e ON s.escenario_id = e.id
    JOIN caso_estudio c ON e.caso_id = c.id
    ORDER BY s.fecha_ejecucion DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    filas = cursor.fetchall()
    conn.close()
    
    historial = []
    for f in filas:
        historial.append({
            "id": f[0],
            "modulo": f[1],
            "escenario": f[2],
            "fecha": f[3],
            "usuario_equipo": f[4],
            "estado": f[5]
        })
    return historial