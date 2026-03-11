<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Escudo_UACJ.svg/3840px-Escudo_UACJ.svg.png" alt="UACJ" width="120"/>
</p>

<h1 align="center">MACS-VRPTW</h1>
<h3 align="center">Multiple Ant Colony System for Vehicle Routing Problems with Time Windows</h3>

<p align="center">
  <strong>Actividad Practica  - Optimizacion Inteligente</strong><br/>
  Maestria en Inteligencia Artificial y Analitica de Datos (MIAAD)<br/>
  Universidad Autonoma de Ciudad Juarez
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Problema-VRPTW-003366?style=for-the-badge" alt="VRPTW"/>
  <img src="https://img.shields.io/badge/Algoritmo-MACS--VRPTW-C8962E?style=for-the-badge" alt="MACS"/>
  <img src="https://img.shields.io/badge/Benchmark-Solomon_C208-2E8B57?style=for-the-badge" alt="Solomon"/>
</p>

---

## Informacion General

| Campo | Detalle |
|:------|:--------|
| **Materia** | Optimizacion Inteligente |
| **Profesor** | Mtro. Raul Gibran Porras Alaniz |
| **Programa** | MIAAD - UACJ |
| **Instancia** | C208 (Solomon, 100 clientes, Clustered tipo 2) |
| **BKS** | 3 vehiculos, 588.32 distancia |
| **Entrega** | 16 de marzo de 2026 |

---

## Equipo

| Nombre | Matricula | Rol |
|--------|-----------|-----|
| **Javier Augusto Rebull Saucedo** | 263483 | Lead Developer & Documentacion |
| **Yazmin Ivonne Flores Martinez** | 261548 | Analisis algoritmico & Validacion |
| **Esther Nohemi Encinas Guerrero** | 261536 | Experimentacion & Benchmarking |

---

## Inicio Rapido

```bash
# Clonar el repositorio
git clone https://github.com/jrebull/MIAAD_SO_MACS-VRPTW.git
cd MIAAD_SO_MACS-VRPTW

# Crear ambiente virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ejecutar el algoritmo
python main.py

# Generar figuras
python generate_figures.py

# Lanzar dashboard interactivo
streamlit run streamlit_app.py

# Ejecutar tests
pytest tests/ -v
```

---

## Estructura del Proyecto

```
MIAAD_SO_MACS-VRPTW/
├── CLAUDE.md                          # Contexto para Claude Code
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias Python
├── main.py                            # Script principal de ejecucion
├── streamlit_app.py                   # Dashboard interactivo
├── generate_figures.py                # Generador de figuras
├── config/
│   ├── default.yaml                   # Configuracion por defecto
│   └── experiments/
│       └── c208.yaml                  # Override para C208
├── src/
│   ├── models/
│   │   ├── customer.py                # Dataclass Customer
│   │   ├── instance.py                # Modelo Instance + matriz distancias
│   │   └── solution.py                # Route y Solution
│   ├── parsers/
│   │   └── solomon_parser.py          # Parser instancias Solomon
│   ├── algorithm/
│   │   ├── ant.py                     # new_active_ant (Figure 6)
│   │   ├── colony_base.py             # ABC ColonyBase (SOLID: DIP)
│   │   ├── acs_time.py                # Colonia ACS-TIME (Figure 3)
│   │   ├── acs_vei.py                 # Colonia ACS-VEI (Figure 4)
│   │   ├── pheromone.py               # Matriz de feromonas (Eq. 2, 3)
│   │   ├── macs_vrptw.py              # Controlador MACS-VRPTW (Figure 2)
│   │   └── local_search/
│   │       ├── base.py                # ABC LocalSearchStrategy (SOLID: OCP)
│   │       ├── cross_exchange.py      # CROSS exchange
│   │       └── or_opt.py              # Or-opt (1, 2, 3 clientes)
│   ├── heuristics/
│   │   └── nearest_neighbor.py        # Heuristica vecino mas cercano
│   ├── evaluation/
│   │   ├── validator.py               # Validacion de factibilidad
│   │   ├── metrics.py                 # Metricas de evaluacion
│   │   └── benchmark.py               # Comparacion vs BKS y paper
│   └── utils/
│       ├── config_loader.py           # Carga configs YAML
│       ├── logger.py                  # Setup loguru
│       └── seed.py                    # Control de semillas
├── data/
│   ├── c208.txt                       # Instancia C208
│   └── c208_bks.txt                   # Best-Known Solution
├── References/                        # Documentos de referencia
├── Figures/                           # Figuras generadas (300 DPI)
├── results/                           # Resultados JSON
├── LaTeX/
│   └── main.tex                       # Documento academico
└── tests/
    ├── test_parser.py
    ├── test_solution.py
    └── test_pheromone.py
```

---

## Algoritmo MACS-VRPTW

Implementacion fiel del algoritmo de **Gambardella, Taillard y Agazzi (1999)** con dos colonias ACS cooperativas:

- **ACS-VEI**: Minimiza el numero de vehiculos (opera con v-1 vehiculos)
- **ACS-TIME**: Minimiza la distancia total (con busqueda local)

Parametros del articulo: `m=10, q0=0.9, beta=1, rho=0.1`

### Principios de diseno

- **SOLID**: Interfaces abstractas, inversion de dependencias, principio abierto/cerrado
- **Clean Code**: Nombres descriptivos, funciones pequenas, sin magic numbers
- **MLOps**: Configuracion YAML, logging estructurado, semillas controladas, resultados JSON

---

## Referencias

1. Gambardella, L. M., Taillard, E., & Agazzi, G. (1999). *MACS-VRPTW: A Multiple Ant Colony System for Vehicle Routing Problems with Time Windows.* New Ideas in Optimization, McGraw-Hill.
2. Dorigo, M. & Gambardella, L. M. (1997). *Ant Colony System: A Cooperative Learning Approach to the Traveling Salesman Problem.* IEEE Trans. Evol. Comput.
3. Solomon, M. M. (1987). *Algorithms for the Vehicle Routing and Scheduling Problem with Time Window Constraints.* Operations Research.

---

<p align="center">
  <sub>MIAAD - Universidad Autonoma de Ciudad Juarez - Optimizacion Inteligente - 2026</sub>
</p>
