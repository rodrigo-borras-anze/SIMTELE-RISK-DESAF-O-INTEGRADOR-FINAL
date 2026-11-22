-- ============================================================
-- SCRIPT DE BASE DE DATOS: SIMTELE-RISK (SQLite)
-- Estudiante A — Persistencia de simulaciones relacionales
-- ============================================================

-- 1. Tabla: caso_estudio (Módulos principales del sistema)
CREATE TABLE IF NOT EXISTS caso_estudio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    modelo_version VARCHAR(20) DEFAULT '1.0'
);

-- 2. Tabla: escenario (Configuraciones de ensayo: NORMAL, ESTRÉS, MAL_CONDICIONADO)
CREATE TABLE IF NOT EXISTS escenario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER NOT NULL,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('NORMAL', 'ESTRES', 'MAL_CONDICIONADO')),
    parametros_json TEXT NOT NULL,
    fuente_datos VARCHAR(100) DEFAULT 'Sintético / Hipotético',
    FOREIGN KEY (caso_id) REFERENCES caso_estudio(id) ON DELETE CASCADE
);

-- 3. Tabla: simulacion (Registro global de ejecuciones por usuario)
CREATE TABLE IF NOT EXISTS simulacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_equipo VARCHAR(50) DEFAULT 'Equipo SIMTELE-RISK',
    estado VARCHAR(20) DEFAULT 'COMPLETADO',
    FOREIGN KEY (escenario_id) REFERENCES escenario(id) ON DELETE CASCADE
);

-- 4. Tabla: ejecucion_metodo (Desempeño del algoritmo numérico evaluado)
CREATE TABLE IF NOT EXISTS ejecucion_metodo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    tolerancia REAL NOT NULL,
    paso REAL,
    max_iter INTEGER,
    convergio BOOLEAN DEFAULT 1,
    tiempo_ms REAL NOT NULL,
    FOREIGN KEY (simulacion_id) REFERENCES simulacion(id) ON DELETE CASCADE
);

-- 5. Tabla: iteracion_resultado (Historial paso a paso de convergencia y errores)
CREATE TABLE IF NOT EXISTS iteracion_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    aproximacion_json TEXT NOT NULL,
    residual REAL,
    error_abs REAL,
    error_rel REAL,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id) ON DELETE CASCADE
);

-- 6. Tabla: resultado_resumen (Métricas globales e interpretación técnica)
CREATE TABLE IF NOT EXISTS resultado_resumen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL,
    referencia TEXT,
    valor_json TEXT NOT NULL,
    metrica_error_json TEXT,
    interpretacion TEXT,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id) ON DELETE CASCADE
);

-- ============================================================
-- POBLADO INICIAL DE DATOS (PRESETS BASE)
-- ============================================================
INSERT OR IGNORE INTO caso_estudio (id, nombre, modelo_version) VALUES 
(1, 'Detención de emergencia de cabinas', '1.0'),
(2, 'Deterioro mecánico y mantenimiento', '1.0'),
(3, 'Oscilaciones por viento', '1.0'),
(4, 'Reconstrucción de señales de sensores', '1.0');

INSERT OR IGNORE INTO escenario (id, caso_id, tipo, parametros_json, fuente_datos) VALUES
(1, 1, 'NORMAL', '{"v0": 12.0, "tr": 0.5, "a": 2.5}', 'Nominal sintético'),
(2, 2, 'NORMAL', '{"alpha": 0.015, "beta": 0.0005, "umbral": 80}', 'Matriz SPD'),
(3, 3, 'NORMAL', '{"m": 1200, "c": 45.0, "F": 350}', 'Viento constante'),
(4, 4, 'NORMAL', '{"nodos": 7, "ruido": 0.02}', 'Sensores sintéticos');