import numpy as np

def gradiente_conjugado(A, b, x0=None, tol=1e-6, max_iter=200):
    """
    Resuelve el sistema Ax = b usando el método iterativo de Gradiente Conjugado.
    """
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = np.array(x0, dtype=float)
        
    r = b - np.dot(A, x)
    p = r.copy()
    rs_old = np.dot(r, r)
    
    historial = []

    for k in range(max_iter):
        Ap = np.dot(A, p)
        alpha = rs_old / np.dot(p, Ap)
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = np.dot(r, r)
        
        # Guardar registro para la tabla de iteraciones
        residual_norm = np.linalg.norm(r, 2)
        residual_relativo = residual_norm / np.linalg.norm(b, 2)
        historial.append({"iteracion": k + 1, "x": x.copy(), "residual_relativo": residual_relativo})
        
        if np.sqrt(rs_new) < tol:
            break
            
        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    return x, historial, k + 1