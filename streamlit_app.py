"""
MACS-VRPTW Dashboard | MIAAD UACJ
Streamlit dashboard for visualizing results of the MACS-VRPTW algorithm.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.parsers.solomon_parser import parse_solomon_instance, parse_bks_solution
from src.evaluation.benchmark import PAPER_RESULTS_C208, BKS_C208, compare_with_references
from src.models.solution import Solution, Route
from src.evaluation.metrics import solution_summary

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

AZUL = "#003366"
ORO = "#C8962E"
GRIS = "#555555"
ACENTO = "#E8F0FE"

ROUTE_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5",
]

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MACS-VRPTW Dashboard | MIAAD UACJ",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    /* Sidebar background */
    [data-testid="stSidebar"] {{
        background-color: {ACENTO};
    }}
    /* Headers */
    h1, h2, h3 {{
        color: {AZUL};
    }}
    /* Metric value */
    [data-testid="stMetricValue"] {{
        color: {AZUL};
    }}
    /* Metric delta */
    [data-testid="stMetricDelta"] {{
        color: {ORO};
    }}
    /* Tab labels */
    .stTabs [data-baseweb="tab"] {{
        color: {AZUL};
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom-color: {ORO};
        color: {AZUL};
        font-weight: bold;
    }}
    /* UACJ badge */
    .uacj-badge {{
        background-color: {AZUL};
        color: white;
        padding: 10px 16px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-top: 20px;
    }}
    .uacj-badge small {{
        color: {ORO};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Cached helpers
# ---------------------------------------------------------------------------

@st.cache_data
def load_instance(filepath: str):
    """Parse a Solomon instance file and return serialisable data."""
    inst = parse_solomon_instance(filepath)
    nodes = []
    for n in inst.all_nodes:
        nodes.append({
            "id": n.id,
            "x": n.x,
            "y": n.y,
            "demand": n.demand,
            "ready_time": n.ready_time,
            "due_date": n.due_date,
            "service_time": n.service_time,
            "is_depot": n.is_depot,
        })
    return {
        "name": inst.name,
        "num_vehicles": inst.num_vehicles,
        "capacity": inst.capacity,
        "num_customers": inst.num_customers,
        "nodes": nodes,
    }


def _get_instance_object(filepath: str):
    """Return the actual Instance object (not cached to avoid unhashable numpy)."""
    return parse_solomon_instance(filepath)


@st.cache_data
def load_results_json(filepath: str) -> dict:
    """Load a results JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_data_files() -> list[str]:
    """Return .txt files in the data/ directory."""
    if not DATA_DIR.exists():
        return []
    return sorted([f.name for f in DATA_DIR.glob("*.txt") if "bks" not in f.name.lower()])


def _list_results_files() -> list[str]:
    """Return .json result files in the results/ directory."""
    if not RESULTS_DIR.exists():
        return []
    return sorted([f.name for f in RESULTS_DIR.glob("*.json")])


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color:{AZUL}; margin-bottom:0;'>MACS-VRPTW</h2>", unsafe_allow_html=True)
    st.caption("Multi-Ant Colony System for VRPTW")
    st.divider()

    # Instance selector
    st.subheader("Instancia Solomon")
    instance_files = _list_data_files()
    if instance_files:
        selected_instance = st.selectbox(
            "Archivo de instancia",
            instance_files,
            index=0,
            help="Archivos .txt en data/",
        )
        instance_path = str(DATA_DIR / selected_instance)
    else:
        st.warning("No se encontraron instancias en data/")
        selected_instance = None
        instance_path = None

    st.divider()

    # Parameter sliders (for reference display only -- no algorithm execution)
    st.subheader("Parametros de referencia")
    param_num_ants = st.slider("Num. hormigas", 1, 50, 10, help="Numero de hormigas por colonia")
    param_beta = st.slider("Beta", 0.0, 10.0, 1.0, 0.1, help="Peso de la heuristica de visibilidad")
    param_q0 = st.slider("q0", 0.0, 1.0, 0.9, 0.01, help="Probabilidad de explotacion vs exploracion")
    param_rho = st.slider("Rho", 0.0, 1.0, 0.1, 0.01, help="Tasa de evaporacion de feromona")
    param_max_iter = st.slider("Max iteraciones", 10, 1000, 200, 10)

    st.divider()

    # Results file selector
    st.subheader("Resultados")
    results_files = _list_results_files()
    if results_files:
        selected_results = st.selectbox(
            "Archivo de resultados",
            results_files,
            index=0,
            help="Archivos .json en results/",
        )
        results_path = str(RESULTS_DIR / selected_results)
    else:
        selected_results = None
        results_path = None
        st.info("Sin archivos en results/. Ejecute main.py primero.")

    st.divider()

    # UACJ badge
    st.markdown(
        """
        <div class="uacj-badge">
            UACJ<br>
            <small>Maestria en Ingenieria y<br>Analisis Avanzado de Datos</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Load selected data
# ---------------------------------------------------------------------------
instance_data = None
results_data = None

if instance_path:
    try:
        instance_data = load_instance(instance_path)
    except Exception as exc:
        st.error(f"Error al cargar la instancia: {exc}")

if results_path:
    try:
        results_data = load_results_json(results_path)
    except Exception as exc:
        st.error(f"Error al cargar resultados: {exc}")

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='text-align:center; color:{AZUL};'>MACS-VRPTW Dashboard</h1>",
    unsafe_allow_html=True,
)
if instance_data:
    st.markdown(
        f"<p style='text-align:center; color:{GRIS};'>Instancia: <b>{instance_data['name']}</b> "
        f"&mdash; {instance_data['num_customers']} clientes, capacidad {instance_data['capacity']}</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# KPI row (if results available)
# ---------------------------------------------------------------------------
if results_data and "solution" in results_data:
    sol = results_data["solution"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vehiculos", sol.get("num_vehicles", "?"))
    col2.metric("Distancia total", f"{sol.get('total_distance', 0):.2f}")
    col3.metric("Clientes servidos", sol.get("num_served_customers", "?"))
    feasible_label = "Si" if results_data.get("feasible", sol.get("is_feasible", False)) else "No"
    col4.metric("Factible", feasible_label)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_map, tab_conv, tab_compare, tab_detail, tab_analysis = st.tabs([
    "Mapa de Rutas",
    "Convergencia",
    "Comparacion con Paper",
    "Detalle de Solucion",
    "Analisis de Instancia",
])

# ===== TAB 1 -- Mapa de Rutas =============================================
with tab_map:
    st.subheader("Mapa de Rutas")

    if instance_data is None:
        st.warning("Seleccione una instancia valida en el panel lateral.")
    elif results_data is None or "solution" not in results_data:
        st.info("No hay resultados cargados. Ejecute el algoritmo con main.py y seleccione un archivo de resultados.")
    else:
        nodes_df = pd.DataFrame(instance_data["nodes"])
        sol_info = results_data["solution"]
        routes = sol_info.get("routes", [])

        fig_map = go.Figure()

        # Draw routes as lines
        for idx, route in enumerate(routes):
            color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
            customer_ids = route.get("customers", [])
            if not customer_ids:
                continue

            # Build path: depot -> customers -> depot
            depot = nodes_df[nodes_df["id"] == 0].iloc[0]
            path_ids = [0] + customer_ids + [0]
            path_x = []
            path_y = []
            for cid in path_ids:
                node = nodes_df[nodes_df["id"] == cid].iloc[0]
                path_x.append(node["x"])
                path_y.append(node["y"])

            fig_map.add_trace(go.Scatter(
                x=path_x, y=path_y,
                mode="lines",
                line=dict(color=color, width=2),
                name=f"Ruta {route.get('route_id', idx + 1)} ({len(customer_ids)} cl, d={route.get('distance', 0):.1f})",
                hoverinfo="name",
                legendgroup=f"route_{idx}",
            ))

            # Customer dots for this route
            route_nodes = nodes_df[nodes_df["id"].isin(customer_ids)]
            fig_map.add_trace(go.Scatter(
                x=route_nodes["x"], y=route_nodes["y"],
                mode="markers",
                marker=dict(color=color, size=8, line=dict(color="white", width=1)),
                customdata=np.stack([
                    route_nodes["id"],
                    route_nodes["demand"],
                    route_nodes["ready_time"],
                    route_nodes["due_date"],
                    route_nodes["service_time"],
                ], axis=-1),
                hovertemplate=(
                    "<b>Cliente %{customdata[0]:.0f}</b><br>"
                    "Demanda: %{customdata[1]:.0f}<br>"
                    "Ventana: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<br>"
                    "Servicio: %{customdata[4]:.0f}<br>"
                    "Pos: (%{x:.1f}, %{y:.1f})<extra></extra>"
                ),
                showlegend=False,
                legendgroup=f"route_{idx}",
            ))

        # Depot marker (red star)
        depot_row = nodes_df[nodes_df["id"] == 0].iloc[0]
        fig_map.add_trace(go.Scatter(
            x=[depot_row["x"]], y=[depot_row["y"]],
            mode="markers",
            marker=dict(symbol="star", color="red", size=18, line=dict(color="darkred", width=1.5)),
            name="Deposito",
            hovertemplate="<b>Deposito</b><br>Pos: (%{x:.1f}, %{y:.1f})<extra></extra>",
        ))

        fig_map.update_layout(
            height=600,
            xaxis_title="X",
            yaxis_title="Y",
            plot_bgcolor="white",
            legend=dict(bgcolor=ACENTO, bordercolor=AZUL, borderwidth=1),
            margin=dict(l=40, r=40, t=40, b=40),
        )
        fig_map.update_xaxes(showgrid=True, gridcolor="#eeeeee")
        fig_map.update_yaxes(showgrid=True, gridcolor="#eeeeee", scaleanchor="x")

        st.plotly_chart(fig_map, use_container_width=True)

# ===== TAB 2 -- Convergencia ===============================================
with tab_conv:
    st.subheader("Convergencia del Algoritmo")

    if results_data is None:
        st.info("No hay resultados cargados.")
    else:
        history = results_data.get("history", [])
        if not history:
            st.info("El archivo de resultados no contiene historial de convergencia.")
        else:
            hist_df = pd.DataFrame(history)

            # Ensure numeric columns
            for col in ["iteration", "total_distance", "num_vehicles", "elapsed_time"]:
                if col in hist_df.columns:
                    hist_df[col] = pd.to_numeric(hist_df[col], errors="coerce")

            # Find best solution point
            if "total_distance" in hist_df.columns and not hist_df.empty:
                best_idx = hist_df["total_distance"].idxmin()
                best_row = hist_df.loc[best_idx]

                # Distance convergence
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Scatter(
                    x=hist_df["iteration"],
                    y=hist_df["total_distance"],
                    mode="lines+markers",
                    name="Distancia total",
                    line=dict(color=AZUL, width=2),
                    marker=dict(size=6),
                    hovertemplate=(
                        "Iter: %{x}<br>Distancia: %{y:.2f}<br>"
                        "<extra></extra>"
                    ),
                ))
                # Marker for best
                fig_dist.add_trace(go.Scatter(
                    x=[best_row["iteration"]],
                    y=[best_row["total_distance"]],
                    mode="markers",
                    marker=dict(color=ORO, size=14, symbol="star", line=dict(color=AZUL, width=2)),
                    name=f"Mejor: {best_row['total_distance']:.2f}",
                    hovertemplate=(
                        "<b>Mejor solucion</b><br>"
                        "Iter: %{x}<br>Distancia: %{y:.2f}<extra></extra>"
                    ),
                ))
                fig_dist.update_layout(
                    title="Distancia total vs Iteracion",
                    xaxis_title="Iteracion",
                    yaxis_title="Distancia total",
                    height=400,
                    plot_bgcolor="white",
                    legend=dict(bgcolor=ACENTO),
                )
                fig_dist.update_xaxes(showgrid=True, gridcolor="#eeeeee")
                fig_dist.update_yaxes(showgrid=True, gridcolor="#eeeeee")
                st.plotly_chart(fig_dist, use_container_width=True)

                # Vehicles convergence
                if "num_vehicles" in hist_df.columns:
                    fig_veh = go.Figure()
                    fig_veh.add_trace(go.Scatter(
                        x=hist_df["iteration"],
                        y=hist_df["num_vehicles"],
                        mode="lines+markers",
                        name="Num. vehiculos",
                        line=dict(color=ORO, width=2),
                        marker=dict(size=6),
                    ))
                    # Best vehicle count marker
                    best_veh_idx = hist_df["num_vehicles"].idxmin()
                    best_veh_row = hist_df.loc[best_veh_idx]
                    fig_veh.add_trace(go.Scatter(
                        x=[best_veh_row["iteration"]],
                        y=[best_veh_row["num_vehicles"]],
                        mode="markers",
                        marker=dict(color="red", size=14, symbol="star", line=dict(color=AZUL, width=2)),
                        name=f"Min vehiculos: {int(best_veh_row['num_vehicles'])}",
                    ))
                    fig_veh.update_layout(
                        title="Numero de vehiculos vs Iteracion",
                        xaxis_title="Iteracion",
                        yaxis_title="Numero de vehiculos",
                        height=400,
                        plot_bgcolor="white",
                        legend=dict(bgcolor=ACENTO),
                    )
                    fig_veh.update_xaxes(showgrid=True, gridcolor="#eeeeee")
                    fig_veh.update_yaxes(showgrid=True, gridcolor="#eeeeee", dtick=1)
                    st.plotly_chart(fig_veh, use_container_width=True)

            # Event log
            with st.expander("Historial de eventos"):
                st.dataframe(
                    hist_df[["iteration", "num_vehicles", "total_distance", "elapsed_time", "event"]],
                    use_container_width=True,
                    hide_index=True,
                )

# ===== TAB 3 -- Comparacion con Paper =====================================
with tab_compare:
    st.subheader("Comparacion con Resultados de Referencia")

    if results_data is None:
        st.info("No hay resultados cargados para comparar.")
    else:
        sol_info = results_data.get("solution", {})
        our_vehicles = sol_info.get("num_vehicles", None)
        our_distance = sol_info.get("total_distance", None)

        if our_vehicles is None or our_distance is None:
            st.warning("El archivo de resultados no contiene informacion de solucion valida.")
        else:
            comparison = results_data.get("comparison", {})

            # Build comparison table
            ref_data = {
                "Fuente": [
                    "Paper Table 1 (Gambardella et al.)",
                    "Paper Table 2 Best",
                    "BKS (Hasle & Kloster, 2003)",
                    "Nuestro resultado",
                ],
                "Vehiculos": [
                    PAPER_RESULTS_C208["table1"]["vehicles"],
                    PAPER_RESULTS_C208["table2_best"]["vehicles"],
                    BKS_C208["vehicles"],
                    our_vehicles,
                ],
                "Distancia": [
                    PAPER_RESULTS_C208["table1"]["distance"],
                    PAPER_RESULTS_C208["table2_best"]["distance"],
                    BKS_C208["distance"],
                    our_distance,
                ],
            }

            # Calculate gaps for our result
            gap_t1 = ((our_distance - PAPER_RESULTS_C208["table1"]["distance"])
                      / PAPER_RESULTS_C208["table1"]["distance"] * 100) if PAPER_RESULTS_C208["table1"]["distance"] else 0
            gap_t2 = ((our_distance - PAPER_RESULTS_C208["table2_best"]["distance"])
                      / PAPER_RESULTS_C208["table2_best"]["distance"] * 100) if PAPER_RESULTS_C208["table2_best"]["distance"] else 0
            gap_bks = ((our_distance - BKS_C208["distance"])
                       / BKS_C208["distance"] * 100) if BKS_C208["distance"] else 0

            ref_data["Gap vs BKS (%)"] = [
                f"{((PAPER_RESULTS_C208['table1']['distance'] - BKS_C208['distance']) / BKS_C208['distance'] * 100):.2f}",
                f"{((PAPER_RESULTS_C208['table2_best']['distance'] - BKS_C208['distance']) / BKS_C208['distance'] * 100):.2f}",
                "0.00 (referencia)",
                f"{gap_bks:.2f}",
            ]

            comp_df = pd.DataFrame(ref_data)
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

            # Gap summary metrics
            gc1, gc2, gc3 = st.columns(3)
            gc1.metric("Gap vs Paper T1", f"{gap_t1:+.2f}%")
            gc2.metric("Gap vs Paper T2", f"{gap_t2:+.2f}%")
            gc3.metric("Gap vs BKS", f"{gap_bks:+.2f}%")

            st.divider()

            # Horizontal bar chart comparing distances
            st.markdown("**Distancia total por fuente**")
            bar_df = pd.DataFrame({
                "Fuente": ref_data["Fuente"],
                "Distancia": [float(d) for d in ref_data["Distancia"]],
            })
            # Assign colors: highlight our result
            bar_colors = [GRIS, GRIS, AZUL, ORO]

            fig_bar = go.Figure()
            for i, row in bar_df.iterrows():
                fig_bar.add_trace(go.Bar(
                    y=[row["Fuente"]],
                    x=[row["Distancia"]],
                    orientation="h",
                    marker_color=bar_colors[i],
                    name=row["Fuente"],
                    text=f"{row['Distancia']:.2f}",
                    textposition="outside",
                    showlegend=False,
                ))
            fig_bar.update_layout(
                height=300,
                xaxis_title="Distancia total",
                plot_bgcolor="white",
                margin=dict(l=20, r=80, t=20, b=40),
                barmode="group",
            )
            fig_bar.update_xaxes(showgrid=True, gridcolor="#eeeeee")
            fig_bar.update_yaxes(showgrid=False)
            st.plotly_chart(fig_bar, use_container_width=True)

            # Vehicles bar
            st.markdown("**Vehiculos por fuente**")
            veh_df = pd.DataFrame({
                "Fuente": ref_data["Fuente"],
                "Vehiculos": [float(v) for v in ref_data["Vehiculos"]],
            })
            fig_vbar = go.Figure()
            for i, row in veh_df.iterrows():
                fig_vbar.add_trace(go.Bar(
                    y=[row["Fuente"]],
                    x=[row["Vehiculos"]],
                    orientation="h",
                    marker_color=bar_colors[i],
                    name=row["Fuente"],
                    text=f"{row['Vehiculos']:.0f}",
                    textposition="outside",
                    showlegend=False,
                ))
            fig_vbar.update_layout(
                height=280,
                xaxis_title="Numero de vehiculos",
                plot_bgcolor="white",
                margin=dict(l=20, r=80, t=20, b=40),
                barmode="group",
            )
            fig_vbar.update_xaxes(showgrid=True, gridcolor="#eeeeee", dtick=1)
            fig_vbar.update_yaxes(showgrid=False)
            st.plotly_chart(fig_vbar, use_container_width=True)

# ===== TAB 4 -- Detalle de Solucion =======================================
with tab_detail:
    st.subheader("Detalle de Solucion")

    if results_data is None or instance_data is None:
        st.info("Cargue una instancia y un archivo de resultados para ver el detalle.")
    else:
        sol_info = results_data.get("solution", {})
        routes = sol_info.get("routes", [])

        if not routes:
            st.info("No hay rutas en la solucion cargada.")
        else:
            nodes_lookup = {n["id"]: n for n in instance_data["nodes"]}
            capacity = instance_data["capacity"]

            # Summary metrics row
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Total rutas", len(routes))
            mc2.metric("Distancia total", f"{sol_info.get('total_distance', 0):.2f}")
            total_demand = sum(r.get("demand", 0) for r in routes)
            mc3.metric("Demanda total", total_demand)
            avg_customers = sum(len(r.get("customers", [])) for r in routes) / max(len(routes), 1)
            mc4.metric("Prom. clientes/ruta", f"{avg_customers:.1f}")

            st.divider()

            # Per-route expandable details
            for route in routes:
                rid = route.get("route_id", "?")
                customers = route.get("customers", [])
                rdist = route.get("distance", 0)
                rdemand = route.get("demand", 0)
                utilization = (rdemand / capacity * 100) if capacity > 0 else 0

                with st.expander(
                    f"Ruta {rid}  |  {len(customers)} clientes  |  "
                    f"Distancia: {rdist:.2f}  |  Demanda: {rdemand}/{capacity} ({utilization:.0f}%)"
                ):
                    # Build detailed sequence table with cumulative load and timeline
                    rows = []
                    cum_load = 0
                    current_time = 0.0
                    prev_id = 0  # depot

                    for cid in customers:
                        node = nodes_lookup.get(cid, {})
                        demand = node.get("demand", 0)
                        ready = node.get("ready_time", 0)
                        due = node.get("due_date", 0)
                        service = node.get("service_time", 0)

                        # Calculate travel from previous node
                        prev_node = nodes_lookup.get(prev_id, {})
                        dx = node.get("x", 0) - prev_node.get("x", 0)
                        dy = node.get("y", 0) - prev_node.get("y", 0)
                        travel = math.sqrt(dx * dx + dy * dy)

                        arrival = current_time + travel
                        wait = max(0, ready - arrival)
                        start_service = max(arrival, ready)
                        departure = start_service + service
                        cum_load += demand

                        rows.append({
                            "Orden": len(rows) + 1,
                            "Cliente": cid,
                            "X": node.get("x", 0),
                            "Y": node.get("y", 0),
                            "Demanda": demand,
                            "Carga acum.": cum_load,
                            "Llegada": round(arrival, 2),
                            "Espera": round(wait, 2),
                            "Inicio serv.": round(start_service, 2),
                            "Salida": round(departure, 2),
                            "Ventana [a,b]": f"[{ready}, {due}]",
                        })
                        current_time = departure
                        prev_id = cid

                    seq_df = pd.DataFrame(rows)
                    st.dataframe(seq_df, use_container_width=True, hide_index=True)

                    # Gantt-style time window chart
                    if rows:
                        gantt_fig = go.Figure()
                        for row in rows:
                            cid = row["Cliente"]
                            node = nodes_lookup.get(cid, {})
                            ready = node.get("ready_time", 0)
                            due = node.get("due_date", 0)

                            # Time window bar (light)
                            gantt_fig.add_trace(go.Bar(
                                y=[f"C{cid}"],
                                x=[due - ready],
                                base=ready,
                                orientation="h",
                                marker_color=ACENTO,
                                marker_line=dict(color=AZUL, width=1),
                                showlegend=False,
                                hovertemplate=f"Cliente {cid}<br>Ventana: [{ready}, {due}]<extra></extra>",
                            ))
                            # Actual service bar
                            gantt_fig.add_trace(go.Bar(
                                y=[f"C{cid}"],
                                x=[node.get("service_time", 0)],
                                base=row["Inicio serv."],
                                orientation="h",
                                marker_color=ORO,
                                showlegend=False,
                                hovertemplate=(
                                    f"Cliente {cid}<br>"
                                    f"Llegada: {row['Llegada']}<br>"
                                    f"Inicio: {row['Inicio serv.']}<br>"
                                    f"Salida: {row['Salida']}<extra></extra>"
                                ),
                            ))
                            # Arrival marker
                            gantt_fig.add_trace(go.Scatter(
                                x=[row["Llegada"]],
                                y=[f"C{cid}"],
                                mode="markers",
                                marker=dict(color="red", size=8, symbol="triangle-right"),
                                showlegend=False,
                                hovertemplate=f"Llegada: {row['Llegada']:.2f}<extra></extra>",
                            ))

                        gantt_fig.update_layout(
                            title=f"Ventanas de tiempo - Ruta {rid}",
                            xaxis_title="Tiempo",
                            height=max(250, len(rows) * 35 + 100),
                            plot_bgcolor="white",
                            barmode="overlay",
                            margin=dict(l=60, r=40, t=40, b=40),
                            showlegend=False,
                        )
                        gantt_fig.update_xaxes(showgrid=True, gridcolor="#eeeeee")
                        gantt_fig.update_yaxes(showgrid=False, autorange="reversed")
                        st.plotly_chart(gantt_fig, use_container_width=True)

# ===== TAB 5 -- Analisis de Instancia =====================================
with tab_analysis:
    st.subheader("Analisis de Instancia")

    if instance_data is None:
        st.warning("Seleccione una instancia valida en el panel lateral.")
    else:
        nodes_df = pd.DataFrame(instance_data["nodes"])
        customers_df = nodes_df[nodes_df["is_depot"] == False].copy()
        depot_row = nodes_df[nodes_df["is_depot"] == True].iloc[0]

        # Descriptive stats
        st.markdown("**Estadisticas descriptivas de clientes**")
        desc_cols = ["demand", "ready_time", "due_date", "service_time"]
        desc = customers_df[desc_cols].describe().T
        desc.columns = ["Count", "Media", "Std", "Min", "25%", "50%", "75%", "Max"]
        desc.index = ["Demanda", "Ready time", "Due date", "Service time"]
        st.dataframe(desc.style.format("{:.2f}"), use_container_width=True)

        st.divider()

        # Three visualizations in columns
        col_geo, col_right = st.columns([3, 2])

        with col_geo:
            st.markdown("**Distribucion geografica**")
            fig_geo = go.Figure()
            # Customers
            fig_geo.add_trace(go.Scatter(
                x=customers_df["x"], y=customers_df["y"],
                mode="markers",
                marker=dict(
                    color=customers_df["demand"],
                    colorscale=[[0, ACENTO], [1, AZUL]],
                    size=8,
                    colorbar=dict(title="Demanda"),
                    line=dict(color="white", width=0.5),
                ),
                customdata=np.stack([
                    customers_df["id"],
                    customers_df["demand"],
                    customers_df["ready_time"],
                    customers_df["due_date"],
                ], axis=-1),
                hovertemplate=(
                    "<b>Cliente %{customdata[0]:.0f}</b><br>"
                    "Demanda: %{customdata[1]:.0f}<br>"
                    "Ventana: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<br>"
                    "(%{x:.1f}, %{y:.1f})<extra></extra>"
                ),
                name="Clientes",
            ))
            # Depot
            fig_geo.add_trace(go.Scatter(
                x=[depot_row["x"]], y=[depot_row["y"]],
                mode="markers",
                marker=dict(symbol="star", color="red", size=16),
                name="Deposito",
            ))
            fig_geo.update_layout(
                height=450,
                xaxis_title="X", yaxis_title="Y",
                plot_bgcolor="white",
                margin=dict(l=40, r=40, t=20, b=40),
            )
            fig_geo.update_xaxes(showgrid=True, gridcolor="#eeeeee")
            fig_geo.update_yaxes(showgrid=True, gridcolor="#eeeeee", scaleanchor="x")
            st.plotly_chart(fig_geo, use_container_width=True)

        with col_right:
            # Demand histogram
            st.markdown("**Distribucion de demanda**")
            fig_demand = go.Figure()
            fig_demand.add_trace(go.Histogram(
                x=customers_df["demand"],
                marker_color=AZUL,
                opacity=0.85,
            ))
            fig_demand.update_layout(
                xaxis_title="Demanda",
                yaxis_title="Frecuencia",
                height=200,
                plot_bgcolor="white",
                margin=dict(l=40, r=20, t=10, b=40),
            )
            fig_demand.update_xaxes(showgrid=True, gridcolor="#eeeeee")
            fig_demand.update_yaxes(showgrid=True, gridcolor="#eeeeee")
            st.plotly_chart(fig_demand, use_container_width=True)

            # Time window histogram (window width = due_date - ready_time)
            st.markdown("**Distribucion de ancho de ventana de tiempo**")
            customers_df["tw_width"] = customers_df["due_date"] - customers_df["ready_time"]
            fig_tw = go.Figure()
            fig_tw.add_trace(go.Histogram(
                x=customers_df["tw_width"],
                marker_color=ORO,
                opacity=0.85,
            ))
            fig_tw.update_layout(
                xaxis_title="Ancho de ventana (due - ready)",
                yaxis_title="Frecuencia",
                height=200,
                plot_bgcolor="white",
                margin=dict(l=40, r=20, t=10, b=40),
            )
            fig_tw.update_xaxes(showgrid=True, gridcolor="#eeeeee")
            fig_tw.update_yaxes(showgrid=True, gridcolor="#eeeeee")
            st.plotly_chart(fig_tw, use_container_width=True)

        # Additional instance info
        st.divider()
        info1, info2, info3, info4 = st.columns(4)
        info1.metric("Clientes", instance_data["num_customers"])
        info2.metric("Capacidad vehiculo", instance_data["capacity"])
        info3.metric("Max vehiculos", instance_data["num_vehicles"])
        total_demand = int(customers_df["demand"].sum())
        min_vehicles_lb = math.ceil(total_demand / instance_data["capacity"]) if instance_data["capacity"] > 0 else "?"
        info4.metric("Cota inf. vehiculos", min_vehicles_lb, help="ceil(demanda_total / capacidad)")
