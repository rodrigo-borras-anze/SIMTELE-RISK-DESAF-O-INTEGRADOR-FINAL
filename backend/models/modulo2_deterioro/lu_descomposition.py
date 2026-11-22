import numpy as np

def lu_decomposition_con_pivoteo(A):
    """
    Realiza la descomposición LU con pivoteo parcial: P * A = L * U
    Retorna P, L, U
    """
    n = len(A)
    # Copia de la matriz para no modificar la original
    U = np.array(A, dtype=float)
    L = np.eye(n, dtype=float)
    P = np.eye(n, dtype=float)

    for k in range(n):
        # Pivoteo parcial: buscar el mayor elemento en la columna k desde la fila k en adelante
        max_row = k + np.argmax(np.abs(U[k:, k]))
        
        if max_row != k:
            # Intercambiar filas en U
            U[[k, max_row], :] = U[[max_row, k], :]
            # Intercambiar filas en P
            P[[k, max_row], :] = P[[max_row, k], :]
            # Intercambiar filas en L (solo en las columnas anteriores a k)
            if k > 0:
                L[[k, max_row], :k] = L[[max_row, k], :k]

        # Eliminación Gaussiana
        for i in range(k + 1, n):
            factor = U[i, k] / U[k, k]
            L[i, k] = factor
            U[i, k:] -= factor * U[k, k:]

    return P, L, U

def resolver_sistema_lu(P, L, U, b):
    """
    Resuelve Ly = Pb usando sustitución hacia adelante, 
    y luego Ux = y usando sustitución hacia atrás.
    """
    b_mod = np.dot(P, b)
    n = len(b)
    
    # 1. Sustitución hacia adelante (L y = b_mod)
    y = np.zeros(n)
    for i in range(n):
        y[i] = b_mod[i] - np.dot(L[i, :i], y[:i])
        
    # 2. Sustitución hacia atrás (U x = y)
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - np.dot(U[i, i+1:], x[i+1:])) / U[i, i]
        
    return x