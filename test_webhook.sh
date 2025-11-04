#!/bin/bash

# Script de teste para o webhook com suporte a email de destino
# Uso: ./test_webhook.sh

# Configurações
WEBHOOK_URL="http://localhost:7000"
WEBHOOK_SECRET="webhook_pessoal_secret_token"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo "   🚀 Testador de Webhook"
echo -e "===================================${NC}"
echo ""

# Função para enviar webhook
send_webhook() {
    local data="$1"
    local endpoint="$2"
    local description="$3"
    
    echo -e "${YELLOW}📤 $description${NC}"
    echo -e "${BLUE}Endpoint:${NC} ${WEBHOOK_URL}${endpoint}"
    echo -e "${BLUE}Dados:${NC}"
    echo "$data" | python3 -m json.tool 2>/dev/null || echo "$data"
    echo ""
    
    response=$(curl -s -X POST "${WEBHOOK_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        -H "X-Webhook-Secret: ${WEBHOOK_SECRET}" \
        -d "$data" \
        -w "\n<<<HTTP_STATUS>>>%{http_code}")
    
    # Separar resposta e status HTTP
    body=$(echo "$response" | sed -n '1,/<<<HTTP_STATUS>>>/p' | sed '$d')
    status=$(echo "$response" | grep -oP '<<<HTTP_STATUS>>>\K\d+')
    
    # Verificar status
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✅ Sucesso (HTTP $status)${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Erro (HTTP $status)${NC}"
        echo "$body"
    fi
    
    echo ""
    echo "-----------------------------------"
    echo ""
    sleep 1
}

# Menu de opções
show_menu() {
    echo -e "${BLUE}Escolha uma opção de teste:${NC}"
    echo ""
    echo "1) Teste básico (email padrão)"
    echo "2) Teste com email específico"
    echo "3) Teste com múltiplos emails"
    echo "4) Teste com ação personalizada"
    echo "5) Teste de payload complexo"
    echo "6) Teste de envio direto de email"
    echo "7) Executar todos os testes"
    echo "8) Teste personalizado (você define o JSON)"
    echo "9) Ver documentação da API"
    echo "0) Sair"
    echo ""
    read -p "Opção: " choice
}

# Testes
run_test_1() {
    echo -e "${GREEN}=== TESTE 1: Webhook Básico ===${NC}"
    send_webhook \
        '{"evento": "teste_basico", "mensagem": "Teste sem email específico", "timestamp": "'$(date -Iseconds)'"}' \
        "/webhook" \
        "Webhook básico (usará email padrão)"
}

run_test_2() {
    echo -e "${GREEN}=== TESTE 2: Email Específico ===${NC}"
    read -p "Digite o email de destino: " custom_email
    send_webhook \
        '{"email": "'$custom_email'", "evento": "teste_email_customizado", "usuario": "Teste Manual", "timestamp": "'$(date -Iseconds)'"}' \
        "/webhook" \
        "Webhook com email específico: $custom_email"
}

run_test_3() {
    echo -e "${GREEN}=== TESTE 3: Múltiplos Emails ===${NC}"
    read -p "Digite o primeiro email: " email1
    read -p "Digite o segundo email: " email2
    send_webhook \
        '{
            "emails": ["'$email1'", "'$email2'"],
            "evento": "notificacao_multipla",
            "tipo": "alerta",
            "severidade": "alta",
            "mensagem": "Notificação enviada para múltiplos destinatários"
        }' \
        "/webhook" \
        "Webhook com múltiplos destinatários"
}

run_test_4() {
    echo -e "${GREEN}=== TESTE 4: Webhook com Ação ===${NC}"
    read -p "Digite a ação (ex: login, pedido, alerta): " action
    read -p "Digite o email de destino (Enter para usar padrão): " dest_email
    
    if [ -z "$dest_email" ]; then
        data='{"usuario": "João Silva", "status": "sucesso", "ip": "192.168.1.100"}'
    else
        data='{"email": "'$dest_email'", "usuario": "João Silva", "status": "sucesso", "ip": "192.168.1.100"}'
    fi
    
    send_webhook "$data" "/webhook/$action" "Webhook com ação: $action"
}

run_test_5() {
    echo -e "${GREEN}=== TESTE 5: Payload Complexo ===${NC}"
    read -p "Digite o email de destino (Enter para usar padrão): " dest_email
    
    complex_data='{
        '$([ ! -z "$dest_email" ] && echo '"email": "'$dest_email'",')' 
        "pedido": {
            "id": "PED-'$(date +%s)'",
            "cliente": {
                "nome": "Maria Silva",
                "cpf": "123.456.789-00",
                "telefone": "(11) 98765-4321"
            },
            "itens": [
                {
                    "produto": "Notebook Dell",
                    "sku": "NB-DELL-001",
                    "quantidade": 1,
                    "preco_unitario": 3500.00,
                    "subtotal": 3500.00
                },
                {
                    "produto": "Mouse Logitech",
                    "sku": "MS-LOG-002",
                    "quantidade": 2,
                    "preco_unitario": 85.00,
                    "subtotal": 170.00
                }
            ],
            "resumo": {
                "subtotal": 3670.00,
                "frete": 50.00,
                "desconto": 100.00,
                "total": 3620.00
            },
            "pagamento": {
                "metodo": "Cartão de Crédito",
                "parcelas": 3,
                "bandeira": "Visa"
            }
        },
        "status": "confirmado",
        "data_pedido": "'$(date -Iseconds)'",
        "previsao_entrega": "'$(date -d "+7 days" -Iseconds)'"
    }'
    
    send_webhook "$complex_data" "/webhook/novo-pedido" "Payload complexo de pedido"
}

run_test_6() {
    echo -e "${GREEN}=== TESTE 6: Envio Direto de Email ===${NC}"
    read -p "Digite o email para teste (Enter para usar padrão): " test_email
    
    if [ -z "$test_email" ]; then
        url="${WEBHOOK_URL}/test-email"
    else
        url="${WEBHOOK_URL}/test-email?email=${test_email}"
    fi
    
    echo -e "${YELLOW}📧 Testando envio direto de email${NC}"
    response=$(curl -s "$url")
    echo "$response" | python3 -m json.tool
}

run_test_8() {
    echo -e "${GREEN}=== TESTE 8: JSON Personalizado ===${NC}"
    echo "Digite seu JSON (termine com uma linha vazia):"
    json_data=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        json_data="${json_data}${line}"
    done
    
    read -p "Endpoint (/webhook ou /webhook/acao): " endpoint
    send_webhook "$json_data" "$endpoint" "JSON personalizado"
}

run_test_9() {
    echo -e "${GREEN}=== Documentação da API ===${NC}"
    echo -e "${YELLOW}📚 Obtendo documentação...${NC}"
    response=$(curl -s "${WEBHOOK_URL}/help")
    echo "$response" | python3 -m json.tool
}

# Executar todos os testes
run_all_tests() {
    echo -e "${BLUE}Executando todos os testes automatizados...${NC}"
    echo ""
    
    # Teste 1
    run_test_1
    
    # Teste 2 com email automático
    email_test="teste@example.com"
    echo -e "${GREEN}=== TESTE 2: Email Específico (Automático) ===${NC}"
    send_webhook \
        '{"email": "'$email_test'", "evento": "teste_automatizado", "numero": 2}' \
        "/webhook" \
        "Email específico: $email_test"
    
    # Teste 3 com múltiplos emails
    echo -e "${GREEN}=== TESTE 3: Múltiplos Emails (Automático) ===${NC}"
    send_webhook \
        '{"emails": ["admin@example.com", "suporte@example.com"], "evento": "teste_multiplo", "numero": 3}' \
        "/webhook" \
        "Múltiplos destinatários"
    
    # Teste 4 com ação
    echo -e "${GREEN}=== TESTE 4: Com Ação (Automático) ===${NC}"
    send_webhook \
        '{"email": "gerente@example.com", "tipo": "aprovacao", "valor": 5000}' \
        "/webhook/aprovacao-pagamento" \
        "Ação: aprovacao-pagamento"
    
    # Teste 5 complexo
    run_test_5
}

# Verificar se o servidor está rodando
check_server() {
    echo -e "${YELLOW}🔍 Verificando se o servidor está rodando...${NC}"
    if curl -s "${WEBHOOK_URL}/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Servidor está online!${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ Servidor não está respondendo em ${WEBHOOK_URL}${NC}"
        echo -e "${YELLOW}Certifique-se de que o servidor está rodando com:${NC}"
        echo "python3 webhook_server.py"
        echo ""
        return 1
    fi
}

# Main
main() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════╗"
    echo -e "║     🚀 WEBHOOK EMAIL TESTER 🚀      ║"
    echo -e "╚══════════════════════════════════════╝${NC}"
    echo ""
    
    # Verificar servidor
    if ! check_server; then
        exit 1
    fi
    
    while true; do
        show_menu
        
        case $choice in
            1) run_test_1 ;;
            2) run_test_2 ;;
            3) run_test_3 ;;
            4) run_test_4 ;;
            5) run_test_5 ;;
            6) run_test_6 ;;
            7) run_all_tests ;;
            8) run_test_8 ;;
            9) run_test_9 ;;
            0) 
                echo -e "${GREEN}Saindo... Até logo!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opção inválida!${NC}"
                ;;
        esac
        
        echo ""
        read -p "Pressione Enter para continuar..."
        clear
    done
}

# Executar
main
