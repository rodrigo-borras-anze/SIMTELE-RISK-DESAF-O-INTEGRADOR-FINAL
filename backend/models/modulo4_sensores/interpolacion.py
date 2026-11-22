import time
import numpy as np


def _validar_nodos(x_nodos, y_nodos):
    x = np.asarray(x_nodos, dtype=float)
    y = np.asarray(y_nodos, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("x e y deben ser vectores 1D de igual longitud.")
    if len(x) < 2:
        raise ValueError("Se requieren al menos 2 nodos para interpolar.")
    if len(np.unique(x)) != len(x):
        raise ValueError("Los nodos en x deben ser distintos.")
    orden = np.argsort(x)
    return x[orden], y[orden]


def interpolacion_lagrange(x_nodos, y_nodos, x_eval):
    t0 = time.perf_counter()
    x, y = _validar_nodos(x_nodos, y_nodos)
    xe = np.asarray(x_eval, dtype=float)
    n = len(x)
    ye = np.zeros_like(xe, dtype=float)

    for i in range(n):
        L_i = np.ones_like(xe, dtype=float)
        for j in range(n):
            if i != j:
                L_i *= (xe - x[j]) / (x[i] - x[j])
        ye += y[i] * L_i

    return {
        "metodo": "Lagrange",
        "y_aprox": ye,
        "tiempo_ms": (time.perf_counter() - t0) * 1000.0,
        "convergio": True,
    }


def tabla_diferencias_divididas(x, y):
    n = len(x)
    tabla = np.zeros((n, n), dtype=float)
    tabla[:, 0] = y
    for j in range(1, n):
        for i in range(n - j):
            tabla[i, j] = (tabla[i + 1, j - 1] - tabla[i, j - 1]) / (x[i + j] - x[i])
    return tabla[0, :], tabla


def interpolacion_newton(x_nodos, y_nodos, x_eval):
    t0 = time.perf_counter()
    x, y = _validar_nodos(x_nodos, y_nodos)
    xe = np.asarray(x_eval, dtype=float)
    coef, tabla = tabla_diferencias_divididas(x, y)
    n = len(coef)

    # Evaluación anidada tipo Horner
    ye = np.full_like(xe, coef[-1], dtype=float)
    for k in range(n - 2, -1, -1):
        ye = ye * (xe - x[k]) + coef[k]

    return {
        "metodo": "Diferencias Divididas de Newton",
        "y_aprox": ye,
        "coeficientes": coef,
        "tabla": tabla,
        "tiempo_ms": (time.perf_counter() - t0) * 1000.0,
        "convergio": True,
    }


def _resolver_tridiagonal(a, b, c, d):
    """Algoritmo de Thomas desde cero para sistema tridiagonal."""
    n = len(d)
    c_mod = np.zeros(n, dtype=float)
    d_mod = np.zeros(n, dtype=float)
    x = np.zeros(n, dtype=float)

    c_mod[0] = c[0] / b[0]
    d_mod[0] = d[0] / b[0]

    for i in range(1, n):
        denom = b[i] - a[i] * c_mod[i - 1]
        if i < n - 1:
            c_mod[i] = c[i] / denom
        d_mod[i] = (d[i] - a[i] * d_mod[i - 1]) / denom

    x[-1] = d_mod[-1]
    for i in range(n - 2, -1, -1):
        x[i] = d_mod[i] - c_mod[i] * x[i + 1]
    return x


def interpolacion_splines_cubicos(x_nodos, y_nodos, x_eval):
    """Spline cúbico natural (M_0 = M_{n-1} = 0)."""
    t0 = time.perf_counter()
    x, y = _validar_nodos(x_nodos, y_nodos)
    xe = np.asarray(x_eval, dtype=float)
    n = len(x)
    h = np.diff(x)

    M = np.zeros(n, dtype=float)
    if n > 2:
        m = n - 2
        a = np.zeros(m, dtype=float)
        b = np.zeros(m, dtype=float)
        c = np.zeros(m, dtype=float)
        d = np.zeros(m, dtype=float)

        for i in range(m):
            idx = i + 1
            a[i] = h[idx - 1] if i > 0 else 0.0
            b[i] = 2.0 * (h[idx - 1] + h[idx])
            c[i] = h[idx] if i < m - 1 else 0.0
            d[i] = 6.0 * (
                (y[idx + 1] - y[idx]) / h[idx] - (y[idx] - y[idx - 1]) / h[idx - 1]
            )

        M[1:-1] = _resolver_tridiagonal(a, b, c, d)

    ye = np.zeros_like(xe, dtype=float)
    for k, val in enumerate(xe):
        if val <= x[0]:
            i = 0
        elif val >= x[-1]:
            i = n - 2
        else:
            i = max(0, min(int(np.searchsorted(x, val)) - 1, n - 2))

        hi = h[i]
        dx1 = x[i + 1] - val
        dx2 = val - x[i]

        ye[k] = (
            (M[i] / (6.0 * hi)) * (dx1 ** 3)
            + (M[i + 1] / (6.0 * hi)) * (dx2 ** 3)
            + (y[i] / hi - (M[i] * hi) / 6.0) * dx1
            + (y[i + 1] / hi - (M[i + 1] * hi) / 6.0) * dx2
        )

    return {
        "metodo": "Splines Cúbicos Naturales",
        "y_aprox": ye,
        "momentos": M,
        "tiempo_ms": (time.perf_counter() - t0) * 1000.0,
        "convergio": True,
    }