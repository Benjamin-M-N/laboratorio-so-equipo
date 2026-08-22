"""
comun.py
Funciones compartidas por las tres versiones del Procesador Concurrente de Archivos.

Aqui NO hay hilos ni bloqueos: solo la logica de negocio (leer, analizar, reportar,
mover, registrar). La concurrencia y las secciones criticas viven en cada version,
para que se puedan explicar por separado en el informe.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
import csv
import shutil

# --------------------------------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------------------------------
BASE = Path.home() / "laboratorio_so"

ENTRADA = BASE / "data" / "entrada"
PROCESADOS = BASE / "data" / "procesados"
REPORTES = BASE / "data" / "reportes"
ERRORES = BASE / "data" / "errores"
LOGS = BASE / "logs"
EVIDENCIA = BASE / "evidencia"

LOG = LOGS / "sistema.log"
MEDICIONES = EVIDENCIA / "mediciones.csv"
CARRERA = EVIDENCIA / "experimento_carrera.csv"

CARPETAS = [ENTRADA, PROCESADOS, REPORTES, ERRORES, LOGS, EVIDENCIA]


def preparar_carpetas():
    """Crea todas las carpetas del proyecto si no existen (idempotente)."""
    for carpeta in CARPETAS:
        carpeta.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Bitacora
# --------------------------------------------------------------------------
def marca_tiempo():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def escribir_log(mensaje, version):
    """Escribe una linea en logs/sistema.log.

    OJO: esta funcion NO es segura por si sola en un contexto multihilo.
    La version concurrente la envuelve con un threading.Lock.
    """
    with LOG.open("a", encoding="utf-8") as archivo_log:
        archivo_log.write(f"[{marca_tiempo()}] [{version}] {mensaje}\n")


# --------------------------------------------------------------------------
# Manejo de archivos
# --------------------------------------------------------------------------
def destino_unico(carpeta, nombre):
    """Devuelve una ruta libre dentro de 'carpeta'.

    Evita que shutil.move sobrescriba silenciosamente un archivo ya existente
    (requisito: mover archivos procesados sin duplicarlos accidentalmente).
    """
    destino = carpeta / nombre
    if not destino.exists():
        return destino
    tallo = Path(nombre).stem
    sufijo = Path(nombre).suffix
    contador = 1
    while True:
        candidato = carpeta / f"{tallo}__{contador}{sufijo}"
        if not candidato.exists():
            return candidato
        contador += 1


def analizar(contenido):
    """Calcula las metricas pedidas para un archivo de texto."""
    palabras = contenido.lower().split()
    if palabras:
        palabra_frecuente, repeticiones = Counter(palabras).most_common(1)[0]
    else:
        palabra_frecuente, repeticiones = "Sin palabras", 0
    return {
        "lineas": len(contenido.splitlines()),
        "palabras": len(palabras),
        "caracteres": len(contenido),
        "palabra_frecuente": palabra_frecuente,
        "repeticiones": repeticiones,
    }


def procesar_archivo(ruta):
    """Lee, analiza, genera el reporte individual y mueve el archivo.

    Devuelve el diccionario de metricas. Si algo falla lanza la excepcion
    hacia arriba para que quien llama decida como registrarla.
    """
    # --- PAUSA TEMPORAL SOLO PARA EL PASO 3 (evidencia de procesos) ---
    # Borrar estas dos lineas antes de hacer las mediciones de tiempo/memoria.
    import time
    time.sleep(3)
    # -------------------------------------------------------------------

    contenido = ruta.read_text(encoding="utf-8")
    metricas = analizar(contenido)

    reporte = REPORTES / f"reporte_{ruta.stem}.txt"
    reporte.write_text(
        f"Archivo: {ruta.name}\n"
        f"Lineas: {metricas['lineas']}\n"
        f"Palabras: {metricas['palabras']}\n"
        f"Caracteres: {metricas['caracteres']}\n"
        f"Palabra mas frecuente: {metricas['palabra_frecuente']} "
        f"({metricas['repeticiones']} repeticiones)\n"
        f"Fecha de proceso: {marca_tiempo()}\n",
        encoding="utf-8",
    )

    shutil.move(str(ruta), str(destino_unico(PROCESADOS, ruta.name)))
    return metricas


def registrar_error(ruta, error, version, log_fn=None):
    """Deja constancia de un archivo que no se pudo procesar.

    1) Escribe un detalle en data/errores/error_<nombre>.txt
    2) Escribe una linea diferenciada en el log
    3) Mueve el archivo problematico a data/errores/ para que no bloquee
       las siguientes ejecuciones
    """
    detalle = ERRORES / f"error_{ruta.stem}.txt"
    detalle.write_text(
        f"Archivo: {ruta.name}\n"
        f"Tipo de error: {type(error).__name__}\n"
        f"Detalle: {error}\n"
        f"Fecha: {marca_tiempo()}\n",
        encoding="utf-8",
    )

    mensaje = f"ERROR en {ruta.name}: {type(error).__name__}: {error}"
    if log_fn is not None:
        log_fn(mensaje)
    else:
        escribir_log(mensaje, version)

    try:
        shutil.move(str(ruta), str(destino_unico(ERRORES, ruta.name)))
    except OSError as fallo:
        mensaje_movida = f"No se pudo mover a errores {ruta.name}: {fallo}"
        if log_fn is not None:
            log_fn(mensaje_movida)
        else:
            escribir_log(mensaje_movida, version)


# --------------------------------------------------------------------------
# Memoria del propio proceso (complementa la salida de ps)
# --------------------------------------------------------------------------
def memoria_proceso():
    """Lee /proc/self/status y devuelve VmSize (VSZ), VmRSS (RSS) y VmHWM (RSS pico) en kB."""
    datos = {"VmSize": 0, "VmRSS": 0, "VmHWM": 0}
    try:
        with open("/proc/self/status", encoding="utf-8") as estado:
            for linea in estado:
                clave = linea.split(":")[0]
                if clave in datos:
                    datos[clave] = int(linea.split()[1])
    except OSError:
        pass
    return datos


# --------------------------------------------------------------------------
# Reporte consolidado y evidencia
# --------------------------------------------------------------------------
def escribir_consolidado(totales, version, duracion, hilos):
    memoria = memoria_proceso()
    consolidado = REPORTES / f"reporte_consolidado_{version}.txt"
    consolidado.write_text(
        f"REPORTE CONSOLIDADO - version {version}\n"
        f"Fecha: {marca_tiempo()}\n"
        f"Hilos trabajadores: {hilos}\n"
        f"----------------------------------------\n"
        f"Archivos procesados correctamente: {totales['archivos']}\n"
        f"Archivos con error: {totales['errores']}\n"
        f"Palabras procesadas: {totales['palabras']}\n"
        f"Caracteres procesados: {totales['caracteres']}\n"
        f"----------------------------------------\n"
        f"Tiempo total de ejecucion: {duracion:.3f} s\n"
        f"VSZ (VmSize): {memoria['VmSize']} kB\n"
        f"RSS actual (VmRSS): {memoria['VmRSS']} kB\n"
        f"RSS maximo (VmHWM): {memoria['VmHWM']} kB\n",
        encoding="utf-8",
    )
    return consolidado


def registrar_medicion(totales, version, duracion, hilos):
    """Agrega una fila a evidencia/mediciones.csv (crea el encabezado si hace falta)."""
    memoria = memoria_proceso()
    existe = MEDICIONES.exists()
    with MEDICIONES.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        if not existe:
            escritor.writerow([
                "fecha", "version", "hilos", "archivos_ok", "archivos_error",
                "palabras", "caracteres", "segundos", "vsz_kb", "rss_kb", "rss_pico_kb",
            ])
        escritor.writerow([
            marca_tiempo(), version, hilos, totales["archivos"], totales["errores"],
            totales["palabras"], totales["caracteres"], f"{duracion:.3f}",
            memoria["VmSize"], memoria["VmRSS"], memoria["VmHWM"],
        ])


def registrar_carrera(version, esperado, registrado):
    """Agrega una fila a evidencia/experimento_carrera.csv."""
    existe = CARRERA.exists()
    with CARRERA.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        if not existe:
            escritor.writerow(["fecha", "version", "esperado", "registrado", "perdidos"])
        escritor.writerow([
            marca_tiempo(), version, esperado, registrado, esperado - registrado,
        ])
