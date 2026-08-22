#!/usr/bin/env bash
# generar_entrada.sh
# Regenera data/entrada/ con N archivos .txt y limpia los resultados previos.
#
# Uso:
#   bash src/generar_entrada.sh            -> 20 archivos + archivos defectuosos
#   bash src/generar_entrada.sh 200        -> 200 archivos + archivos defectuosos
#   bash src/generar_entrada.sh 120 no     -> 120 archivos, SIN defectuosos
#
# El segundo argumento "no" se usa para el experimento de condicion de carrera,
# donde conviene que todos los archivos se procesen sin error.

set -euo pipefail

BASE="$HOME/laboratorio_so"
ENTRADA="$BASE/data/entrada"
N="${1:-20}"
DEFECTUOSOS="${2:-si}"

mkdir -p "$ENTRADA" "$BASE/data/procesados" "$BASE/data/reportes" \
         "$BASE/data/errores" "$BASE/logs" "$BASE/evidencia/capturas"

# Limpieza de la corrida anterior (el log y las mediciones se conservan)
chmod -R u+rw "$ENTRADA" 2>/dev/null || true
rm -f "$ENTRADA"/* "$BASE/data/procesados"/* "$BASE/data/reportes"/* "$BASE/data/errores"/* 2>/dev/null || true

PALABRAS=(proceso hilo memoria archivo cola bloqueo nucleo kernel semaforo pagina)

for i in $(seq 1 "$N"); do
    indice=$(( (i - 1) % ${#PALABRAS[@]} ))
    dominante="${PALABRAS[$indice]}"
    lineas=$(( (i % 5) + 3 ))
    destino="$ENTRADA/archivo_$(printf '%03d' "$i").txt"
    : > "$destino"
    for l in $(seq 1 "$lineas"); do
        echo "$dominante $dominante concurrencia seccion critica $dominante linea $l" >> "$destino"
    done
done

if [ "$DEFECTUOSOS" = "si" ]; then
    # Caso borde: archivo vacio (NO es error, debe reportar 0 palabras)
    : > "$ENTRADA/archivo_vacio.txt"

    # Error 1: bytes que no son UTF-8 validos -> UnicodeDecodeError
    printf 'texto \xff\xfe invalido' > "$ENTRADA/archivo_corrupto.txt"

    # Error 2: archivo sin permiso de lectura -> PermissionError
    printf 'contenido no legible' > "$ENTRADA/archivo_sin_permisos.txt"
    chmod 000 "$ENTRADA/archivo_sin_permisos.txt"
fi

echo "Entrada regenerada en $ENTRADA"
echo "Archivos .txt: $(ls -1 "$ENTRADA" | wc -l)"
ls -lh "$ENTRADA" | head -n 8
