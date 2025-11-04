# WEBHOOK - Memória do Projeto

<!-- CHAPTER: 0 Configurações da IDE -->

## 🔧 Configurações da IDE

> **⚠️ LEITURA OBRIGATÓRIA**: Este projeto utiliza a IDE Customizada.
>
> **Documentação essencial** (leia sempre ao carregar o projeto):
> - [RELACIONAMENTO_COM_IDE.md](.claude/RELACIONAMENTO_COM_IDE.md) - **Como este projeto se relaciona com a IDE**
> - [TEMPLATE_PROJETO.md](.claude/TEMPLATE_PROJETO.md) - Template de organização de projetos
> - [GUIA_SISTEMA_PROJETOS.md](.claude/GUIA_SISTEMA_PROJETOS.md) - Sistema de gerenciamento de projetos

### Comandos Slash Disponíveis

- `/iniciar` - Gerenciar projetos (listar, ativar, criar novo)
- `/subir` - Git commit + push automatizado
- `/subir_estavel` - Git commit + push + tag de versão estável
- `/tryGPT "prompt"` - Consultar ChatGPT manualmente
- `/implantacao_automatica` - Deploy com comparação Claude vs ChatGPT

### Funcionalidades da IDE

Este projeto utiliza:
- **Terminal virtual** integrado (xterm.js)
- **Explorador de arquivos** lateral com tree view
- **Sistema de planejamento** hierárquico (interface web)
- **Draft/Rascunho** automático por projeto
- **Memórias persistentes** com capítulos
- **Visualização de commits** git com tags
- **Integração ChatGPT** via Playwright


<!-- CHAPTER: 1 Descrição Breve -->

## Descrição Breve

Servidor webhook Flask profissional que recebe notificações HTTP e envia emails HTML formatados através do Gmail SMTP. Desenvolvido inicialmente para integração com Airbyte, mas funciona com qualquer sistema que necessite enviar notificações por email via webhook.

<!-- CHAPTER: 2 Informações Principais -->

## Informações Principais

**Versão Atual**: v1.0.0

**Stack Tecnológica**:
- Python 3.8+
- Flask 2.x (servidor web WSGI)
- Flask-Mail (integração SMTP)
- python-dotenv (gerenciamento de variáveis de ambiente)

**Status**: ✅ Em produção

**Porta Padrão**: 7000 (configurável)

**Autor**: cazouvilela@gmail.com

---

<!-- CHAPTER: 3 Arquitetura do Sistema -->

## Arquitetura do Sistema

### Servidor Principal: webhook_server.py

**Estrutura de código:**
1. **Importações e Configuração Inicial** (linhas 1-26)
   - Carregamento de dependências
   - Configuração de logging
   - Inicialização do Flask

2. **Configuração SMTP** (linhas 30-46)
   - Configuração dinâmica via variáveis de ambiente
   - Suporte a TLS/SSL
   - Validação de credenciais na inicialização

3. **Funções Auxiliares** (linhas 55-118)
   - `verify_token()`: Autenticação flexível (header ou URL)
   - `validate_email()`: Validação regex de emails
   - `extract_emails_from_data()`: Extração inteligente de emails do payload

4. **Endpoints HTTP** (linhas 120-503)
   - `/` - Status e lista de endpoints
   - `/help` - Documentação da API
   - `/webhook` - Endpoint genérico
   - `/webhook/<action>` - Endpoint com ações customizadas
   - `/airbyte/<event_type>` - Endpoints específicos do Airbyte
   - `/test-email` - Teste de configuração SMTP

5. **Função de Envio de Email** (linhas 286-426)
   - `send_notification_email()`: Geração de HTML formatado
   - Templates dinâmicos com cores baseadas em ação
   - Remoção de campos sensíveis do payload
   - Suporte a versão texto simples (fallback)

6. **Inicialização** (linhas 504-528)
   - Validação de configurações essenciais
   - Exibição de configuração atual
   - Inicialização do servidor em 0.0.0.0:7000

### Arquivo Auxiliar: airbyte_endpoints.py

Contém a definição dos endpoints específicos do Airbyte que são inseridos dinamicamente no webhook_server.py pelo script `fix_airbyte_endpoints.sh`.

**Funcionalidades:**
- Endpoint universal `/airbyte/<event_type>` (GET e POST)
- Suporte a 6 tipos de eventos: failed, success, update, action-required, warning, disabled
- Extração automática de nome da conexão do payload
- Templates de email específicos para Airbyte

---

<!-- CHAPTER: 4 Principais Funcionalidades -->

## Principais Funcionalidades

### 1. Autenticação Flexível
**Implementação:** função `verify_token()` (linhas 55-79)

Suporta três modos:
- **Header-based**: `X-Webhook-Secret: token`
- **URL-based**: `?token=token` (compatibilidade Airbyte)
- **Localhost sem token**: Acesso local permitido sem autenticação

### 2. Extração Inteligente de Emails
**Implementação:** função `extract_emails_from_data()` (linhas 86-118)

Procura por emails em múltiplos campos:
- `email`, `emails` (padrão)
- `destinatario`, `destinatarios` (português)
- `recipient`, `recipients`, `to` (inglês)
- `para`, `dest` (alternativas)

Suporta:
- String única: `"email": "user@example.com"`
- Lista: `"emails": ["user1@example.com", "user2@example.com"]`

### 3. Emails HTML Formatados
**Implementação:** função `send_notification_email()` (linhas 286-426)

**Características:**
- Design responsivo (max-width: 800px)
- Header com gradiente de cor dinâmica
- Emojis contextuais por tipo de ação
- Seção de informações gerais (timestamp, IP, ação)
- Dados recebidos em formato JSON pretty-print
- Headers HTTP colapsáveis (elemento `<details>`)
- Footer com informações do sistema
- Versão texto simples para clientes sem HTML

**Mapeamento de cores por ação:**
```python
color_map = {
    'failed': '#FF4444',        # Vermelho
    'success': '#44BB44',       # Verde
    'update': '#4444FF',        # Azul
    'warning': '#FFA500',       # Laranja
    'disabled': '#808080',      # Cinza
    'alerta': '#FF6B6B',        # Vermelho claro
    'erro': '#DC3545'           # Vermelho escuro
}
```

### 4. Logging Detalhado
**Configuração:** linhas 21-25

- Nível: INFO
- Formato: `timestamp - level - message`
- **Destino**: Systemd Journal (quando rodado via serviço systemd)
- **Comando para ver logs**: `journalctl -u webhook-email.service -n 50`
- Logs de todas as requisições recebidas
- Logs de autenticação (sucesso/falha)
- Logs de envio de email
- Logs de erros com stack trace

**IMPORTANTE:** O arquivo `webhook.log` está desatualizado. Os logs ativos estão no systemd journal!

### 5. Tratamento de Erros Robusto

Cada endpoint possui:
- Bloco `try/except` completo
- Logging de erros
- Respostas JSON estruturadas
- Códigos HTTP apropriados (200, 401, 500)

---

<!-- CHAPTER: 5 Estrutura de Dados -->

## Estrutura de Dados

### Payload de Webhook Genérico
```json
{
  "email": "destino@example.com",           // Opcional: destinatário
  "emails": ["dest1@...", "dest2@..."],     // Opcional: múltiplos
  "evento": "nome_do_evento",               // Livre
  "dados": {                                // Livre
    "campo1": "valor1",
    "campo2": "valor2"
  }
}
```

### Payload do Airbyte
```json
{
  "connection": {
    "name": "Nome da Conexão",
    "source": {"name": "Fonte"},
    "destination": {"name": "Destino"}
  },
  "error": "Mensagem de erro",              // Se falha
  "summary": {                               // Se sucesso
    "recordsSynced": 1000
  },
  "timestamp": "2025-10-30T23:17:00"
}
```

### Resposta de Sucesso
```json
{
  "status": "success",
  "message": "Webhook processado e email enviado para 1 destinatário(s)",
  "recipients": ["destino@example.com"]
}
```

### Resposta de Erro
```json
{
  "status": "error",
  "message": "Descrição do erro"
}
```

---

<!-- CHAPTER: 6 Scripts Utilitários -->

## Scripts Utilitários

### 1. test_webhook.sh (302 linhas)
**Propósito**: Menu interativo completo para testes

**Funcionalidades:**
- 9 opções de teste diferentes
- Verificação automática de servidor online
- Testes com cores no output (RED, GREEN, YELLOW, BLUE)
- Suporte a JSON personalizado
- Teste de múltiplos destinatários
- Teste de payload complexo (e-commerce)
- Consulta à documentação da API

**Funções principais:**
- `send_webhook()`: Envia requisição e exibe resposta formatada
- `check_server()`: Verifica se servidor está online
- `show_menu()`: Exibe menu interativo
- `run_test_X()`: Funções específicas para cada tipo de teste

### 2. diagnostic_airbyte.sh (245 linhas)
**Propósito**: Diagnóstico completo de problemas de conexão

**Verificações realizadas:**
1. Processo webhook rodando (pgrep)
2. Conectividade local (curl localhost:7000)
3. Portas abertas (netstat)
4. Configuração de firewall (firewall-cmd)
5. IPs disponíveis (hostname -I, docker inspect)
6. Token de segurança (.env)
7. Endpoints do Airbyte (testes HTTP)
8. Geração de URLs recomendadas
9. Logs recentes (tail webhook.log)
10. Teste de ponta a ponta com payload real

**Saída:** Relatório completo com erros encontrados e sugestões de correção

### 3. fix_airbyte_endpoints.sh (274 linhas)
**Propósito**: Adicionar/atualizar endpoints do Airbyte

**Processo:**
1. Backup automático com timestamp
2. Criação do airbyte_endpoints.py
3. Remoção de versão antiga (se existir)
4. Inserção no webhook_server.py
5. Validação de sintaxe Python (py_compile)
6. Reinício do servidor
7. Testes dos novos endpoints
8. Geração de URLs prontas para uso

**Segurança:** Rollback automático se detectar erro de sintaxe

### 4. generate_airbyte_urls.sh (187 linhas)
**Propósito**: Gerar URLs formatadas para Airbyte

**Funcionalidades:**
- Leitura automática do token do .env
- Detecção de IPs (localhost e rede local)
- Geração de URLs para 6 tipos de eventos
- Opção de salvar em arquivo (airbyte_urls.txt)
- Testes opcionais dos endpoints
- Interface interativa com cores

---

<!-- CHAPTER: 7 Configuração -->

## Configuração

### Arquivo .env (NÃO versionar!)
```bash
# SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Gmail Credentials (App Password required!)
MAIL_USERNAME=cazouvilela@gmail.com
MAIL_PASSWORD=vszd hslw tacb xvud    # App Password de 16 caracteres

# Email Settings
MAIL_DEFAULT_SENDER=cazouvilela@gmail.com
DEFAULT_RECIPIENT_EMAIL=cazouvilela@gmail.com

# Security
WEBHOOK_SECRET=webhook_pessoal_secret_token
```

**IMPORTANTE:**
- Usar senha de app do Gmail (não senha normal)
- 2FA deve estar ativo na conta Google
- Gerar em: https://myaccount.google.com/apppasswords

### Requisitos de Sistema
- Python 3.8+
- Porta 7000 disponível
- Acesso SMTP ao Gmail (porta 587)
- Firewall liberado (se necessário)

### Dependências Python
```bash
pip3 install flask flask-mail python-dotenv
```

---

<!-- CHAPTER: 8 Endpoints Disponíveis -->

## Endpoints Disponíveis

### 1. GET / - Status
**Retorna:** JSON com status e lista de endpoints

### 2. GET /help - Documentação
**Retorna:** JSON com exemplos de uso completos

### 3. POST /webhook - Genérico
**Auth:** Header ou query param
**Body:** JSON livre
**Response:** Status + recipients

### 4. POST /webhook/<action> - Com ação
**Actions disponíveis:**
- failed, success, update, warning, disabled
- login, pedido, alerta, erro, info

**Diferencial:** Emoji e cor específicos no email

### 5. POST /airbyte/<event_type> - Airbyte
**Event types:**
- failed, success, update
- action-required, warning, disabled

**Suporte:** GET (teste) e POST (webhook)

### 6. GET/POST /test-email - Teste SMTP
**Query param:** `?email=teste@example.com`
**Uso:** Validar configuração SMTP

---

<!-- CHAPTER: 9 Integração com Airbyte -->

## Integração com Airbyte

### Configuração no Airbyte
1. Settings → Notifications
2. Configurar webhook URLs com token
3. Testar cada endpoint
4. Salvar configurações

### URLs Necessárias
- Failed syncs: `/airbyte/failed?token=XXX`
- Successful syncs: `/airbyte/success?token=XXX`
- Connection updates: `/airbyte/update?token=XXX`
- Action required: `/airbyte/action-required?token=XXX`
- Warning: `/airbyte/warning?token=XXX`
- Disabled: `/airbyte/disabled?token=XXX`

### Docker Considerations
- Airbyte em Docker não consegue acessar `localhost` do host
- Usar IP da máquina: `hostname -I | awk '{print $1}'`
- Exemplo: `http://192.168.1.100:7000/airbyte/failed?token=XXX`

---

<!-- CHAPTER: 10 Segurança -->

## Segurança

### Proteções Implementadas
1. **Autenticação por token**
   - Verificação em cada requisição
   - Suporte a header ou URL
   - Exceção para localhost

2. **Validação de emails**
   - Regex pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
   - Previne injeção de headers SMTP

3. **Sanitização de dados**
   - Remoção de campos de email do payload antes de enviar
   - Previne vazamento de informações sensíveis

4. **Logging de segurança**
   - Log de tentativas de acesso não autorizado
   - Log de IPs de origem

### Boas Práticas Recomendadas
1. Token forte (32+ caracteres aleatórios)
2. Não compartilhar .env (adicionar ao .gitignore)
3. HTTPS em produção (proxy reverso)
4. Firewall restritivo
5. Monitoramento de logs

---

<!-- CHAPTER: 11 Estrutura de Arquivos -->

## Estrutura de Arquivos

```
webhook/
├── .claude/                           # Configuração Claude Code
│   ├── commands/ → symlink
│   ├── GUIA_SISTEMA_PROJETOS.md → symlink
│   ├── settings.local.json → symlink
│   └── memory.md                      # Este arquivo
│
├── webhook_server.py                  # ⭐ Servidor principal (529 linhas)
├── airbyte_endpoints.py               # Endpoints Airbyte (115 linhas)
├── .env                               # ⚠️ Configurações sensíveis
├── webhook.log                        # Logs do servidor
│
├── Scripts Shell:
├── test_webhook.sh                    # 🧪 Testador interativo (302 linhas)
├── diagnostic_airbyte.sh              # 🔍 Diagnóstico (245 linhas)
├── fix_airbyte_endpoints.sh           # 🔧 Instalador endpoints (274 linhas)
├── generate_airbyte_urls.sh           # 🔗 Gerador URLs (187 linhas)
│
├── Backups:
├── webhook_server_OLD.py
├── webhook_server.py.backup
├── webhook_server.py.backup.*
│
├── __pycache__/                       # Cache Python
│
└── README.md                          # 📖 Documentação completa
```

---

<!-- CHAPTER: 12 Troubleshooting Comum -->

## Troubleshooting Comum

### 1. Servidor não inicia
**Causa:** Variáveis de ambiente faltando
**Solução:** Verificar MAIL_USERNAME e MAIL_PASSWORD no .env

### 2. Airbyte não conecta
**Causa:** Docker não acessa localhost do host
**Solução:** Usar IP da máquina ao invés de localhost

### 3. Email não enviado
**Causa:** Senha de app incorreta ou 2FA desativado
**Solução:** Gerar nova senha de app no Google

### 4. Token inválido
**Causa:** Token no .env diferente do usado na URL
**Solução:** Verificar WEBHOOK_SECRET no .env

### 5. Porta em uso
**Causa:** Processo anterior não foi encerrado
**Solução:** `pkill -f webhook_server.py`

---

<!-- CHAPTER: 13 Performance e Escalabilidade -->

## Performance e Escalabilidade

### Configuração Atual
- **Servidor:** Flask development server
- **Threading:** Não configurado
- **Max concurrent:** ~10-20 requisições
- **Latência média:** 1-3 segundos (envio SMTP)

### Melhorias Futuras Possíveis
1. **Servidor WSGI de produção:** Gunicorn ou uWSGI
2. **Fila de emails:** Celery + Redis/RabbitMQ
3. **Cache de templates:** Jinja2 templates compilados
4. **Rate limiting:** Flask-Limiter
5. **Monitoramento:** Prometheus + Grafana
6. **Load balancing:** Nginx upstream

---

<!-- CHAPTER: 14 Padrões de Código -->

## Padrões de Código

### Convenções Python
- PEP 8 compliance
- Docstrings em funções principais
- Type hints não utilizados (pode ser adicionado)
- Logging estruturado

### Organização
- Configuração no topo
- Funções auxiliares no meio
- Endpoints HTTP agrupados
- Inicialização no final (`if __name__ == '__main__'`)

---

<!-- CHAPTER: 15 Changelog Detalhado -->

## Changelog Detalhado

### v1.0.0 (2025-10-30)
**Adicionado:**
- Servidor webhook Flask completo
- Integração com Gmail SMTP
- Endpoints genéricos e específicos do Airbyte
- Autenticação por token flexível
- Emails HTML formatados com cores dinâmicas
- 4 scripts utilitários bash
- Validação de email
- Extração automática de destinatários
- Logging detalhado
- Documentação completa (README.md)
- Estrutura .claude para gerenciamento

**Configuração:**
- Porta padrão: 7000
- SMTP: Gmail (porta 587, TLS)
- Logs: webhook.log

---

<!-- CHAPTER: 16 Conhecimento Técnico Importante -->

## Conhecimento Técnico Importante

### 1. Flask-Mail Configuration
O Flask-Mail usa a biblioteca `smtplib` do Python internamente. As configurações:
- `MAIL_USE_TLS=true`: Inicia conexão não criptografada e faz upgrade para TLS
- `MAIL_PORT=587`: Porta padrão para STARTTLS
- `MAIL_USE_SSL=true`: Usaria porta 465 (conexão SSL desde o início)

### 2. Token Verification Logic
```python
token = token_header or token_url  # Precedência: header primeiro
is_local = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
```
Localhost tem acesso sem token para facilitar testes locais.

### 3. Email HTML Generation
Usa f-strings Python para gerar HTML inline (não templates externos).
Benefício: Sem dependências adicionais.
Desvantagem: Difícil manutenção de HTML complexo.

### 4. Airbyte Integration Pattern
Airbyte envia webhooks no formato:
```json
{
  "workspace": {...},
  "connection": {...},
  "error": "...",  // se falha
  "summary": {...} // se sucesso
}
```

O servidor extrai `connection.name` para personalizar o assunto do email.

---

<!-- CHAPTER: 17 Manutenção e Evolução -->

## Manutenção e Evolução

### Próximos Passos Sugeridos
1. Adicionar banco de dados para histórico de webhooks
2. Interface web para visualizar webhooks recebidos
3. Suporte a outros provedores SMTP (SendGrid, SES)
4. Webhooks assíncronos (Celery)
5. API REST para consulta de status
6. Testes automatizados (pytest)
7. CI/CD pipeline
8. Containerização (Docker)

### Pontos de Atenção
- Senha de app do Gmail precisa ser renovada periodicamente
- ~~Logs crescem indefinidamente~~ ✅ Logs gerenciados pelo systemd journal (rotação automática)
- Sem rate limiting (vulnerável a spam)
- Servidor development do Flask (não usar em produção alta carga)

---

<!-- CHAPTER: 18 Última Atualização -->

## Última Atualização

**Data:** 2025-10-31 08:30
**Ação:** Correção completa de inconsistências de porta
**Mudanças:**
- ✅ Corrigidos todos os scripts shell (.sh) para usar porta 7000
- ✅ Documentado que logs vão para systemd journal (não arquivo .log)
- ✅ Verificado que webhook_server.py usa porta 7000
- ✅ Verificado que serviço systemd (webhook-email.service) está correto
- ✅ Todas as documentações (README.md, memory.md, AIRBYTE_URLS_CONFIGURACAO.md) verificadas

**Status:** Projeto 100% consistente com porta 7000 em todos os arquivos ativos

