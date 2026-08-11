# Roadmap do Projeto — Android SOC Network Sensor

## 1. Visão geral

O projeto transforma um celular Android antigo — atualmente um LG K41S — em parte de um laboratório
defensivo de segurança de redes. O celular atuará como sensor/coletor portátil,
enquanto uma máquina virtual Ubuntu executará os componentes centrais de coleta,
análise e visualização.

O projeto deverá:

- identificar dispositivos presentes em redes locais autorizadas;
- manter um inventário de IP, MAC e fabricante;
- diferenciar dispositivos conhecidos e desconhecidos;
- registrar entrada, saída e mudança de endereço dos dispositivos;
- enviar eventos estruturados ao Wazuh;
- gerar alertas e dashboards úteis para investigação;
- operar em mais de uma rede autorizada;
- armazenar eventos temporariamente quando o servidor estiver indisponível;
- analisar tráfego disponível em uma rede de laboratório controlada;
- validar detecções com testes de segurança autorizados, incluindo ARP spoofing.

O projeto não promete capturar todo o tráfego de uma rede apenas conectando o
celular ao Wi-Fi. Em redes comutadas, o sensor normalmente enxerga o próprio
tráfego, broadcasts, multicasts e respostas às suas próprias consultas. Para
observar o tráfego completo de outros dispositivos, ele deverá ser posicionado
como gateway ou receber uma cópia do tráfego em uma rede controlada.

## 2. Arquitetura planejada

```text
Celular Android
  ├── identifica a rede autorizada
  ├── coleta informações observáveis
  ├── executa descoberta de dispositivos
  └── envia eventos JSON
              |
              v
API coletora na VM Ubuntu
  ├── autentica e valida eventos
  ├── registra eventos em NDJSON
  └── disponibiliza os logs ao Wazuh
              |
              v
Wazuh
  ├── indexa eventos
  ├── aplica decoders e regras
  ├── gera alertas
  └── apresenta dashboards
```

Na fase avançada, uma rede isolada adicionará Suricata ou Zeek para analisar o
tráfego que passar deliberadamente pelo sensor ou gateway do laboratório.

## 3. Mapa das etapas

| Etapa | Nome | Resultado principal | Estado |
|---:|---|---|---|
| 0 | Definição e organização | Escopo, repositório e documentação inicial | Concluída |
| 1 | Laboratório virtual e rede | VM Ubuntu acessível e pronta para o Wazuh | Concluída |
| 2 | Instalação do Wazuh | Manager, Indexer e Dashboard operacionais | Concluída |
| 3 | API coletora | Endpoint autenticado e log NDJSON | Concluída |
| 4 | Preparação do Android | Ambiente de coleta reproduzível no celular | Concluída |
| 5 | Primeiro evento ponta a ponta | Evento do celular visível no Wazuh | Próxima |
| 6 | Descoberta de dispositivos | Inventário de dispositivos sem depender de ping | Pendente |
| 7 | Baseline e detecção de mudanças | Alertas de dispositivo desconhecido e alterações | Pendente |
| 8 | Perfis de múltiplas redes | Baselines separadas por rede autorizada | Pendente |
| 9 | Coleta offline e sincronização | Fila local confiável no Android | Pendente |
| 10 | Regras e dashboard no Wazuh | Visualização e correlação úteis para SOC | Pendente |
| 11 | Testes, investigação e PCAP | Evidências e validação das detecções | Pendente |
| 12 | Segurança, documentação e portfólio | Projeto reproduzível e publicável | Pendente |

## 4. Caminho crítico do MVP

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 10 → 11 → 12
```

As Etapas 8 e 9 adicionam portabilidade e tolerância a falhas. Elas deverão ser
executadas depois que a descoberta, a baseline e o envio ao Wazuh estiverem
funcionando corretamente em uma única rede.

---

## Etapa 0 — Definição e organização

### Objetivo

Definir o escopo defensivo, organizar o repositório e estabelecer uma base
documental antes de instalar ferramentas.

### Atividades

- definir o objetivo e as limitações do projeto;
- registrar que os testes serão executados somente em redes próprias ou
  explicitamente autorizadas;
- definir a arquitetura inicial;
- criar a estrutura de pastas do repositório;
- criar `README.md`, `.gitignore` e documentação de arquitetura;
- definir o formato inicial dos eventos JSON;
- separar códigos, configurações, exemplos, relatórios e evidências;
- impedir a publicação de senhas, tokens, IPs públicos e dados sensíveis.

### Entregável

Repositório organizado e documentado, ainda sem monitoramento ativo.

### Critério de conclusão

- [x] Escopo definido.
- [x] Arquitetura inicial registrada.
- [x] Estrutura do projeto criada.
- [x] Regras de uso autorizado documentadas.

---

## Etapa 1 — Laboratório virtual e rede

### Objetivo

Preparar a VM que hospedará os serviços centrais do laboratório.

### Atividades realizadas

- criação de VM com Ubuntu Server 24.04 no VirtualBox;
- configuração de rede em modo Bridge;
- atualização do sistema;
- configuração e teste do SSH;
- ativação do UFW;
- validação de acesso à internet, DNS e HTTPS;
- teste de comunicação entre Windows, VM e Android;
- validação do endereço IPv4 durante reinicializações;
- criação do snapshot `stage-01-clean-ubuntu`;
- expansão do LVM e validação do volume raiz com aproximadamente 57 GB;
- criação do snapshot `stage-01b-expanded-disk`;
- registro das limitações encontradas.

### Resultado

A VM está pronta para receber o Wazuh. O roteador não responde a ICMP e seu
painel administrativo não ficou acessível, mas isso não impede o projeto.
A reserva DHCP permanece pendente, e o endereço da VM deverá ser conferido
sempre que necessário.

A VM foi temporariamente mantida com 2 vCPUs após travamentos intermitentes. O
LVM foi expandido e um novo teste com 4 vCPUs foi bem-sucedido. A configuração
final utiliza 4 vCPUs, 8 GB de RAM e volume raiz de aproximadamente 57 GB.

### Entregável

Relatório `reports/stage-01-lab-network.md` e snapshots
`stage-01-clean-ubuntu` e `stage-01b-expanded-disk`.

### Critério de conclusão

- [x] VM inicia corretamente.
- [x] Acesso externo e DNS funcionam.
- [x] SSH funciona na rede local.
- [x] Android alcança um serviço temporário na VM.
- [x] Firewall está ativo.
- [x] LVM foi expandido e validado.
- [x] Snapshots da preparação foram criados.
- [ ] Reserva DHCP configurada — pendência não bloqueante.

---

## Etapa 2 — Instalação do Wazuh

### Objetivo

Instalar e validar o núcleo do SIEM que receberá os eventos do projeto.

### Pré-validação

Antes da instalação:

- conferir CPU, memória e espaço disponível;
- validar que não existem serviços do sistema em falha;
- verificar se a VM inicializa de forma confiável;
- confirmar compatibilidade dos recursos disponíveis com a implantação
  all-in-one;
- documentar qualquer ajuste de recursos do VirtualBox.

### Atividades realizadas

- instalação all-in-one da linha Wazuh 4.14;
- validação de Manager, Indexer, Dashboard e Filebeat;
- validação do Indexer em estado `green`;
- liberação das portas 22 e 443 somente para a rede local autorizada;
- manutenção das portas 9200 e 55000 sem liberação no UFW;
- teste do Dashboard a partir do Windows por HTTPS;
- preservação da credencial administrativa única sem incluí-la nos relatórios;
- teste de reinicialização e retorno automático dos serviços;
- criação do snapshot após a instalação saudável.

### Entregável

Servidor Wazuh operacional, acesso restrito ao Dashboard, relatório
`reports/stage-02-wazuh-installation.md` e snapshot de recuperação.

### Critério de conclusão

- [x] Manager, Indexer, Dashboard e Filebeat ativos.
- [x] Indexer com cluster em estado `green`.
- [x] Dashboard acessível apenas pela rede autorizada.
- [x] Credencial administrativa única preservada sem exposição.
- [x] Serviços sem falhas e estáveis após reinicialização.
- [x] Snapshot `stage-02-wazuh-working` criado.

---

## Etapa 3 — API coletora de eventos

### Objetivo

Criar um serviço simples para receber eventos do Android e entregá-los ao
pipeline de análise.

### Atividades

- implementar uma API em FastAPI;
- criar endpoint de saúde;
- criar endpoint de ingestão de eventos;
- definir e validar o schema JSON;
- autenticar o sensor com token próprio do laboratório;
- rejeitar eventos inválidos, grandes demais ou não autorizados;
- registrar os eventos em `events.ndjson`;
- usar timestamps em UTC;
- impedir que tokens apareçam nos logs;
- executar o serviço com `systemd`;
- restringir a porta da API à rede local autorizada.

### Campos iniciais do evento

```json
{
  "event_type": "heartbeat",
  "sensor_id": "android-sensor-01",
  "network_id": "home-lab",
  "observed_at": "2026-07-23T12:00:00Z",
  "source": "android"
}
```

### Entregável

API coletora ativa, autenticada e escrevendo eventos válidos em NDJSON.

### Critério de conclusão

- [x] Requisição autorizada retorna sucesso.
- [x] Requisição sem token é rejeitada.
- [x] JSON inválido é rejeitado.
- [x] Evento válido aparece uma única vez no arquivo.
- [x] Serviço volta automaticamente após reinicialização.

---

## Etapa 4 — Preparação do celular Android

### Objetivo

Preparar o LG K41S como sensor portátil e reproduzível.

### Atividades

- registrar modelo, versão do Android e limitações do aparelho;
- instalar Termux por uma fonte confiável;
- atualizar os pacotes;
- instalar apenas as ferramentas necessárias;
- criar uma identificação persistente para o sensor;
- configurar o endereço e o token da API fora do código;
- criar script de heartbeat;
- verificar conectividade com a VM;
- avaliar limitações de permissões, economia de bateria e execução em segundo
  plano;
- decidir quais funções exigiriam root e mantê-las fora do MVP quando possível.

### Observação técnica

Descoberta ARP ativa pode exigir acesso a recursos de rede que variam conforme
a versão do Android, as permissões e o estado de root. A Etapa 6 deverá validar
experimentalmente quais métodos o aparelho suporta. A VM poderá executar a
primeira implementação de referência, sem alterar o objetivo de tornar o
celular o sensor portátil.

### Entregável

Ambiente do Android documentado, acesso SSH protegido e script capaz de enviar
heartbeat autenticado à API. Relatório
`reports/stage-04-android-sensor-preparation.md`.

### Critério de conclusão

- [x] Sensor possui ID próprio.
- [x] Configuração não contém segredo versionado.
- [x] Heartbeat pode ser executado manualmente.
- [x] Restrições do Android foram documentadas.

---

## Etapa 5 — Primeiro evento ponta a ponta

### Objetivo

Comprovar todo o caminho entre o Android e o Wazuh antes de adicionar a lógica
de descoberta.

### Fluxo esperado

```text
LG K41S → FastAPI → events.ndjson → Wazuh → Dashboard
```

### Atividades

- enviar um heartbeat JSON pelo celular;
- validar o recebimento e a gravação na API;
- configurar o Wazuh para ler o arquivo NDJSON;
- criar decoder inicial, se necessário;
- criar regra de baixa severidade para o heartbeat;
- localizar o evento no Dashboard;
- registrar timestamps para avaliar atraso e duplicidade.

### Entregável

Primeiro evento real do Android visível e pesquisável no Wazuh.

### Critério de conclusão

- [ ] Um único heartbeat percorre o fluxo completo.
- [ ] Campos principais ficam pesquisáveis.
- [ ] O evento não expõe o token.
- [ ] A evidência é registrada no relatório da etapa.

---

## Etapa 6 — Descoberta de dispositivos

### Objetivo

Identificar dispositivos na rede local sem depender de resposta a `ping`.

### Métodos

- tabela de vizinhos com `ip neigh`;
- descoberta ARP ativa, quando suportada;
- observação passiva de ARP;
- anúncios mDNS;
- anúncios SSDP;
- varredura TCP limitada como complemento autorizado;
- identificação de fabricante por prefixo OUI do MAC.

O ICMP poderá ser usado como informação complementar, mas nunca como único
critério para considerar um dispositivo ativo ou inativo.

### Implementação em duas partes

#### Referência na VM

- validar `arp-scan` na rede local;
- comparar o resultado com `ip neigh`;
- estudar dispositivos que não respondem a ICMP;
- observar ARP, mDNS e SSDP com `tcpdump` ou Wireshark;
- criar o primeiro inventário de IP e MAC.

#### Sensor Android

- testar os métodos disponíveis sem root;
- registrar permissões e limitações;
- implementar o método mais confiável suportado pelo aparelho;
- produzir eventos com `first_seen` e `last_seen`;
- usar a VM como fallback documentado caso uma função não seja possível no
  Android sem root.

### Evento de observação

```json
{
  "event_type": "device_observed",
  "sensor_id": "android-sensor-01",
  "network_id": "home-lab",
  "observed_at": "2026-07-23T12:10:00Z",
  "device": {
    "ip": "192.168.1.25",
    "mac": "AA:BB:CC:DD:EE:FF",
    "vendor": "Example Vendor"
  },
  "discovery_method": "arp"
}
```

### Entregável

Inventário inicial e coletor capaz de emitir observações estruturadas.

### Critério de conclusão

- [ ] Dispositivos são encontrados mesmo quando não respondem a ping.
- [ ] Cada registro informa o método de descoberta.
- [ ] IP, MAC, fabricante, primeira e última observação são armazenados.
- [ ] Limites de visibilidade da rede foram demonstrados e documentados.

---

## Etapa 7 — Baseline e detecção de mudanças

### Objetivo

Transformar observações em eventos de segurança relevantes.

### Atividades

- criar uma baseline de dispositivos conhecidos;
- permitir nome amigável, proprietário, categoria e criticidade;
- gerar evento quando surgir um MAC desconhecido;
- registrar mudança de IP de um MAC conhecido;
- identificar possível troca de MAC associada a um IP importante;
- registrar retorno de dispositivo ausente;
- definir janela de ausência antes de declarar saída;
- reduzir alertas repetidos com cooldown e deduplicação;
- registrar o motivo de cada decisão.

### Eventos previstos

- `new_device`;
- `known_device_seen`;
- `device_ip_changed`;
- `device_missing`;
- `device_returned`;
- `ip_mac_conflict`;
- `scan_summary`.

### Entregável

Baseline versionável e motor de detecção de mudanças com testes.

### Critério de conclusão

- [ ] Dispositivo conhecido não gera alerta repetitivo.
- [ ] MAC desconhecido gera um único alerta útil.
- [ ] Mudança de IP é registrada sem alterar a identidade baseada em MAC.
- [ ] Ausências breves não causam excesso de falsos positivos.

---

## Etapa 8 — Perfis de múltiplas redes

### Objetivo

Permitir que o sensor seja utilizado em mais de uma rede própria ou autorizada
sem misturar dispositivos e baselines.

### Atividades

- criar um identificador não sensível para cada rede;
- manter baseline independente por `network_id`;
- impedir descoberta ativa em rede não autorizada;
- criar modo de cadastro e confirmação de nova rede;
- registrar localmente apenas os dados necessários;
- testar troca entre rede doméstica e rede de laboratório;
- documentar o consentimento ao utilizar a rede de outra pessoa.

### Entregável

Perfis separados para múltiplas redes autorizadas.

### Critério de conclusão

- [ ] Baselines de redes diferentes não se misturam.
- [ ] Rede desconhecida não é escaneada automaticamente.
- [ ] O usuário consegue identificar em qual perfil cada evento foi coletado.

---

## Etapa 9 — Coleta offline e sincronização

### Objetivo

Evitar perda de eventos quando a VM ou a rede estiver indisponível.

### Atividades

- criar fila local no Android;
- adicionar identificador único a cada evento;
- aplicar tentativas com backoff;
- reenviar quando a API voltar;
- confirmar recebimento antes de remover da fila;
- impedir duplicação no servidor;
- definir retenção e limite de armazenamento;
- proteger tokens e arquivos locais;
- testar desconexão, reconexão e reinicialização do celular.

### Entregável

Coleta resiliente com sincronização posterior e deduplicação.

### Critério de conclusão

- [ ] Eventos offline são preservados.
- [ ] Eventos sincronizados não são duplicados.
- [ ] A fila possui limite e política de retenção.

---

## Etapa 10 — Regras e dashboard no Wazuh

### Objetivo

Apresentar os eventos como informações úteis para uma rotina de SOC.

### Atividades

- criar decoders para os eventos personalizados;
- criar regras com níveis adequados;
- mapear alertas relevantes ao MITRE ATT&CK;
- criar visualizações de dispositivos conhecidos e desconhecidos;
- exibir novos dispositivos por período e por rede;
- exibir mudanças de IP e conflitos IP/MAC;
- acompanhar saúde e último contato do sensor;
- criar busca salva para investigação;
- documentar como ajustar falsos positivos.

### Alertas mínimos

- novo dispositivo desconhecido;
- conflito ou alteração inesperada de IP/MAC;
- sensor sem enviar heartbeat;
- volume anormal de descobertas;
- falha persistente de autenticação na API.

### Entregável

Dashboard funcional e conjunto versionado de regras e decoders.

### Critério de conclusão

- [ ] Alertas são compreensíveis e acionáveis.
- [ ] Dados podem ser filtrados por sensor, rede e dispositivo.
- [ ] Regras possuem descrição, severidade e justificativa.
- [ ] Falsos positivos conhecidos estão documentados.

---

## Etapa 11 — Testes, investigação e PCAP

### Objetivo

Validar a solução com cenários reproduzíveis e produzir evidências técnicas.

### Parte A — Testes defensivos na rede atual

- adicionar um dispositivo autorizado não cadastrado;
- desligar e religar um dispositivo conhecido;
- provocar mudança legítima de IP;
- interromper temporariamente a API;
- testar token inválido;
- analisar ARP, mDNS e SSDP observáveis;
- gerar e examinar uma captura PCAP autorizada.

### Parte B — Rede isolada para monitoramento completo

Criar uma rede separada contendo, no mínimo:

- um gateway virtual ou roteador próprio;
- uma máquina cliente;
- uma máquina de emulação;
- um sensor ou interface de captura;
- Wazuh e, quando apropriado, Suricata ou Zeek.

O tráfego deverá passar deliberadamente pelo gateway/sensor ou ser copiado por
port mirroring. Assim será possível comparar a visibilidade limitada da rede
doméstica com a visibilidade de um sensor corretamente posicionado.

### Parte C — Laboratório defensivo de ARP spoofing

O teste será executado exclusivamente na rede isolada e com máquinas próprias.
Seu propósito será validar detecção, investigação e mitigação de ARP Cache
Poisoning, associado à técnica MITRE ATT&CK T1557.002.

Sequência:

1. registrar a associação legítima entre IP e MAC do gateway;
2. iniciar captura de tráfego e coleta de eventos;
3. executar a emulação autorizada entre as máquinas do laboratório;
4. observar respostas ARP inesperadas ou mudanças na associação IP/MAC;
5. gerar evento `arp_anomaly`;
6. confirmar o alerta no Wazuh;
7. investigar a linha do tempo e o PCAP;
8. interromper a emulação;
9. restaurar e validar a associação legítima;
10. documentar medidas de mitigação.

Não usar esse teste na rede doméstica em produção, em Wi-Fi público ou em rede
de terceiros. Ele pode interromper conexões e expor tráfego de outros
dispositivos.

### Entregável

Relatório de investigação contendo cenário, evidências, evento, regra, alerta,
linha do tempo, conclusão, falsos positivos e mitigação.

### Critério de conclusão

- [ ] Casos normais e anômalos foram testados.
- [ ] Existe pelo menos um PCAP autorizado analisado.
- [ ] A diferença de visibilidade entre as duas redes foi demonstrada.
- [ ] Uma anomalia ARP foi detectada e investigada.
- [ ] O ambiente retornou ao estado normal após os testes.

---

## Etapa 12 — Segurança, documentação e portfólio

### Objetivo

Consolidar o projeto como material técnico reproduzível e seguro para
apresentação profissional.

### Atividades

- revisar autenticação, firewall, permissões e armazenamento de segredos;
- revisar retenção e minimização dos dados coletados;
- adicionar testes automatizados relevantes;
- criar scripts de instalação e configuração;
- documentar recuperação por snapshots e backup;
- criar diagrama final da arquitetura;
- criar guia de reprodução do laboratório;
- produzir demonstração ou capturas sem dados sensíveis;
- limpar histórico e arquivos antes da publicação;
- criar relatório executivo e relatório técnico;
- relacionar aprendizados a SOC, Blue Team, Wazuh e MITRE ATT&CK.

### Entregável

Repositório público seguro, documentação completa e demonstração do projeto.

### Critério de conclusão

- [ ] Outra pessoa consegue reproduzir o laboratório com a documentação.
- [ ] Nenhum segredo ou identificador sensível foi publicado.
- [ ] Arquitetura, limitações e decisões estão explicadas.
- [ ] Alertas e investigações possuem evidências anonimizadas.
- [ ] O projeto demonstra habilidades aplicáveis a SOC e Blue Team.

---

## 5. Critérios de sucesso do projeto

O projeto será considerado bem-sucedido quando conseguir:

- identificar dispositivos sem depender de resposta ICMP;
- diferenciar dispositivos conhecidos e desconhecidos;
- registrar entrada, saída e mudança de IP sem excesso de alertas;
- transportar eventos do Android até o Wazuh;
- operar com baselines independentes em redes autorizadas;
- preservar eventos durante indisponibilidade temporária;
- explicar e demonstrar os limites de visibilidade em uma rede comutada;
- analisar tráfego em uma rede na qual o sensor esteja bem posicionado;
- detectar pelo menos uma anomalia de ARP em laboratório isolado;
- apresentar evidência, regra, alerta, investigação e mitigação;
- manter documentação segura e reproduzível.

## 6. Próxima ação

As Etapas 1 e 2 estão concluídas e possuem relatórios próprios. A próxima ação
é iniciar a Etapa 3 — API coletora de eventos:

- definir o schema inicial dos eventos;
- implementar os endpoints de saúde e ingestão em FastAPI;
- proteger a ingestão com token;
- registrar eventos válidos em NDJSON;
- executar a API com `systemd`;
- restringir o acesso à rede local autorizada.
