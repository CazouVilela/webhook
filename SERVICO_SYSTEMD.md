# 🚀 Serviço Systemd - Webhook Email Server

## ✅ Status Atual

O webhook **JÁ ESTÁ CONFIGURADO** para iniciar automaticamente no boot do Fedora!

---

## 📊 Informações do Serviço

**Nome do Serviço**: `webhook-email.service`
**Status**: ✅ **ATIVO E RODANDO**
**Habilitado no Boot**: ✅ **SIM**
**Versão Atual**: **2.0** (com suporte detalhado ao Airbyte)
**PID Atual**: Varia (reinicia automaticamente se falhar)
**Porta**: `7000`
**Usuário**: `cazouvilela`

---

## 🔧 Configuração do Serviço

**Localização**: `/etc/systemd/system/webhook-email.service`

```ini
[Unit]
Description=Webhook Email Server
After=network.target

[Service]
Type=simple
User=cazouvilela
WorkingDirectory=/home/cazouvilela/projetos/webhook
ExecStart=/usr/bin/python3 /home/cazouvilela/projetos/webhook/webhook_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webhook-email

[Install]
WantedBy=multi-user.target
```

### 📝 Explicação da Configuração

- **After=network.target**: Inicia após a rede estar disponível
- **Restart=always**: Reinicia automaticamente se falhar ou parar
- **RestartSec=10**: Aguarda 10 segundos antes de tentar reiniciar
- **StandardOutput/Error=journal**: Logs vão para o systemd journal
- **WantedBy=multi-user.target**: Inicia no boot normal do sistema

---

## 🎯 Recursos do Serviço

✅ **Inicia automaticamente** no boot do Fedora
✅ **Reinicia automaticamente** se crashar
✅ **Aguarda 10 segundos** entre tentativas de reinício
✅ **Logs integrados** ao systemd journal
✅ **Roda como usuário** cazouvilela (não precisa de root)

---

## 🔍 Comandos Úteis

### Ver status do serviço
```bash
systemctl status webhook-email.service
```

### Ver logs do serviço (últimas 50 linhas)
```bash
journalctl -u webhook-email.service -n 50 --no-pager
```

### Ver logs em tempo real
```bash
journalctl -u webhook-email.service -f
```

### Reiniciar o serviço (requer sudo)
```bash
sudo systemctl restart webhook-email.service
```

### Parar o serviço (requer sudo)
```bash
sudo systemctl stop webhook-email.service
```

### Iniciar o serviço (requer sudo)
```bash
sudo systemctl start webhook-email.service
```

### Desabilitar do boot (requer sudo)
```bash
sudo systemctl disable webhook-email.service
```

### Habilitar no boot (requer sudo)
```bash
sudo systemctl enable webhook-email.service
```

### Ver configuração completa
```bash
systemctl cat webhook-email.service
```

---

## 🧪 Testar se está funcionando

### Teste rápido
```bash
curl http://localhost:7000/
```

**Resposta esperada**: JSON com status "online"

### Teste do endpoint Airbyte
```bash
curl http://localhost:7000/airbyte/test
```

**Resposta esperada**:
```json
{
    "status": "success",
    "message": "Airbyte webhook test successful",
    "timestamp": "2025-10-30T...",
    "version": "2.0"
}
```

---

## 📊 Verificar se está no boot

```bash
systemctl is-enabled webhook-email.service
```

**Resposta**: `enabled` ✅

```bash
systemctl list-unit-files | grep webhook
```

**Resposta**: `webhook-email.service    enabled    disabled` ✅

---

## 🔄 O que acontece no boot?

1. **Sistema inicia**
2. **Rede fica disponível** (network.target)
3. **Systemd inicia automaticamente** o webhook-email.service
4. **Servidor começa a escutar** na porta 7000
5. **Airbyte pode enviar webhooks** imediatamente

---

## ⚠️ Troubleshooting

### Serviço não está rodando?

```bash
# Ver erro específico
systemctl status webhook-email.service

# Ver logs de erro
journalctl -u webhook-email.service -n 100 --no-pager
```

### Serviço falha ao iniciar?

**Problemas comuns**:
1. **Porta 7000 ocupada**: Outro processo usando a porta
   ```bash
   sudo lsof -i :7000
   ```

2. **Arquivo .env faltando**: Configurações SMTP ausentes
   ```bash
   ls -la /home/cazouvilela/projetos/webhook/.env
   ```

3. **Permissões**: Usuário cazouvilela sem acesso aos arquivos
   ```bash
   ls -la /home/cazouvilela/projetos/webhook/
   ```

### Forçar reinício completo

```bash
# Matar processo manualmente
pkill -f webhook_server.py

# Aguardar reinício automático (10 segundos)
sleep 12

# Verificar status
systemctl status webhook-email.service
```

---

## 📝 Logs

### Localização dos logs

1. **Systemd Journal** (recomendado):
   ```bash
   journalctl -u webhook-email.service
   ```

2. **Arquivo de log** (se configurado):
   ```bash
   tail -f /home/cazouvilela/projetos/webhook/webhook.log
   ```

### Ver logs desde o último boot

```bash
journalctl -u webhook-email.service -b
```

### Ver logs de ontem

```bash
journalctl -u webhook-email.service --since yesterday
```

### Ver logs das últimas 2 horas

```bash
journalctl -u webhook-email.service --since "2 hours ago"
```

---

## 🔐 Segurança

- ✅ Roda como usuário **não-root** (cazouvilela)
- ✅ Reinicia automaticamente após falhas
- ✅ Logs protegidos no systemd journal
- ✅ Token de autenticação configurado

---

## 📚 Informações Adicionais

**Criado**: Antes de 2025-10-30
**Última Atualização**: 2025-10-30 23:57:00
**Versão do Código**: 2.0 (Airbyte otimizado)
**Arquivos**:
- Serviço: `/etc/systemd/system/webhook-email.service`
- Código: `/home/cazouvilela/projetos/webhook/webhook_server.py`
- Config: `/home/cazouvilela/projetos/webhook/.env`

---

## ✅ Checklist de Verificação

- [x] Serviço existe no systemd
- [x] Serviço está habilitado no boot
- [x] Serviço está rodando atualmente
- [x] Versão 2.0 está ativa
- [x] Endpoint de teste funciona
- [x] Reinício automático configurado
- [x] Logs integrados ao systemd

---

**Tudo está funcionando perfeitamente!** 🎉

O webhook inicia automaticamente quando o Fedora liga e fica disponível para receber notificações do Airbyte.
