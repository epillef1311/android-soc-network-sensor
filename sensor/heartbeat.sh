\
#!/data/data/com.termux/files/usr/bin/bash

set -u

BASE_DIR="$HOME/soc-sensor"
SENSOR_CONFIG="$BASE_DIR/config/sensor.env"
API_CONFIG="$BASE_DIR/config/api.env"

if [ ! -r "$SENSOR_CONFIG" ] || [ ! -r "$API_CONFIG" ]; then
    echo "Erro: arquivos de configuração não encontrados."
    exit 1
fi

set -a
. "$SENSOR_CONFIG"
. "$API_CONFIG"
set +a

for variable in SENSOR_ID NETWORK_ID SENSOR_SOURCE API_URL SOC_COLLECTOR_TOKEN; do
    eval "value=\${$variable:-}"

    if [ -z "$value" ]; then
        echo "Erro: variável $variable não configurada."
        exit 1
    fi
done

OBSERVED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

PAYLOAD="$(jq -n \
    --arg event_type "heartbeat" \
    --arg sensor_id "$SENSOR_ID" \
    --arg network_id "$NETWORK_ID" \
    --arg observed_at "$OBSERVED_AT" \
    --arg source "$SENSOR_SOURCE" \
    '{
        event_type: $event_type,
        sensor_id: $sensor_id,
        network_id: $network_id,
        observed_at: $observed_at,
        source: $source,
        data: {
            message: "sensor online"
        }
    }'
)"

RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$RESPONSE_FILE"; unset SOC_COLLECTOR_TOKEN' EXIT

if ! HTTP_CODE="$(curl \
    --silent \
    --show-error \
    --output "$RESPONSE_FILE" \
    --write-out '%{http_code}' \
    --connect-timeout 5 \
    --max-time 15 \
    --request POST \
    --header "Authorization: Bearer $SOC_COLLECTOR_TOKEN" \
    --header "Content-Type: application/json" \
    --data "$PAYLOAD" \
    "$API_URL/events")"; then
    echo "Erro: não foi possível comunicar com a API."
    exit 1
fi

if [ "$HTTP_CODE" = "202" ]; then
    echo "Heartbeat aceito pela API."
    echo "Horário observado: $OBSERVED_AT"
    jq . "$RESPONSE_FILE"
else
    echo "Erro: API respondeu HTTP $HTTP_CODE."
    jq . "$RESPONSE_FILE" 2>/dev/null || cat "$RESPONSE_FILE"
    exit 1
fi
