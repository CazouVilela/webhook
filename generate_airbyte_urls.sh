#!/bin/bash

# Script para gerar URLs do Airbyte com o token correto
# Executa: ./generate_airbyte_urls.sh

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================="
echo -e "   🚀 Gerador de URLs para Airbyte"
echo -e "===============================================${NC}"
echo ""

# Ler token do arquivo .env
ENV_FILE="$HOME/webhook/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado em $ENV_FILE${NC}"
    exit 1
fi

# Extrair o token
TOKEN=$(grep WEBHOOK_SECRET "$ENV_FILE" | cut -d= -f2 | tr -d '"' | tr -d "'")

if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Token não configurado no .env${NC}"
    echo "Usando URLs sem token (apenas para localhost)"
    TOKEN=""
    QUERY_PARAM=""
else
    echo -e "${GREEN}✅ Token encontrado: ${TOKEN:0:20}...${NC}"
    QUERY_PARAM="?token=$TOKEN"
fi

# Descobrir IPs disponíveis
LOCALHOST="localhost"
IP_LOCAL=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${BLUE}📍 Endereços disponíveis:${NC}"
echo "   - Localhost: $LOCALHOST"
echo "   - IP Local: $IP_LOCAL"

# Função para gerar URLs
generate_urls() {
    local HOST=$1
    
    echo ""
    echo -e "${GREEN}URLs para HOST: $HOST${NC}"
    echo "================================================"
    echo ""
    
    echo -e "${YELLOW}1️⃣  Failed syncs (Falhas)${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/failed$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: 🔴 [FALHA] Sincronização Airbyte"
    echo ""
    
    echo -e "${YELLOW}2️⃣  Successful syncs (Sucessos)${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/success$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: ✅ [SUCESSO] Sincronização Airbyte"
    echo ""
    
    echo -e "${YELLOW}3️⃣  Connection Updates${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/update$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: 🔄 [ATUALIZAÇÃO] Conexão Airbyte"
    echo ""
    
    echo -e "${YELLOW}4️⃣  Connection Updates Requiring Action${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/action-required$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: ⚠️ [AÇÃO NECESSÁRIA] Airbyte"
    echo ""
    
    echo -e "${YELLOW}5️⃣  Warning - Repeated Failures${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/warning$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: ⚠️ [AVISO] Falhas Repetidas"
    echo ""
    
    echo -e "${YELLOW}6️⃣  Sync Disabled - Repeated Failures${NC}"
    echo -e "   URL: ${BLUE}http://$HOST:7000/airbyte/disabled$QUERY_PARAM${NC}"
    echo -e "   📧 Subject: 🚫 [DESABILITADO] Sincronização"
    echo ""
}

# Gerar URLs para localhost
generate_urls "$LOCALHOST"

# Perguntar se quer ver para IP também
echo -e "${YELLOW}Deseja ver as URLs com IP local? (útil se Airbyte está em Docker) [s/N]${NC}"
read -r response
if [[ "$response" =~ ^[Ss]$ ]]; then
    generate_urls "$IP_LOCAL"
fi

# Salvar em arquivo
echo ""
echo -e "${YELLOW}Deseja salvar as URLs em um arquivo? [s/N]${NC}"
read -r save_response
if [[ "$save_response" =~ ^[Ss]$ ]]; then
    OUTPUT_FILE="$HOME/webhook/airbyte_urls.txt"
    
    {
        echo "URLs de Configuração do Airbyte"
        echo "Gerado em: $(date)"
        echo "Token: $TOKEN"
        echo ""
        echo "LOCALHOST URLS:"
        echo "==============="
        echo "Failed syncs:        http://localhost:7000/airbyte/failed$QUERY_PARAM"
        echo "Successful syncs:    http://localhost:7000/airbyte/success$QUERY_PARAM"
        echo "Connection Updates:  http://localhost:7000/airbyte/update$QUERY_PARAM"
        echo "Action Required:     http://localhost:7000/airbyte/action-required$QUERY_PARAM"
        echo "Warning:            http://localhost:7000/airbyte/warning$QUERY_PARAM"
        echo "Sync Disabled:      http://localhost:7000/airbyte/disabled$QUERY_PARAM"
        echo ""
        echo "IP LOCAL URLS ($IP_LOCAL):"
        echo "==============="
        echo "Failed syncs:        http://$IP_LOCAL:7000/airbyte/failed$QUERY_PARAM"
        echo "Successful syncs:    http://$IP_LOCAL:7000/airbyte/success$QUERY_PARAM"
        echo "Connection Updates:  http://$IP_LOCAL:7000/airbyte/update$QUERY_PARAM"
        echo "Action Required:     http://$IP_LOCAL:7000/airbyte/action-required$QUERY_PARAM"
        echo "Warning:            http://$IP_LOCAL:7000/airbyte/warning$QUERY_PARAM"
        echo "Sync Disabled:      http://$IP_LOCAL:7000/airbyte/disabled$QUERY_PARAM"
    } > "$OUTPUT_FILE"
    
    echo -e "${GREEN}✅ URLs salvas em: $OUTPUT_FILE${NC}"
fi

# Teste rápido
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${YELLOW}🧪 Testar conexão com o webhook?${NC}"
echo "1) Testar endpoint de falha"
echo "2) Testar endpoint de sucesso"
echo "3) Testar todos os endpoints"
echo "4) Não testar"
echo ""
read -p "Escolha: " test_choice

case $test_choice in
    1)
        echo -e "${YELLOW}Testando endpoint de falha...${NC}"
        curl -s -X POST "http://localhost:7000/airbyte/failed$QUERY_PARAM" \
            -H "Content-Type: application/json" \
            -d '{"connection": {"name": "Teste Manual"}, "error": "Teste de falha"}' | python3 -m json.tool
        echo -e "${GREEN}✅ Verifique seu email!${NC}"
        ;;
    2)
        echo -e "${YELLOW}Testando endpoint de sucesso...${NC}"
        curl -s -X POST "http://localhost:7000/airbyte/success$QUERY_PARAM" \
            -H "Content-Type: application/json" \
            -d '{"connection": {"name": "Teste Manual"}, "summary": {"recordsSynced": 1000}}' | python3 -m json.tool
        echo -e "${GREEN}✅ Verifique seu email!${NC}"
        ;;
    3)
        echo -e "${YELLOW}Testando todos os endpoints...${NC}"
        
        endpoints=("failed" "success" "update" "action-required" "warning" "disabled")
        for endpoint in "${endpoints[@]}"; do
            echo -e "${BLUE}Testando /airbyte/$endpoint...${NC}"
            curl -s -X POST "http://localhost:7000/airbyte/$endpoint$QUERY_PARAM" \
                -H "Content-Type: application/json" \
                -d '{"connection": {"name": "Teste Completo"}, "test": true}' \
                -o /dev/null -w "Status: %{http_code}\n"
            sleep 1
        done
        echo -e "${GREEN}✅ Testes concluídos! Verifique seus emails.${NC}"
        ;;
    *)
        echo "Testes pulados."
        ;;
esac

echo ""
echo -e "${GREEN}================================================"
echo "   ✅ Configuração Concluída!"
echo "================================================${NC}"
echo ""
echo "📝 Próximos passos:"
echo "1. Copie as URLs geradas acima"
echo "2. Cole no Airbyte em Settings > Notifications"
echo "3. Clique em 'Test' para cada URL"
echo "4. Salve com 'Save changes'"
echo ""
