# Arquitetura

## Android / Termux

O sensor Android possui dois fluxos:

1. **Heartbeat**
   - `heartbeat.sh`
   - Envia um evento `heartbeat` ao Collector.

2. **Network discovery**
   - `network_discovery.sh`
   - Executa Nmap `-sn --unprivileged`.
   - Gera XML.
   - `nmap_to_events.py` converte o XML para NDJSON.
   - `send_events.py` envia os eventos ao Collector.

## Ubuntu / Collector

- FastAPI em `/opt/soc-collector/app/main.py`.
- Uvicorn em `0.0.0.0:8000`.
- Bearer Token.
- Persistência em `/var/lib/soc-collector/events.ndjson`.

## Ubuntu / Device Observer

- Executa `arp-scan --localnet`.
- Compara MACs observados com inventário autorizado.
- Classifica dispositivos como `known` ou `unknown`.
- Mantém `first_seen`, `last_seen` e métodos de descoberta.
- Persiste estado em `/var/lib/soc-collector/device_state.json`.
- Envia eventos `device_observed` ao Collector.
- Executa periodicamente via systemd timer.
