# Procesador Concurrente de Archivos — Laboratorio Integrador Unidad 01

Sistema en Python 3 que detecta archivos `.txt` en una carpeta de entrada, calcula
métricas por archivo, genera reportes individuales y consolidados, mueve los archivos
tratados, registra eventos en una bitácora y permite comparar una ejecución secuencial
contra una concurrente.

---

## 1. Integrantes y roles

| Integrante | Rol | Responsabilidad principal |
|---|---|---|
| Benjamín Morales | Responsable de ambiente | VirtualBox, Ubuntu, instalación de herramientas |
| Kevin Lener | Responsable de concurrencia | `version_concurrente.py`, cola y bloqueos |
| Máximo Inostroza | Responsable de pruebas y evidencias | Mediciones, capturas, experimento de carrera |
| Máximo Inostroza, Benjamín Morales, Kevin lener | Responsable de integración y documentación | README, informe técnico, estructura final |

---

## 2. Requisitos para ejecutar

- Ubuntu Desktop 24.04 LTS de 64 bits (máquina virtual en Oracle VM VirtualBox)
- Python 3.12 o superior (incluido en Ubuntu 24.04)
- Utilidades de sistema: `ps`, `top`, `htop`, `free`, `df`, `du`, `pstree`, `tree`

Instalación de dependencias del sistema:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git htop tree bsdmainutils
python3 --version
```

**El proyecto no utiliza librerías externas.** Todo se resuelve con la biblioteca
estándar de Python (`pathlib`, `collections`, `queue`, `threading`, `shutil`,
`datetime`, `csv`, `time`). Por eso `requirements.txt` no declara paquetes.

---

## 3. Instrucciones paso a paso

```bash
# 1. Ubicarse en el proyecto
cd ~/laboratorio_so

# 2. Generar archivos de entrada (20 archivos + casos con error)
bash src/generar_entrada.sh 20

# 3. Ejecutar la versión secuencial
python3 src/version_secuencial.py

# 4. Regenerar la entrada y ejecutar la versión concurrente
bash src/generar_entrada.sh 20
python3 src/version_concurrente.py

# 5. Revisar resultados
cat data/reportes/reporte_consolidado_secuencial.txt
cat data/reportes/reporte_consolidado_concurrente.txt
cat logs/sistema.log
column -s, -t < evidencia/mediciones.csv
```

**Importante:** el programa *mueve* los archivos a `data/procesados/`, por lo que
`data/entrada/` queda vacía al terminar. Hay que ejecutar `generar_entrada.sh` antes
de cada corrida para comparar ambas versiones con la misma carga.

---

## 5. Comandos utilizados para ejecutar cada versión

| Versión | Comando |
|---|---|
| Secuencial | `python3 src/version_secuencial.py` |
| Concurrente | `python3 src/version_concurrente.py` |
| Experimental (sin Lock) | `python3 src/version_sincronizacion_experimental.py` |
| Medición completa | `bash src/medir.sh secuencial 200` |
| Experimento de carrera | `bash src/ejecutar_experimento.sh 120 5` |

---

## 5. Estructura de carpetas

```
laboratorio_so/
├── README.md
├── requirements.txt
├── informe.pdf
├── src/
│   ├── comun.py                                  # funciones compartidas
│   ├── version_secuencial.py                     # sin hilos
│   ├── version_concurrente.py                    # productor + cola + 3 trabajadores + Lock
│   ├── version_sincronizacion_experimental.py    # sin Lock (condición de carrera)
│   ├── generar_entrada.sh                        # regenera data/entrada/
│   ├── ejecutar_experimento.sh                   # repite el experimento de carrera
│   └── medir.sh                                  # mide tiempo, memoria y disco
├── data/
│   ├── entrada/        # archivos .txt por procesar
│   ├── procesados/     # archivos ya tratados
│   ├── errores/        # archivos fallidos + detalle del error
│   └── reportes/       # reporte por archivo + consolidados
├── logs/
│   └── sistema.log     # bitácora de todos los eventos
└── evidencia/
    ├── capturas/
    ├── comandos_ejecutados.txt
    ├── mediciones.csv
    └── experimento_carrera.csv
```

---

## 6. Mecanismo de concurrencia aplicado

- **Modelo:** productor / consumidores.
- **Cola:** `queue.Queue`, sincronizada internamente. El productor deposita rutas y
  los trabajadores las retiran sin que dos hilos puedan obtener el mismo elemento.
- **Trabajadores:** 3 hilos (`threading.Thread`), configurables en la constante
  `CANTIDAD_TRABAJADORES`.
- **Término ordenado:** el productor termina, el hilo principal inserta un centinela
  `None` por cada trabajador, luego `cola.join()` espera a que todo se consuma y
  finalmente `hilo.join()` espera a que cada trabajador muera.
- **Secciones críticas protegidas con `threading.Lock`:**
  1. `bloqueo_log`: escritura sobre `logs/sistema.log`.
  2. `bloqueo_totales`: actualización del diccionario `totales`.

---

## 7. Cómo reproducir el experimento de condición de carrera

```bash
cd ~/laboratorio_so
bash src/ejecutar_experimento.sh 120 5
```

El script ejecuta cinco veces la versión sin `Lock` y cinco veces la versión con
`Lock`, sobre 120 archivos y con la misma entrada regenerada en cada corrida.
El resultado queda en `evidencia/experimento_carrera.csv` con las columnas
`esperado`, `registrado` y `perdidos`.

**Qué se observa:** sin `Lock`, el contador registrado es menor que el número real de
archivos procesados. Con `Lock`, ambos valores coinciden en todas las corridas.

**Por qué ocurre:** `totales["archivos"] += 1` no es una operación atómica. Se
descompone en leer el valor, sumar 1 y escribir el resultado. Si el intérprete cambia
de contexto entre la lectura y la escritura, dos hilos pueden leer el mismo valor y
uno de los dos incrementos se pierde. La versión experimental separa explícitamente
esas operaciones con `time.sleep(0.001)` para ampliar esa ventana y hacer el efecto
reproducible en cada ejecución.

Para ejecutarlo manualmente una sola vez:

```bash
bash src/generar_entrada.sh 120 no
python3 src/version_sincronizacion_experimental.py
```

## 8. Evidencia
![Descripción de la imagen](evidencia/Mediciones,capturas, experimento de carrera/01_baseline_sistema.png)
