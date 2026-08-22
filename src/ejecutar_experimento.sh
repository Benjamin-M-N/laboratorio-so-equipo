#!/usr/bin/env bash
# ejecutar_experimento.sh
# Repite el experimento de condicion de carrera y deja la evidencia en
# evidencia/experimento_carrera.csv
#
# Uso:
#   bash src/ejecutar_experimento.sh           -> 120 archivos, 5 repeticiones
#   bash src/ejecutar_experimento.sh 200 10    -> 200 archivos, 10 repeticiones

set -euo pipefail

BASE="$HOME/laboratorio_so"
cd "$BASE"

N="${1:-120}"
REPETICIONES="${2:-5}"

echo "############################################################"
echo "# BLOQUE 1: version SIN Lock (se esperan perdidas)"
echo "############################################################"
for r in $(seq 1 "$REPETICIONES"); do
    echo ""
    echo "--- Corrida $r/$REPETICIONES (sin lock, $N archivos) ---"
    bash src/generar_entrada.sh "$N" no > /dev/null
    python3 src/version_sincronizacion_experimental.py
done

echo ""
echo "############################################################"
echo "# BLOQUE 2: version CON Lock (no debe haber perdidas)"
echo "############################################################"
for r in $(seq 1 "$REPETICIONES"); do
    echo ""
    echo "--- Corrida $r/$REPETICIONES (con lock, $N archivos) ---"
    bash src/generar_entrada.sh "$N" no > /dev/null
    python3 src/version_concurrente.py
done

echo ""
echo "############################################################"
echo "# RESUMEN (evidencia/experimento_carrera.csv)"
echo "############################################################"
column -s, -t < evidencia/experimento_carrera.csv

