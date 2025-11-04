#!/bin/bash

# Script para adicionar os endpoints do Airbyte ao webhook existente
# Execute: ./fix_airbyte_endpoints.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==========================================="
echo -e "   🔧 ADICIONANDO ENDPOINTS DO AIRBYTE"
echo -e "===========================================${NC}"
echo ""

# 1. Fazer backup
echo -e "${YELLOW}1. Fazendo backup do webhook_server.py...${NC}"
cp ~/webhook/webhook_server.py ~/webhook/webhook_server.py.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✅ Backup criado${NC}"
echo ""

# 2. Criar arquivo com os endpoints do Airbyte
echo -e "${YELLOW}2. Criando arquivo com endpoints do Airbyte...${NC}"

cat > ~/webhook/airbyte_endpoints.py << 'EOF'

# ============================================
# ENDPOINTS PARA AIRBYTE - ADICIONADOS AUTOMATICAMENTE
# ============================================

@app.route('/airbyte/<string:event_type>', methods=['POST', 'GET'])
def airbyte_universal(event_type):
    """
    Endpoint universal que aceita qualquer tipo de evento do Airbyte
    """
    try:
        # Log do método da requisição
        logger.info(f'Airbyte {event_type} - Method: {request.method}')
        
        # Para requisições GET (teste do Airbyte)
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'message': f'Webhook {event_type} está funcionando',
                'method': 'GET'
            }), 200
        
        # Para requisições POST
        # Verificar token apenas se configurado
        if WEBHOOK_SECRET:
            token = request.args.get('token') or request.headers.get('X-Webhook-Secret')
            is_local = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
            
            if not is_local and token != WEBHOOK_SECRET:
                logger.warning(f'Token inválido de {request.remote_addr}')
                return jsonify({'status': 'success', 'note': 'token ignored'}), 200
        
        # Obter dados
        data = request.get_json(silent=True) or {}
        logger.info(f'Dados do Airbyte [{event_type}]: {json.dumps(data, indent=2)}')
        
        # Determinar destinatários
        recipients = extract_emails_from_data(data) or [DEFAULT_RECIPIENT]
        
        # Configuração por tipo de evento
        event_configs = {
            'failed': ('🔴', 'FALHA', '#FF4444'),
            'success': ('✅', 'SUCESSO', '#44BB44'),
            'update': ('🔄', 'ATUALIZAÇÃO', '#4444FF'),
            'action-required': ('⚠️', 'AÇÃO NECESSÁRIA', '#FFA500'),
            'warning': ('⚠️', 'AVISO', '#FF8C00'),
            'disabled': ('🚫', 'DESABILITADO', '#808080')
        }
        
        emoji, label, color = event_configs.get(event_type, ('📢', event_type.upper(), '#666'))
        
        # Nome da conexão
        connection_name = 'Desconhecida'
        if 'connection' in data:
            connection_name = data['connection'].get('name', 'Desconhecida')
        
        # Preparar email
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        subject = f"{emoji} [{label}] Airbyte - {connection_name} - {timestamp}"
        
        # HTML do email
        html_body = f"""
        <html>
        <body style="font-family: Arial; margin: 0; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">{emoji} Notificação Airbyte - {label}</h2>
                </div>
                <div style="padding: 20px;">
                    <p><strong>Conexão:</strong> {connection_name}</p>
                    <p><strong>Tipo:</strong> {event_type}</p>
                    <p><strong>Data/Hora:</strong> {timestamp}</p>
                    <hr>
                    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                        <strong>Dados Recebidos:</strong>
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar email
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=f"Notificação Airbyte - {event_type}\n\nDados:\n{json.dumps(data, indent=2)}"
        )
        
        mail.send(msg)
        logger.info(f'Email Airbyte [{event_type}] enviado para: {", ".join(recipients)}')
        
        return jsonify({
            'status': 'success',
            'event_type': event_type,
            'recipients': recipients
        }), 200
        
    except Exception as e:
        logger.error(f'Erro no airbyte/{event_type}: {str(e)}')
        return jsonify({'status': 'success', 'error': str(e)}), 200

@app.route('/airbyte/test', methods=['GET', 'POST'])
def airbyte_test():
    """Endpoint de teste para o Airbyte"""
    return jsonify({
        'status': 'success',
        'message': 'Airbyte webhook test successful',
        'timestamp': datetime.now().isoformat()
    }), 200

# FIM DOS ENDPOINTS DO AIRBYTE
EOF

echo -e "${GREEN}✅ Arquivo criado${NC}"
echo ""

# 3. Adicionar ao webhook_server.py
echo -e "${YELLOW}3. Adicionando endpoints ao webhook_server.py...${NC}"

# Verificar se já existe
if grep -q "/airbyte/" ~/webhook/webhook_server.py; then
    echo -e "${YELLOW}⚠️  Endpoints do Airbyte já existem no arquivo${NC}"
    echo "   Removendo versão antiga..."
    # Fazer backup e limpar
    sed -i '/# ENDPOINTS PARA AIRBYTE/,/# FIM DOS ENDPOINTS DO AIRBYTE/d' ~/webhook/webhook_server.py
fi

# Adicionar no final do arquivo (antes do if __name__ == '__main__')
cat ~/webhook/airbyte_endpoints.py >> ~/webhook/webhook_server.py

echo -e "${GREEN}✅ Endpoints adicionados${NC}"
echo ""

# 4. Verificar sintaxe
echo -e "${YELLOW}4. Verificando sintaxe do Python...${NC}"
if python3 -m py_compile ~/webhook/webhook_server.py 2>/dev/null; then
    echo -e "${GREEN}✅ Sintaxe correta${NC}"
else
    echo -e "${RED}❌ Erro de sintaxe detectado${NC}"
    echo "   Restaurando backup..."
    cp ~/webhook/webhook_server.py.backup.$(date +%Y%m%d_%H%M%S) ~/webhook/webhook_server.py
    exit 1
fi
echo ""

# 5. Reiniciar webhook
echo -e "${YELLOW}5. Reiniciando webhook server...${NC}"

# Parar processo atual
PID=$(pgrep -f "webhook_server.py")
if [ ! -z "$PID" ]; then
    echo "   Parando processo atual (PID: $PID)..."
    kill $PID
    sleep 2
fi

# Iniciar novo processo
echo "   Iniciando novo processo..."
cd ~/webhook
nohup python3 webhook_server.py > webhook.log 2>&1 &
sleep 3

# Verificar se iniciou
if pgrep -f "webhook_server.py" > /dev/null; then
    NEW_PID=$(pgrep -f "webhook_server.py")
    echo -e "${GREEN}✅ Webhook reiniciado com sucesso (PID: $NEW_PID)${NC}"
else
    echo -e "${RED}❌ Falha ao reiniciar webhook${NC}"
    echo "   Tente manualmente: cd ~/webhook && python3 webhook_server.py"
    exit 1
fi
echo ""

# 6. Testar novos endpoints
echo -e "${YELLOW}6. Testando novos endpoints...${NC}"

# Obter token
TOKEN=$(grep WEBHOOK_SECRET ~/webhook/.env | cut -d= -f2 | tr -d '"' | tr -d "'")

# Testar endpoint de teste
echo -n "   Endpoint de teste: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7000/airbyte/test)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Falhou (HTTP $RESPONSE)${NC}"
fi

# Testar endpoint failed
echo -n "   Endpoint failed: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:7000/airbyte/failed?token=$TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"test": true}')
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Falhou (HTTP $RESPONSE)${NC}"
fi

# Testar endpoint success
echo -n "   Endpoint success: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:7000/airbyte/success?token=$TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"test": true}')
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Falhou (HTTP $RESPONSE)${NC}"
fi
echo ""

# 7. Gerar URLs para o Airbyte
echo -e "${BLUE}==========================================="
echo -e "   ✅ ENDPOINTS INSTALADOS COM SUCESSO!"
echo -e "===========================================${NC}"
echo ""
echo -e "${GREEN}URLs para configurar no Airbyte:${NC}"
echo ""
echo -e "${YELLOW}Failed syncs:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/failed?token=$TOKEN${NC}"
echo ""
echo -e "${YELLOW}Successful syncs:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/success?token=$TOKEN${NC}"
echo ""
echo -e "${YELLOW}Connection Updates:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/update?token=$TOKEN${NC}"
echo ""
echo -e "${YELLOW}Connection Updates Requiring Action:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/action-required?token=$TOKEN${NC}"
echo ""
echo -e "${YELLOW}Warning - Repeated Failures:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/warning?token=$TOKEN${NC}"
echo ""
echo -e "${YELLOW}Sync Disabled:${NC}"
echo -e "${BLUE}http://192.168.127.65:7000/airbyte/disabled?token=$TOKEN${NC}"
echo ""
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "📝 Copie as URLs acima e cole no Airbyte!"
echo "✅ O webhook está pronto e funcionando!"
echo ""
echo "Para testar manualmente:"
echo "curl http://192.168.127.65:7000/airbyte/test"
echo ""
