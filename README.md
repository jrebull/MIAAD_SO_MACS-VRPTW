<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Escudo_UACJ.svg/3840px-Escudo_UACJ.svg.png" alt="UACJ" width="120"/>
</p>

<h1 align="center">MACS-VRPTW</h1>
<h3 align="center">Multiple Ant Colony System for Vehicle Routing Problems with Time Windows</h3>

<p align="center">
  <strong>Actividad Practica - Optimizacion Inteligente</strong><br/>
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
| **Entrega** | 17 de marzo de 2026 |

---

## Equipo

| Nombre | Matricula | Rol |
|--------|-----------|-----|
| **Esther Nohemi Encinas Guerrero** | 261536 | Experimentacion & Benchmarking |
| **Javier Augusto Rebull Saucedo** | 263483 | Lead Developer & Documentacion |
| **Jesus Alejandro Gutierrez Araiza** | 261537 | Demostracion & Resultados |
| **Yazmin Ivonne Flores Martinez** | 261548 | Analisis algoritmico & Validacion |

---

## Requisitos Previos

| Requisito | Version minima | Verificar con |
|-----------|---------------|---------------|
| **Python** | 3.11 o superior | `python --version` (Windows) / `python3 --version` (macOS) |
| **pip** | Incluido con Python | `pip --version` (Windows) / `pip3 --version` (macOS) |
| **Git** | Cualquier version reciente | `git --version` |

> **Nota Windows**: Al instalar Python desde [python.org](https://www.python.org/downloads/), marcar la casilla **"Add Python to PATH"** durante la instalacion. Esto es indispensable para que los comandos `python` y `pip` funcionen desde la terminal.

> **Nota macOS**: Python 3 viene preinstalado en versiones recientes. Si no lo tienes, instala con [Homebrew](https://brew.sh/): `brew install python`.

---

## Despliegue en macOS

### Paso 1: Clonar el repositorio

Abre la app **Terminal** (busca "Terminal" en Spotlight con Cmd + Espacio) y ejecuta:

```bash
git clone https://github.com/jrebull/MIAAD_SO_MACS-VRPTW.git
cd MIAAD_SO_MACS-VRPTW
```

### Paso 2: Crear entorno virtual

```bash
python3 -m venv .venv
```

### Paso 3: Activar el entorno virtual

```bash
source .venv/bin/activate
```

Despues de activar, veras `(.venv)` al inicio de tu linea de terminal. **Este paso se debe repetir cada vez que abras una terminal nueva.**

### Paso 4: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 5: Ejecutar el algoritmo

```bash
python main.py
```

Esto ejecuta 3 corridas del algoritmo MACS-VRPTW sobre la instancia C208. Los resultados se guardan en la carpeta `results/` como archivos JSON. El tiempo aproximado es de ~6 minutos por corrida (~18 minutos en total).

### Paso 6: Generar figuras

```bash
python generate_figures.py
```

Las 6 figuras PNG (300 DPI) se guardan en la carpeta `Figures/`.

### Paso 7: Lanzar el dashboard interactivo

```bash
streamlit run streamlit_app.py
```

Se abrira automaticamente en tu navegador en `http://localhost:8501`. Para detener el dashboard, presiona `Ctrl + C` en la terminal.

### Paso 8: Ejecutar tests

```bash
pytest tests/ -v
```

Deberias ver 22 tests pasando (todo en verde).

### Desactivar el entorno virtual (cuando termines)

```bash
deactivate
```

---

## Despliegue en Windows

### Paso 1: Clonar el repositorio

Abre **PowerShell** (busca "PowerShell" en el menu de inicio) y ejecuta:

```powershell
git clone https://github.com/jrebull/MIAAD_SO_MACS-VRPTW.git
cd MIAAD_SO_MACS-VRPTW
```

### Paso 2: Crear entorno virtual

```powershell
python -m venv .venv
```

> Si `python` no se reconoce, prueba con `python3` o verifica que Python este en el PATH (ver nota en Requisitos Previos).

### Paso 3: Activar el entorno virtual

```powershell
.venv\Scripts\Activate.ps1
```

> **Si te aparece un error de permisos** ("execution of scripts is disabled"), ejecuta primero este comando y responde "S" (si):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Luego intenta activar de nuevo con `.venv\Scripts\Activate.ps1`

> **Alternativa con CMD** (si no usas PowerShell): abre `cmd.exe` y ejecuta:
> ```cmd
> .venv\Scripts\activate.bat
> ```

Despues de activar, veras `(.venv)` al inicio de tu linea de terminal. **Este paso se debe repetir cada vez que abras una terminal nueva.**

### Paso 4: Instalar dependencias

```powershell
pip install -r requirements.txt
```

### Paso 5: Ejecutar el algoritmo

```powershell
python main.py
```

Esto ejecuta 3 corridas del algoritmo MACS-VRPTW sobre la instancia C208. Los resultados se guardan en la carpeta `results/` como archivos JSON. El tiempo aproximado es de ~6 minutos por corrida (~18 minutos en total).

### Paso 6: Generar figuras

```powershell
python generate_figures.py
```

Las 6 figuras PNG (300 DPI) se guardan en la carpeta `Figures/`.

### Paso 7: Lanzar el dashboard interactivo

```powershell
streamlit run streamlit_app.py
```

Se abrira automaticamente en tu navegador en `http://localhost:8501`. Para detener el dashboard, presiona `Ctrl + C` en la terminal.

### Paso 8: Ejecutar tests

```powershell
pytest tests/ -v
```

Deberias ver 22 tests pasando (todo en verde).

### Desactivar el entorno virtual (cuando termines)

```powershell
deactivate
```

---

## Estructura del Proyecto

```
MIAAD_SO_MACS-VRPTW/
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
│   │   ├── colony_base.py             # ABC ColonyBase
│   │   ├── acs_time.py                # Colonia ACS-TIME (Figure 3)
│   │   ├── acs_vei.py                 # Colonia ACS-VEI (Figure 4)
│   │   ├── pheromone.py               # Matriz de feromonas (Eq. 2, 3)
│   │   ├── macs_vrptw.py              # Controlador MACS-VRPTW (Figure 2)
│   │   └── local_search/
│   │       ├── base.py                # ABC LocalSearchStrategy
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
├── Figures/                           # Figuras generadas (300 DPI)
├── results/                           # Resultados JSON
├── LaTeX/
│   └── MACS_VRPTW_Documento_Academico.tex  # Documento academico
├── References/                        # Documentos de referencia
└── tests/
    ├── test_parser.py
    ├── test_solution.py
    └── test_pheromone.py
```

---

## Algoritmo MACS-VRPTW

Implementacion fiel del algoritmo de **Gambardella, Taillard y Agazzi (1999)** con dos colonias ACS cooperativas:

- **ACS-VEI**: Minimiza el numero de vehiculos (opera con v-1 vehiculos)
- **ACS-TIME**: Minimiza la distancia total (con busqueda local Or-opt)

### Parametros

| Parametro | Valor | Descripcion |
|-----------|-------|-------------|
| `m` | 5 (10 en articulo) | Numero de hormigas por colonia |
| `q0` | 0.9 | Probabilidad de explotacion |
| `beta` | 1 | Peso de la informacion heuristica |
| `rho` | 0.1 | Coeficiente de evaporacion |
| `max_iterations` | 50 | Iteraciones maximas |
| `max_no_improvement` | 10 | Iteraciones sin mejora antes de parar |

### Resultados sobre C208

| Corrida | Semilla | Vehiculos | Distancia | Tiempo (s) |
|---------|---------|-----------|-----------|------------|
| 1 | 42 | 3 | 588.32 | 367.46 |
| 2 | 43 | 3 | 588.32 | 362.50 |
| 3 | 44 | 3 | 588.32 | 389.55 |
| **Promedio** | --- | **3.00** | **588.32** | **373.17** |

Gap vs BKS: **0.00%** (alcanza la mejor solucion conocida en las 3 corridas).

### Principios de diseno

- **SOLID**: Interfaces abstractas, inversion de dependencias, principio abierto/cerrado
- **Clean Code**: Nombres descriptivos, funciones pequenas, sin magic numbers
- **MLOps**: Configuracion YAML, logging estructurado, semillas controladas, resultados JSON

---

## Documento LaTeX

El documento academico se encuentra en `LaTeX/MACS_VRPTW_Documento_Academico.tex`. Para compilarlo en **Overleaf**:

1. Sube el archivo `MACS_VRPTW_Documento_Academico.tex`
2. Crea una carpeta `Figures/` en Overleaf y sube las 6 imagenes de la carpeta `Figures/` del repositorio
3. Compila con pdfLaTeX

---

## Referencias

1. Gambardella, L. M., Taillard, E., & Agazzi, G. (1999). *MACS-VRPTW: A Multiple Ant Colony System for Vehicle Routing Problems with Time Windows.* New Ideas in Optimization, McGraw-Hill.
2. Dorigo, M. & Gambardella, L. M. (1997). *Ant Colony System: A Cooperative Learning Approach to the Traveling Salesman Problem.* IEEE Trans. Evol. Comput.
3. Solomon, M. M. (1987). *Algorithms for the Vehicle Routing and Scheduling Problem with Time Window Constraints.* Operations Research.

---

<p align="center">
  <sub>MIAAD - Universidad Autonoma de Ciudad Juarez - Optimizacion Inteligente - 2026</sub>
</p>
