# 🔗 URLs para Configuração do Airbyte

## Informações do Sistema

**IP Local**: `192.168.127.65`
**Porta**: `7000`
**Token**: `webhook_pessoal_secret_token`
**Versão**: `2.0 - Emails Detalhados`

---

## 📋 URLs Para Configurar no Airbyte

### 1. 🔴 Failed Syncs (Sincronizações com Falha)
**Prioridade**: ALTA

```
http://192.168.127.65:7000/airbyte/failed?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- ⚙️ Tipo de erro (config_error, transient_error, system_error)
- 📥/📤 Origem do erro (source ou destination)
- 📝 Mensagem de erro detalhada
- 🔧 Ação recomendada baseada no tipo de erro
- 📊 Métricas completas de sincronização
- ⚠️ Alerta de perda de dados (se aplicável)

---

### 2. ✅ Successful Syncs (Sincronizações Bem-Sucedidas)
**Prioridade**: NORMAL

```
http://192.168.127.65:7000/airbyte/success?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- 📝 Número de registros sincronizados
- 💾 Volume de dados transferidos
- ⏱️ Duração da sincronização
- 🔗 Links diretos para workspace, fonte e destino

---

### 3. 🔄 Connection Updates (Atualizações de Conexão)
**Prioridade**: MÉDIA

```
http://192.168.127.65:7000/airbyte/update?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- 📊 Detalhes da atualização
- 🔗 Informações da conexão atualizada
- 📅 Data e hora da modificação

---

### 4. ⚠️ Connection Updates Requiring Action (Ações Necessárias)
**Prioridade**: ALTA

```
http://192.168.127.65:7000/airbyte/action-required?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- ⚠️ Destaque visual de prioridade ALTA
- 📝 Descrição da ação necessária
- 🔗 Link direto para resolver o problema

---

### 5. ⚠️ Warning - Repeated Failures (Aviso de Falhas Repetidas)
**Prioridade**: ALTA

```
http://192.168.127.65:7000/airbyte/warning?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- 🚨 Aviso de risco de desativação automática
- 📊 Histórico de falhas
- 🔧 Sugestões de correção

---

### 6. 🚫 Sync Disabled - Repeated Failures (Sincronização Desabilitada)
**Prioridade**: CRÍTICA

```
http://192.168.127.65:7000/airbyte/disabled?token=webhook_pessoal_secret_token
```

**Email enviado inclui**:
- 🔴 Alerta crítico de sincronização desabilitada
- 📝 Motivo da desativação
- 🔧 Passos para reativar

---

## 🧪 Endpoint de Teste

Para testar a conexão sem enviar emails:

```
http://192.168.127.65:7000/airbyte/test
```

Resposta esperada:
```json
{
  "status": "success",
  "message": "Airbyte webhook test successful",
  "timestamp": "2025-10-30T...",
  "version": "2.0"
}
```

---

## 📖 Como Configurar no Airbyte

### Passo 1: Acessar Configurações
1. Abra o Airbyte
2. Vá em **Settings** → **Notifications**

### Passo 2: Configurar Webhooks
Para cada tipo de notificação que deseja receber:

1. **Ative o toggle** na coluna "Webhook"
2. **Cole a URL correspondente** (copie deste documento)
3. **Clique em "Test"** para verificar a conexão
4. ✅ Você deve receber um email se o teste for bem-sucedido

### Passo 3: Salvar
- Clique em **"Save changes"** no final da página

---

## 🔍 Detalhes Técnicos

### Estrutura do Payload Recebido

O Airbyte envia um payload JSON com a seguinte estrutura:

```json
{
  "data": {
    "workspace": {
      "id": "uuid",
      "name": "Nome do Workspace",
      "url": "link para o workspace"
    },
    "connection": {
      "id": "uuid",
      "name": "Nome da Conexão",
      "url": "link para a conexão"
    },
    "source": {
      "id": "uuid",
      "name": "Nome da Fonte",
      "url": "link para a fonte"
    },
    "destination": {
      "id": "uuid",
      "name": "Nome do Destino",
      "url": "link para o destino"
    },
    "jobId": 123456,
    "startedAt": "2025-10-30T00:00:00Z",
    "finishedAt": "2025-10-30T01:00:00Z",
    "bytesEmitted": 1000000,
    "bytesCommitted": 1000000,
    "recordsEmitted": 50000,
    "recordsCommitted": 50000,
    "bytesEmittedFormatted": "1 MB",
    "bytesCommittedFormatted": "1 MB",
    "durationInSeconds": 3600,
    "durationFormatted": "1 hours 0 min",
    "success": false,
    "errorMessage": "Connection timeout",
    "errorType": "config_error",
    "errorOrigin": "source"
  }
}
```

### Campos Específicos de Erro (apenas em failed syncs)

| Campo | Valores Possíveis | Descrição |
|-------|-------------------|-----------|
| `errorType` | `config_error` | Problema na configuração da fonte ou destino |
| | `transient_error` | Erro temporário que pode se resolver |
| | `system_error` | Erro interno do Airbyte |
| `errorOrigin` | `source` | Erro na origem dos dados |
| | `destination` | Erro no destino dos dados |

---

## 📧 Formato do Email Enviado

### Características dos Emails

✨ **Design Responsivo**
- Layout otimizado para desktop e mobile
- Largura máxima de 800px
- Cores dinâmicas baseadas no tipo de evento

📊 **Seções Informativas**
1. **Header**: Com emoji, tipo de evento e prioridade
2. **Informações da Conexão**: Nome, fonte, destino, workspace, job ID
3. **Seção de Erro** (apenas em falhas): Tipo, origem, mensagem, ação recomendada
4. **Alerta de Perda de Dados** (se aplicável): Quantidade e percentual
5. **Métricas de Sincronização**: Cards visuais com registros e volume
6. **Links Rápidos**: Acesso direto ao Airbyte
7. **Payload Completo**: Colapsável para análise técnica

🎨 **Cores por Tipo de Evento**
- 🔴 Failed: `#DC3545` (vermelho)
- ✅ Success: `#28A745` (verde)
- 🔄 Update: `#17A2B8` (azul)
- ⚠️ Action Required: `#FFC107` (amarelo)
- ⚠️ Warning: `#FF6B6B` (laranja)
- 🚫 Disabled: `#6C757D` (cinza)

---

## 🔧 Troubleshooting

### Problema: Airbyte não consegue conectar

**Verificações**:

1. **Servidor está rodando?**
   ```bash
   curl http://localhost:7000/
   ```

2. **Porta 7000 está aberta?**
   ```bash
   sudo netstat -tuln | grep 7000
   ```

3. **Firewall está bloqueando?**
   ```bash
   sudo firewall-cmd --list-ports
   ```

### Problema: Emails não estão sendo enviados

**Verificações**:

1. **Teste direto do endpoint**:
   ```bash
   curl -X POST "http://localhost:7000/test-email"
   ```

2. **Verifique os logs**:
   ```bash
   tail -50 webhook.log
   ```

3. **Credenciais Gmail corretas?**
   - Senha de app configurada?
   - 2FA ativo na conta Google?

---

## 🚀 Iniciar/Parar o Servidor

### Iniciar
```bash
cd /home/cazouvilela/projetos/webhook
python3 webhook_server.py
```

### Iniciar em background
```bash
nohup python3 webhook_server.py > webhook.log 2>&1 &
```

### Verificar se está rodando
```bash
ps aux | grep webhook_server.py
```

### Parar o servidor
```bash
pkill -f webhook_server.py
```

---

## 📝 Notas Importantes

1. **Airbyte em Docker**: Se o Airbyte está rodando em Docker na mesma máquina, use o IP `192.168.127.65` ao invés de `localhost`

2. **Token de Segurança**: O token está configurado no arquivo `.env` como `WEBHOOK_SECRET`

3. **Email Padrão**: Os emails serão enviados para `cazouvilela@gmail.com` (configurado no `.env`)

4. **Versão**: Esta é a versão 2.0 do sistema, otimizada para processar a estrutura oficial do Airbyte

5. **Logs**: Todos os webhooks recebidos são registrados em `webhook.log` com timestamp

---

## 📚 Documentação Adicional

- **README.md**: Documentação completa do projeto
- **memory.md**: Detalhes técnicos e arquitetura
- **test_webhook.sh**: Script para testar manualmente

---

**Data de Criação**: 2025-10-30
**Última Atualização**: 2025-10-30
**Versão do Sistema**: 2.0
