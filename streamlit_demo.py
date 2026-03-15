"""
MACS-VRPTW — Demo Interactivo en Vivo | Streamlit + Plotly
Ejecuta el algoritmo en tiempo real y muestra convergencia interactiva.

Uso:
    streamlit run streamlit_demo.py
"""

import time
import threading
import queue
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.algorithm.local_search.or_opt import OrOpt
from src.algorithm.macs_vrptw import MACS_VRPTW
from src.parsers.solomon_parser import parse_solomon_instance
from src.models.instance import Instance
from src.utils.seed import set_global_seed

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AZUL = "#003366"
ORO = "#C8962E"
GRIS = "#555555"
VERDE = "#2D936C"
ROJO = "#D64045"
ACENTO = "#E8F0FE"

ROUTE_COLORS = [
    "#003366", "#C8962E", "#5A72A0", "#D64045", "#2D936C",
    "#7B2D8E", "#E8823A", "#3A86FF", "#FF006E", "#8338EC",
]

BKS_DISTANCE = 588.32
BKS_VEHICLES = 3

DATA_DIR = Path(__file__).resolve().parent / "data"

PHASE_DESC = {
    "init": {
        "title": "Construyendo solucion inicial con Nearest Neighbor",
        "detail": "Cada vehiculo visita al cliente mas cercano factible. "
                  "Solucion rapida pero no optima — punto de partida para las hormigas.",
        "icon": "🏗️",
    },
    "ACS-VEI": {
        "title": "Colonia ACS-VEI: reduciendo vehiculos",
        "detail": "Las hormigas intentan servir a los 100 clientes con un vehiculo menos (v-1). "
                  "Usan feromonas + regla pseudo-aleatoria (q0=0.9).",
        "icon": "🚛",
    },
    "ACS-TIME": {
        "title": "Colonia ACS-TIME: optimizando distancia",
        "detail": "Con vehiculos fijos, las hormigas buscan rutas mas cortas. "
                  "Or-opt reordena segmentos de 1-3 clientes entre rutas.",
        "icon": "📏",
    },
    "done": {
        "title": "Algoritmo finalizado",
        "detail": "Criterio de paro alcanzado: sin mejora en las ultimas iteraciones. "
                  "La mejor solucion global (psi_gb) es el resultado final.",
        "icon": "✅",
    },
}

COMPONENT_LEGEND = [
    ("⬤", "#aaaaaa", "100 clientes (instancia C208)"),
    ("★", ROJO, "Deposito central"),
    ("■", GRIS, "Nearest Neighbor — solucion inicial"),
    ("■", ORO, "ACS-VEI — colonia que reduce vehiculos"),
    ("■", AZUL, "ACS-TIME — colonia que optimiza distancia"),
    ("■", VERDE, "Or-opt — busqueda local (mejora rutas)"),
]

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MACS-VRPTW Demo en Vivo",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
    h1, h2, h3 {{ color: {AZUL}; }}
    [data-testid="stMetricValue"] {{ font-size: 1.6rem !important; color: {AZUL}; }}
    [data-testid="stMetricLabel"] {{ font-size: 0.95rem !important; }}
    div[data-testid="stStatusWidget"] {{ display: none; }}
    .phase-box {{
        background: linear-gradient(135deg, {ACENTO} 0%, #f0f4fa 100%);
        border-left: 5px solid {ORO};
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .bks-badge {{
        background: linear-gradient(135deg, {VERDE} 0%, #238c5a 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 1.15em;
        margin: 12px 0;
        box-shadow: 0 3px 12px rgba(45,147,108,0.3);
    }}
    .metric-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }}
    .metric-card .value {{
        font-size: 2em;
        font-weight: bold;
        color: {AZUL};
        line-height: 1.2;
    }}
    .metric-card .label {{
        font-size: 0.85em;
        color: {GRIS};
        margin-top: 4px;
    }}
    .log-box {{
        background: #f8f9fb;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.88em;
        line-height: 1.7;
    }}
    .legend-box {{
        background: #f8f9fb;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        line-height: 2.0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@st.cache_resource
def get_instance() -> Instance:
    return parse_solomon_instance(str(DATA_DIR / "c208.txt"))


def _metrics_html(nv, dist, gap, elapsed_str):
    """Builds a custom 4-column metrics row."""
    gap_color = VERDE if abs(gap) < 0.01 else ORO
    return f"""
    <div style="display:flex; gap:16px; margin:10px 0;">
        <div class="metric-card" style="flex:1;">
            <div class="value">{nv}</div>
            <div class="label">Vehiculos</div>
        </div>
        <div class="metric-card" style="flex:1;">
            <div class="value">{dist:.2f}</div>
            <div class="label">Distancia total</div>
        </div>
        <div class="metric-card" style="flex:1;">
            <div class="value" style="color:{gap_color};">{gap:.2f}%</div>
            <div class="label">Gap vs BKS</div>
        </div>
        <div class="metric-card" style="flex:1;">
            <div class="value" style="color:{ORO};">{elapsed_str}</div>
            <div class="label">Tiempo</div>
        </div>
    </div>"""


def build_route_map(instance: Instance, solution_data: dict | None) -> go.Figure:
    """Construye el mapa de rutas Plotly interactivo."""
    fig = go.Figure()

    cx = [c.x for c in instance.customers]
    cy = [c.y for c in instance.customers]
    cids = [c.id for c in instance.customers]
    demands = [c.demand for c in instance.customers]
    readys = [c.ready_time for c in instance.customers]
    dues = [c.due_date for c in instance.customers]

    fig.add_trace(go.Scatter(
        x=cx, y=cy, mode="markers",
        marker=dict(color="#cccccc", size=7),
        customdata=np.stack([cids, demands, readys, dues], axis=-1),
        hovertemplate=(
            "<b>Cliente %{customdata[0]:.0f}</b><br>"
            "Demanda: %{customdata[1]:.0f}<br>"
            "Ventana: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<br>"
            "Pos: (%{x:.1f}, %{y:.1f})<extra></extra>"
        ),
        name="Clientes", showlegend=False,
    ))

    if solution_data:
        for r_idx, route_ids in enumerate(solution_data["routes"]):
            if not route_ids:
                continue
            color = ROUTE_COLORS[r_idx % len(ROUTE_COLORS)]
            path_ids = [0] + route_ids + [0]
            rx = [instance.all_nodes[nid].x for nid in path_ids]
            ry = [instance.all_nodes[nid].y for nid in path_ids]

            fig.add_trace(go.Scatter(
                x=rx, y=ry, mode="lines",
                line=dict(color=color, width=3),
                name=f"Ruta {r_idx + 1} ({len(route_ids)} cl)",
                hoverinfo="name",
            ))

            route_x = [instance.all_nodes[nid].x for nid in route_ids]
            route_y = [instance.all_nodes[nid].y for nid in route_ids]
            route_demands = [instance.all_nodes[nid].demand for nid in route_ids]
            route_readys = [instance.all_nodes[nid].ready_time for nid in route_ids]
            route_dues = [instance.all_nodes[nid].due_date for nid in route_ids]

            fig.add_trace(go.Scatter(
                x=route_x, y=route_y, mode="markers",
                marker=dict(color=color, size=9, line=dict(color="white", width=1.5)),
                customdata=np.stack([route_ids, route_demands, route_readys, route_dues], axis=-1),
                hovertemplate=(
                    "<b>Cliente %{customdata[0]:.0f}</b><br>"
                    "Demanda: %{customdata[1]:.0f}<br>"
                    "Ventana: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<extra></extra>"
                ),
                showlegend=False,
            ))

    fig.add_trace(go.Scatter(
        x=[instance.depot.x], y=[instance.depot.y],
        mode="markers",
        marker=dict(symbol="star", color="red", size=18,
                    line=dict(color="darkred", width=1.5)),
        name="Deposito",
        hovertemplate="<b>Deposito</b><br>(%{x:.1f}, %{y:.1f})<extra></extra>",
    ))

    title_text = "Mapa de Rutas — 100 clientes"
    if solution_data:
        nv = solution_data["num_vehicles"]
        dist = solution_data["total_distance"]
        title_text = f"Mapa de Rutas — {nv} vehiculos, {dist:.2f} dist"

    fig.update_layout(
        title=dict(text=title_text, font=dict(color=AZUL, size=15)),
        xaxis_title="Posicion X", yaxis_title="Posicion Y",
        height=520, plot_bgcolor="white",
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd",
                    borderwidth=1, font=dict(size=11), x=0.01, y=0.01,
                    xanchor="left", yanchor="bottom"),
        margin=dict(l=50, r=20, t=45, b=50),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", scaleanchor="x")
    return fig


def build_convergence(history: list[dict]) -> go.Figure:
    """Dos graficas apiladas: distancia arriba (grande), vehiculos abajo (compacta)."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3], vertical_spacing=0.10,
        subplot_titles=(
            "<b>Distancia total</b> <span style='color:#888;font-size:0.8em;'>"
            "(cada punto = mejora encontrada)</span>",
            "<b>Vehiculos</b>",
        ),
    )

    if history:
        times = [h["elapsed_time"] for h in history]
        dists = [h["total_distance"] for h in history]
        vehs = [h["num_vehicles"] for h in history]
        events = [h.get("event", "") for h in history]

        # Event labels for hover
        labels = []
        for ev in events:
            if "NN" in ev or "inicial" in ev.lower():
                labels.append("Nearest Neighbor")
            elif "VEI" in ev:
                labels.append("ACS-VEI (menos vehiculos)")
            elif "TIME" in ev:
                labels.append("ACS-TIME (mejor distancia)")
            else:
                labels.append("Mejora")

        # Marker colors by event type
        colors = []
        for ev in events:
            if "NN" in ev or "inicial" in ev.lower():
                colors.append(GRIS)
            elif "VEI" in ev:
                colors.append(ORO)
            elif "TIME" in ev:
                colors.append(AZUL)
            else:
                colors.append(GRIS)

        # --- Distancia (arriba) ---
        fig.add_trace(go.Scatter(
            x=times, y=dists, mode="lines",
            name="Distancia", legendgroup="dist",
            line=dict(color=AZUL, width=2.5),
            hoverinfo="skip",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=times, y=dists, mode="markers+text",
            showlegend=False, legendgroup="dist",
            marker=dict(size=14, color=colors,
                        line=dict(color="white", width=2.5)),
            text=[f"{d:.0f}" for d in dists],
            textposition="top center",
            textfont=dict(size=11, color=AZUL),
            customdata=labels,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Tiempo: %{x:.1f}s<br>"
                "Distancia: %{y:.2f}<extra></extra>"
            ),
        ), row=1, col=1)

        # --- Vehiculos (abajo) ---
        fig.add_trace(go.Scatter(
            x=times, y=vehs, mode="lines",
            name="Vehiculos", legendgroup="veh",
            line=dict(color=ORO, width=2.5),
            hoverinfo="skip",
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=times, y=vehs, mode="markers+text",
            showlegend=False, legendgroup="veh",
            marker=dict(size=14, color=ORO, symbol="square",
                        line=dict(color="white", width=2.5)),
            text=[str(int(v)) for v in vehs],
            textposition="top center",
            textfont=dict(size=12, color=ORO),
            customdata=labels,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Tiempo: %{x:.1f}s<br>"
                "Vehiculos: %{y:.0f}<extra></extra>"
            ),
        ), row=2, col=1)

    # BKS references
    fig.add_hline(y=BKS_DISTANCE, line_dash="dot", line_color=VERDE,
                  line_width=2, annotation_text=f"  BKS = {BKS_DISTANCE}",
                  annotation_position="top left",
                  annotation_font=dict(color=VERDE, size=12, weight="bold"),
                  row=1, col=1)
    fig.add_hline(y=BKS_VEHICLES, line_dash="dot", line_color=VERDE,
                  line_width=2, annotation_text=f"  BKS = {BKS_VEHICLES}",
                  annotation_position="top left",
                  annotation_font=dict(color=VERDE, size=11, weight="bold"),
                  row=2, col=1)

    fig.update_layout(
        height=520, plot_bgcolor="white",
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd",
                    borderwidth=1, x=0.98, y=0.98, xanchor="right"),
        margin=dict(l=60, r=20, t=35, b=45),
        showlegend=True,
    )

    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", row=1, col=1)
    fig.update_xaxes(title_text="Tiempo (s)", showgrid=True,
                     gridcolor="#f0f0f0", row=2, col=1)
    fig.update_yaxes(title_text="Distancia", showgrid=True,
                     gridcolor="#f0f0f0", title_font_color=AZUL,
                     row=1, col=1)
    fig.update_yaxes(title_text="Vehiculos", showgrid=True,
                     gridcolor="#f0f0f0", title_font_color=ORO,
                     dtick=1, row=2, col=1)

    # Subtitle styling
    for ann in fig.layout.annotations:
        ann.update(font=dict(size=13))

    return fig


def _build_log_html(log_lines):
    html = f"<div class='log-box'><b style='color:{AZUL};'>Modulos ejecutados:</b><br>"
    for entry in log_lines[-6:]:
        is_last = entry is log_lines[-1]
        opacity = "1.0" if is_last else "0.50"
        weight = "bold" if is_last else "normal"
        html += (
            f"<span style='opacity:{opacity}; font-weight:{weight}; "
            f"color:{entry['color']};'>"
            f"[{entry['icon']:>3s}] {entry['module']:<22s} {entry['msg']}"
            f"</span><br>"
        )
    html += "</div>"
    return html


def _build_legend_html():
    html = f"<div class='legend-box'><b style='color:{AZUL};'>Componentes del algoritmo</b><br><br>"
    for symbol, color, label in COMPONENT_LEGEND:
        html += f"<span style='color:{color}; font-size:1.3em;'>{symbol}</span> &nbsp;{label}<br>"
    html += "</div>"
    return html


def _build_bks_html():
    return (
        f'<div class="bks-badge">'
        f"✅ Best Known Solution Alcanzada<br>"
        f"3 vehiculos &nbsp;|&nbsp; {BKS_DISTANCE} distancia &nbsp;|&nbsp; Gap 0.00%"
        f"</div>"
    )


def _build_phase_html(pd_info, mins, secs, objective_text, progress_bar,
                      border_color=None):
    bc = border_color or ORO
    obj_line = ""
    if objective_text:
        obj_line = f"<br><b style='color:{ORO};'>▶ {objective_text}</b>"
    return f"""
    <div class="phase-box" style="border-left-color:{bc};">
        <span style="font-size:1.4em;">{pd_info['icon']}</span>
        &nbsp;<b style="font-size:1.15em;">{pd_info['title']}</b>
        &nbsp;&nbsp;<span style="color:{GRIS};">⏱️ {mins:02d}:{secs:02d}</span>
        <br><span style="color:{GRIS}; font-size:0.92em;">{pd_info['detail']}</span>
        {obj_line}
        <br><span style="font-family:monospace; font-size:0.88em; color:{AZUL};">{progress_bar}</span>
    </div>"""


# ---------------------------------------------------------------------------
# Algorithm runner
# ---------------------------------------------------------------------------
def run_algorithm(instance, params, event_queue):
    set_global_seed(params["seed"])

    def on_improvement(solution, entry):
        sol_data = {
            "routes": [r.customer_ids[:] for r in solution.routes if r.customer_ids],
            "num_vehicles": solution.num_vehicles(),
            "total_distance": round(solution.total_distance(instance), 2),
        }
        event_queue.put(("improvement", sol_data, entry))

    def on_iteration(info):
        event_queue.put(("iteration", None, info))

    macs = MACS_VRPTW(
        instance=instance,
        num_ants=params["num_ants"],
        beta=1.0, q0=0.9, rho=0.1,
        max_iterations=params["max_iterations"],
        max_no_improvement=params["max_no_improvement"],
        local_search=OrOpt(),
        on_improvement=on_improvement,
        on_iteration=on_iteration,
    )
    result = macs.solve()
    sol_data = {
        "routes": [r.customer_ids[:] for r in result.routes if r.customer_ids],
        "num_vehicles": result.num_vehicles(),
        "total_distance": round(result.total_distance(instance), 2),
    }
    event_queue.put(("done", sol_data, None))


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    instance = get_instance()

    # ==================== HEADER ====================
    st.markdown(
        f"""
        <h1 style="text-align:center; margin-bottom:2px; font-size:2.2em;">
            MACS-VRPTW — Demo en Vivo
        </h1>
        <p style="text-align:center; color:{GRIS}; margin-top:0; font-size:1.0em;">
            Rutas optimas para vehiculos con ventanas de tiempo
            &nbsp;|&nbsp; Minimizar vehiculos y distancia
            &nbsp;|&nbsp; C208 (100 clientes)
            &nbsp;|&nbsp; BKS: 3 veh / 588.32
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ==================== SIDEBAR PARAMS ====================
    with st.sidebar:
        st.markdown(f"<h3 style='color:{AZUL};'>Parametros</h3>",
                    unsafe_allow_html=True)
        seed = st.number_input("Semilla", value=42, min_value=0, max_value=9999)
        num_ants = st.slider("Hormigas por colonia", 3, 20, 5)
        max_iterations = st.slider("Max iteraciones", 10, 200, 50)
        max_no_improvement = st.slider("Max sin mejora", 2, 20, 3)
        st.divider()
        st.markdown(
            f"""<div style="background:{AZUL}; color:white; padding:12px;
            border-radius:10px; text-align:center;">
            <b>UACJ — MIAAD</b><br>
            <small style="color:{ORO};">Optimizacion Inteligente 2026</small>
            </div>""",
            unsafe_allow_html=True,
        )

    # ==================== SESSION STATE ====================
    for key, default in [
        ("running", False), ("history", []), ("log_lines", []),
        ("solution", None), ("phase", "init"),
        ("bks_reached", False), ("final_time", 0.0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ==================== RUN BUTTON ====================
    run_clicked = st.button(
        "▶  Ejecutar Algoritmo" if not st.session_state.running else "⏳ Ejecutando...",
        type="primary", disabled=st.session_state.running,
        use_container_width=True,
    )

    if run_clicked:
        st.session_state.running = True
        for k in ["history", "log_lines"]:
            st.session_state[k] = []
        st.session_state.solution = None
        st.session_state.phase = "init"
        st.session_state.bks_reached = False
        st.session_state.final_time = 0.0

        params = {"seed": seed, "num_ants": num_ants,
                  "max_iterations": max_iterations,
                  "max_no_improvement": max_no_improvement}
        event_q = queue.Queue()

        worker = threading.Thread(
            target=run_algorithm, args=(instance, params, event_q), daemon=True)
        start_time = time.time()
        worker.start()

        log_lines = [
            {"icon": "CFG", "module": "config_loader.py",
             "msg": f"seed={seed}  ants={num_ants}  iter={max_iterations}", "color": GRIS},
            {"icon": "DAT", "module": "solomon_parser.py",
             "msg": f"100 clientes, Q={instance.capacity}", "color": GRIS},
            {"icon": "OPT", "module": "or_opt.py",
             "msg": "Busqueda local Or-opt lista", "color": GRIS},
        ]
        history = []
        solution_data = None
        phase = "init"
        bks_reached = False
        iteration_info = None

        # Placeholders
        phase_ph = st.empty()
        metrics_ph = st.empty()
        col_map, col_conv = st.columns([1, 1], gap="medium")
        with col_map:
            map_ph = st.empty()
        with col_conv:
            conv_ph = st.empty()
        col_log, col_legend = st.columns([3, 2], gap="medium")
        with col_log:
            log_ph = st.empty()
        with col_legend:
            legend_ph = st.empty()
            bks_ph = st.empty()

        map_ph.plotly_chart(build_route_map(instance, None),
                            use_container_width=True, key="map_init")
        conv_ph.plotly_chart(build_convergence([]),
                             use_container_width=True, key="conv_init")

        finished = False
        uctr = 0

        while not finished:
            time.sleep(0.3)
            elapsed = time.time() - start_time
            mins, secs = int(elapsed) // 60, int(elapsed) % 60

            events = []
            while True:
                try:
                    events.append(event_q.get_nowait())
                except queue.Empty:
                    break

            needs_chart = False
            for ev in events:
                etype = ev[0]
                if etype == "done":
                    finished = True
                    solution_data = ev[1]
                    phase = "done"
                    break
                elif etype == "improvement":
                    _, sol_data, entry = ev
                    solution_data = sol_data
                    history.append(entry)
                    evt = entry["event"]
                    nv = entry["num_vehicles"]
                    dist = entry["total_distance"]
                    el = entry["elapsed_time"]
                    m, s = int(el) // 60, int(el) % 60
                    if "NN" in evt or "inicial" in evt.lower():
                        log_lines.append({"icon": "NN", "module": "nearest_neighbor.py",
                                          "msg": f"{nv} veh | {dist:.2f} | {m:02d}:{s:02d}", "color": GRIS})
                    elif "VEI" in evt:
                        log_lines.append({"icon": "VEI", "module": "acs_vei.py",
                                          "msg": f"{nv} veh | {dist:.2f} | {m:02d}:{s:02d}", "color": ORO})
                    elif "TIME" in evt:
                        log_lines.append({"icon": "TIM", "module": "acs_time.py",
                                          "msg": f"{nv} veh | {dist:.2f} | {m:02d}:{s:02d}", "color": AZUL})
                    if abs(dist - BKS_DISTANCE) < 0.01 and nv <= BKS_VEHICLES:
                        bks_reached = True
                    needs_chart = True
                elif etype == "iteration":
                    _, _, info = ev
                    phase = info["phase"]
                    iteration_info = info

            # --- UI updates ---
            pd_info = PHASE_DESC.get(phase, PHASE_DESC["init"])
            obj_txt = ""
            progress = "Preparando..."
            if iteration_info:
                nv_i = iteration_info.get("num_vehicles", "?")
                dist_i = iteration_info.get("total_distance", 0)
                it = iteration_info.get("iteration", 0)
                mx = iteration_info.get("max_iterations", 50)
                pct = min(it / max(mx, 1), 1.0) * 100
                progress = f"Iteracion {it}/{mx} ({pct:.0f}%)"
                if phase == "ACS-VEI":
                    obj_txt = f"Reducir vehiculos ({nv_i} actuales → intentando {nv_i - 1})"
                elif phase == "ACS-TIME":
                    obj_txt = f"Minimizar distancia ({dist_i:.2f}) con {nv_i} vehiculos"

            phase_ph.markdown(
                _build_phase_html(pd_info, mins, secs, obj_txt, progress),
                unsafe_allow_html=True)

            if solution_data:
                gap = ((solution_data["total_distance"] - BKS_DISTANCE) / BKS_DISTANCE * 100)
                metrics_ph.markdown(
                    _metrics_html(solution_data["num_vehicles"],
                                  solution_data["total_distance"],
                                  gap, f"{mins:02d}:{secs:02d}"),
                    unsafe_allow_html=True)

            if needs_chart:
                uctr += 1
                map_ph.plotly_chart(build_route_map(instance, solution_data),
                                    use_container_width=True, key=f"map_{uctr}")
                conv_ph.plotly_chart(build_convergence(history),
                                     use_container_width=True, key=f"conv_{uctr}")

            log_ph.markdown(_build_log_html(log_lines), unsafe_allow_html=True)
            legend_ph.markdown(_build_legend_html(), unsafe_allow_html=True)

            if bks_reached:
                bks_ph.markdown(_build_bks_html(), unsafe_allow_html=True)

        # --- Finished ---
        elapsed = time.time() - start_time
        mins, secs = int(elapsed) // 60, int(elapsed) % 60
        st.session_state.running = False
        st.session_state.history = history
        st.session_state.log_lines = log_lines
        st.session_state.solution = solution_data
        st.session_state.phase = "done"
        st.session_state.bks_reached = bks_reached
        st.session_state.final_time = elapsed

        uctr += 1
        pd_info = PHASE_DESC["done"]
        if bks_reached:
            obj_final = "✅ Best Known Solution alcanzada — Gap 0.00%"
        else:
            gap = ((solution_data["total_distance"] - BKS_DISTANCE) / BKS_DISTANCE * 100)
            obj_final = f"Finalizado — Gap vs BKS: {gap:.2f}%"

        phase_ph.markdown(
            _build_phase_html(pd_info, mins, secs, obj_final,
                              "COMPLETADO", border_color=VERDE),
            unsafe_allow_html=True)

        gap = ((solution_data["total_distance"] - BKS_DISTANCE) / BKS_DISTANCE * 100)
        metrics_ph.markdown(
            _metrics_html(solution_data["num_vehicles"],
                          solution_data["total_distance"],
                          gap, f"{mins:02d}:{secs:02d}"),
            unsafe_allow_html=True)

        map_ph.plotly_chart(build_route_map(instance, solution_data),
                            use_container_width=True, key=f"map_{uctr}")
        conv_ph.plotly_chart(build_convergence(history),
                             use_container_width=True, key=f"conv_{uctr}")

        log_lines.append({"icon": "FIN", "module": "macs_vrptw.py",
                          "msg": f"FINAL: {solution_data['num_vehicles']} veh | "
                                 f"{solution_data['total_distance']:.2f} | {mins:02d}:{secs:02d}",
                          "color": VERDE})
        log_ph.markdown(_build_log_html(log_lines), unsafe_allow_html=True)

        if bks_reached:
            bks_ph.markdown(_build_bks_html(), unsafe_allow_html=True)

        if history:
            with st.expander("📋 Historial completo de mejoras"):
                st.dataframe(
                    pd.DataFrame(history)[["iteration", "num_vehicles",
                                           "total_distance", "elapsed_time", "event"]],
                    use_container_width=True, hide_index=True)

    # ==================== STATIC VIEW ====================
    elif not st.session_state.running and st.session_state.solution:
        sol_d = st.session_state.solution
        hist = st.session_state.history
        el = st.session_state.final_time
        mins, secs = int(el) // 60, int(el) % 60

        pd_info = PHASE_DESC["done"]
        if st.session_state.bks_reached:
            obj_final = "✅ Best Known Solution alcanzada — Gap 0.00%"
        else:
            gap = ((sol_d["total_distance"] - BKS_DISTANCE) / BKS_DISTANCE * 100)
            obj_final = f"Finalizado — Gap vs BKS: {gap:.2f}%"

        st.markdown(
            _build_phase_html(pd_info, mins, secs, obj_final,
                              "COMPLETADO", border_color=VERDE),
            unsafe_allow_html=True)

        gap = ((sol_d["total_distance"] - BKS_DISTANCE) / BKS_DISTANCE * 100)
        st.markdown(
            _metrics_html(sol_d["num_vehicles"], sol_d["total_distance"],
                          gap, f"{mins:02d}:{secs:02d}"),
            unsafe_allow_html=True)

        col_map, col_conv = st.columns([1, 1], gap="medium")
        with col_map:
            st.plotly_chart(build_route_map(instance, sol_d),
                            use_container_width=True)
        with col_conv:
            st.plotly_chart(build_convergence(hist),
                            use_container_width=True)

        col_log, col_legend = st.columns([3, 2], gap="medium")
        with col_log:
            st.markdown(_build_log_html(st.session_state.log_lines),
                        unsafe_allow_html=True)
        with col_legend:
            st.markdown(_build_legend_html(), unsafe_allow_html=True)
            if st.session_state.bks_reached:
                st.markdown(_build_bks_html(), unsafe_allow_html=True)

        if hist:
            with st.expander("📋 Historial completo de mejoras"):
                st.dataframe(
                    pd.DataFrame(hist)[["iteration", "num_vehicles",
                                        "total_distance", "elapsed_time", "event"]],
                    use_container_width=True, hide_index=True)

    # ==================== EMPTY STATE ====================
    else:
        st.markdown(
            f"""<div style="background:{ACENTO}; border-radius:12px; padding:24px;
            text-align:center; margin:16px 0;">
            <p style="font-size:1.1em; color:{AZUL}; margin:0;">
            Presiona <b>▶ Ejecutar Algoritmo</b> para iniciar la demo en vivo.<br>
            <span style="color:{GRIS}; font-size:0.9em;">
            Ajusta parametros en el panel lateral (☰) si lo deseas.</span>
            </p></div>""",
            unsafe_allow_html=True)

        col_map, col_conv = st.columns([1, 1], gap="medium")
        with col_map:
            st.plotly_chart(build_route_map(instance, None),
                            use_container_width=True)
        with col_conv:
            st.plotly_chart(build_convergence([]),
                            use_container_width=True)

        st.markdown(_build_legend_html(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
