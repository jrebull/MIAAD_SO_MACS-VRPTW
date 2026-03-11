# MACS-VRPTW — Proyecto de Replicación

## Contexto
Replicación del algoritmo MACS-VRPTW (Gambardella, Taillard, Agazzi 1999) para la materia de Optimización Inteligente, MIAAD UACJ.

## Instancia
- **C208** (Solomon Benchmark, 100 clientes, Clustered tipo 2)
- BKS: 3 vehículos, 588.32 distancia

## Arquitectura
- Python 3.11+, principios SOLID/Clean Code
- Configuración vía YAML (`config/`)
- Logging con loguru (nunca print)
- Seeds controlados para reproducibilidad
- Type hints en todas las funciones
- Docstrings en español, código en inglés

## Parámetros del artículo
- m=10 hormigas, q0=0.9, beta=1, rho=0.1
- tau_0 = 1/(n * J_nn)

## Comandos
- Ejecutar: `python main.py`
- Dashboard: `streamlit run streamlit_app.py`
- Tests: `pytest tests/`
