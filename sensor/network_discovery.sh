\
#!/data/data/com.termux/files/usr/bin/bash

set -Eeuo pipefail
umask 077

BASE_DIR="$HOME/soc-sensor"
BIN_DIR="$BASE_DIR/bin"
CONFIG_DIR="$BASE_DIR/config"
SCANS_DIR="$BASE_DIR/data/scans"
LOG_DIR="$BASE_DIR/logs"

TARGETS_FILE="$CONFIG_DIR/expected-hosts.txt"
SENSOR_ENV="$CONFIG_DIR/sensor.env"
API_ENV="$CONFIG_DIR/api.env"

timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
xml_file="$SCANS_DIR/discovery-${timestamp}.xml"
events_file="$SCANS_DIR/discovery-${timestamp}.ndjson"
nmap_log="$LOG_DIR/discovery-${timestamp}.nmap.log"

lock_dir="$BASE_DIR/data/network-discovery.lock"

cleanup() {
  rmdir "$lock_dir" 2>/dev/null || true
}

if ! mkdir "$lock_dir" 2>/dev/null; then
  echo "ERRO: outra descoberta de rede parece estar em execução"
  exit 1
fi

trap cleanup EXIT INT TERM

mkdir -p "$SCANS_DIR" "$LOG_DIR"

for required_file in "$TARGETS_FILE" "$SENSOR_ENV" "$API_ENV"; do
  if [ ! -r "$required_file" ]; then
    echo "ERRO: arquivo ausente ou sem leitura: $required_file"
    exit 1
  fi
done

set -a
source "$SENSOR_ENV"
source "$API_ENV"
set +a

if [ -z "${SENSOR_ID:-}" ] ||
   [ -z "${NETWORK_ID:-}" ] ||
   [ -z "${API_URL:-}" ] ||
   [ -z "${SOC_COLLECTOR_TOKEN:-}" ]; then
  echo "ERRO: configuração obrigatória ausente"
  exit 1
fi

targets=()

while IFS= read -r target || [ -n "$target" ]; do
  target="${target#"${target%%[![:space:]]*}"}"
  target="${target%"${target##*[![:space:]]}"}"

  case "$target" in
    ""|\#*) continue ;;
  esac

  targets+=("$target")
done < "$TARGETS_FILE"

if [ "${#targets[@]}" -eq 0 ]; then
  echo "ERRO: nenhuma máquina definida em $TARGETS_FILE"
  exit 1
fi

echo "Iniciando descoberta de ${#targets[@]} alvos..."
echo "Horário UTC: $timestamp"

if ! nmap \
  -sn \
  --unprivileged \
  --reason \
  --max-retries 1 \
  --host-timeout 10s \
  -oX "$xml_file" \
  "${targets[@]}" \
  >"$nmap_log" 2>&1; then
  echo "ERRO: Nmap falhou. Consulte: $nmap_log"
  exit 1
fi

if [ ! -s "$xml_file" ]; then
  echo "ERRO: o Nmap não produziu um XML válido"
  exit 1
fi

python "$BIN_DIR/nmap_to_events.py" \
  "$xml_file" \
  "$TARGETS_FILE" \
  --output "$events_file"

event_count="$(wc -l < "$events_file")"

if [ "$event_count" -ne "${#targets[@]}" ]; then
  echo "ERRO: esperados ${#targets[@]} eventos, produzidos $event_count"
  exit 1
fi

python "$BIN_DIR/send_events.py" "$events_file"

echo
echo "Descoberta concluída:"
echo "  Alvos: ${#targets[@]}"
echo "  Eventos enviados: $event_count"
echo "  XML: $xml_file"
echo "  NDJSON: $events_file"
echo "  Log Nmap: $nmap_log"
