#!/bin/bash

# Script de diagnóstico para problemas de conexão Airbyte-Webhook
# Execute: ./diagnostic_airbyte.sh

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================="
echo -e "   🔍 DIAGNÓSTICO AIRBYTE-WEBHOOK"
echo -e "=========================================${NC}"
echo ""

# Variáveis
WEBHOOK_DIR="$HOME/webhook"
ENV_FILE="$WEBHOOK_DIR/.env"
ERRORS=0

# 1. Verificar se o webhook está rodando
echo -e "${YELLOW}1. Verificando se o webhook está rodando...${NC}"
if pgrep -f "webhook_server.py" > /dev/null; then
    echo -e "${GREEN}✅ Processo webhook_server.py está rodando${NC}"
    PID=$(pgrep -f "webhook_server.py")
    echo "   PID: $PID"
else
    echo -e "${RED}❌ Webhook NÃO está rodando!${NC}"
    echo -e "${YELLOW}   Iniciando webhook...${NC}"
    cd $WEBHOOK_DIR
    python3 webhook_server.py > webhook.log 2>&1 &
    sleep 3
    if pgrep -f "webhook_server.py" > /dev/null; then
        echo -e "${GREEN}   ✅ Webhook iniciado com sucesso${NC}"
    else
        echo -e "${RED}   ❌ Falha ao iniciar webhook${NC}"
        echo "   Verifique o arquivo webhook.log para erros"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# 2. Testar conectividade local
echo -e "${YELLOW}2. Testando conectividade local...${NC}"
if curl -s http://localhost:7000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Webhook respondendo em localhost:7000${NC}"
else
    echo -e "${RED}❌ Webhook NÃO está respondendo em localhost:7000${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Verificar portas abertas
echo -e "${YELLOW}3. Verificando portas abertas...${NC}"
if netstat -tuln | grep -q ":7000"; then
    echo -e "${GREEN}✅ Porta 7000 está aberta${NC}"
    netstat -tuln | grep ":7000"
else
    echo -e "${RED}❌ Porta 7000 NÃO está aberta${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. Verificar firewall
echo -e "${YELLOW}4. Verificando firewall...${NC}"
if command -v firewall-cmd &> /dev/null; then
    if sudo firewall-cmd --list-ports | grep -q "7000/tcp"; then
        echo -e "${GREEN}✅ Porta 7000 liberada no firewall${NC}"
    else
        echo -e "${YELLOW}⚠️  Porta 7000 não está liberada no firewall${NC}"
        echo -e "   Liberando porta..."
        sudo firewall-cmd --permanent --add-port=7000/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}   ✅ Porta liberada${NC}"
    fi
else
    echo "   Firewall-cmd não encontrado (pode estar usando outro firewall)"
fi
echo ""

# 5. Descobrir IPs disponíveis
echo -e "${YELLOW}5. IPs disponíveis para configuração...${NC}"
echo -e "${BLUE}   Localhost:${NC} localhost ou 127.0.0.1"
IP_LOCAL=$(hostname -I | awk '{print $1}')
echo -e "${BLUE}   IP Local:${NC} $IP_LOCAL"

# Verificar se Airbyte está em Docker
if docker ps 2>/dev/null | grep -q airbyte; then
    echo -e "${YELLOW}   📦 Airbyte detectado em Docker${NC}"
    
    # IP do Docker bridge
    DOCKER_IP=$(ip addr show docker0 2>/dev/null | grep inet | awk '{print $2}' | cut -d/ -f1)
    if [ ! -z "$DOCKER_IP" ]; then
        echo -e "${BLUE}   Docker Bridge IP:${NC} $DOCKER_IP"
    fi
    
    # IP do host visto de dentro do Docker
    echo -e "${BLUE}   Para Docker use:${NC}"
    echo "      - host.docker.internal (se suportado)"
    echo "      - $IP_LOCAL (IP da máquina)"
    echo "      - gateway.docker.internal"
fi
echo ""

# 6. Verificar token
echo -e "${YELLOW}6. Verificando token de segurança...${NC}"
if [ -f "$ENV_FILE" ]; then
    TOKEN=$(grep WEBHOOK_SECRET "$ENV_FILE" | cut -d= -f2 | tr -d '"' | tr -d "'")
    if [ ! -z "$TOKEN" ]; then
        echo -e "${GREEN}✅ Token configurado: ${TOKEN:0:20}...${NC}"
    else
        echo -e "${YELLOW}⚠️  Token não configurado (webhook aceitará qualquer requisição local)${NC}"
    fi
else
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 7. Testar endpoints do Airbyte
echo -e "${YELLOW}7. Testando endpoints do Airbyte...${NC}"

test_endpoint() {
    local url=$1
    local description=$2
    
    echo -n "   $description: "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d '{"test": true}' 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ OK (HTTP $response)${NC}"
    elif [ "$response" = "401" ]; then
        echo -e "${YELLOW}⚠️  Não autorizado (token incorreto)${NC}"
    else
        echo -e "${RED}❌ Falhou (HTTP $response)${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

# Testar com localhost
test_endpoint "http://localhost:7000/airbyte/failed?token=$TOKEN" "localhost"

# Testar com IP local
test_endpoint "http://$IP_LOCAL:7000/airbyte/failed?token=$TOKEN" "IP Local ($IP_LOCAL)"

echo ""

# 8. Gerar URLs corretas
echo -e "${YELLOW}8. URLs recomendadas para o Airbyte:${NC}"
echo ""

if docker ps 2>/dev/null | grep -q airbyte; then
    echo -e "${GREEN}📦 Airbyte em Docker - Use estas URLs:${NC}"
    echo ""
    echo "   Failed syncs:"
    echo -e "   ${BLUE}http://$IP_LOCAL:7000/airbyte/failed?token=$TOKEN${NC}"
    echo ""
    echo "   Successful syncs:"
    echo -e "   ${BLUE}http://$IP_LOCAL:7000/airbyte/success?token=$TOKEN${NC}"
    echo ""
else
    echo -e "${GREEN}💻 Airbyte local - Use estas URLs:${NC}"
    echo ""
    echo "   Failed syncs:"
    echo -e "   ${BLUE}http://localhost:7000/airbyte/failed?token=$TOKEN${NC}"
    echo ""
    echo "   Successful syncs:"
    echo -e "   ${BLUE}http://localhost:7000/airbyte/success?token=$TOKEN${NC}"
    echo ""
fi

# 9. Verificar logs
echo -e "${YELLOW}9. Últimas linhas do log do webhook...${NC}"
if [ -f "$WEBHOOK_DIR/webhook.log" ]; then
    tail -5 $WEBHOOK_DIR/webhook.log
else
    echo "   Sem arquivo de log"
fi
echo ""

# 10. Teste completo de ponta a ponta
echo -e "${YELLOW}10. Teste completo de ponta a ponta...${NC}"
echo -e "   Enviando webhook de teste..."

TEST_URL="http://localhost:7000/airbyte/failed?token=$TOKEN"
RESPONSE=$(curl -s -X POST "$TEST_URL" \
    -H "Content-Type: application/json" \
    -d '{
        "connection": {
            "name": "Teste Diagnóstico",
            "source": {"name": "Test Source"},
            "destination": {"name": "Test Destination"}
        },
        "error": "Teste de diagnóstico",
        "email": "cazouvilela@gmail.com"
    }')

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Webhook funcionando corretamente!${NC}"
    echo "   Verifique seu email para confirmar o recebimento"
else
    echo -e "${RED}❌ Falha no teste${NC}"
    echo "   Resposta: $RESPONSE"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Resumo
echo -e "${BLUE}=========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ DIAGNÓSTICO CONCLUÍDO - TUDO OK!${NC}"
    echo ""
    echo "Use uma das URLs acima no Airbyte."
else
    echo -e "${RED}❌ DIAGNÓSTICO CONCLUÍDO - $ERRORS ERRO(S) ENCONTRADO(S)${NC}"
    echo ""
    echo "Correções necessárias listadas acima."
fi
echo -e "${BLUE}=========================================${NC}"

# Sugestões finais
echo ""
echo -e "${YELLOW}💡 DICAS IMPORTANTES:${NC}"
echo ""
echo "1. Se o Airbyte está em DOCKER:"
echo "   - Use o IP da máquina ($IP_LOCAL) ao invés de localhost"
echo "   - O container precisa acessar o host"
echo ""
echo "2. Se receber 'Connection refused':"
echo "   - Verifique se o webhook está rodando: ps aux | grep webhook"
echo "   - Reinicie o webhook: cd ~/webhook && python3 webhook_server.py"
echo ""
echo "3. Se receber 'Unauthorized':"
echo "   - Verifique o token no .env"
echo "   - Use o token correto na URL"
echo ""
echo "4. Para ver logs em tempo real:"
echo "   - tail -f ~/webhook/webhook.log"
echo ""
