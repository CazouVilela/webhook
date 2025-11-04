# Webhook Email Notification Server

Servidor webhook Flask profissional que recebe notificações via HTTP e envia emails formatados através do Gmail SMTP. Desenvolvido especialmente para integração com Airbyte, mas funciona com qualquer sistema que precise enviar notificações por email via webhook.

## Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Endpoints Disponíveis](#endpoints-disponíveis)
- [Integração com Airbyte](#integração-com-airbyte)
- [Scripts Utilitários](#scripts-utilitários)
- [Exemplos de Uso](#exemplos-de-uso)
- [Troubleshooting](#troubleshooting)
- [Segurança](#segurança)

---

## Características

- **Servidor Flask robusto** rodando na porta 7000 (padrão)
- **Envio de emails HTML formatados** com design responsivo e cores dinâmicas
- **Autenticação flexível** por token (header ou query parameter)
- **Compatibilidade total com Airbyte** através de endpoints dedicados
- **Extração automática de emails** do payload JSON
- **Validação de formato de email**
- **Logging detalhado** de todas as requisições
- **Múltiplos destinatários** por notificação
- **Ações customizáveis** com emojis e cores específicas
- **Endpoint de teste** para validar configuração SMTP
- **Scripts de diagnóstico** e geração de URLs
- **Tratamento de erros** robusto e mensagens claras

---

## Requisitos

### Sistema Operacional
- Linux (testado em Fedora)
- Python 3.8+

### Dependências Python
```bash
flask
flask-mail
python-dotenv
```

### Requisitos de Rede
- Porta 7000 liberada (ou configurar outra porta)
- Acesso SMTP ao Gmail (porta 587)

---

## Instalação

### 1. Instalar dependências Python

```bash
pip3 install flask flask-mail python-dotenv
```

### 2. Clonar ou baixar os arquivos do projeto

```bash
cd ~/projetos/webhook
```

### 3. Configurar permissões dos scripts

```bash
chmod +x *.sh
chmod +x webhook_server.py
```

---

## Configuração

### 1. Configurar arquivo .env

Edite o arquivo `.env` com suas credenciais:

```bash
# Configurações de Email - Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Credenciais do Gmail com Senha de App
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app

# Email remetente
MAIL_DEFAULT_SENDER=seu_email@gmail.com

# Email padrão para notificações
DEFAULT_RECIPIENT_EMAIL=destinatario@gmail.com

# Token secreto para segurança (mude para algo único!)
WEBHOOK_SECRET=seu_token_secreto_aqui
```

### 2. Gerar Senha de App do Gmail

1. Acesse: https://myaccount.google.com/security
2. Ative a "Verificação em duas etapas"
3. Vá em "Senhas de app"
4. Crie uma senha para "Outro (nome personalizado)"
5. Use a senha gerada (16 caracteres) no arquivo `.env`

### 3. Configurar Firewall (se necessário)

```bash
# Fedora/RHEL/CentOS
sudo firewall-cmd --permanent --add-port=7000/tcp
sudo firewall-cmd --reload

# Ubuntu/Debian (UFW)
sudo ufw allow 7000/tcp
```

---

## Uso

### Iniciar o servidor

```bash
cd ~/projetos/webhook
python3 webhook_server.py
```

O servidor irá:
- Validar configurações essenciais
- Mostrar configuração atual
- Iniciar na porta 7000
- Escutar em todas as interfaces (0.0.0.0)

### Executar em background

```bash
nohup python3 webhook_server.py > webhook.log 2>&1 &
```

### Verificar se está rodando

```bash
curl http://localhost:7000/
```

### Ver logs em tempo real

```bash
tail -f webhook.log
```

### Parar o servidor

```bash
pkill -f webhook_server.py
```

---

## Endpoints Disponíveis

### 1. GET / - Status do servidor
Verifica se o servidor está online e lista todos os endpoints disponíveis.

```bash
curl http://localhost:7000/
```

**Resposta:**
```json
{
  "status": "online",
  "message": "Webhook server está rodando",
  "timestamp": "2025-10-30T23:17:00",
  "endpoints": {
    "/": "Status do servidor",
    "/webhook": "Endpoint principal (POST)",
    "/webhook/<action>": "Webhook com ação específica (POST)",
    "/test-email": "Testar envio de email (GET)",
    "/help": "Documentação de uso (GET)"
  }
}
```

### 2. GET /help - Documentação da API
Retorna documentação completa de uso dos endpoints.

```bash
curl http://localhost:7000/help
```

### 3. POST /webhook - Endpoint principal
Recebe webhook genérico e envia email.

**Autenticação:**
- Header: `X-Webhook-Secret: seu_token`
- OU Query: `?token=seu_token`

**Exemplo:**
```bash
curl -X POST http://localhost:7000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: seu_token" \
  -d '{
    "email": "destino@example.com",
    "evento": "novo_pedido",
    "dados": {
      "pedido_id": "12345",
      "valor": 250.00
    }
  }'
```

### 4. POST /webhook/<action> - Webhook com ação
Recebe webhook com ação específica (adiciona emoji e cor ao email).

**Ações suportadas:**
- `failed` - 🔴 FALHA (#FF4444)
- `success` - ✅ SUCESSO (#44BB44)
- `update` - 🔄 ATUALIZAÇÃO (#4444FF)
- `warning` - ⚠️ AVISO (#FFA500)
- `login` - 👤 LOGIN
- `pedido` - 🛒 PEDIDO
- `alerta` - 🚨 ALERTA
- `erro` - ❌ ERRO

**Exemplo:**
```bash
curl -X POST "http://localhost:7000/webhook/pedido?token=seu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "loja@example.com",
    "pedido_id": "PED-001",
    "cliente": "João Silva",
    "valor": 350.00
  }'
```

### 5. POST /airbyte/<event_type> - Endpoints Airbyte
Endpoints específicos para integração com Airbyte.

**Event types:**
- `/airbyte/failed` - Sincronizações falhas
- `/airbyte/success` - Sincronizações bem-sucedidas
- `/airbyte/update` - Atualizações de conexão
- `/airbyte/action-required` - Ações necessárias
- `/airbyte/warning` - Avisos de falhas repetidas
- `/airbyte/disabled` - Sincronização desabilitada

**Exemplo:**
```bash
curl -X POST "http://localhost:7000/airbyte/failed?token=seu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "name": "PostgreSQL → BigQuery",
      "source": {"name": "PostgreSQL"},
      "destination": {"name": "BigQuery"}
    },
    "error": "Connection timeout",
    "timestamp": "2025-10-30T23:17:00"
  }'
```

### 6. GET /test-email - Testar envio de email
Testa configuração SMTP enviando um email de teste.

```bash
# Email padrão
curl http://localhost:7000/test-email

# Email específico
curl "http://localhost:7000/test-email?email=teste@example.com"
```

---

## Integração com Airbyte

### Configuração Automática

Use o script de geração de URLs:

```bash
./generate_airbyte_urls.sh
```

Este script irá:
1. Ler o token do arquivo `.env`
2. Detectar IPs disponíveis (localhost e IP local)
3. Gerar URLs formatadas para todos os tipos de eventos
4. Permitir salvar em arquivo
5. Testar endpoints (opcional)

### Configuração Manual no Airbyte

1. Acesse Airbyte: **Settings → Notifications**
2. Configure os webhooks:

**Failed Syncs:**
```
http://SEU_IP:7000/airbyte/failed?token=seu_token
```

**Successful Syncs:**
```
http://SEU_IP:7000/airbyte/success?token=seu_token
```

**Connection Updates:**
```
http://SEU_IP:7000/airbyte/update?token=seu_token
```

3. Clique em **Test** para cada URL
4. Salve com **Save changes**

### Airbyte em Docker

Se o Airbyte está rodando em Docker, use o IP da máquina host ao invés de `localhost`:

```bash
# Descobrir IP local
hostname -I | awk '{print $1}'

# Exemplo: http://192.168.1.100:7000/airbyte/failed?token=seu_token
```

---

## Scripts Utilitários

### 1. test_webhook.sh - Testador Interativo
Menu interativo completo para testar todos os recursos do webhook.

```bash
./test_webhook.sh
```

**Opções disponíveis:**
1. Teste básico (email padrão)
2. Teste com email específico
3. Teste com múltiplos emails
4. Teste com ação personalizada
5. Teste de payload complexo
6. Teste de envio direto de email
7. Executar todos os testes
8. Teste personalizado (JSON customizado)
9. Ver documentação da API

### 2. diagnostic_airbyte.sh - Diagnóstico Completo
Verifica todos os aspectos da configuração e identifica problemas.

```bash
./diagnostic_airbyte.sh
```

**O que verifica:**
1. Se o webhook está rodando
2. Conectividade local (localhost:7000)
3. Portas abertas
4. Configuração do firewall
5. IPs disponíveis (útil para Docker)
6. Token de segurança
7. Endpoints do Airbyte
8. Gera URLs recomendadas
9. Verifica logs recentes
10. Teste completo de ponta a ponta

### 3. fix_airbyte_endpoints.sh - Instalador de Endpoints
Adiciona/atualiza endpoints do Airbyte no webhook_server.py.

```bash
./fix_airbyte_endpoints.sh
```

**O que faz:**
1. Backup do webhook_server.py
2. Cria arquivo airbyte_endpoints.py
3. Adiciona endpoints ao servidor
4. Verifica sintaxe Python
5. Reinicia o servidor
6. Testa novos endpoints
7. Gera URLs prontas para uso

### 4. generate_airbyte_urls.sh - Gerador de URLs
Gera URLs formatadas prontas para configurar no Airbyte.

```bash
./generate_airbyte_urls.sh
```

**Recursos:**
- Lê token automaticamente do .env
- Mostra URLs para localhost e IP local
- Permite salvar em arquivo
- Testa endpoints (opcional)
- Mostra emoji e assunto de email para cada tipo

---

## Exemplos de Uso

### Exemplo 1: Notificação Simples

```bash
curl -X POST "http://localhost:7000/webhook?token=seu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "backup_concluido",
    "servidor": "prod-db-01",
    "tamanho": "2.5 GB"
  }'
```

**Email recebido:**
- Assunto: `📢 [Webhook] Notificação - 30/10/2025 23:17:00`
- Destinatário: Email padrão configurado no .env
- Conteúdo: JSON formatado com todas as informações

### Exemplo 2: Múltiplos Destinatários

```bash
curl -X POST "http://localhost:7000/webhook/alerta?token=seu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["admin@example.com", "suporte@example.com"],
    "severidade": "alta",
    "mensagem": "Disco quase cheio no servidor prod-web-01",
    "uso_atual": "95%"
  }'
```

**Email recebido:**
- Assunto: `🚨 [ALERTA] Webhook - 30/10/2025 23:17:00`
- Destinatários: admin@example.com, suporte@example.com
- Cor do header: #FF6B6B (vermelho)

### Exemplo 3: Pedido de E-commerce

```bash
curl -X POST "http://localhost:7000/webhook/pedido?token=seu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendas@loja.com",
    "pedido": {
      "id": "PED-98765",
      "cliente": "Maria Silva",
      "valor_total": 1250.00,
      "itens": 5,
      "pagamento": "Cartão de Crédito"
    }
  }'
```

**Email recebido:**
- Assunto: `🛒 [PEDIDO] Webhook - 30/10/2025 23:17:00`
- Destinatário: vendas@loja.com
- Cor do header: #667eea (roxo padrão)

### Exemplo 4: Python Integration

```python
import requests
import json

webhook_url = "http://localhost:7000/webhook/login"
token = "seu_token_secreto"

data = {
    "email": "seguranca@empresa.com",
    "usuario": "joao.silva",
    "ip": "203.0.113.45",
    "localizacao": "São Paulo, BR",
    "dispositivo": "Chrome on Linux"
}

headers = {
    "Content-Type": "application/json",
    "X-Webhook-Secret": token
}

response = requests.post(webhook_url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### Exemplo 5: JavaScript/Node.js Integration

```javascript
const axios = require('axios');

const webhookUrl = 'http://localhost:7000/webhook/erro';
const token = 'seu_token_secreto';

const data = {
  email: 'devops@empresa.com',
  servico: 'api-gateway',
  erro: 'Database connection timeout',
  stack_trace: 'Error at ...',
  timestamp: new Date().toISOString()
};

axios.post(`${webhookUrl}?token=${token}`, data, {
  headers: { 'Content-Type': 'application/json' }
})
.then(response => {
  console.log('Webhook enviado:', response.data);
})
.catch(error => {
  console.error('Erro ao enviar webhook:', error);
});
```

---

## Troubleshooting

### Problema: Servidor não inicia

**Sintomas:**
- Erro ao executar `python3 webhook_server.py`
- Mensagem: "MAIL_USERNAME e MAIL_PASSWORD devem ser configurados!"

**Solução:**
1. Verifique o arquivo `.env`
2. Certifique-se de que MAIL_USERNAME e MAIL_PASSWORD estão configurados
3. Use senha de app do Gmail (não a senha normal)

### Problema: Airbyte não consegue conectar

**Sintomas:**
- Airbyte mostra "Connection refused" ou "Timeout"
- Teste do webhook falha no Airbyte

**Solução:**
1. Execute o diagnóstico:
   ```bash
   ./diagnostic_airbyte.sh
   ```

2. Se Airbyte está em Docker, use IP da máquina:
   ```bash
   # Descubra o IP
   hostname -I | awk '{print $1}'

   # Use: http://192.168.X.X:7000/airbyte/failed?token=TOKEN
   ```

3. Verifique firewall:
   ```bash
   sudo firewall-cmd --list-ports
   sudo firewall-cmd --permanent --add-port=7000/tcp
   sudo firewall-cmd --reload
   ```

### Problema: Email não é enviado

**Sintomas:**
- Webhook retorna sucesso mas email não chega
- Erro "Authentication failed" nos logs

**Solução:**
1. Verifique senha de app do Gmail:
   - Acesse: https://myaccount.google.com/apppasswords
   - Gere nova senha de app
   - Atualize no `.env`

2. Verifique se 2FA está ativo na conta Google

3. Teste o envio direto:
   ```bash
   curl http://localhost:7000/test-email
   ```

4. Verifique logs:
   ```bash
   tail -50 webhook.log
   ```

### Problema: Token inválido

**Sintomas:**
- Resposta HTTP 401 "Não autorizado"
- Log mostra "Token inválido ou ausente"

**Solução:**
1. Verifique o token no `.env`:
   ```bash
   grep WEBHOOK_SECRET ~/.env
   ```

2. Use o token correto na URL ou header:
   ```bash
   # Query parameter
   curl "http://localhost:7000/webhook?token=TOKEN_CORRETO"

   # Header
   curl -H "X-Webhook-Secret: TOKEN_CORRETO" http://localhost:7000/webhook
   ```

### Problema: Porta já em uso

**Sintomas:**
- Erro: "Address already in use"
- Não consegue iniciar na porta 7000

**Solução:**
1. Encontre o processo usando a porta:
   ```bash
   sudo lsof -i :7000
   ```

2. Mate o processo:
   ```bash
   kill -9 PID
   ```

3. Ou use outra porta editando `webhook_server.py`:
   ```python
   app.run(host='0.0.0.0', port=8000, debug=False)
   ```

---

## Segurança

### Boas Práticas

1. **Token forte e único**
   ```bash
   # Gerar token aleatório
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Não compartilhe o arquivo .env**
   - Adicione ao `.gitignore`
   - Use variáveis de ambiente em produção

3. **HTTPS em produção**
   - Use proxy reverso (nginx/Apache)
   - Configure certificado SSL/TLS

4. **Firewall configurado**
   - Limite acesso por IP se possível
   - Abra apenas porta necessária

5. **Logs monitorados**
   - Verifique logs regularmente
   - Alerta em tentativas de acesso não autorizado

### Exemplo de Configuração Nginx (Produção)

```nginx
server {
    listen 443 ssl;
    server_name webhook.exemplo.com;

    ssl_certificate /etc/letsencrypt/live/webhook.exemplo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webhook.exemplo.com/privkey.pem;

    location / {
        proxy_pass http://localhost:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Estrutura de Arquivos

```
webhook/
├── webhook_server.py           # Servidor principal
├── airbyte_endpoints.py        # Endpoints Airbyte (separado)
├── .env                        # Configurações (NÃO versionar!)
├── webhook.log                 # Logs do servidor
│
├── Scripts utilitários:
├── test_webhook.sh            # Testador interativo
├── diagnostic_airbyte.sh      # Diagnóstico completo
├── fix_airbyte_endpoints.sh   # Instalador de endpoints
├── generate_airbyte_urls.sh   # Gerador de URLs
│
├── Backups:
├── webhook_server_OLD.py      # Backup antigo
├── webhook_server.py.backup   # Backups automáticos
│
└── README.md                  # Esta documentação
```

---

## Contribuindo

Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Adicionar novos endpoints
- Melhorar a documentação

---

## Licença

Projeto pessoal desenvolvido por cazouvilela@gmail.com

---

## Changelog

### v1.0.0 (2025-10-30)
- Servidor webhook Flask funcional
- Integração completa com Airbyte
- Scripts utilitários para diagnóstico e testes
- Emails HTML formatados com cores dinâmicas
- Autenticação por token (header ou URL)
- Suporte a múltiplos destinatários
- Documentação completa

---

## Contato

**Email:** cazouvilela@gmail.com
**Projeto:** ~/projetos/webhook
