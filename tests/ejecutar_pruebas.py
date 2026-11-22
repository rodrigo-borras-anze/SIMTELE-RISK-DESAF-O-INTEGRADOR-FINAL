import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lu_descomposition import lu_decomposition_con_pivoteo, resolver_sistema_lu
from src.conjugate_gradient import gradiente_conjugado
from src.scenarios_metrics import calcular_metricas_error, evaluar_escenarios

if __name__ == "__main__":
    print("=== EJECUCIÓN DE PRUEBAS - ESTUDIANTE C ===")
    
    # Cargar escenario normal
    escenarios = evaluar_escenarios()
    A = escenarios["normal"]["A"]
    b = escenarios["normal"]["b"]
    kappa = escenarios["normal"]["kappa"]
    x_ref = np.array([1.0, 2.0, -1.0, 1.0])
    
    print(f"\n[1] Número de condición de la matriz A (kappa): {kappa:.4f}")
    
    # Probar LU con pivoteo
    P, L, U = lu_decomposition_con_pivoteo(A)
    x_lu = resolver_sistema_lu(P, L, U, b)
    metricas_lu = calcular_metricas_error(x_ref, x_lu, A, b)
    print(f"\n[2] Solución por Factorización LU: {x_lu}")
    print(f"    Residuo relativo (LU): {metricas_lu['residuo_relativo']:.2e}")
    
    # Probar Gradiente Conjugado
    x_gc, historial, iters = gradiente_conjugado(A, b)
    metricas_gc = calcular_metricas_error(x_ref, x_gc, A, b)
    print(f"\n[3] Solución por Gradiente Conjugado (Iteraciones: {iters}): {x_gc}")
    print(f"    Residuo relativo (GC): {metricas_gc['residuo_relativo']:.2e}")