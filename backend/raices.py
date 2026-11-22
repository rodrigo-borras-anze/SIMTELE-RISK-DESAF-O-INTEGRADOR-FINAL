import math
import time

# -------------------------------------------------------------
# MÉTODOS DE BÚSQUEDA DE RAÍCES
# -------------------------------------------------------------

def biseccion(f, a, b, tol=1e-6, max_iter=100):
    t_start = time.perf_counter()
    iteraciones = []
    
    if f(a) * f(b) >= 0:
        return {
            "raiz": None,
            "convergio": False,
            "iteraciones": [],
            "tiempo_ms": (time.perf_counter() - t_start) * 1000,
            "motivo": "Intervalo no válido: f(a) y f(b) tienen el mismo signo"
        }
    
    x_prev = a
    for k in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = f(c)
        err_abs = abs(c - x_prev)
        err_rel = err_abs / abs(c) if abs(c) > 1e-12 else err_abs
        
        iteraciones.append({
            "k": k,
            "x": round(c, 6),
            "residuo": round(abs(fc), 8),
            "error_abs": round(err_abs, 8),
            "error_rel": round(err_rel, 8)
        })
        
        if abs(fc) < tol or err_abs < tol:
            return {
                "raiz": round(c, 6),
                "convergio": True,
                "iteraciones": iteraciones,
                "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
                "motivo": f"Convergencia lograda en {k} iteraciones"
            }
            
        if f(a) * fc < 0:
            b = c
        else:
            a = c
        x_prev = c
        
    return {
        "raiz": round((a + b) / 2.0, 6),
        "convergio": False,
        "iteraciones": iteraciones,
        "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
        "motivo": "Se alcanzó el número máximo de iteraciones"
    }

def newton_raphson(f, df, x0, tol=1e-6, max_iter=100):
    t_start = time.perf_counter()
    iteraciones = []
    x_k = x0
    
    for k in range(1, max_iter + 1):
        df_val = df(x_k)
        if abs(df_val) < 1e-12:
            return {
                "raiz": round(x_k, 6),
                "convergio": False,
                "iteraciones": iteraciones,
                "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
                "motivo": "Derivada cercana a cero (frenado por raíz múltiple)"
            }
            
        x_next = x_k - f(x_k) / df_val
        err_abs = abs(x_next - x_k)
        err_rel = err_abs / abs(x_next) if abs(x_next) > 1e-12 else err_abs
        
        iteraciones.append({
            "k": k,
            "x": round(x_next, 6),
            "residuo": round(abs(f(x_next)), 8),
            "error_abs": round(err_abs, 8),
            "error_rel": round(err_rel, 8)
        })
        
        if abs(f(x_next)) < tol or err_abs < tol:
            return {
                "raiz": round(x_next, 6),
                "convergio": True,
                "iteraciones": iteraciones,
                "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
                "motivo": f"Convergencia alcanzada en {k} iteraciones"
            }
            
        x_k = x_next
        
    return {
        "raiz": round(x_k, 6),
        "convergio": False,
        "iteraciones": iteraciones,
        "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
        "motivo": "Máximo de iteraciones alcanzado sin convergencia"
    }

def secante(f, x0, x1, tol=1e-6, max_iter=100):
    t_start = time.perf_counter()
    iteraciones = []
    
    for k in range(1, max_iter + 1):
        f0 = f(x0)
        f1 = f(x1)
        
        if abs(f1 - f0) < 1e-12:
            return {
                "raiz": round(x1, 6),
                "convergio": False,
                "iteraciones": iteraciones,
                "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
                "motivo": "División por cero en fórmula de secante"
            }
            
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        err_abs = abs(x2 - x1)
        err_rel = err_abs / abs(x2) if abs(x2) > 1e-12 else err_abs
        
        iteraciones.append({
            "k": k,
            "x": round(x2, 6),
            "residuo": round(abs(f(x2)), 8),
            "error_abs": round(err_abs, 8),
            "error_rel": round(err_rel, 8)
        })
        
        if abs(f(x2)) < tol or err_abs < tol:
            return {
                "raiz": round(x2, 6),
                "convergio": True,
                "iteraciones": iteraciones,
                "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
                "motivo": f"Convergencia alcanzada en {k} iteraciones"
            }
            
        x0 = x1
        x1 = x2
        
    return {
        "raiz": round(x1, 6),
        "convergio": False,
        "iteraciones": iteraciones,
        "tiempo_ms": round((time.perf_counter() - t_start) * 1000, 4),
        "motivo": "Máximo de iteraciones alcanzado"
    }

# -------------------------------------------------------------
# SIMULACIÓN MÓDULO 1: Detención de Emergencia
# -------------------------------------------------------------

def simular_modulo1_raices(escenario="NORMAL"):
    esc = escenario.upper()
    v0 = 12.0
    
    if esc == "NORMAL":
        a_const = 2.4
        t_det = v0 / a_const
        f_v = lambda t: v0 - a_const * t
        df_v = lambda t: -a_const
    elif esc == "ESTRES":
        f_v = lambda t: v0 * math.exp(-0.4 * t) - 0.5
        df_v = lambda t: -0.4 * v0 * math.exp(-0.4 * t)
        t_det = 7.94
    elif esc == "MAL_CONDICIONADO":
        t_det = 6.0
        m_mult = 3
        f_v = lambda t: (1.0 - t / t_det)**m_mult if t <= t_det else 0.0
        df_v = lambda t: (-m_mult / t_det) * ((1.0 - t / t_det)**(m_mult - 1)) if t <= t_det else 0.0
    else:
        raise ValueError("Escenario no válido")
        
    res_bis = biseccion(f_v, 0.0, 10.0)
    res_bis["metodo"] = "Bisección"
    res_bis["tolerancia"] = 1e-6

    res_nr = newton_raphson(f_v, df_v, 1.0)
    res_nr["metodo"] = "Newton-Raphson"
    res_nr["tolerancia"] = 1e-6

    res_sec = secante(f_v, 0.0, 1.0)
    res_sec["metodo"] = "Secante"
    res_sec["tolerancia"] = 1e-6

    t_vals = [round(i * 0.2, 1) for i in range(51)]
    v_vals = [round(max(0.0, f_v(t)), 4) for t in t_vals]

    return {
        "escenario": esc,
        "metodos": [res_bis, res_nr, res_sec],
        "graficos": {
            "curva_velocidad": {"t": t_vals, "v": v_vals}
        }
    }

# -------------------------------------------------------------
# SIMULACIÓN MÓDULO 2: Cruce de Umbral de Desgaste
# -------------------------------------------------------------

def simular_modulo2_umbral():
    D_umbral = 0.80
    f_D = lambda t: (0.1 + 0.02 * t + 0.001 * (t**2) + 0.00005 * (t**3)) - D_umbral
    df_D = lambda t: 0.02 + 0.002 * t + 0.00015 * (t**2)

    res_nr = newton_raphson(f_D, df_D, 10.0)
    res_nr["metodo"] = "Newton-Raphson"
    res_nr["tolerancia"] = 1e-6

    t_vals = [i for i in range(0, 61, 2)]
    D_vals = [round(0.1 + 0.02 * t + 0.001 * (t**2) + 0.00005 * (t**3), 4) for t in t_vals]

    return {
        "metodos": [res_nr],
        "graficos": {
            "curva_deterioro": {"t": t_vals, "D": D_vals, "umbral": D_umbral}
        }
    }