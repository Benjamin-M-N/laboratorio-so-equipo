"""
version_sincronizacion_experimental.py
VERSION DELIBERADAMENTE INSEGURA. No usar como solucion final.

Es identica a version_concurrente.py salvo en un punto: el diccionario de
totales se actualiza SIN threading.Lock, y ademas se separa la lectura de la
escritura del contador con una pausa breve.

    valor = totales["archivos"]   <-- lectura
    time.sleep(0.001)             <-- ventana para el cambio de contexto
    totales["archivos"] = valor+1 <-- escritura

Esa separacion hace visible que 'contador += 1' NO es una operacion atomica:
si dos hilos leen el mismo valor antes de que alguno escriba, uno de los dos
incrementos se pierde.

Uso:  python3 src/version_sincronizacion_experimental.py
"""

import time
from queue import Queue
from threading import Lock, Thread

from comun import (
    ENTRADA,
    escribir_log,
    preparar_carpetas,
    procesar_archivo,
    registrar_carrera,
    registrar_error,
)

VERSION = "experimental_sin_lock"
CANTIDAD_TRABAJADORES = 3
CENTINELA = None
PAUSA = 0.001  # segundos entre la lectura y la escritura del contador

cola = Queue()
bloqueo_log = Lock()          # el log SI se protege, para no ensuciar el experimento

# SIN bloqueo_totales: esta es justamente la falla que se quiere demostrar.
totales = {"archivos": 0, "palabras": 0, "caracteres": 0, "errores": 0}
control = {"encolados": 0}


def log_seguro(mensaje):
    with bloqueo_log:
        escribir_log(mensaje, VERSION)


def productor():
    for ruta in sorted(ENTRADA.glob("*.txt")):
        cola.put(ruta)
        control["encolados"] += 1
    log_seguro(f"Productor finalizado. Archivos encolados: {control['encolados']}")


def trabajador(numero):
    while True:
        ruta = cola.get()

        if ruta is CENTINELA:
            cola.task_done()
            break

        try:
            metricas = procesar_archivo(ruta)
        except Exception as error:  # noqa: BLE001
            totales["errores"] += 1
            registrar_error(ruta, error, VERSION, log_fn=log_seguro)
        else:
            # ---------- SECCION CRITICA SIN PROTEGER ----------
            valor_actual = totales["archivos"]
            time.sleep(PAUSA)
            totales["archivos"] = valor_actual + 1

            valor_palabras = totales["palabras"]
            time.sleep(PAUSA)
            totales["palabras"] = valor_palabras + metricas["palabras"]

            valor_caracteres = totales["caracteres"]
            time.sleep(PAUSA)
            totales["caracteres"] = valor_caracteres + metricas["caracteres"]
            # --------------------------------------------------
        finally:
            cola.task_done()


def main():
    preparar_carpetas()
    log_seguro("=== Inicio de ejecucion EXPERIMENTAL (sin Lock en totales) ===")
    inicio = time.perf_counter()

    trabajadores = [
        Thread(target=trabajador, args=(numero + 1,), name=f"trabajador-{numero + 1}")
        for numero in range(CANTIDAD_TRABAJADORES)
    ]
    for hilo in trabajadores:
        hilo.start()

    hilo_productor = Thread(target=productor, name="productor")
    hilo_productor.start()
    hilo_productor.join()

    for _ in trabajadores:
        cola.put(CENTINELA)

    cola.join()
    for hilo in trabajadores:
        hilo.join()

    duracion = time.perf_counter() - inicio
    esperado = control["encolados"] - totales["errores"]
    registrado = totales["archivos"]
    perdidos = esperado - registrado

    registrar_carrera(VERSION, esperado, registrado)
    log_seguro(
        f"=== Fin EXPERIMENTAL en {duracion:.3f} s | "
        f"esperado={esperado} registrado={registrado} perdidos={perdidos} ==="
    )

    print("--------------------------------------------------")
    print(f"[{VERSION}] archivos realmente procesados (esperado): {esperado}")
    print(f"[{VERSION}] contador registrado por los hilos:        {registrado}")
    print(f"[{VERSION}] incrementos PERDIDOS:                     {perdidos}")
    print("--------------------------------------------------")
    if perdidos == 0:
        print("Sin perdidas en esta corrida. Ejecute de nuevo o suba la carga:")
        print("  la condicion de carrera es intermitente por naturaleza.")
    else:
        print("Condicion de carrera reproducida. Evidencia en evidencia/experimento_carrera.csv")


if __name__ == "__main__":
    main()
