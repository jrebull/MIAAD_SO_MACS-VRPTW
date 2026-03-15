"""Demo en vivo del algoritmo MACS-VRPTW con visualización de convergencia en tiempo real."""

import time
import sys
import platform
import threading
import queue
import matplotlib
if platform.system() == "Darwin":
    matplotlib.use("macosx")
else:
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="WARNING")

from src.algorithm.local_search.or_opt import OrOpt
from src.algorithm.macs_vrptw import MACS_VRPTW
from src.parsers.solomon_parser import parse_solomon_instance
from src.utils.seed import set_global_seed

# --- Paleta UACJ ---
AZUL = "#003366"
ORO = "#C8962E"
GRIS = "#555555"
VERDE = "#2D936C"
ROJO = "#D64045"
LIGHT_BG = "#f5f6f8"

ROUTE_COLORS = [
    "#003366", "#C8962E", "#5A72A0", "#D64045", "#2D936C",
    "#7B2D8E", "#E8823A", "#3A86FF", "#FF006E", "#8338EC",
]

BKS_DISTANCE = 588.32
BKS_VEHICLES = 3

PHASE_DESC = {
    "init": (
        "Construyendo solucion inicial con Nearest Neighbor...",
        "Cada vehiculo visita al cliente mas cercano factible.\n"
        "Solucion rapida pero no optima — punto de partida.",
    ),
    "ACS-VEI": (
        "Colonia ACS-VEI: reduciendo vehiculos...",
        "Hormigas intentan servir clientes con v-1 vehiculos.\n"
        "Feromonas + regla pseudo-aleatoria (q0=0.9).",
    ),
    "ACS-TIME": (
        "Colonia ACS-TIME: optimizando distancia...",
        "Hormigas buscan rutas mas cortas con vehiculos fijos.\n"
        "Or-opt reordena segmentos de 1-3 clientes.",
    ),
    "done": (
        "Algoritmo finalizado.",
        "Sin mejora en ultimas iteraciones — paro automatico.\n"
        "La mejor solucion global (psi_gb) es el resultado.",
    ),
}

IMPROVEMENT_DESC = {
    "nn": (
        "Solucion inicial construida por Nearest Neighbor.",
        "Heuristica greedy: visita al cliente mas cercano.\n"
        "Rapida pero no optima — las hormigas la mejoraran.",
    ),
    "vei": (
        "ACS-VEI redujo vehiculos!",
        "Hormiga encontro solucion factible con menos vehiculos.\n"
        "Se reinician colonias con el nuevo limite.",
    ),
    "time": (
        "ACS-TIME encontro ruta mas corta!",
        "Hormiga construyo rutas con menor distancia total.\n"
        "Or-opt reordeno segmentos para acortar recorrido.",
    ),
}

PHASE_OBJ = {
    "init": "Construyendo solucion inicial con heuristica greedy",
    "ACS-VEI": "Fase 1: Reducir numero de vehiculos",
    "ACS-TIME": "Fase 2: Minimizar distancia total de las rutas",
    "done": "Busqueda finalizada",
}

plt.rcParams.update({"font.size": 12})


def create_figure(instance):
    """Crea la figura compacta optimizada para caber en pantalla."""
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor("white")

    gs = GridSpec(3, 2, figure=fig,
                  height_ratios=[0.5, 2.2, 1.2],
                  hspace=0.30, wspace=0.25)

    # ===================== HEADER =====================
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")

    ax_header.text(0.50, 0.82,
                   "MACS-VRPTW  —  Demo en Vivo",
                   fontsize=22, fontweight="bold", color=AZUL,
                   ha="center", va="center")
    ax_header.text(0.50, 0.45,
                   "Rutas optimas para vehiculos con ventanas de tiempo  |  "
                   "Min. vehiculos y distancia  |  "
                   "C208 (100 clientes)  |  BKS: 3 veh / 588.32",
                   fontsize=10.5, color=GRIS, ha="center", va="center")

    obj_text = ax_header.text(
        0.50, 0.10,
        "▶  " + PHASE_OBJ["init"],
        fontsize=12, color=ORO, ha="center", va="center", fontweight="bold")

    # ===================== GRAFICAS =====================
    ax_routes = fig.add_subplot(gs[1, 0])
    ax_conv = fig.add_subplot(gs[1, 1])

    n = instance.num_customers
    ax_routes.set_title(f"Mapa de Rutas — {n} clientes",
                        fontsize=14, color=AZUL, fontweight="bold", pad=6)
    ax_routes.set_xlabel("Posicion X", fontsize=11)
    ax_routes.set_ylabel("Posicion Y", fontsize=11)
    ax_routes.tick_params(labelsize=9)
    ax_routes.grid(True, alpha=0.3)

    xs = [c.x for c in instance.customers]
    ys = [c.y for c in instance.customers]
    ax_routes.scatter(xs, ys, c="#aaaaaa", s=22, zorder=2, alpha=0.6)
    for c in instance.customers:
        ax_routes.annotate(str(c.id), (c.x, c.y), fontsize=5, color="#888888",
                           ha="center", va="bottom", xytext=(0, 2),
                           textcoords="offset points", zorder=2)
    ax_routes.scatter(instance.depot.x, instance.depot.y, marker="*", s=220,
                      c="red", edgecolors="darkred", linewidth=1, zorder=5)
    ax_routes.annotate("Deposito", (instance.depot.x, instance.depot.y),
                       fontsize=9, color="darkred", fontweight="bold",
                       ha="center", va="bottom", xytext=(0, 10),
                       textcoords="offset points", zorder=5)

    ax_conv.set_title("Convergencia", fontsize=14, color=AZUL,
                      fontweight="bold", pad=6)
    ax_conv.set_xlabel("Tiempo (s)", fontsize=11)
    ax_conv.set_ylabel("Distancia total", color=AZUL, fontsize=11)
    ax_conv.tick_params(labelsize=9)
    ax_conv.grid(True, alpha=0.3)
    ax_conv.axhline(y=BKS_DISTANCE, color=VERDE, linestyle="--",
                    linewidth=1.5, alpha=0.7)
    ax_conv.text(0.02, BKS_DISTANCE + 5, f"BKS = {BKS_DISTANCE}",
                 transform=ax_conv.get_yaxis_transform(),
                 fontsize=10, color=VERDE, fontweight="bold")
    ax_conv2 = ax_conv.twinx()
    ax_conv2.set_ylabel("Vehiculos", color=ORO, fontsize=11)
    ax_conv2.tick_params(axis="y", labelcolor=ORO, labelsize=9)

    # ===================== BOTTOM LEFT — Log =====================
    ax_log = fig.add_subplot(gs[2, 0])
    ax_log.set_xlim(0, 1)
    ax_log.set_ylim(0, 1)
    ax_log.axis("off")
    ax_log.set_facecolor(LIGHT_BG)
    for spine in ax_log.spines.values():
        spine.set_visible(True)
        spine.set_color("#cccccc")

    # ===================== BOTTOM RIGHT — Legend =====================
    ax_legend = fig.add_subplot(gs[2, 1])
    ax_legend.set_xlim(0, 1)
    ax_legend.set_ylim(0, 1)
    ax_legend.axis("off")
    ax_legend.set_facecolor(LIGHT_BG)
    for spine in ax_legend.spines.values():
        spine.set_visible(True)
        spine.set_color("#cccccc")

    ax_legend.text(0.05, 0.95, "Componentes del algoritmo",
                   fontsize=12, fontweight="bold", color=AZUL, va="top")

    legend_items = [
        ("#aaaaaa", "o",  "100 clientes (C208)"),
        ("red",     "*",  "Deposito central"),
        (GRIS,      "s",  "Nearest Neighbor — sol. inicial"),
        (ORO,       "s",  "ACS-VEI — reduce vehiculos"),
        (AZUL,      "s",  "ACS-TIME — optimiza distancia"),
        (VERDE,     "s",  "Or-opt — busqueda local"),
    ]
    for i, (color, marker, label) in enumerate(legend_items):
        y = 0.83 - i * 0.11
        ax_legend.plot(0.05, y, marker, color=color, markersize=10,
                       transform=ax_legend.transAxes, markeredgecolor="white",
                       markeredgewidth=0.5)
        ax_legend.text(0.11, y, label, fontsize=10.5, color="#333333",
                       va="center", transform=ax_legend.transAxes)

    # Timer en esquina inferior derecha del panel leyenda
    timer_text = ax_legend.text(0.95, 0.07, "00:00",
                                fontsize=28, fontweight="bold", color=ORO,
                                ha="right", va="center", fontfamily="monospace")

    plt.subplots_adjust(top=0.97, bottom=0.04, left=0.06, right=0.95)
    return (fig, ax_header, ax_routes, ax_conv, ax_conv2,
            ax_log, ax_legend, timer_text, obj_text)


def update_routes(ax, instance, solution):
    """Redibuja las rutas."""
    while len(ax.lines) > 0:
        ax.lines[0].remove()
    while len(ax.collections) > 2:
        ax.collections[-1].remove()

    nv = solution.num_vehicles()
    dist = solution.total_distance(instance)

    for r_idx, route in enumerate(solution.routes):
        if not route.customer_ids:
            continue
        color = ROUTE_COLORS[r_idx % len(ROUTE_COLORS)]
        all_ids = [0] + route.customer_ids + [0]
        rx = [instance.all_nodes[nid].x for nid in all_ids]
        ry = [instance.all_nodes[nid].y for nid in all_ids]
        ax.plot(rx, ry, "-", color=color, linewidth=2, alpha=0.8, zorder=3)
        ax.scatter(rx[1:-1], ry[1:-1], s=30, color=color,
                   edgecolors="white", linewidth=0.5, zorder=4)

    ax.set_title(f"Mapa de Rutas — {nv} vehiculos, distancia = {dist:.2f}",
                 fontsize=14, color=AZUL, fontweight="bold", pad=6)


def update_convergence(ax1, ax2, times, distances, vehicles):
    """Actualiza la convergencia."""
    for line in ax1.lines[:]:
        line.remove()
    for line in ax2.lines[:]:
        line.remove()
    for coll in ax1.collections[:]:
        coll.remove()
    for coll in ax2.collections[:]:
        coll.remove()

    ax1.axhline(y=BKS_DISTANCE, color=VERDE, linestyle="--", linewidth=1.5, alpha=0.7)
    ax1.step(times, distances, where="post", color=AZUL, linewidth=2.5, alpha=0.8)
    ax1.scatter(times, distances, color=AZUL, s=80, zorder=5,
                edgecolors="white", linewidth=1.5)
    ax1.annotate(f"{distances[-1]:.2f}",
                 (times[-1], distances[-1]),
                 fontsize=12, color=AZUL, fontweight="bold",
                 ha="center", xytext=(0, 14), textcoords="offset points")

    ax2.step(times, vehicles, where="post", color=ORO, linewidth=2.5, alpha=0.7)
    ax2.scatter(times, vehicles, color=ORO, s=60, zorder=5,
                edgecolors="white", linewidth=1.5, marker="s")
    ax2.set_ylim(0, max(vehicles) + 2)
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    if len(times) > 1:
        ax1.set_xlim(-5, max(times) * 1.15)


def update_log(ax_log, log_lines, description, detail, progress_text,
               bks_reached=False):
    """Redibuja el panel de log con historial de modulos ejecutados.

    Layout vertical (y 0→1):
        0.95  barra de progreso
        0.78  descripcion principal
        0.63  detalle secundario (2 lineas)
        0.44  separador
        0.40  "Modulos ejecutados:"
        0.30, 0.20, 0.10  ultimas 3 entradas del log
        0.02  BKS badge (si aplica)
    """
    ax_log.clear()
    ax_log.set_xlim(0, 1)
    ax_log.set_ylim(0, 1)
    ax_log.axis("off")
    ax_log.set_facecolor(LIGHT_BG)
    for spine in ax_log.spines.values():
        spine.set_visible(True)
        spine.set_color("#cccccc")

    # Barra de progreso
    ax_log.text(0.03, 0.95, progress_text, fontsize=9.5, fontweight="bold",
                color=AZUL, fontfamily="monospace", va="top")

    # Descripcion principal
    ax_log.text(0.03, 0.78, description, fontsize=11,
                color=AZUL, va="top", fontweight="bold")

    # Detalle secundario
    ax_log.text(0.03, 0.63, detail, fontsize=9.5,
                color=GRIS, va="top", fontstyle="italic", linespacing=1.3)

    # Separador
    ax_log.plot([0.03, 0.97], [0.44, 0.44], color="#cccccc", linewidth=0.8,
                transform=ax_log.transAxes)

    # Titulo log
    ax_log.text(0.03, 0.40, "Modulos ejecutados:", fontsize=9.5,
                fontweight="bold", color=GRIS, va="top")

    # Ultimas 3 entradas
    recent = log_lines[-3:]
    for i, (icon, module, msg, color) in enumerate(recent):
        y = 0.30 - i * 0.10
        is_last = (i == len(recent) - 1)
        weight = "bold" if is_last else "normal"
        alpha = 1.0 if is_last else 0.50
        ax_log.text(0.03, y, f"[{icon}] {module:<22s} {msg}",
                    fontsize=9.5, fontfamily="monospace", color=color,
                    fontweight=weight, alpha=alpha, va="center")



def main():
    """Ejecuta la demo en vivo."""
    print("\n  MACS-VRPTW — Demo en Vivo", flush=True)
    print("  Abriendo ventana...\n", flush=True)

    seed = 42
    num_ants = 5
    max_iterations = 50
    max_no_improvement = 3

    instance = parse_solomon_instance("data/c208.txt")
    set_global_seed(seed)

    plt.ion()
    (fig, ax_header, ax_routes, ax_conv, ax_conv2,
     ax_log, ax_legend, timer_text, obj_text) = create_figure(instance)
    fig.canvas.draw()
    plt.show(block=False)
    fig.canvas.flush_events()

    state = {
        "times": [], "distances": [], "vehicles": [],
        "log_lines": [],
        "description": "", "detail": "",
        "progress_text": "",
        "bks_reached": False,
    }

    event_queue = queue.Queue()

    def on_improvement(solution, entry):
        event_queue.put(("improvement", solution.copy(), entry))

    def on_iteration(info):
        event_queue.put(("iteration", None, info))

    local_search = OrOpt()

    state["log_lines"].append(("CFG", "config_loader.py",
        f"seed={seed}  ants={num_ants}  iter={max_iterations}", GRIS))
    state["log_lines"].append(("DAT", "solomon_parser.py",
        f"{instance.num_customers} clientes, Q={instance.capacity}", GRIS))
    state["log_lines"].append(("OPT", "or_opt.py",
        "Busqueda local Or-opt lista", GRIS))
    state["description"], state["detail"] = PHASE_DESC["init"]
    state["progress_text"] = "Preparando..."
    obj_text.set_text("▶  " + PHASE_OBJ["init"])
    update_log(ax_log, state["log_lines"],
               state["description"], state["detail"], state["progress_text"])
    fig.canvas.draw()
    fig.canvas.flush_events()

    result_holder = [None]

    def run_algorithm():
        macs = MACS_VRPTW(
            instance=instance,
            num_ants=num_ants,
            beta=1.0,
            q0=0.9,
            rho=0.1,
            max_iterations=max_iterations,
            max_no_improvement=max_no_improvement,
            local_search=local_search,
            on_improvement=on_improvement,
            on_iteration=on_iteration,
        )
        result_holder[0] = macs.solve()
        event_queue.put(("done", None, None))

    worker = threading.Thread(target=run_algorithm, daemon=True)
    start_time = time.time()
    worker.start()

    finished = False
    last_draw_time = 0

    while not finished:
        now = time.time()
        elapsed = now - start_time
        mins, secs = int(elapsed) // 60, int(elapsed) % 60
        timer_text.set_text(f"{mins:02d}:{secs:02d}")

        needs_full_draw = False
        needs_log_draw = False

        while True:
            try:
                event = event_queue.get_nowait()
            except queue.Empty:
                break

            etype = event[0]

            if etype == "done":
                finished = True
                break

            elif etype == "improvement":
                _, solution, entry = event
                ev = entry["event"]
                nv = entry["num_vehicles"]
                dist = entry["total_distance"]
                el = entry["elapsed_time"]
                m, s = int(el) // 60, int(el) % 60

                state["times"].append(el)
                state["distances"].append(dist)
                state["vehicles"].append(nv)

                if "NN" in ev or "inicial" in ev.lower():
                    icon, module, color = "NN ", "nearest_neighbor.py", GRIS
                    state["description"], state["detail"] = \
                        IMPROVEMENT_DESC["nn"]
                elif "VEI" in ev:
                    icon, module, color = "VEI", "acs_vei.py", ORO
                    state["description"] = \
                        f"ACS-VEI redujo a {nv} vehiculos!"
                    state["detail"] = IMPROVEMENT_DESC["vei"][1]
                elif "TIME" in ev:
                    icon, module, color = "TIM", "acs_time.py", AZUL
                    state["description"] = \
                        f"ACS-TIME mejoro distancia a {dist:.2f}"
                    state["detail"] = IMPROVEMENT_DESC["time"][1]
                else:
                    icon, module, color = "SYS", "macs_vrptw.py", GRIS

                state["log_lines"].append((icon, module,
                    f"{nv} veh | {dist:.2f} | {m:02d}:{s:02d}", color))

                update_routes(ax_routes, instance, solution)
                update_convergence(ax_conv, ax_conv2,
                                   state["times"], state["distances"],
                                   state["vehicles"])

                if abs(dist - BKS_DISTANCE) < 0.01 and nv <= BKS_VEHICLES:
                    state["bks_reached"] = True
                    obj_text.set_text(
                        "BKS Alcanzada  |  3 veh  |  588.32  |  Gap 0.00%")
                    obj_text.set_color(VERDE)
                    obj_text.set_fontsize(14)
                    obj_text.set_bbox(dict(
                        facecolor=VERDE, edgecolor=VERDE, alpha=0.95,
                        pad=8, boxstyle="round,pad=0.4"))
                    obj_text.set_color("white")

                needs_full_draw = True

            elif etype == "iteration":
                _, _, info = event
                phase = info["phase"]
                iteration = info["iteration"]
                max_iter = info["max_iterations"]
                nv = info["num_vehicles"]
                dist = info["total_distance"]

                bar_w = 20
                progress = min(iteration / max(max_iter, 1), 1.0)
                filled = int(bar_w * progress)
                bar = "\u2588" * filled + "\u2591" * (bar_w - filled)

                state["progress_text"] = (
                    f"[{bar}] iter {iteration}/{max_iter} "
                    f"| {phase} | {nv} veh | {dist:.2f}")
                phase_info = PHASE_DESC.get(phase, ("Ejecutando...", ""))
                state["description"], state["detail"] = phase_info

                if phase == "ACS-VEI":
                    obj_label = (
                        f"Fase 1: Reducir vehiculos "
                        f"({nv} actuales → intentando {nv - 1})")
                elif phase == "ACS-TIME":
                    obj_label = (
                        f"Fase 2: Minimizar distancia "
                        f"({dist:.2f}) con {nv} vehiculos")
                else:
                    obj_label = PHASE_OBJ.get(phase, "Ejecutando...")
                if not state["bks_reached"]:
                    obj_text.set_text("▶  " + obj_label)

                needs_log_draw = True

        # --- Redraw strategy ---
        if needs_full_draw or needs_log_draw:
            update_log(ax_log, state["log_lines"],
                       state["description"], state["detail"],
                       state["progress_text"], state["bks_reached"])
            fig.canvas.draw()
            fig.canvas.flush_events()
            last_draw_time = now
        elif now - last_draw_time > 0.8:
            # Timer-only update: full draw to ensure timer renders
            fig.canvas.draw()
            fig.canvas.flush_events()
            last_draw_time = now

        try:
            plt.pause(0.3)
        except Exception:
            break

    # --- Final ---
    elapsed = time.time() - start_time
    solution = result_holder[0]
    nv = solution.num_vehicles()
    dist = solution.total_distance(instance)
    mins, secs = int(elapsed) // 60, int(elapsed) % 60

    timer_text.set_text(f"{mins:02d}:{secs:02d}")
    timer_text.set_color(VERDE if state["bks_reached"] else AZUL)

    state["log_lines"].append(("FIN", "macs_vrptw.py",
        f"FINAL: {nv} veh | {dist:.2f} | {mins:02d}:{secs:02d}",
        VERDE))
    state["description"], state["detail"] = PHASE_DESC["done"]

    if state["bks_reached"]:
        state["progress_text"] = (
            f"OPTIMO ENCONTRADO | {nv} veh | "
            f"{dist:.2f} dist | Gap = 0.00%")
        obj_text.set_text(
            "  BKS Alcanzada  |  3 veh  |  588.32  |  Gap 0.00%  ")
        obj_text.set_color("white")
        obj_text.set_fontsize(14)
        obj_text.set_bbox(dict(
            facecolor=VERDE, edgecolor=VERDE, alpha=0.95,
            pad=8, boxstyle="round,pad=0.4"))
    else:
        gap = ((dist - BKS_DISTANCE) / BKS_DISTANCE) * 100
        state["progress_text"] = (
            f"FINALIZADO | {nv} veh | "
            f"{dist:.2f} dist | Gap = {gap:.2f}%")
        obj_text.set_text(f"Finalizado — Gap vs BKS: {gap:.2f}%")
        obj_text.set_color(AZUL)

    update_log(ax_log, state["log_lines"],
               state["description"], state["detail"], state["progress_text"],
               state["bks_reached"])

    if not state["bks_reached"]:
        update_routes(ax_routes, instance, solution)

    fig.canvas.draw()
    fig.canvas.flush_events()

    print(f"  Resultado: {nv} vehiculos, {dist:.2f} distancia", flush=True)
    print(f"  Tiempo: {mins:02d}:{secs:02d} ({elapsed:.1f}s)", flush=True)
    print("  Cierra la ventana para terminar.\n", flush=True)

    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
