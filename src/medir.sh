#!/usr/bin/env bash
# medir.sh
# Ejecuta una version midiendo tiempo, memoria y disco antes/despues.
#
# Uso:
#   bash src/medir.sh secuencial 20
#   bash src/medir.sh concurrente 20
#   bash src/medir.sh secuencial 200
#   bash src/medir.sh concurrente 200

set -euo pipefail

BASE="$HOME/laboratorio_so"
cd "$BASE"

VERSION="${1:-secuencial}"
N="${2:-20}"
SALIDA="evidencia/comandos_ejecutados.txt"

mkdir -p evidencia

{
echo ""
echo "============================================================"
echo "MEDICION | version=$VERSION | archivos=$N | $(date '+%F %T')"
echo "============================================================"

echo ""
echo "--- Preparando entrada ---"
bash src/generar_entrada.sh "$N"

echo ""
echo "--- MEMORIA ANTES (free -h) ---"
free -h
echo ""
echo "--- DISCO ANTES (df -h /) ---"
df -h /
echo ""
echo "--- Uso de la carpeta data (du -sh) ---"
du -sh data

echo ""
echo "--- EJECUCION ---"
TIMEFORMAT='real=%3R  user=%3U  sys=%3S'
time python3 "src/version_${VERSION}.py"

echo ""
echo "--- MEMORIA DESPUES (free -h) ---"
free -h
echo ""
echo "--- DISCO DESPUES (df -h /) ---"
df -h /
echo ""
echo "--- Archivos y permisos resultantes ---"
ls -lh data/procesados | head -n 6
echo "Total procesados: $(ls -1 data/procesados | wc -l)"
echo "Total reportes:   $(ls -1 data/reportes | wc -l)"
echo "Total errores:    $(ls -1 data/errores | wc -l)"

echo ""
echo "--- Consolidado ---"
cat "data/reportes/reporte_consolidado_${VERSION}.txt"

} 2>&1 | tee -a "$SALIDA"

echo ""
echo "Salida guardada en $SALIDA"
echo "Fila agregada a evidencia/mediciones.csv"
