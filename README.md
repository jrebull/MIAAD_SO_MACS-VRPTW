<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Escudo_UACJ_2015.svg/1200px-Escudo_UACJ_2015.svg.png" alt="UACJ" width="120"/>
</p>

<h1 align="center">MACS-VRPTW</h1>
<h3 align="center">Multiple Ant Colony System for Vehicle Routing Problems with Time Windows</h3>

<p align="center">
  <strong>Actividad Práctica — Optimización Inteligente</strong><br/>
  Maestría en Inteligencia Artificial y Analítica de Datos (MIAAD)<br/>
  Universidad Autónoma de Ciudad Juárez
</p>

<p align="center">
  <a href="#descripción-del-problema"><img src="https://img.shields.io/badge/Problema-VRPTW-003366?style=for-the-badge" alt="VRPTW"/></a>
  <a href="#algoritmo"><img src="https://img.shields.io/badge/Algoritmo-MACS--VRPTW-C8962E?style=for-the-badge" alt="MACS"/></a>
  <a href="#instancias-de-benchmark"><img src="https://img.shields.io/badge/Benchmark-Solomon-2E8B57?style=for-the-badge" alt="Solomon"/></a>
</p>

---

## 📋 Información General

| Campo | Detalle |
|:------|:--------|
| **Materia** | Optimización Inteligente |
| **Profesor** | Mtro. Raúl Gibrán Porras Alaniz |
| **Programa** | MIAAD — UACJ |
| **Modalidad** | Trabajo en equipo (4 integrantes) |
| **Entrega** | Presentación en vivo (siguiente clase) |

---

## 📖 Descripción del Problema

El **Vehicle Routing Problem with Time Windows (VRPTW)** es un problema clásico de optimización combinatoria NP-hard que consiste en diseñar un conjunto óptimo de rutas para una flota de vehículos de capacidad homogénea que deben atender a un grupo de clientes, cada uno con:

- **Ubicación geográfica** (coordenadas `x`, `y`)
- **Demanda** de producto (`qᵢ ≤ Q`)
- **Ventana de tiempo** `[bᵢ, eᵢ]` en la que debe iniciarse el servicio
- **Tiempo de servicio** (`sᵢ`)

Todas las rutas inician y terminan en un **depósito central** con su propio horario de operación `[b₀, e₀]`.

### Objetivos jerárquicos

1. **Minimizar** el número de vehículos utilizados
2. **Minimizar** la distancia total recorrida

---

## 🐜 Algoritmo

### MACS-VRPTW (Gambardella, Taillard & Agazzi, 1999)

El **Multiple Ant Colony System** organiza jerárquicamente dos colonias de hormigas artificiales que cooperan intercambiando información a través de feromonas:

```
┌──────────────────────────────────────────┐
│            MACS-VRPTW Controller         │
│                                          │
│   ┌─────────────┐   ┌─────────────────┐ │
│   │  ACS-VEI    │   │   ACS-TIME      │ │
│   │ (Minimiza   │◄─►│  (Minimiza      │ │
│   │  vehículos) │   │   distancia)    │ │
│   └─────────────┘   └─────────────────┘ │
│          │                   │           │
│          └───────┬───────────┘           │
│                  ▼                       │
│        Intercambio de feromonas          │
│        + Búsqueda local                  │
└──────────────────────────────────────────┘
```

**Componentes clave:**

- **ACS-VEI:** Colonia enfocada en minimizar el número de vehículos/tours
- **ACS-TIME:** Colonia enfocada en minimizar la distancia/tiempo total de viaje
- **Regla de transición pseudo-aleatoria proporcional** para la construcción de soluciones
- **Actualización global y local de feromonas** para intensificación y diversificación
- **Procedimientos de búsqueda local** para mejorar la calidad de las soluciones

### Referencia del artículo

> Gambardella, L. M., Taillard, É., & Agazzi, G. (1999). *MACS-VRPTW: A Multiple Ant Colony System for Vehicle Routing Problems with Time Windows.* In D. Corne, M. Dorigo & F. Glover (Eds.), New Ideas in Optimization (pp. 63–76). McGraw-Hill, London.

---

## 📦 Instancias de Benchmark

Se utilizan las instancias clásicas de **Solomon (1987)** con 100 clientes, organizadas en 6 categorías:

| Tipo | Distribución geográfica | Horizonte | Clientes/ruta |
|:-----|:------------------------|:----------|:--------------|
| **C1** | Agrupada (clustered) | Corto | 5–10 |
| **C2** | Agrupada (clustered) | Largo | 30+ |
| **R1** | Aleatoria (random) | Corto | 5–10 |
| **R2** | Aleatoria (random) | Largo | 30+ |
| **RC1** | Mixta (random + clustered) | Corto | 5–10 |
| **RC2** | Mixta (random + clustered) | Largo | 30+ |

### Formato de las instancias

```
CUST_NO.  XCOORD.  YCOORD.  DEMAND  READY_TIME  DUE_DATE  SERVICE_TIME
    0       40       50        0        0          230          0
    1       45       68       10       912          967         90
    2       42       66       10      825           870         90
   ...
```

- **Fila 0:** Depósito (demanda = 0)
- **Filas 1–100:** Clientes con sus respectivos atributos

### Fuentes

- 🔗 [Solomon's Benchmarks (SINTEF)](https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/)
- 🔗 [Solomon's Original Page](http://w.cba.neu.edu/~msolomon/problems.htm)
- 🔗 [Resultados best-known (100 clientes)](https://www.sintef.no/projectweb/top/vrptw/100-customers/)

---

## 🗂️ Estructura del Repositorio

```
MIAAD_SO_MACS-VRPTW/
├── README.md
├── docs/
│   └── paper.pdf                  # Artículo de referencia
├── instances/
│   └── solomon_100/               # Instancias de benchmark
│       ├── C101.txt
│       ├── R101.txt
│       └── ...
├── src/
│   ├── macs_vrptw.py              # Implementación principal
│   ├── acs_vei.py                 # Colonia ACS-VEI
│   ├── acs_time.py                # Colonia ACS-TIME
│   ├── local_search.py            # Procedimientos de búsqueda local
│   └── utils.py                   # Utilidades y parseo de instancias
├── results/
│   └── ...                        # Resultados experimentales
├── presentation/
│   └── ...                        # Presentación del equipo
└── requirements.txt
```

> **Nota:** Esta estructura es sugerida. Cada equipo puede adaptarla según su implementación.

---

## 🚀 Inicio Rápido

```bash
# Clonar el repositorio
git clone https://github.com/jrebull/MIAAD_SO_MACS-VRPTW.git
cd MIAAD_SO_MACS-VRPTW

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el algoritmo sobre una instancia
python src/macs_vrptw.py --instance instances/solomon_100/C101.txt
```

---

## ✅ Entregables

| # | Entregable | Descripción |
|:-:|:-----------|:------------|
| 1 | **Código fuente** | Implementación completa y funcional del MACS-VRPTW |
| 2 | **Presentación** | Explicación del algoritmo, implementación, instancia y resultados |
| 3 | **Portada en Aula Virtual** | Cada integrante sube la portada como registro de participación |
| 4 | **Exposición en vivo** | Presentación frente al grupo el día de entrega |

---

## 👥 Equipo

| Integrante | Rol |
|:-----------|:----|
| | |
| | |
| | |
| | |

---

## 📚 Referencias

- Gambardella, L. M., Taillard, É., & Agazzi, G. (1999). *MACS-VRPTW: A Multiple Ant Colony System for Vehicle Routing Problems with Time Windows.* New Ideas in Optimization, 63–76.
- Solomon, M. M. (1987). *Algorithms for the Vehicle Routing and Scheduling Problem with Time Window Constraints.* Operations Research, 35(2), 254–265.
- Dorigo, M. & Gambardella, L. M. (1997). *Ant Colony System: A Cooperative Learning Approach to the Traveling Salesman Problem.* IEEE Trans. Evol. Comput., 1(1), 53–66.

---

<p align="center">
  <sub>MIAAD — Universidad Autónoma de Ciudad Juárez — Optimización Inteligente — 2026</sub>
</p>
