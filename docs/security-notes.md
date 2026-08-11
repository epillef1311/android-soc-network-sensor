# Segurança e hardening

## Collector

O serviço do Collector usa:

- usuário e grupo dedicados `soccollector`;
- `NoNewPrivileges=true`;
- `PrivateTmp=true`;
- `ProtectSystem=strict`;
- `ProtectHome=true`;
- proteção de kernel e cgroups;
- diretório de escrita restrito a `/var/lib/soc-collector`.

## Device Observer

O Observer executa como root devido ao uso de descoberta ARP e possui:

- `NoNewPrivileges=true`;
- `ProtectSystem=strict`;
- `ProtectHome=true`;
- restrição de address families;
- `CapabilityBoundingSet`.

Hardening futuro: investigar execução com usuário dedicado e conjunto mínimo de capabilities.

## Segredos

Arquivos reais de ambiente não devem ser versionados. Use somente os exemplos fornecidos.
