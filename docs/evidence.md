# Evidências recuperadas

Este snapshot foi montado a partir de arquivos e comandos efetivamente recuperados do laboratório.

## Android / Termux

Arquivos confirmados:

- `~/soc-sensor/bin/heartbeat.sh`
- `~/soc-sensor/bin/network_discovery.sh`
- `~/soc-sensor/bin/nmap_to_events.py`
- `~/soc-sensor/bin/send_events.py`

Também foram observados artefatos reais de scans `.xml`, `.ndjson` e logs, mas eles não foram incluídos neste repositório para evitar exposição de IPs, MACs e dados de rede.

## Ubuntu

Arquivos confirmados:

- `/opt/soc-collector/app/main.py`
- `/usr/local/sbin/soc-device-observer`
- `/etc/systemd/system/soc-collector.service`
- `/etc/systemd/system/soc-device-observer.service`
- `/etc/systemd/system/soc-device-observer.timer`
- `/var/lib/soc-collector/events.ndjson`
- `/var/lib/soc-collector/device_state.json`

Configurações reais com segredo/inventário não foram incluídas.
