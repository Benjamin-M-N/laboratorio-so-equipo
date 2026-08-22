"""
version_concurrente.py
Procesador CONCURRENTE de archivos.

Arquitectura productor / consumidores:
  - 1 hilo productor: recorre data/entrada/ y encola las rutas.
  - N hilos trabajadores (>= 3): consumen la cola y procesan cada archivo.
  - queue.Queue: cola sincronizada compartida (thread-safe por diseno).
  - 2 threading.Lock: uno protege el archivo de log, otro el diccionario de totales.
  - Centinelas (None): una por trabajador, para lograr un termino ordenado.

Uso:  python3 src/version_concurrente.py
"""

import time
from queue import Queue
from threading import Lock, Thread

from comun import (
    ENTRADA,
    escribir_consolidado,
    escribir_log,
    preparar_carpetas,
    procesar_archivo,
    registrar_carrera,
    registrar_error,
    registrar_medicion,
)

VERSION = "concurrente"
CANTIDAD_TRABAJADORES = 3   # requisito: al menos tres
CENTINELA = None            # senal de termino para los trabajadores

# ---------------------------------------------------------------------------
# Recursos COMPARTIDOS entre los hilos
# ---------------------------------------------------------------------------
cola = Queue()
bloqueo_log = Lock()
bloqueo_totales = Lock()

totales = {"archivos": 0, "palabras": 0, "caracteres": 0, "errores": 0}
control = {"encolados": 0}   # solo lo toca el productor (un unico hilo)


def log_seguro(mensaje):
    """Seccion critica 1: escritura en el archivo de log."""
    with bloqueo_log:
        escribir_log(mensaje, VERSION)


def productor():
    """Recorre la carpeta de entrada y agrega cada ruta a la cola."""
    for ruta in sorted(ENTRADA.glob("*.txt")):
        cola.put(ruta)
        control["encolados"] += 1
        log_seguro(f"Archivo agregado a la cola: {ruta.name}")
    log_seguro(f"Productor finalizado. Archivos encolados: {control['encolados']}")


def trabajador(numero):
    """Consume rutas de la cola hasta recibir el centinela."""
    log_seguro(f"Trabajador {numero} iniciado")

    while True:
        ruta = cola.get()

        if ruta is CENTINELA:
            cola.task_done()
            log_seguro(f"Trabajador {numero} recibio centinela y termina")
            break

        try:
            metricas = procesar_archivo(ruta)
        except Exception as error:  # noqa: BLE001
            with bloqueo_totales:
                totales["errores"] += 1
            registrar_error(ruta, error, VERSION, log_fn=log_seguro)
        else:
            # Seccion critica 2: actualizacion del contador compartido.
            with bloqueo_totales:
                totales["archivos"] += 1
                totales["palabras"] += metricas["palabras"]
                totales["caracteres"] += metricas["caracteres"]
            log_seguro(
                f"Trabajador {numero} proceso {ruta.name} "
                f"(lineas={metricas['lineas']}, palabras={metricas['palabras']}, "
                f"caracteres={metricas['caracteres']}, "
                f"frecuente={metricas['palabra_frecuente']})"
            )
        finally:
            cola.task_done()


def main():
    preparar_carpetas()
    log_seguro("=== Inicio de ejecucion CONCURRENTE ===")
    inicio = time.perf_counter()

    # 1) Levantar primero los consumidores, para que empiecen a trabajar
    #    apenas el productor deposite la primera ruta.
    trabajadores = [
        Thread(target=trabajador, args=(numero + 1,), name=f"trabajador-{numero + 1}")
        for numero in range(CANTIDAD_TRABAJADORES)
    ]
    for hilo in trabajadores:
        hilo.start()

    # 2) Levantar el productor y esperar a que termine de encolar.
    hilo_productor = Thread(target=productor, name="productor")
    hilo_productor.start()
    hilo_productor.join()

    # 3) Termino ordenado: una centinela por trabajador.
    for _ in trabajadores:
        cola.put(CENTINELA)

    # 4) Esperar a que la cola quede vacia y luego a que mueran los hilos.
    cola.join()
    for hilo in trabajadores:
        hilo.join()

    duracion = time.perf_counter() - inicio
    escribir_consolidado(totales, VERSION, duracion, hilos=CANTIDAD_TRABAJADORES)
    registrar_medicion(totales, VERSION, duracion, hilos=CANTIDAD_TRABAJADORES)
    registrar_carrera(VERSION, control["encolados"] - totales["errores"], totales["archivos"])
    log_seguro(
        f"=== Fin de ejecucion CONCURRENTE en {duracion:.3f} s "
        f"(ok={totales['archivos']}, errores={totales['errores']}) ==="
    )

    esperado = control["encolados"] - totales["errores"]
    print(f"[{VERSION}] hilos trabajadores: {CANTIDAD_TRABAJADORES}")
    print(f"[{VERSION}] esperado: {esperado} | registrado: {totales['archivos']}")
    print(f"[{VERSION}] errores: {totales['errores']}")
    print(f"[{VERSION}] palabras: {totales['palabras']} | caracteres: {totales['caracteres']}")
    print(f"[{VERSION}] tiempo total: {duracion:.3f} s")


if __name__ == "__main__":
    main()
