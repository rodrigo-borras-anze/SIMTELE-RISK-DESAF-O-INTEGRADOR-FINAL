import os
import time
import numpy as np
from backend.models.modulo2_deterioro.lu_descomposition import lu_decomposition_con_pivoteo, resolver_sistema_lu
from backend.models.modulo2_deterioro.conjugate_gradient import gradiente_conjugado
from backend.models.modulo2_deterioro.scenarios_metrics import evaluar_escenarios, calcular_metricas_error
from backend.models.modulo3_oscilaciones.modulo3_completo import (
    obtener_todos as mod3_obtener_todos,
    casos_modulo1 as mod3_casos_modulo1,
    pruebas_analiticas as mod3_pruebas_analiticas,
)
from backend.models.modulo4_sensores.modulo4_sensores import (
    configurar_escenario as mod4_configurar_escenario,
    evaluar_errores as mod4_evaluar_errores,
)
from backend.models.modulo4_sensores.interpolacion import (
    interpolacion_lagrange,
    interpolacion_newton,
    interpolacion_splines_cubicos,
)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.database import guardar_simulacion, obtener_historial_simulaciones
from backend.raices import simular_modulo1_raices, simular_modulo2_umbral


app = Flask(__name__)
CORS(app)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# MÓDULO 1: Detención de Emergencia
@app.route('/api/modulo1/<escenario>', methods=['GET'])
def api_modulo1(escenario):
    try:
        res = simular_modulo1_raices(escenario=escenario)
        ejecuciones = []
        for m in res["metodos"]:
            ejecuciones.append({
                "metodo": m["metodo"],
                "tolerancia": m["tolerancia"],
                "tiempo_ms": m["tiempo_ms"],
                "convergio": m["convergio"],
                "valor_final": {"raiz": m["raiz"], "motivo": m["motivo"]},
                "interpretacion": f"Tiempo de detención calculado en escenario {escenario.upper()}.",
                "iteraciones": m["iteraciones"]
            })
        sim_id = guardar_simulacion(1, "Integrante 1 + 4", ejecuciones,escenario)
        res["simulacion_id_guardada"] = sim_id
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# MÓDULO 2: Deterioro Mecánico (Calibración LU / Gradiente Conjugado + Umbral)
@app.route('/api/modulo2/<escenario>', methods=['GET'])
@app.route('/api/modulo2/umbral', defaults={'escenario': 'NORMAL'}, methods=['GET'])
def api_modulo2(escenario):
    esc_key = escenario.lower()
    escenarios = evaluar_escenarios()
    if esc_key not in escenarios:
        return jsonify({"error": "Escenario no válido"}), 400

    # 1. Calibración de sistema lineal 4x4 (EstudianteC)
    datos_esc = escenarios[esc_key]
    A = datos_esc["A"]
    b = datos_esc["b"]
    kappa = float(datos_esc["kappa"])
    x_ref = np.linalg.solve(A, b)

    # Método 1: Factorización LU con Pivoteo
    t0 = time.perf_counter()
    P, L, U = lu_decomposition_con_pivoteo(A)
    x_lu = resolver_sistema_lu(P, L, U, b)
    t_lu_ms = round((time.perf_counter() - t0) * 1000, 4)
    metricas_lu = calcular_metricas_error(x_ref, x_lu, A, b)

    # Método 2: Gradiente Conjugado
    t0 = time.perf_counter()
    x_cg, hist_cg, iters_cg = gradiente_conjugado(A, b)
    t_cg_ms = round((time.perf_counter() - t0) * 1000, 4)
    metricas_cg = calcular_metricas_error(x_ref, x_cg, A, b)

    # 2. Curva de umbral de mantenimiento existente
    res = simular_modulo2_umbral()

    ejecuciones = []
    for m in res["metodos"]:
        ejecuciones.append({
            "metodo": m["metodo"],
            "tolerancia": m["tolerancia"],
            "tiempo_ms": m["tiempo_ms"],
            "convergio": m["convergio"],
            "valor_final": {"t_umbral_dias": m["raiz"]},
            "interpretacion": "Cruce de umbral de mantenimiento D(t) - D_umbral = 0.",
            "iteraciones": m["iteraciones"]
        })

    # Agregar ejecuciones de LU y Gradiente Conjugado para SQLite
    ejecuciones.append({
        "metodo": "Factorización LU con Pivoteo",
        "tolerancia": 0.0,
        "tiempo_ms": t_lu_ms,
        "convergio": True,
        "valor_final": {"x": [round(float(v), 6) for v in x_lu], "residuo": float(metricas_lu["residuo_relativo"])},
        "interpretacion": f"Calibración 4x4 en escenario {escenario.upper()} (kappa={kappa:.2f}).",
        "iteraciones": []
    })
    ejecuciones.append({
        "metodo": "Gradiente Conjugado",
        "tolerancia": 1e-6,
        "tiempo_ms": t_cg_ms,
        "convergio": iters_cg < 200,
        "valor_final": {"x": [round(float(v), 6) for v in x_cg], "iteraciones": iters_cg, "residuo": float(metricas_cg["residuo_relativo"])},
        "interpretacion": f"Calibración iterativa 4x4 en escenario {escenario.upper()} ({iters_cg} iteraciones).",
        "iteraciones": []
    })

    sim_id = guardar_simulacion(2, "Integrante 1 + 3 + 4", ejecuciones,escenario)
    res["simulacion_id_guardada"] = sim_id
    res["calibracion_lineal"] = {
        "escenario": escenario.upper(),
        "kappa": round(kappa, 4),
        "lu": {
            "x": [round(float(v), 4) for v in x_lu],
            "residuo_relativo": f"{metricas_lu['residuo_relativo']:.2e}",
            "tiempo_ms": t_lu_ms
        },
        "gradiente_conjugado": {
            "x": [round(float(v), 4) for v in x_cg],
            "iteraciones": iters_cg,
            "residuo_relativo": f"{metricas_cg['residuo_relativo']:.2e}",
            "tiempo_ms": t_cg_ms
        }
    }
    return jsonify(res)

# MÓDULO 3: Oscilaciones por Viento (Semana 2: Solución exacta forzada, RK2/RK4, Integrales y Sensibilidad)
@app.route('/api/modulo3/<escenario>', methods=['GET'])
def api_modulo3(escenario):
    esc_upper = escenario.upper()
    todos = mod3_obtener_todos()
    if esc_upper not in todos:
        return jsonify({"error": "Escenario no válido"}), 400

    res = dict(todos[esc_upper])
    ejecuciones = [
        {
            "metodo": "RK2 (Heun)",
            "tolerancia": 1e-4,
            "tiempo_ms": round(res["rk2"]["tiempo_ms"], 4),
            "convergio": res["rk2"]["convergio"],
            "valor_final": {"error_max": res["rk2"]["error_max"]},
            "interpretacion": f"Oscilaciones RK2 en escenario {esc_upper}.",
            "iteraciones": []
        },
        {
            "metodo": "RK4 + Integración (Trapecio/Simpson/Romberg)",
            "tolerancia": 1e-4,
            "tiempo_ms": round(res["rk4"]["tiempo_ms"], 4),
            "convergio": res["rk4"]["convergio"],
            "valor_final": {
                "error_max_rk4": res["rk4"]["error_max"],
                "integral": res["integral"],
                "integral_referencia": res["integral_referencia"]["valor"]
            },
            "interpretacion": f"Oscilaciones RK4 e integral de x² en escenario {esc_upper}.",
            "iteraciones": []
        }
    ]
    sim_id = guardar_simulacion(3, "Integrante 2 + 4", ejecuciones,esc_upper)
    res["simulacion_id_guardada"] = sim_id
    return jsonify(res)

# APOYO MÓDULO 1 Y PRUEBAS ANALÍTICAS (Semana 2 - Integrante 2)
@app.route('/api/modulo1_apoyo/<tipo>', methods=['GET'])
def api_modulo1_apoyo(tipo):
    casos = mod3_casos_modulo1()
    if tipo.lower() not in casos:
        return jsonify({"error": "Use 'constante' o 'variable'"}), 400
    return jsonify(casos[tipo.lower()])

@app.route('/api/pruebas', methods=['GET'])
def api_pruebas():
    return jsonify(mod3_pruebas_analiticas())

# MÓDULO 4: Reconstrucción de Sensores (Semana 2: Lagrange, Newton y Splines Cúbicos Naturales)
@app.route('/api/modulo4/<escenario>', methods=['GET'])
def api_modulo4(escenario):
    try:
        esc_upper = escenario.upper()
        senal = "exponencial" if esc_upper == "ESTRES" else "seno"
        datos = mod4_configurar_escenario(esc_upper, senal=senal)

        algoritmos = [
            ("lagrange", interpolacion_lagrange),
            ("newton", interpolacion_newton),
            ("splines", interpolacion_splines_cubicos),
        ]

        curvas = {}
        metricas = {}
        ejecuciones = []

        for clave, fn in algoritmos:
            r_ref = fn(datos["t_nodos"], datos["y_nodos"], datos["t_ref"])
            r_oc = fn(datos["t_nodos"], datos["y_nodos"], datos["t_ocultos"])
            err_oc = mod4_evaluar_errores(datos["y_ocultos"], r_oc["y_aprox"])

            curvas[clave] = [round(float(v), 5) for v in r_ref["y_aprox"]]
            metricas[clave] = {
                "metodo": r_ref["metodo"],
                "ea_max_ocultos": err_oc["error_abs_max_inf"],
                "ep_medio": err_oc["error_porcentual_medio"],
                "tiempo_ms": round(r_ref["tiempo_ms"], 4),
            }
            ejecuciones.append({
                "metodo": r_ref["metodo"],
                "tolerancia": 1e-12,
                "tiempo_ms": round(r_ref["tiempo_ms"], 4),
                "convergio": r_ref["convergio"],
                "valor_final": {
                    "ea_max_ocultos": err_oc["error_abs_max_inf"],
                    "ep_medio": err_oc["error_porcentual_medio"]
                },
                "interpretacion": f"{datos['descripcion']} en escenario {esc_upper}.",
                "iteraciones": []
            })

        sim_id = guardar_simulacion(4, "Integrante 3 + 4", ejecuciones,esc_upper)

        return jsonify({
            "escenario": esc_upper,
            "descripcion": datos["descripcion"],
            "nota": datos["nota"],
            "simulacion_id_guardada": sim_id,
            "metricas": metricas,
            "graficos": {
                "curva_sensores": {
                    "t": [round(float(v), 3) for v in datos["t_ref"]],
                    "y_original": [round(float(v), 5) for v in datos["y_ref"]],
                    "y_lagrange": curvas["lagrange"],
                    "y_newton": curvas["newton"],
                    "y_splines": curvas["splines"],
                }
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# HISTORIAL GENERAL
@app.route('/api/historial', methods=['GET'])
def api_historial():
    return jsonify({"status": "ok", "historial": obtener_historial_simulaciones()})

if __name__ == '__main__':
    print("🚀 Servidor SIMTELE-RISK activo en http://localhost:5000")
    app.run(debug=True, port=5000)