"""
SIMTELE-RISK | Integrante 2
MODULO 3 (Oscilaciones por viento) + apoyo al MODULO 1 (Deteccion de cabinas)
EDO (RK2 Heun, RK4) e Integracion (Trapecio, Simpson 1/3, Romberg).
Todo programado desde cero (sin NumPy ni SciPy).

Uso:
    python modulo3_completo.py                  consola + graficos + API
    python modulo3_completo.py --sin-servidor   consola + graficos (sin Flask)
    python modulo3_completo.py --sin-graficos   consola + API
    python modulo3_completo.py --mostrar        ademas abre las ventanas de graficos
    python modulo3_completo.py --json           guarda resultados_modulo3.json

Dependencias: flask (API) y matplotlib (graficos). Ambas son opcionales
para correr la consola.
"""
import json
import math
import os
import sys
import time

try:
    from flask import Flask, jsonify
except ImportError:          # permite correr consola y graficos sin Flask
    Flask = None
    jsonify = None

# ============================================================
# 0) UTILIDADES DE ERROR (teoria de errores transversal)
# ============================================================

def error_abs(ref, aprox):
    return abs(ref - aprox)


def error_rel(ref, aprox, eps=1e-12):
    """Error relativo; devuelve None si la referencia es (casi) cero."""
    if abs(ref) < eps:
        return None
    return abs(ref - aprox) / abs(ref)


def _finito(valores):
    return all(math.isfinite(v) for v in valores)


# ============================================================
# 1) METODOS NUMERICOS (desde cero)
# ============================================================

def f_oscilador(t, y, m, c, k, F):
    """Ecuacion del oscilador: y = [x, v]; x' = v; v' = (F(t) - c v - k x)/m."""
    x, v = y
    return [v, (F(t) - c * v - k * x) / m]


def rk2_heun(f, t0, y0, tf, h, params):
    """Runge-Kutta de 2.o orden, variante de Heun (trapezoidal)."""
    ts, ys = [t0], [list(y0)]
    y = list(y0)
    n = int(round((tf - t0) / h))
    for i in range(n):
        t = t0 + i * h
        k1 = f(t, y, *params)
        y_pred = [y[j] + h * k1[j] for j in range(len(y))]
        k2 = f(t + h, y_pred, *params)
        y = [y[j] + (h / 2.0) * (k1[j] + k2[j]) for j in range(len(y))]
        ts.append(t0 + (i + 1) * h)
        ys.append(list(y))
    return ts, ys


def rk4(f, t0, y0, tf, h, params):
    """Runge-Kutta clasico de 4.o orden."""
    ts, ys = [t0], [list(y0)]
    y = list(y0)
    n = int(round((tf - t0) / h))
    for i in range(n):
        t = t0 + i * h
        k1 = f(t, y, *params)
        y2 = [y[j] + 0.5 * h * k1[j] for j in range(len(y))]
        k2 = f(t + 0.5 * h, y2, *params)
        y3 = [y[j] + 0.5 * h * k2[j] for j in range(len(y))]
        k3 = f(t + 0.5 * h, y3, *params)
        y4 = [y[j] + h * k3[j] for j in range(len(y))]
        k4 = f(t + h, y4, *params)
        y = [y[j] + (h / 6.0) * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j])
             for j in range(len(y))]
        ts.append(t0 + (i + 1) * h)
        ys.append(list(y))
    return ts, ys


# ---- Integracion sobre una funcion f(x) ----

def trapecio_compuesto(f, a, b, n):
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += 2 * f(a + i * h)
    return (h / 2.0) * s


def simpson13_compuesto(f, a, b, n):
    if n % 2 != 0:
        raise ValueError("n debe ser par")
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 == 1 else 2) * f(a + i * h)
    return (h / 3.0) * s


def romberg_tabla(f, a, b, nivel_max=5, tol=1e-12):
    """Tabla de Romberg R[i][j]. Devuelve (tabla, nivel_final)."""
    R = [[0.0] * (nivel_max + 1) for _ in range(nivel_max + 1)]
    h = b - a
    R[0][0] = 0.5 * h * (f(a) + f(b))
    nivel = 0
    for i in range(1, nivel_max + 1):
        h /= 2.0
        suma = sum(f(a + k * h) for k in range(1, 2 ** i, 2))
        R[i][0] = 0.5 * R[i - 1][0] + h * suma
        for j in range(1, i + 1):
            R[i][j] = R[i][j - 1] + (R[i][j - 1] - R[i - 1][j - 1]) / (4 ** j - 1)
        nivel = i
        if abs(R[i][i] - R[i - 1][i - 1]) < tol:
            break
    return R, nivel


def romberg(f, a, b, nivel_max=5, tol=1e-12):
    R, nivel = romberg_tabla(f, a, b, nivel_max, tol)
    return R[nivel][nivel]


# ---- Integracion sobre datos equiespaciados (solucion numerica) ----

def trapecio_datos(y, h):
    return h * ((y[0] + y[-1]) / 2.0 + sum(y[1:-1]))


def simpson_datos(y, h):
    n = len(y) - 1
    if n % 2 != 0:
        raise ValueError("Simpson 1/3 requiere un numero par de subintervalos")
    return (h / 3.0) * (y[0] + y[-1] + 4 * sum(y[1:-1:2]) + 2 * sum(y[2:-1:2]))


def romberg_datos(y, h):
    """Romberg sobre datos; requiere n = 2^m subintervalos. Devuelve (tabla, valor)."""
    n = len(y) - 1
    m = int(round(math.log2(n)))
    if 2 ** m != n:
        raise ValueError("Romberg sobre datos requiere n potencia de 2")
    R = [[0.0] * (m + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        paso = 2 ** (m - i)
        R[i][0] = trapecio_datos(y[::paso], h * paso)
        for j in range(1, i + 1):
            R[i][j] = R[i][j - 1] + (R[i][j - 1] - R[i - 1][j - 1]) / (4 ** j - 1)
    return R, R[m][m]


def refinamiento_integral(f, a, b, ref, kmax=12):
    """Tabla de refinamiento (n = 2, 4, ..., 2^kmax) con error de cada metodo."""
    n_max = 2 ** kmax
    h = (b - a) / n_max
    ys = [f(a + i * h) for i in range(n_max + 1)]
    R, _ = romberg_datos(ys, h)
    filas = []
    for i in range(1, kmax + 1):
        paso = 2 ** (kmax - i)
        sub, hs = ys[::paso], h * paso
        t_val, s_val, r_val = trapecio_datos(sub, hs), simpson_datos(sub, hs), R[i][i]
        filas.append({"n": 2 ** i, "h": hs,
                      "trapecio": t_val, "error_trapecio": error_abs(ref, t_val),
                      "simpson": s_val, "error_simpson": error_abs(ref, s_val),
                      "romberg": r_val, "error_romberg": error_abs(ref, r_val)})
    return filas


# ============================================================
# 2) MODELO Y SOLUCIONES ANALITICAS
# ============================================================

def solucion_analitica(t, x0, v0, m, c, k):
    """Caso libre y subamortiguado: x(t) = e^(-z w0 t)[C1 cos(wd t) + C2 sin(wd t)]."""
    return solucion_analitica_forzada(t, x0, v0, m, c, k, 0.0, 0.0)[0]


def solucion_analitica_forzada(t, x0, v0, m, c, k, F0, wf):
    """Solucion exacta de m x'' + c x' + k x = F0 sin(wf t), subamortiguado.
    Devuelve (x, v). Con F0 = 0 es la vibracion libre."""
    w0 = math.sqrt(k / m)
    z = c / (2.0 * math.sqrt(k * m))
    if z >= 1.0:
        raise ValueError("Requiere zeta < 1 (caso subamortiguado)")
    wd = w0 * math.sqrt(1.0 - z * z)
    a = z * w0
    if F0 != 0.0:
        den = (k - m * wf ** 2) ** 2 + (c * wf) ** 2
        A = F0 * (k - m * wf ** 2) / den
        B = -F0 * c * wf / den
    else:
        A = B = 0.0
    C1 = x0 - B
    C2 = (v0 - A * wf + a * C1) / wd
    e = math.exp(-a * t)
    cw, sw = math.cos(wd * t), math.sin(wd * t)
    xh = e * (C1 * cw + C2 * sw)
    vh = e * ((-a * C1 + wd * C2) * cw + (-a * C2 - wd * C1) * sw)
    xp = A * math.sin(wf * t) + B * math.cos(wf * t)
    vp = A * wf * math.cos(wf * t) - B * wf * math.sin(wf * t)
    return xp + xh, vp + vh


def amplitud_permanente(m, c, k, F0, w):
    """Amplitud de la respuesta en regimen permanente: X(w)."""
    return F0 / math.sqrt((k - m * w * w) ** 2 + (c * w) ** 2)


def sensibilidad_amplitud(m, c, k, F0, w, delta=0.01):
    """Cuanto cambia X cuando w cambia un 'delta' relativo (cond. del problema)."""
    X1 = amplitud_permanente(m, c, k, F0, w)
    X2 = amplitud_permanente(m, c, k, F0, w * (1 + delta))
    cambio_rel = abs(X2 - X1) / X1
    return {"w": w, "w_perturbada": w * (1 + delta), "X": X1, "X_perturbada": X2,
            "cambio_relativo_entrada": delta, "cambio_relativo_salida": cambio_rel,
            "factor_amplificacion": cambio_rel / delta}


# ============================================================
# 3) ESCENARIOS DEL MODULO 3
# ============================================================

W0 = math.sqrt(4000.0 / 800.0)   # frecuencia natural de la estructura (rad/s)

PARAMETROS = {
    # NORMAL: vibracion libre, paso fino. h = 0.01, n = 1024 (potencia de 2)
    "NORMAL": dict(m=800.0, c=120.0, k=4000.0, x0=1.0, v0=0.0, F0=0.0, wf=0.0,
                   T=10.24, n=1024),
    # ESTRES: viento fuerte cerca de la resonancia, paso grande y mas tiempo
    "ESTRES": dict(m=800.0, c=120.0, k=4000.0, x0=0.0, v0=0.0, F0=500.0, wf=2.0,
                   T=16.0, n=64),
    # MAL CONDICIONADO: amortiguamiento casi nulo y viento a 0.99 w0.
    # Subexperimento de SENSIBILIDAD: un 1% de cambio en wf cambia mucho la amplitud.
    "MAL_CONDICIONADO": dict(m=800.0, c=0.5, k=4000.0, x0=0.0, v0=0.0, F0=500.0,
                             wf=0.99 * W0, T=40.96, n=2048),
}


def _decimar(lista, max_pts):
    if len(lista) <= max_pts:
        return list(range(len(lista)))
    paso = len(lista) / float(max_pts)
    idx = sorted(set(int(i * paso) for i in range(max_pts)))
    if idx[-1] != len(lista) - 1:
        idx.append(len(lista) - 1)
    return idx


def _filas_iteraciones(ts, xs, vs, xr, vr, max_filas=200):
    """Formato para la tabla iteracion_resultado de la BD."""
    filas = []
    for k in _decimar(ts, max_filas):
        filas.append({"numero": k,
                      "aproximacion": {"t": ts[k], "x": xs[k], "v": vs[k]},
                      "residual": abs(vs[k] - vr[k]),   # error de la 2.a variable de estado
                      "error_abs": error_abs(xr[k], xs[k]),
                      "error_rel": error_rel(xr[k], xs[k])})
    return filas


def _ejecutar_metodo(nombre, metodo, p, params, ref_x, ref_v, h):
    t0 = time.perf_counter()
    ts, ys = metodo(f_oscilador, 0.0, [p["x0"], p["v0"]], p["T"], h, params)
    ms = (time.perf_counter() - t0) * 1000.0
    xs, vs = [y[0] for y in ys], [y[1] for y in ys]
    errs = [abs(xs[i] - ref_x[i]) for i in range(len(xs))]
    max_ref = max(abs(r) for r in ref_x)
    estable = _finito(xs) and max(abs(x) for x in xs) < 10 * max_ref
    return {"metodo": nombre, "paso": h, "convergio": estable, "tiempo_ms": ms,
            "ts": ts, "xs": xs, "vs": vs, "error_max": max(errs), "errores": errs,
            "error_max_rel": error_rel(max_ref, max(abs(x) for x in xs)),
            "amplitud_max": max(abs(x) for x in xs),
            "amplificacion": max(abs(x) for x in xs) / max_ref,
            "iteraciones": _filas_iteraciones(ts, xs, vs, ref_x, ref_v)}


def _integrales_sobre(xs, h):
    x2 = [x * x for x in xs]
    _, rom = romberg_datos(x2, h)
    return {"trapecio": trapecio_datos(x2, h), "simpson": simpson_datos(x2, h),
            "romberg": rom}


def ejecutar_escenario(tipo):
    """Corre RK2 y RK4, integra x^2 y calcula errores frente a la solucion exacta."""
    p = PARAMETROS[tipo]
    m, c, k = p["m"], p["c"], p["k"]
    F = lambda t: p["F0"] * math.sin(p["wf"] * t)
    params = (m, c, k, F)
    h = p["T"] / p["n"]

    def exacta(t):
        return solucion_analitica_forzada(t, p["x0"], p["v0"], m, c, k, p["F0"], p["wf"])

    ts_ref = [i * h for i in range(p["n"] + 1)]
    ref = [exacta(t) for t in ts_ref]
    ref_x, ref_v = [r[0] for r in ref], [r[1] for r in ref]

    rk2_res = _ejecutar_metodo("RK2 (Heun)", rk2_heun, p, params, ref_x, ref_v, h)
    rk4_res = _ejecutar_metodo("RK4", rk4, p, params, ref_x, ref_v, h)

    # Referencia de la integral de x^2: Simpson muy fino sobre la solucion exacta
    f_int = lambda t: exacta(t)[0] ** 2
    n_ref = 2 ** 17
    ref_int = simpson13_compuesto(f_int, 0.0, p["T"], n_ref)

    def con_error(valores):
        return {mt: {"valor": v, "error_abs": error_abs(ref_int, v),
                     "error_rel": error_rel(ref_int, v)} for mt, v in valores.items()}

    int_rk4 = _integrales_sobre(rk4_res["xs"], h)
    int_rk2 = _integrales_sobre(rk2_res["xs"], h)

    res = {
        "escenario": tipo,
        "parametros": dict(p, h=h, w0=W0, zeta=c / (2 * math.sqrt(k * m))),
        "rk2": {kk: vv for kk, vv in rk2_res.items() if kk != "iteraciones"},
        "rk4": {kk: vv for kk, vv in rk4_res.items() if kk != "iteraciones"},
        "iteraciones": {"rk2": rk2_res["iteraciones"], "rk4": rk4_res["iteraciones"]},
        "integral": int_rk4,                      # x^2 integrada sobre la solucion RK4
        "integral_rk2": int_rk2,
        "integral_errores": {"rk4": con_error(int_rk4), "rk2": con_error(int_rk2)},
        "integral_referencia": {"valor": ref_int,
                                "metodo": "Simpson 1/3 sobre la solucion exacta, n = %d" % n_ref},
        "refinamiento": refinamiento_integral(f_int, 0.0, p["T"], ref_int, kmax=12),
        "analitica": ref_x,
    }
    if tipo == "MAL_CONDICIONADO":
        res["sensibilidad"] = sensibilidad_amplitud(m, c, k, p["F0"], p["wf"], 0.01)
    return res


def escenario_normal():
    return ejecutar_escenario("NORMAL")


def escenario_estres():
    return ejecutar_escenario("ESTRES")


def escenario_mal_condicionado():
    return ejecutar_escenario("MAL_CONDICIONADO")


# ============================================================
# 4) APOYO AL MODULO 1 (detencion de cabinas)
# ============================================================

def f_frenado(t, y, a0, beta):
    """x' = v ; v' = -a0 (1 + beta t). Con beta = 0 la desaceleracion es constante."""
    return [y[1], -a0 * (1.0 + beta * t)]


def modulo1_apoyo(nombre, v0, a0, beta, tr, n=256):
    """RK2/RK4 con desaceleracion variable + posicion por integracion de v(t).
    El tiempo de detencion t_det es analitico; el Integrante 1 puede reemplazarlo
    por la raiz que calculen sus metodos (biseccion, Newton, secante)."""
    t_det = v0 / a0 if beta == 0 else (-1 + math.sqrt(1 + 2 * beta * v0 / a0)) / beta
    x_ex = lambda t: v0 * t - a0 * (t * t / 2 + beta * t ** 3 / 6)
    v_ex = lambda t: v0 - a0 * (t + beta * t * t / 2)
    dist_frenado = x_ex(t_det)
    h = t_det / n
    params = (a0, beta)
    out = {"nombre": nombre, "parametros": dict(v0=v0, a0=a0, beta=beta, tr=tr, n=n, h=h),
           "t_detencion": t_det, "tiempo_total": tr + t_det,
           "distancia_frenado_ref": dist_frenado,
           "distancia_total_ref": v0 * tr + dist_frenado, "metodos": {}}
    for nom, met in (("RK2 (Heun)", rk2_heun), ("RK4", rk4)):
        ts, ys = met(f_frenado, 0.0, [0.0, v0], t_det, h, params)
        vs = [y[1] for y in ys]
        integ = {"trapecio": trapecio_datos(vs, h), "simpson": simpson_datos(vs, h),
                 "romberg": romberg_datos(vs, h)[1]}
        out["metodos"][nom] = {
            "ts": ts, "xs": [y[0] for y in ys], "vs": vs,
            "x_final": ys[-1][0], "v_final": ys[-1][1],
            "error_posicion": error_abs(dist_frenado, ys[-1][0]),
            "posicion_por_integracion": {
                mt: {"valor": v, "error_abs": error_abs(dist_frenado, v)}
                for mt, v in integ.items()}}
    return out


def casos_modulo1():
    return {"constante": modulo1_apoyo("Desaceleracion constante", 12.0, 2.5, 0.0, 0.5),
            "variable": modulo1_apoyo("Desaceleracion variable", 12.0, 2.5, 0.2, 0.5)}


# ============================================================
# 5) PRUEBAS CON SOLUCION ANALITICA
# ============================================================

def pruebas_analiticas():
    pruebas = []

    def reg(nombre, esperado, obtenido, tol, detalle=""):
        e = abs(esperado - obtenido)
        pruebas.append({"prueba": nombre, "esperado": esperado, "obtenido": obtenido,
                        "error_abs": e, "tolerancia": tol, "pasa": e <= tol,
                        "detalle": detalle})

    # 1) Integral de x^2 en [0, 2] = 8/3 (n = 8)
    g = lambda x: x * x
    reg("Trapecio: integral de x^2 en [0,2], n=8", 8 / 3, trapecio_compuesto(g, 0, 2, 8),
        0.03, "error teorico = (b-a) h^2 f''/12 = 0.0208")
    reg("Simpson 1/3: integral de x^2 en [0,2], n=8", 8 / 3, simpson13_compuesto(g, 0, 2, 8), 1e-12)
    reg("Romberg: integral de x^2 en [0,2], nivel 4", 8 / 3, romberg(g, 0, 2, 4), 1e-12)

    # 2) Orden de convergencia de RK2 y RK4 con y' = -y, y(0)=1, t=1
    fy = lambda t, y: [-y[0]]
    ex = math.exp(-1.0)
    for nombre, met, orden in (("RK2 (Heun)", rk2_heun, 2), ("RK4", rk4, 4)):
        e1 = abs(met(fy, 0.0, [1.0], 1.0, 0.1, ())[1][-1][0] - ex)
        e2 = abs(met(fy, 0.0, [1.0], 1.0, 0.05, ())[1][-1][0] - ex)
        reg("%s: razon de errores al reducir h a la mitad" % nombre, 2 ** orden, e1 / e2,
            0.5 if orden == 2 else 2.0,
            "debe ser cercana a 2^%d" % orden)

    # 3) RK4 contra la solucion libre exacta
    r = escenario_normal()
    reg("RK4 vs solucion analitica libre (error maximo)", 0.0, r["rk4"]["error_max"], 1e-6)

    # 4) Solucion forzada exacta vs RK4 con paso muy fino
    p = PARAMETROS["ESTRES"]
    F = lambda t: p["F0"] * math.sin(p["wf"] * t)
    ts, ys = rk4(f_oscilador, 0.0, [0.0, 0.0], 4.0, 1e-3, (p["m"], p["c"], p["k"], F))
    e = max(abs(ys[i][0] - solucion_analitica_forzada(ts[i], 0, 0, p["m"], p["c"], p["k"], p["F0"], p["wf"])[0])
            for i in range(0, len(ts), 100))
    reg("Solucion analitica forzada vs RK4 (h=0.001)", 0.0, e, 1e-8)

    # 5) La columna 2 de Romberg coincide con Simpson
    R, _ = romberg_tabla(g, 0, 2, 4, tol=0.0)
    reg("Romberg R[3][1] = Simpson con n=8", simpson13_compuesto(g, 0, 2, 8), R[3][1], 1e-12)
    return pruebas


# ============================================================
# 6) CONSOLA
# ============================================================

def probar_en_consola(resultados=None):
    resultados = resultados or obtener_todos()
    print("=" * 66)
    print("MODULO 3: OSCILACIONES POR VIENTO")
    print("=" * 66)
    for tipo, res in resultados.items():
        p = res["parametros"]
        print("\n--- Escenario %s  (h = %.4g, n = %d, zeta = %.5f) ---"
              % (tipo, p["h"], p["n"], p["zeta"]))
        for clave, nom in (("rk2", "RK2"), ("rk4", "RK4")):
            r = res[clave]
            print("  %s  error max = %.3e | amplitud max = %.4f | amplificacion = %.3f | estable = %s"
                  % (nom, r["error_max"], r["amplitud_max"], r["amplificacion"], r["convergio"]))
        ref = res["integral_referencia"]["valor"]
        print("  Integral de x^2 (referencia exacta) = %.8f" % ref)
        for mt in ("trapecio", "simpson", "romberg"):
            e = res["integral_errores"]["rk4"][mt]
            print("    %-9s sobre RK4: %.8f  (error abs = %.2e)" % (mt, e["valor"], e["error_abs"]))
        if "sensibilidad" in res:
            s = res["sensibilidad"]
            print("  SENSIBILIDAD: un cambio de %.0f%% en wf cambia la amplitud permanente de %.3f a %.3f"
                  " (factor de amplificacion = %.1f)"
                  % (100 * s["cambio_relativo_entrada"], s["X"], s["X_perturbada"],
                     s["factor_amplificacion"]))
    print("\n--- Apoyo al Modulo 1 ---")
    for clave, c in casos_modulo1().items():
        print("  %s: t_det = %.4f s, distancia de frenado = %.4f m, distancia total = %.4f m"
              % (c["nombre"], c["t_detencion"], c["distancia_frenado_ref"], c["distancia_total_ref"]))
        for nom, m in c["metodos"].items():
            print("     %-10s error posicion = %.2e | Simpson sobre v(t): error = %.2e"
                  % (nom, m["error_posicion"], m["posicion_por_integracion"]["simpson"]["error_abs"]))
    print("\n--- Pruebas con solucion analitica ---")
    for pr in pruebas_analiticas():
        print("  [%s] %s -> esperado %.6g, obtenido %.6g"
              % ("OK " if pr["pasa"] else "FALLA", pr["prueba"], pr["esperado"], pr["obtenido"]))


# ============================================================
# 7) GRAFICOS (matplotlib)
# ============================================================

def generar_graficos(resultados=None, carpeta="graficos_modulo3", mostrar=False):
    import matplotlib
    if not mostrar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    resultados = resultados or obtener_todos()
    os.makedirs(carpeta, exist_ok=True)
    archivos = []
    nombres = {"NORMAL": "Normal", "ESTRES": "Estres", "MAL_CONDICIONADO": "Mal condicionado"}

    for tipo, res in resultados.items():
        ts = res["rk4"]["ts"]
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
        ax[0].plot(ts, res["analitica"], "k-", lw=2, label="Solucion exacta")
        ax[0].plot(ts, res["rk2"]["xs"], "r--", lw=1.2, label="RK2 (Heun)")
        ax[0].plot(ts, res["rk4"]["xs"], "b:", lw=1.8, label="RK4")
        ax[0].set_title("Escenario %s: desplazamiento x(t)" % nombres[tipo])
        ax[0].set_xlabel("t (s)"); ax[0].set_ylabel("x (m)"); ax[0].grid(alpha=.3); ax[0].legend()
        ax[1].semilogy(ts[1:], [max(e, 1e-16) for e in res["rk2"]["errores"][1:]], "r-", label="RK2 (Heun)")
        ax[1].semilogy(ts[1:], [max(e, 1e-16) for e in res["rk4"]["errores"][1:]], "b-", label="RK4")
        ax[1].set_title("Error absoluto |x - x exacta|")
        ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("error (m)"); ax[1].grid(alpha=.3, which="both"); ax[1].legend()
        fig.tight_layout()
        f1 = os.path.join(carpeta, "m3_%s_solucion_error.png" % tipo.lower())
        fig.savefig(f1, dpi=120); archivos.append(f1)

        fig2, ax2 = plt.subplots(figsize=(6.5, 4.5))
        ns = [r["n"] for r in res["refinamiento"]]
        for clave, et, col in (("error_trapecio", "Trapecio", "r"),
                               ("error_simpson", "Simpson 1/3", "g"),
                               ("error_romberg", "Romberg", "b")):
            ax2.loglog(ns, [max(r[clave], 1e-18) for r in res["refinamiento"]], "o-", color=col, label=et)
        ax2.set_title("Escenario %s: convergencia de la integral de x^2" % nombres[tipo])
        ax2.set_xlabel("subintervalos n"); ax2.set_ylabel("error absoluto")
        ax2.grid(alpha=.3, which="both"); ax2.legend()
        fig2.tight_layout()
        f2 = os.path.join(carpeta, "m3_%s_integracion.png" % tipo.lower())
        fig2.savefig(f2, dpi=120); archivos.append(f2)

    # Sensibilidad (escenario mal condicionado)
    p = PARAMETROS["MAL_CONDICIONADO"]
    fr = [0.80 + 0.4 * i / 2000 for i in range(2001)]
    X = [amplitud_permanente(p["m"], p["c"], p["k"], p["F0"], f * W0) for f in fr]
    s = resultados["MAL_CONDICIONADO"]["sensibilidad"]
    fig3, ax3 = plt.subplots(figsize=(7, 4.5))
    ax3.semilogy(fr, X, "b-")
    ax3.plot([s["w"] / W0, s["w_perturbada"] / W0], [s["X"], s["X_perturbada"]], "ro")
    ax3.set_title("Sensibilidad: +1%% en w multiplica la amplitud por %.0f"
                  % (s["X_perturbada"] / s["X"]))
    ax3.set_xlabel("w / w0"); ax3.set_ylabel("X (m)"); ax3.grid(alpha=.3, which="both")
    fig3.tight_layout()
    f3 = os.path.join(carpeta, "m3_mal_condicionado_sensibilidad.png")
    fig3.savefig(f3, dpi=120); archivos.append(f3)

    # Apoyo al Modulo 1
    for clave, c in casos_modulo1().items():
        m4 = c["metodos"]["RK4"]
        fig4, ax4 = plt.subplots(1, 2, figsize=(11, 4))
        ax4[0].plot(m4["ts"], m4["vs"], "b-"); ax4[0].set_title("%s: v(t)" % c["nombre"])
        ax4[0].set_xlabel("t (s)"); ax4[0].set_ylabel("v (m/s)"); ax4[0].grid(alpha=.3)
        ax4[1].plot(m4["ts"], m4["xs"], "g-"); ax4[1].axhline(c["distancia_frenado_ref"], color="k", ls="--")
        ax4[1].set_title("Posicion durante el frenado (RK4)"); ax4[1].set_xlabel("t (s)")
        ax4[1].set_ylabel("x (m)"); ax4[1].grid(alpha=.3)
        fig4.tight_layout()
        f4 = os.path.join(carpeta, "m1_apoyo_%s.png" % clave)
        fig4.savefig(f4, dpi=120); archivos.append(f4)

    if mostrar:
        plt.show()
    plt.close("all")
    return archivos


# ============================================================
# 8) EXPORTACION JSON Y CACHE
# ============================================================

_CACHE = {}


def obtener_todos():
    if not _CACHE:
        for tipo in PARAMETROS:
            _CACHE[tipo] = ejecutar_escenario(tipo)
    return _CACHE


def guardar_json(ruta="resultados_modulo3.json"):
    datos = {"integrante": 2, "modulo3": obtener_todos(), "modulo1_apoyo": casos_modulo1(),
             "pruebas": pruebas_analiticas()}
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False)
    return ruta


# ============================================================
# 9) API (Flask) PARA EL INTEGRANTE 4
# ============================================================

app = Flask(__name__) if Flask else None

if app:
    @app.route("/api/modulo3/<tipo>")
    def api_modulo3(tipo):
        tipo = tipo.upper()
        if tipo not in PARAMETROS:
            return jsonify({"error": "Escenario no valido"}), 400
        return jsonify(obtener_todos()[tipo])

    @app.route("/api/modulo1_apoyo/<tipo>")
    def api_modulo1(tipo):
        casos = casos_modulo1()
        if tipo.lower() not in casos:
            return jsonify({"error": "Use 'constante' o 'variable'"}), 400
        return jsonify(casos[tipo.lower()])

    @app.route("/api/pruebas")
    def api_pruebas():
        return jsonify(pruebas_analiticas())


if __name__ == "__main__":
    args = set(sys.argv[1:])
    probar_en_consola()
    if "--sin-graficos" not in args:
        try:
            for a in generar_graficos(mostrar="--mostrar" in args):
                print("grafico guardado:", a)
        except ImportError:
            print("\n(matplotlib no esta instalado: pip install matplotlib)")
    if "--json" in args:
        print("JSON guardado en:", guardar_json())
    if "--sin-servidor" not in args:
        if app is None:
            print("\n(Flask no esta instalado: pip install flask)")
        else:
            print("\n" + "=" * 66)
            print("Servidor API en http://localhost:5001  (Ctrl+C para detener)")
            print("=" * 66)
            app.run(debug=False, port=5001)
