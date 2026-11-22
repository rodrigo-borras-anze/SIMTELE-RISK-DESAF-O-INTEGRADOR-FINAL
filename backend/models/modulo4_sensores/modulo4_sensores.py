import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from .interpolacion import (
        interpolacion_lagrange,
        interpolacion_newton,
        interpolacion_splines_cubicos,
    )
except ImportError:
    from interpolacion import (
        interpolacion_lagrange,
        interpolacion_newton,
        interpolacion_splines_cubicos,
    )

def evaluar_errores(y_ref, y_aprox, eps_cero=1e-12):
    y_ref = np.asarray(y_ref, dtype=float)
    y_aprox = np.asarray(y_aprox, dtype=float)

    ea = np.abs(y_ref - y_aprox)
    ea_max = float(np.max(ea))
    ea_medio = float(np.mean(ea))

    mask = np.abs(y_ref) > eps_cero
    if np.any(mask):
        er = ea[mask] / np.abs(y_ref[mask])
        er_max = float(np.max(er))
        er_medio = float(np.mean(er))
        ep_medio = 100.0 * er_medio
    else:
        er_max = None
        er_medio = None
        ep_medio = None

    return {
        "error_abs_max_inf": ea_max,
        "error_abs_medio": ea_medio,
        "error_rel_max": er_max,
        "error_rel_medio": er_medio,
        "error_porcentual_medio": ep_medio,
    }


def configurar_escenario(escenario, senal="seno"):
    escenario = escenario.upper()

    if escenario == "NORMAL":
        t_min, t_max = 0.0, 2.0 * np.pi
        t_ref = np.linspace(t_min, t_max, 400)
        if senal == "exponencial":
            f = lambda t: np.exp(-0.5 * t)
            desc = "y(t) = exp(-0.5t)"
        else:
            f = lambda t: np.sin(t)
            desc = "y(t) = sin(t)"

        t_sensor = np.linspace(t_min, t_max, 21)
        idx_ocultos = np.array([2, 6, 10, 14, 18])
        idx_visibles = np.setdiff1d(np.arange(len(t_sensor)), idx_ocultos)
        nota = "Escenario Normal: muestreo uniforme con pérdida leve de datos."

    elif escenario == "ESTRES":
        t_min, t_max = 0.0, 2.0 * np.pi
        t_ref = np.linspace(t_min, t_max, 400)
        if senal == "exponencial":
            f = lambda t: np.exp(-t)
            desc = "y(t) = exp(-t)"
        else:
            f = lambda t: np.sin(t)
            desc = "y(t) = sin(t)"

        # Retiro agresivo: se conservan 7 de 25 lecturas (~72% oculto)
        t_sensor = np.linspace(t_min, t_max, 25)
        idx_visibles = np.array([0, 4, 8, 12, 16, 20, 24])
        idx_ocultos = np.setdiff1d(np.arange(len(t_sensor)), idx_visibles)
        nota = "Escenario Estrés: pérdida agresiva de lecturas del sensor."

    elif escenario == "MAL_CONDICIONADO":
        # Fenómeno de Runge con 15 nodos equiespaciados en [-1, 1]
        t_min, t_max = -1.0, 1.0
        t_ref = np.linspace(t_min, t_max, 500)
        f = lambda t: 1.0 / (1.0 + 25.0 * (t ** 2))
        desc = "y(t) = 1 / (1 + 25t²) [Runge]"

        t_sensor = np.linspace(t_min, t_max, 29)
        idx_visibles = np.arange(0, 29, 2)
        idx_ocultos = np.setdiff1d(np.arange(len(t_sensor)), idx_visibles)
        nota = "Escenario Mal Condicionado: nodos equiespaciados propensos a Runge."

    else:
        raise ValueError("Escenario inválido: use NORMAL, ESTRES o MAL_CONDICIONADO.")

    return {
        "escenario": escenario,
        "descripcion": desc,
        "nota": nota,
        "t_ref": t_ref,
        "y_ref": f(t_ref),
        "t_nodos": t_sensor[idx_visibles],
        "y_nodos": f(t_sensor[idx_visibles]),
        "t_ocultos": t_sensor[idx_ocultos],
        "y_ocultos": f(t_sensor[idx_ocultos]),
    }


def simular_modulo4(escenario="NORMAL", senal="seno", carpeta_salida="resultados"):
    os.makedirs(carpeta_salida, exist_ok=True)
    datos = configurar_escenario(escenario, senal)

    algoritmos = [
        interpolacion_lagrange,
        interpolacion_newton,
        interpolacion_splines_cubicos,
    ]

    resultados = []
    for fn in algoritmos:
        r_ref = fn(datos["t_nodos"], datos["y_nodos"], datos["t_ref"])
        r_oc = fn(datos["t_nodos"], datos["y_nodos"], datos["t_ocultos"])

        resultados.append({
            "metodo": r_ref["metodo"],
            "y_aprox_ref": r_ref["y_aprox"],
            "y_aprox_ocultos": r_oc["y_aprox"],
            "tiempo_ms": r_ref["tiempo_ms"],
            "convergio": r_ref["convergio"],
            "error_continuo": evaluar_errores(datos["y_ref"], r_ref["y_aprox"]),
            "error_ocultos": evaluar_errores(datos["y_ocultos"], r_oc["y_aprox"]),
        })

    # Gráfico superpuesto
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(
        datos["t_ref"],
        datos["y_ref"],
        color="black",
        lw=2.2,
        label=f"Señal original ({datos['descripcion']})",
    )

    estilos = [("--", "#1f77b4", 1.8), (":", "#ff7f0e", 2.2), ("-.", "#2ca02c", 2.0)]
    for res, (ls, col, lw) in zip(resultados, estilos):
        ea_inf = res["error_ocultos"]["error_abs_max_inf"]
        ax.plot(
            datos["t_ref"],
            res["y_aprox_ref"],
            linestyle=ls,
            color=col,
            lw=lw,
            label=f"{res['metodo']} (Ea máx ocultos={ea_inf:.2e})",
        )

    ax.scatter(
        datos["t_nodos"],
        datos["y_nodos"],
        color="#0055aa",
        s=55,
        zorder=5,
        label="Nodos conocidos",
    )
    ax.scatter(
        datos["t_ocultos"],
        datos["y_ocultos"],
        facecolors="none",
        edgecolors="#d62728",
        lw=1.8,
        s=75,
        zorder=6,
        label="Puntos ocultados",
    )

    y_min, y_max = np.min(datos["y_ref"]), np.max(datos["y_ref"])
    margen = 0.6 * max(y_max - y_min, 1e-3)
    ax.set_ylim(y_min - margen, y_max + margen)

    ax.set_title(f"SIMTELE-RISK | Módulo 4 — {datos['escenario']}")
    ax.set_xlabel("Tiempo t (s)")
    ax.set_ylabel("Magnitud y(t)")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(loc="best", fontsize=8.5)
    plt.tight_layout()

    ruta_img = os.path.join(carpeta_salida, f"modulo4_{escenario.lower()}.png")
    plt.savefig(ruta_img, dpi=150)
    plt.close(fig)

    return datos, resultados, ruta_img


if __name__ == "__main__":
    casos = [
        ("NORMAL", "seno"),
        ("ESTRES", "exponencial"),
        ("MAL_CONDICIONADO", "runge"),
    ]
    for esc, sen in casos:
        datos, res_lista, ruta = simular_modulo4(esc, sen)
        print(f"\n=== {esc} | {datos['descripcion']} ===")
        print(datos["nota"])
        for r in res_lista:
            eo = r["error_ocultos"]
            ep = (
                f"{eo['error_porcentual_medio']:.4f}%"
                if eo["error_porcentual_medio"] is not None
                else "N/A"
            )
            print(
                f"  - {r['metodo']:32s} | "
                f"Ea_max(ocultos)={eo['error_abs_max_inf']:.6e} | "
                f"E%_medio={ep} | "
                f"{r['tiempo_ms']:.3f} ms"
            )
        print(f"  Gráfico guardado en: {ruta}")
        