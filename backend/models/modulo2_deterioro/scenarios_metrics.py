import numpy as np

def calcular_metricas_error(x_ref, x_aprox, A, b):
    """
    Calcula el error absoluto, relativo, porcentual y el residual.
    """
    e_abs = np.abs(x_ref - x_aprox)
    e_abs_inf = np.max(e_abs)
    
    # Evitar división por cero si x_ref es 0
    e_rel = np.where(x_ref != 0, e_abs / np.abs(x_ref), 0)
    e_porc = e_rel * 100
    
    # Residuo r = b - A*x_aprox
    r = b - np.dot(A, x_aprox)
    res_relativo = np.linalg.norm(r, 2) / np.linalg.norm(b, 2)
    
    return {
        "error_absoluto": e_abs,
        "error_absoluto_inf": e_abs_inf,
        "error_relativo": e_rel,
        "error_porcentual": e_porc,
        "residuo_relativo": res_relativo
    }

def evaluar_escenarios():
    """
    Define y evalúa los 3 escenarios requeridos para el sistema lineal (Módulo 2).
    """
    # Sistema Base (Escenario Normal - Bien condicionado)
    # Matriz simétrica definida positiva 4x4 vinculada a la calibración de coeficientes D(t)
    A_normal = np.array([
        [10.0, -1.0,  2.0,  0.0],
        [-1.0, 11.0, -1.0,  3.0],
        [ 2.0, -1.0, 10.0, -1.0],
        [ 0.0,  3.0, -1.0,  8.0]
    ])
    x_ref = np.array([1.0, 2.0, -1.0, 1.0])
    b_normal = np.dot(A_normal, x_ref)
    
    # Número de condición kappa(A) usando norma 2
    kappa_normal = np.linalg.cond(A_normal, 2)
    
    # Escenario de Estrés: Carga computacional o iteraciones forzadas / perturbación leve en b
    b_estres = b_normal + np.array([0.0, 0.25, 0.0, 0.0]) # Perturbación descrita en el proyecto
    
    # Escenario Mal Condicionado: Modificar matriz para elevar drásticamente kappa(A)
    A_mal = np.array([
        [10.0, 10.0,  0.0,  0.0],
        [10.0, 10.01, 0.0,  0.0],
        [ 0.0,  0.0, 10.0, -1.0],
        [ 0.0,  0.0, -1.0,  8.0]
    ])
    kappa_mal = np.linalg.cond(A_mal, 2)
    
    return {
        "normal": {"A": A_normal, "b": b_normal, "kappa": kappa_normal},
        "estres": {"A": A_normal, "b": b_estres, "kappa": kappa_normal},
        "mal_condicionado": {"A": A_mal, "b": np.dot(A_mal, x_ref), "kappa": kappa_mal}
    }
