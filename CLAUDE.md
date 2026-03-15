# MACS-VRPTW — Proyecto de Replicacion

## Contexto
Replicacion del algoritmo MACS-VRPTW (Gambardella, Taillard, Agazzi 1999) para la materia de Optimizacion Inteligente, MIAAD UACJ. Entrega: 17 de marzo de 2026.

## Instancia
- **C208** (Solomon Benchmark, 100 clientes, Clustered tipo 2)
- BKS: 3 vehiculos, 588.32 distancia

## Arquitectura
- Python 3.11+, principios SOLID/Clean Code
- Configuracion via YAML (`config/`)
- Logging con loguru (nunca print)
- Seeds controlados para reproducibilidad
- Type hints en todas las funciones
- Docstrings en espanol, codigo en ingles

## Parametros del articulo
- m=10 hormigas, q0=0.9, beta=1, rho=0.1
- tau_0 = 1/(n * J_nn)

## Comandos principales
- Ejecutar algoritmo (3 corridas): `python main.py`
- Dashboard de resultados (5 tabs): `streamlit run streamlit_app.py`
- Demo en vivo Streamlit + Plotly: `streamlit run streamlit_demo.py`
- Demo en vivo matplotlib: `python demo_live.py`
- Generar figuras: `python generate_figures.py`
- Tests: `pytest tests/ -v`

## Archivos de visualizacion
- `streamlit_app.py` — Dashboard principal con 5 pestanas (Mapa, Convergencia, Comparacion, Detalle, Analisis). Muestra resultados pre-calculados desde `results/*.json`. NO tiene demo en vivo integrada.
- `streamlit_demo.py` — Demo standalone con Plotly interactivo, parametros en sidebar, cards HTML customizadas, convergencia con subplots apilados (distancia + vehiculos), log de modulos y badge BKS. Este es el unico lugar con demo en vivo Streamlit.
- `demo_live.py` — Demo matplotlib con GridSpec (18x10), timer en vivo cada 0.8s con `fig.canvas.draw()`, mapa de rutas animado, convergencia en dos subplots, log de modulos .py ejecutados. BKS badge se muestra en el header via `obj_text`.

## Algoritmo (src/algorithm/)
- `macs_vrptw.py` — Controlador principal (Figure 2). Callbacks `on_improvement` y `on_iteration` para visualizacion en tiempo real.
- `acs_vei.py` — Colonia ACS-VEI (Figure 4). Minimiza vehiculos con v-1.
- `acs_time.py` — Colonia ACS-TIME (Figure 3). Minimiza distancia con Or-opt.
- `ant.py` — Construccion de hormiga (Figure 6).
- `pheromone.py` — Matriz de feromonas (Eq. 2, 3).
- `local_search/or_opt.py` — Or-opt (1, 2, 3 clientes).
- `local_search/cross_exchange.py` — CROSS exchange.

## Colores del proyecto
- AZUL `#003366` — color primario, ACS-TIME
- ORO `#C8962E` — secundario, ACS-VEI
- VERDE `#2D936C` — BKS alcanzada
- GRIS `#555555` — Nearest Neighbor, texto secundario
- ROJO `#D64045` — deposito
- ACENTO `#E8F0FE` — fondos claros

## Convergencia (graficas)
- Siempre dos subplots apilados: distancia arriba (70%), vehiculos abajo (30%)
- Markers coloreados por tipo de evento (GRIS=NN, ORO=VEI, AZUL=TIME)
- Lineas BKS de referencia en estilo dot con color VERDE
- Hover labels con nombre del evento

## Notas importantes
- No usar `st.balloons()` en Streamlit
- En matplotlib macOS usar `fig.canvas.draw()` (no `draw_idle()`) para timer en vivo
- Los resultados JSON se guardan en `results/`
- Las figuras PNG (300 DPI) se guardan en `Figures/`
- La demo en vivo solo esta en `streamlit_demo.py` y `demo_live.py`, NO en `streamlit_app.py`
