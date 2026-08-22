"""
version_secuencial.py
Procesador de archivos SIN concurrencia: un solo hilo, un archivo a la vez.
Sirve como linea base para comparar tiempo y memoria contra la version concurrente.

Uso:  python3 src/version_secuencial.py
"""

import time

from comun import (
    ENTRADA,
    escribir_consolidado,
    escribir_log,
    preparar_carpetas,
    procesar_archivo,
    registrar_error,
    registrar_medicion,
)

VERSION = "secuencial"


def main():
    preparar_carpetas()
    escribir_log("=== Inicio de ejecucion SECUENCIAL ===", VERSION)
    inicio = time.perf_counter()

    totales = {"archivos": 0, "palabras": 0, "caracteres": 0, "errores": 0}

    # sorted() materializa la lista ANTES de empezar a mover archivos.
    # Si se itera el generador de glob() mientras se modifica la carpeta,
    # el recorrido puede saltarse archivos.
    rutas = sorted(ENTRADA.glob("*.txt"))
    escribir_log(f"Archivos detectados en data/entrada: {len(rutas)}", VERSION)

    for ruta in rutas:
        try:
            metricas = procesar_archivo(ruta)
        except Exception as error:  # noqa: BLE001 - se registra cualquier fallo por archivo
            totales["errores"] += 1
            registrar_error(ruta, error, VERSION)
            continue

        # No hay seccion critica: un unico hilo actualiza los totales.
        totales["archivos"] += 1
        totales["palabras"] += metricas["palabras"]
        totales["caracteres"] += metricas["caracteres"]
        escribir_log(
            f"Procesado {ruta.name} "
            f"(lineas={metricas['lineas']}, palabras={metricas['palabras']}, "
            f"caracteres={metricas['caracteres']}, "
            f"frecuente={metricas['palabra_frecuente']})",
            VERSION,
        )

    duracion = time.perf_counter() - inicio
    escribir_consolidado(totales, VERSION, duracion, hilos=0)
    registrar_medicion(totales, VERSION, duracion, hilos=0)
    escribir_log(
        f"=== Fin de ejecucion SECUENCIAL en {duracion:.3f} s "
        f"(ok={totales['archivos']}, errores={totales['errores']}) ===",
        VERSION,
    )

    print(f"[{VERSION}] archivos ok: {totales['archivos']} | errores: {totales['errores']}")
    print(f"[{VERSION}] palabras: {totales['palabras']} | caracteres: {totales['caracteres']}")
    print(f"[{VERSION}] tiempo total: {duracion:.3f} s")
    print("Revise data/reportes/, data/errores/ y logs/sistema.log")


if __name__ == "__main__":
    main()
