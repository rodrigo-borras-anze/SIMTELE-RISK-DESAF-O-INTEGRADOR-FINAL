import numpy as np

def calcular_metricas_error(x_ref, x_aprox, A=None, b=None):
    """Calcula errores absoluto, relativo, porcentual y residuo relativo."""
    x_ref = np.array(x_ref, dtype=float)
    x_aprox = np.array(x_aprox, dtype=float)
    
    e_abs = np.abs(x_ref - x_aprox)
    e_abs_inf = float(np.max(e_abs))
    e_rel = np.where(x_ref != 0, e_abs / np.abs(x_ref), 0.0)
    e_porc = e_rel * 100.0
    
    res_relativo = None
    if A is not None and b is not None:
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float)
        r = b - np.dot(A, x_aprox)
        res_relativo = float(np.linalg.norm(r, 2) / np.linalg.norm(b, 2))
        
    return {
        "error_absoluto_inf": e_abs_inf,
        "error_relativo_max": float(np.max(e_rel)),
        "error_porcentual_max": float(np.max(e_porc)),
        "residuo_relativo": res_relativo
    }