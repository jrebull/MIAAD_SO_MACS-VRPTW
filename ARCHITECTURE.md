# Arquitectura del Proyecto MACS-VRPTW

## Diagrama General

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PUNTOS DE ENTRADA                           │
│                                                                     │
│   main.py              streamlit_app.py        generate_figures.py  │
│   (Ejecutar algo.)     (Dashboard web)         (Figuras PNG)        │
└──────┬─────────────────────┬──────────────────────┬─────────────────┘
       │                     │                      │
       ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                   src/algorithm/                             │     │
│  │                                                             │     │
│  │   ┌─────────────────────────────────────┐                   │     │
│  │   │        macs_vrptw.py                │                   │     │
│  │   │     MACS_VRPTW (Controlador)        │                   │     │
│  │   │                                     │                   │     │
│  │   │  1. Genera solucion inicial (NN)    │                   │     │
│  │   │  2. Crea colonias ACS-VEI/TIME     │                   │     │
│  │   │  3. Alterna ciclos hasta converger  │                   │     │
│  │   └────────┬──────────────┬─────────────┘                   │     │
│  │            │              │                                  │     │
│  │   ┌───────▼──────┐ ┌─────▼────────┐                        │     │
│  │   │ acs_vei.py   │ │ acs_time.py  │                        │     │
│  │   │ ACS_VEI      │ │ ACS_TIME     │                        │     │
│  │   │              │ │              │                        │     │
│  │   │ Min vehiculos│ │ Min distancia│                        │     │
│  │   │ (v-1)        │ │ (v)          │                        │     │
│  │   │ Vector IN    │ │ IN = 0       │                        │     │
│  │   │ Sin busq.loc.│ │ Con busq.loc.│                        │     │
│  │   └───────┬──────┘ └──────┬───────┘                        │     │
│  │           │               │                                 │     │
│  │           ▼               ▼                                 │     │
│  │   ┌──────────────────────────┐  ┌───────────────────┐      │     │
│  │   │       ant.py             │  │   pheromone.py     │      │     │
│  │   │   new_active_ant()       │  │  PheromoneMatrix   │      │     │
│  │   │                          │  │                    │      │     │
│  │   │  - Regla transicion Eq.1 │  │  - get(i,j)       │      │     │
│  │   │  - Calculo eta_ij        │  │  - local_update    │      │     │
│  │   │  - Proc. insercion       │  │  - global_update   │      │     │
│  │   └──────────────────────────┘  └───────────────────┘      │     │
│  │                                                             │     │
│  │   ┌─────────────────────────────────────────┐               │     │
│  │   │        local_search/                    │               │     │
│  │   │                                         │               │     │
│  │   │  base.py ← interfaz abstracta          │               │     │
│  │   │    ├── or_opt.py      (segmentos 1-3)   │               │     │
│  │   │    └── cross_exchange.py (inter-ruta)   │               │     │
│  │   └─────────────────────────────────────────┘               │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ src/models/   │  │ src/parsers/ │  │ src/heuristics/          │   │
│  │               │  │              │  │                          │   │
│  │ customer.py   │  │ solomon_     │  │ nearest_neighbor.py      │   │
│  │ instance.py   │  │ parser.py    │  │                          │   │
│  │ solution.py   │  │              │  │ Solucion greedy inicial  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐   │
│  │ src/evaluation/       │  │ src/utils/                         │   │
│  │                       │  │                                    │   │
│  │ validator.py          │  │ config_loader.py  (YAML merge)     │   │
│  │ metrics.py            │  │ logger.py         (loguru)         │   │
│  │ benchmark.py          │  │ seed.py           (reproducibilid.)│   │
│  └──────────────────────┘  └────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
       │                     │                      │
       ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    DATOS Y CONFIGURACION                             │
│                                                                      │
│   config/default.yaml          data/c208.txt      results/*.json     │
│   config/experiments/c208.yaml data/c208_bks.txt  Figures/*.png      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de Ejecucion: `main.py`

```
main.py
  │
  ├─ 1. load_config()                      ← config/default.yaml + config/experiments/c208.yaml
  ├─ 2. setup_logger()                     ← loguru (consola + archivo)
  ├─ 3. validate_bks()                     ← Verifica que la BKS sea factible
  │     ├─ parse_solomon_instance()        ← data/c208.txt → Instance
  │     ├─ parse_bks_solution()            ← data/c208_bks.txt → Solution
  │     └─ validate_solution()             ← Capacidad + TW + cobertura
  │
  └─ 4. Por cada corrida (seeds 42, 43, 44):
        │
        ├─ set_global_seed(seed)
        ├─ parse_solomon_instance()
        ├─ Crear OrOpt() como busqueda local
        ├─ Crear MACS_VRPTW(instance, params, local_search)
        │
        ├─ macs.solve()  ─────────────────────────────────────┐
        │                                                      │
        │   ┌──────────────────────────────────────────────┐   │
        │   │ 1. nearest_neighbor_solution() → ψ⁰          │   │
        │   │ 2. tau_0 = 1/(n · distancia_NN)              │   │
        │   │ 3. Bucle principal:                           │   │
        │   │    a. ACS-VEI.run_cycle() con v-1 vehiculos  │   │
        │   │       └─ new_active_ant() × m hormigas       │   │
        │   │    b. ACS-TIME.run_cycle() con v vehiculos   │   │
        │   │       └─ new_active_ant() × m hormigas       │   │
        │   │       └─ OrOpt.apply() en cada solucion      │   │
        │   │    c. Si ACS-VEI reduce vehiculos → v = v-1  │   │
        │   │    d. Si no hay mejora → parar               │   │
        │   │ 4. Retorna ψᵍᵇ (mejor solucion global)      │   │
        │   └──────────────────────────────────────────────┘   │
        │                                                      │
        ├─ validate_solution()     ← Verifica factibilidad
        ├─ solution_summary()      ← Metricas (veh, dist, rutas)
        ├─ compare_with_references() ← Gap vs paper y BKS
        └─ Guardar → results/run_N.json
```

---

## Flujo de `streamlit_app.py`

```
streamlit_app.py
  │
  ├─ Carga data/c208.txt → Instance
  ├─ Carga results/run_*.json → Resultados
  │
  └─ 5 Pestanas:
       │
       ├─ Tab 1: Mapa de Rutas
       │   └─ Plotly scatter + lines por vehiculo (color-coded)
       │
       ├─ Tab 2: Convergencia
       │   └─ Plotly line chart (distancia + vehiculos vs iteracion)
       │
       ├─ Tab 3: Comparacion con Paper
       │   └─ Tabla: Paper T1, Paper T2, BKS, Nuestro + gaps %
       │
       ├─ Tab 4: Detalle de Solucion
       │   └─ Desglose por ruta + Gantt de ventanas de tiempo
       │
       └─ Tab 5: Analisis de Instancia
           └─ Histogramas de demanda, TW, distribucion geografica
```

---

## Flujo de `generate_figures.py`

```
generate_figures.py
  │
  ├─ parse_solomon_instance() → Instance
  ├─ parse_bks_solution() → BKS Solution
  ├─ Carga results/run_*.json → Mejor resultado
  │
  └─ Genera 6 figuras (300 DPI) en Figures/:
       │
       ├─ c208_instance.png      ← Mapa de clientes con demanda
       ├─ c208_routes_bks.png    ← Rutas de la BKS
       ├─ c208_routes_ours.png   ← Nuestras rutas
       ├─ convergence.png        ← Distancia y vehiculos vs eventos
       ├─ architecture_macs.png  ← Diagrama arquitectura algoritmo
       └─ comparison_chart.png   ← Barras: nosotros vs paper vs BKS
```

---

## Modulos y sus Dependencias

```
                    ┌─────────────┐
                    │  customer.py │ ← Sin dependencias
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ instance.py  │ ← Usa Customer + numpy
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ solution.py  │ ← Usa Instance para validar
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐ ┌──────▼──────┐  ┌──────▼──────┐
   │solomon_parser│ │ validator.py │  │ metrics.py  │
   │              │ │              │  │             │
   │ Texto → Obj. │ │ Factibilidad│  │ Resumen     │
   └──────────────┘ └─────────────┘  └─────────────┘
          │
   ┌──────▼──────────┐
   │nearest_neighbor  │ ← Usa Instance
   └──────┬───────────┘
          │
   ┌──────▼──────┐    ┌─────────────┐
   │ pheromone.py │    │ base.py (LS)│ ← Interfaz abstracta
   └──────┬───────┘    └──────┬──────┘
          │                   │
          │            ┌──────┼──────┐
          │            │             │
          │     ┌──────▼───┐  ┌─────▼──────┐
          │     │ or_opt.py │  │cross_exch. │
          │     └──────────┘  └────────────┘
          │
   ┌──────▼──────┐
   │   ant.py     │ ← Usa PheromoneMatrix + Instance + LocalSearch
   └──────┬───────┘
          │
   ┌──────▼──────────┐
   │  colony_base.py  │ ← Interfaz abstracta
   └──────┬───────────┘
          │
   ┌──────┼──────────┐
   │                  │
┌──▼──────┐   ┌──────▼───┐
│acs_vei  │   │acs_time  │ ← Usan ant.py + PheromoneMatrix
└──┬──────┘   └──────┬───┘
   │                  │
   └────────┬─────────┘
            │
   ┌────────▼─────────┐
   │  macs_vrptw.py    │ ← Coordina ambas colonias
   └──────────────────┘
```

---

## Archivos del Proyecto

| Archivo | Lineas | Descripcion |
|---------|--------|-------------|
| `main.py` | 178 | Script principal — ejecuta N corridas |
| `streamlit_app.py` | ~846 | Dashboard interactivo (5 pestanas) |
| `generate_figures.py` | ~348 | Genera 6 figuras para el reporte |
| `src/algorithm/macs_vrptw.py` | ~150 | Controlador MACS-VRPTW |
| `src/algorithm/ant.py` | ~200 | Construccion de soluciones (new_active_ant) |
| `src/algorithm/acs_vei.py` | ~80 | Colonia minimizar vehiculos |
| `src/algorithm/acs_time.py` | ~70 | Colonia minimizar distancia |
| `src/algorithm/pheromone.py` | ~60 | Matriz de feromonas |
| `src/algorithm/local_search/or_opt.py` | ~120 | Busqueda local Or-opt |
| `src/algorithm/local_search/cross_exchange.py` | ~100 | Busqueda local CROSS |
| `src/models/customer.py` | ~20 | Dataclass Customer |
| `src/models/instance.py` | ~50 | Modelo Instance + matriz distancias |
| `src/models/solution.py` | ~80 | Route y Solution |
| `src/parsers/solomon_parser.py` | ~80 | Parser formato Solomon |
| `src/heuristics/nearest_neighbor.py` | ~60 | Heuristica vecino mas cercano |
| `src/evaluation/validator.py` | ~60 | Validacion de factibilidad |
| `src/evaluation/metrics.py` | ~40 | Metricas y resumen |
| `src/evaluation/benchmark.py` | ~50 | Comparacion con paper y BKS |
| `src/utils/config_loader.py` | ~30 | Carga y merge de YAML |
| `src/utils/logger.py` | ~20 | Configuracion loguru |
| `src/utils/seed.py` | ~10 | Control de semillas |
| `tests/test_parser.py` | ~100 | 12 tests del parser |
| `tests/test_solution.py` | ~60 | 5 tests de Solution |
| `tests/test_pheromone.py` | ~50 | 5 tests de PheromoneMatrix |

---

## Parametros del Algoritmo

| Parametro | Valor | Donde se configura |
|-----------|-------|--------------------|
| `num_ants` | 5 (10 en articulo) | `config/experiments/c208.yaml` |
| `q0` | 0.9 | `config/default.yaml` |
| `beta` | 1.0 | `config/default.yaml` |
| `rho` | 0.1 | `config/default.yaml` |
| `max_iterations` | 50 | `config/experiments/c208.yaml` |
| `max_no_improvement` | 10 | `config/experiments/c208.yaml` |
| `num_runs` | 3 | `config/experiments/c208.yaml` |
| `seed` | 42 (base) | `config/default.yaml` |

---

## Comandos

```bash
# Activar entorno
source .venv/bin/activate       # macOS
.venv\Scripts\Activate.ps1      # Windows

# Ejecutar algoritmo (~18 min total)
python main.py

# Generar figuras
python generate_figures.py

# Dashboard interactivo
streamlit run streamlit_app.py

# Tests
pytest tests/ -v
```
