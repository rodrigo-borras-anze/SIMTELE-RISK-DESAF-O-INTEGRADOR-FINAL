import math
import time
import numpy as np

# -------------------------------------------------------------
# ALGORITMOS DE INTERPOLACIÓN (MÓDULO 4)
# -------------------------------------------------------------

def interpolacion_lagrange(x_nodos, y_nodos, x_eval):
    """Calcula el polinomio interpolador de Lagrange en x_eval."""
    n = len(x_nodos)
    resultado = []
    for x in x_eval:
        y_val = 0.0
        for i in range(n):
            L_i = 1.0
            for j in range(n):
                if i != j:
                    L_i *= (x - x_nodos[j]) / (x_nodos[i] - x_nodos[j])
            y_val += y_nodos[i] * L_i
        resultado.append(y_val)
    return resultado

# -------------------------------------------------------------
# SIMULACIÓN MÓDULO 4: Reconstrucción de Sensores
# -------------------------------------------------------------

def simular_modulo4_sensores(escenario="NORMAL"):
    esc = escenario.upper()
    t_start = time.perf_counter()
    
    # Señal sintética de referencia: y(t) = sin(t)
    t_full = np.linspace(0, 6.28, 50)
    y_full = np.sin(t_full)
    
    if esc == "NORMAL":
        indices_nodos = [0, 5, 11, 16, 22, 27, 33, 38, 44, 49]
    elif esc == "ESTRES":
        indices_nodos = [0, 12, 25, 37, 49]
    elif esc == "MAL_CONDICIONADO":
        indices_nodos = [0, 1, 2, 3, 25, 46, 47, 48, 49]
    else:
        indices_nodos = [0, 10, 20, 30, 40, 49]

    t_nodos = t_full[indices_nodos]
    y_nodos = y_full[indices_nodos]
    
    # Reconstrucción con Lagrange
    y_rec = interpolacion_lagrange(t_nodos, y_nodos, t_full)
    
    # Error absoluto máximo respecto a la señal pura
    err_abs_max = float(np.max(np.abs(y_full - y_rec)))
    tiempo_ms = round((time.perf_counter() - t_start) * 1000.0, 4)
    
    return {
        "caso_id": 4,
        "escenario": esc,
        "metodos": [{
            "metodo": "Interpolación de Lagrange",
            "tolerancia": 1e-4,
            "tiempo_ms": tiempo_ms,
            "convergio": True,
            "valor_final": {"error_max_reconstruccion": round(err_abs_max, 6)},
            "iteraciones": []
        }],
        "graficos": {
            "curva_sensores": {
                "t": [round(val, 2) for val in t_full.tolist()],
                "y_original": [round(val, 4) for val in y_full.tolist()],
                "y_reconstruida": [round(val, 4) for val in y_rec],
                "t_nodos": [round(val, 2) for val in t_nodos.tolist()],
                "y_nodos": [round(val, 4) for val in y_nodos.tolist()]
            }
        }
    }