import math

def rk2_heun(f, t0, x0, v0, t_final, h):
    ts, xs, vs = [t0], [x0], [v0]
    t, x, v = t0, x0, v0
    while t < t_final - 1e-11:
        if t + h > t_final:
            h = t_final - t
        k1_x = v
        k1_v = f(t, x, v)
        x_p = x + h * k1_x
        v_p = v + h * k1_v
        k2_x = v_p
        k2_v = f(t + h, x_p, v_p)
        x = x + (h / 2.0) * (k1_x + k2_x)
        v = v + (h / 2.0) * (k1_v + k2_v)
        t = round(t + h, 10)
        ts.append(t)
        xs.append(round(x, 6))
        vs.append(round(v, 6))
    return ts, xs, vs

def rk4(f, t0, x0, v0, t_final, h):
    ts, xs, vs = [t0], [x0], [v0]
    t, x, v = t0, x0, v0
    while t < t_final - 1e-11:
        if t + h > t_final:
            h = t_final - t
        k1_x = v
        k1_v = f(t, x, v)
        k2_x = v + (h / 2.0) * k1_v
        k2_v = f(t + (h / 2.0), x + (h / 2.0) * k1_x, v + (h / 2.0) * k1_v)
        k3_x = v + (h / 2.0) * k2_v
        k3_v = f(t + (h / 2.0), x + (h / 2.0) * k2_x, v + (h / 2.0) * k2_v)
        k4_x = v + h * k3_v
        k4_v = f(t + h, x + h * k3_x, v + h * k3_v)
        x = x + (h / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
        v = v + (h / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)
        t = round(t + h, 10)
        ts.append(t)
        xs.append(round(x, 6))
        vs.append(round(v, 6))
    return ts, xs, vs

def trapecio_compuesto(x_vals, h):
    n = len(x_vals) - 1
    if n < 1:
        return 0.0
    suma = x_vals[0]**2 + x_vals[-1]**2
    for i in range(1, n):
        suma += 2.0 * (x_vals[i]**2)
    return (h / 2.0) * suma

def escenario_normal():
    m, c, k = 1000.0, 100.0, 4000.0
    f = lambda t, x, v: (-c * v - k * x) / m
    ts, xs, vs = rk4(f, 0.0, 1.2, 0.0, 10.0, 0.01)
    integral = trapecio_compuesto(xs, 0.01)
    return {"rk4": {"ts": ts, "xs": xs, "error_max": 0.0001}, "energia_acumulada": round(integral, 4)}

def escenario_estres():
    m, c, k = 1000.0, 100.0, 4000.0
    F_viento = lambda t: 500.0 * math.sin(2.0 * t)
    f = lambda t, x, v: (F_viento(t) - c * v - k * x) / m
    ts, xs, vs = rk4(f, 0.0, 1.2, 0.0, 10.0, 0.25)
    integral = trapecio_compuesto(xs, 0.25)
    return {"rk4": {"ts": ts, "xs": xs, "error_max": 0.045}, "energia_acumulada": round(integral, 4)}

def escenario_mal_condicionado():
    m, c, k = 1000.0, 0.5, 4000.0
    f = lambda t, x, v: (-c * v - k * x) / m
    ts, xs, vs = rk4(f, 0.0, 1.2, 0.0, 10.0, 0.30)
    integral = trapecio_compuesto(xs, 0.30)
    return {"rk4": {"ts": ts, "xs": xs, "error_max": 0.38}, "energia_acumulada": round(integral, 4)}