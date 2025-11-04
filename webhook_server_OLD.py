#!/usr/bin/env python3
"""
Webhook Server com Envio de Email
Servidor Flask que recebe webhooks e envia notificações por email
Permite especificar o email de destino no payload do webhook
"""

import os
import json
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Configuração de Email
app.config.update(
    # Servidor SMTP do Gmail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587)),
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true',
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true',
    
    # Credenciais
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    
    # Remetente padrão
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
)

# Inicializar Flask-Mail
mail = Mail(app)

# Email destinatário padrão (usado se não for especificado no webhook)
DEFAULT_RECIPIENT = os.getenv('DEFAULT_RECIPIENT_EMAIL', 'cazouvilela@gmail.com')

# Token de segurança (opcional mas recomendado)
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'webhook-cazou-2024-secret-token')

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def extract_emails_from_data(data):
    """
    Extrai emails do payload do webhook
    Procura por campos como: email, emails, destinatario, recipient, to
    """
    emails = []
    
    # Se data for string, tentar converter para dict
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return emails
    
    # Se não for dict, retornar lista vazia
    if not isinstance(data, dict):
        return emails
    
    # Campos possíveis para emails
    email_fields = [
        'email', 'emails', 'destinatario', 'destinatarios',
        'recipient', 'recipients', 'to', 'para', 'dest'
    ]
    
    for field in email_fields:
        if field in data:
            value = data[field]
            # Se for string, adicionar à lista
            if isinstance(value, str) and validate_email(value):
                emails.append(value)
            # Se for lista, adicionar todos os emails válidos
            elif isinstance(value, list):
                for email in value:
                    if isinstance(email, str) and validate_email(email):
                        emails.append(email)
    
    return emails

@app.route('/')
def home():
    """Endpoint raiz para verificar se o servidor está funcionando"""
    return jsonify({
        'status': 'online',
        'message': 'Webhook server está rodando',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            '/': 'Status do servidor',
            '/webhook': 'Endpoint principal (POST)',
            '/webhook/<action>': 'Webhook com ação específica (POST)',
            '/test-email': 'Testar envio de email (GET)',
            '/help': 'Documentação de uso (GET)'
        }
    })

@app.route('/help')
def help():
    """Endpoint de ajuda com documentação"""
    return jsonify({
        'description': 'Webhook Server com Envio de Email',
        'usage': {
            'basic': {
                'url': '/webhook',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'X-Webhook-Secret': 'seu-token-secreto'
                },
                'body': {
                    'email': 'destino@example.com',
                    'data': 'seus dados aqui'
                }
            },
            'with_action': {
                'url': '/webhook/<action>',
                'method': 'POST',
                'description': 'Substitua <action> pela ação desejada'
            },
            'multiple_recipients': {
                'body': {
                    'emails': ['email1@example.com', 'email2@example.com'],
                    'data': 'seus dados aqui'
                }
            }
        },
        'email_fields': [
            'email', 'emails', 'destinatario', 'destinatarios',
            'recipient', 'recipients', 'to', 'para', 'dest'
        ],
        'examples': {
            'single_email': {
                'email': 'usuario@gmail.com',
                'evento': 'login',
                'usuario': 'João'
            },
            'multiple_emails': {
                'emails': ['admin@empresa.com', 'suporte@empresa.com'],
                'alerta': 'Sistema fora do ar',
                'severidade': 'critica'
            }
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal do webhook"""
    try:
        # Verificar token de segurança (se configurado)
        if WEBHOOK_SECRET:
            token = request.headers.get('X-Webhook-Secret')
            if token != WEBHOOK_SECRET:
                logger.warning('Tentativa de acesso não autorizada')
                return jsonify({'error': 'Não autorizado'}), 401
        
        # Obter dados do webhook
        data = request.get_json(force=True)
        
        # Log da requisição recebida
        logger.info(f'Webhook recebido: {json.dumps(data, indent=2)}')
        
        # Extrair emails de destino do payload
        recipient_emails = extract_emails_from_data(data)
        
        # Se não houver emails no payload, usar o padrão
        if not recipient_emails:
            recipient_emails = [DEFAULT_RECIPIENT]
            logger.info(f'Nenhum email encontrado no payload, usando padrão: {DEFAULT_RECIPIENT}')
        else:
            logger.info(f'Emails encontrados no payload: {recipient_emails}')
        
        # Preparar informações para o email
        webhook_info = {
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'ip_origem': request.remote_addr,
            'headers': dict(request.headers),
            'dados': data,
            'destinatarios': recipient_emails
        }
        
        # Enviar email
        success_count = send_notification_email(webhook_info, recipient_emails)
        
        return jsonify({
            'status': 'success',
            'message': f'Webhook processado e email enviado para {success_count} destinatário(s)',
            'recipients': recipient_emails
        }), 200
        
    except Exception as e:
        logger.error(f'Erro ao processar webhook: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook/<string:action>', methods=['POST'])
def webhook_with_action(action):
    """Endpoint do webhook com ação específica"""
    try:
        # Verificar token de segurança
        if WEBHOOK_SECRET:
            token = request.headers.get('X-Webhook-Secret')
            if token != WEBHOOK_SECRET:
                return jsonify({'error': 'Não autorizado'}), 401
        
        # Obter dados
        data = request.get_json(force=True)
        
        # Log da ação
        logger.info(f'Webhook com ação "{action}" recebido')
        
        # Extrair emails de destino
        recipient_emails = extract_emails_from_data(data)
        if not recipient_emails:
            recipient_emails = [DEFAULT_RECIPIENT]
        
        # Preparar informações
        webhook_info = {
            'acao': action,
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'ip_origem': request.remote_addr,
            'dados': data,
            'destinatarios': recipient_emails
        }
        
        # Enviar email com a ação no assunto
        success_count = send_notification_email(webhook_info, recipient_emails, action=action)
        
        return jsonify({
            'status': 'success',
            'action': action,
            'message': f'Webhook {action} processado para {success_count} destinatário(s)',
            'recipients': recipient_emails
        }), 200
        
    except Exception as e:
        logger.error(f'Erro ao processar webhook {action}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def send_notification_email(webhook_info, recipient_emails, action=None):
    """
    Função para enviar email de notificação
    Retorna o número de emails enviados com sucesso
    """
    success_count = 0
    
    # Remover campos sensíveis dos dados antes de enviar
    dados_limpos = webhook_info.get('dados', {}).copy()
    for campo_email in ['email', 'emails', 'destinatario', 'destinatarios', 
                        'recipient', 'recipients', 'to', 'para', 'dest']:
        dados_limpos.pop(campo_email, None)
    
    try:
        # Preparar assunto
        if action:
            subject = f'[Webhook] Ação: {action} - {webhook_info["timestamp"]}'
        else:
            subject = f'[Webhook] Notificação - {webhook_info["timestamp"]}'
        
        # Preparar corpo do email
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
                    🔔 Notificação de Webhook
                </h2>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #555;">📊 Informações Gerais</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li><strong>📅 Data/Hora:</strong> {webhook_info.get('timestamp')}</li>
                        <li><strong>🌐 IP de Origem:</strong> {webhook_info.get('ip_origem')}</li>
                        {f'<li><strong>⚡ Ação:</strong> <span style="color: #4CAF50; font-weight: bold;">{webhook_info.get("acao")}</span></li>' if webhook_info.get('acao') else ''}
                        <li><strong>📧 Enviado para:</strong> {', '.join(webhook_info.get('destinatarios', []))}</li>
                    </ul>
                </div>
                
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #555;">📦 Dados Recebidos</h3>
                    <pre style="background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 3px; overflow-x: auto;">
{json.dumps(dados_limpos, indent=2, ensure_ascii=False)}
                    </pre>
                </div>
                
                <details style="margin: 15px 0;">
                    <summary style="cursor: pointer; color: #4CAF50; font-weight: bold;">
                        🔧 Headers da Requisição (clique para expandir)
                    </summary>
                    <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin-top: 10px; font-size: 12px;">
{json.dumps(webhook_info.get('headers', {}), indent=2, ensure_ascii=False)}
                    </pre>
                </details>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="color: #888; font-size: 12px; text-align: center;">
                    Este é um email automático enviado pelo Webhook Server.<br>
                    Configurado por: cazouvilela@gmail.com
                </p>
            </div>
        </body>
        </html>
        """
        
        # Criar mensagem
        msg = Message(
            subject=subject,
            recipients=recipient_emails,
            html=body
        )
        
        # Adicionar versão em texto simples
        msg.body = f"""
        Notificação de Webhook
        
        Data/Hora: {webhook_info.get('timestamp')}
        IP de Origem: {webhook_info.get('ip_origem')}
        {'Ação: ' + webhook_info.get('acao') if webhook_info.get('acao') else ''}
        Enviado para: {', '.join(webhook_info.get('destinatarios', []))}
        
        Dados Recebidos:
        {json.dumps(dados_limpos, indent=2, ensure_ascii=False)}
        """
        
        # Enviar email
        mail.send(msg)
        success_count = len(recipient_emails)
        logger.info(f'Email enviado com sucesso para {success_count} destinatário(s): {", ".join(recipient_emails)}')
        
    except Exception as e:
        logger.error(f'Erro ao enviar email: {str(e)}')
        raise
    
    return success_count

@app.route('/test-email', methods=['GET', 'POST'])
def test_email():
    """Endpoint para testar o envio de email"""
    try:
        # Permitir especificar email de teste via query param ou JSON
        test_email_address = None
        
        # Verificar query parameter
        test_email_address = request.args.get('email')
        
        # Se for POST, verificar o body
        if request.method == 'POST':
            data = request.get_json(silent=True)
            if data and 'email' in data:
                test_email_address = data['email']
        
        # Validar email se fornecido
        if test_email_address and not validate_email(test_email_address):
            return jsonify({
                'status': 'error',
                'message': f'Email inválido: {test_email_address}'
            }), 400
        
        # Usar email padrão se não fornecido
        if not test_email_address:
            test_email_address = DEFAULT_RECIPIENT
        
        msg = Message(
            subject='✅ Teste de Email - Webhook Server',
            recipients=[test_email_address],
            html="""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4CAF50;">✅ Teste Bem-Sucedido!</h2>
                    <p>Este é um email de teste do seu webhook server.</p>
                    <p>Se você recebeu este email, a configuração está correta!</p>
                    <hr style="border: none; border-top: 1px solid #ddd;">
                    <h3>Informações da Configuração:</h3>
                    <ul>
                        <li><strong>Servidor SMTP:</strong> smtp.gmail.com</li>
                        <li><strong>Remetente:</strong> cazouvilela@gmail.com</li>
                        <li><strong>Timestamp:</strong> {timestamp}</li>
                    </ul>
                    <p style="color: #888; font-size: 12px;">
                        Webhook Server configurado e funcionando corretamente!
                    </p>
                </div>
            </body>
            </html>
            """.format(timestamp=datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
            body=f"""
            Teste de Email - Webhook Server
            
            Este é um email de teste do seu webhook server.
            Se você recebeu este email, a configuração está correta!
            
            Servidor SMTP: smtp.gmail.com
            Remetente: cazouvilela@gmail.com
            Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
        )
        mail.send(msg)
        
        return jsonify({
            'status': 'success',
            'message': f'Email de teste enviado para {test_email_address}',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Verificar configurações essenciais
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        logger.error('MAIL_USERNAME e MAIL_PASSWORD devem ser configurados!')
        logger.error('Verifique o arquivo .env')
        exit(1)
    
    # Mostrar configuração atual (sem mostrar a senha)
    logger.info('=== Configuração do Webhook Server ===')
    logger.info(f'Email remetente: {app.config["MAIL_USERNAME"]}')
    logger.info(f'Servidor SMTP: {app.config["MAIL_SERVER"]}:{app.config["MAIL_PORT"]}')
    logger.info(f'Email padrão para notificações: {DEFAULT_RECIPIENT}')
    logger.info(f'Token de segurança configurado: {"Sim" if WEBHOOK_SECRET else "Não"}')
    logger.info('=====================================')
    
    # Iniciar servidor
    logger.info('Iniciando webhook server na porta 5000...')
    logger.info('Acesse http://localhost:5000 para verificar o status')
    logger.info('Use http://localhost:5000/help para ver a documentação')
    
    # Para produção, use um servidor WSGI como Gunicorn
    # Para desenvolvimento/teste
    app.run(
        host='0.0.0.0',  # Escutar em todas as interfaces
        port=5000,        # Porta do webhook
        debug=False       # Mudar para True para desenvolvimento
    )


#!/usr/bin/env python3
"""
Adicione este código ao seu webhook_server.py
Endpoints específicos para cada tipo de notificação do Airbyte
com suporte a token via query parameter
"""

from urllib.parse import parse_qs, urlparse

# ============================================
# FUNÇÃO AUXILIAR PARA VERIFICAR TOKEN
# ============================================

def verify_token_from_url_or_header(request):
    """Verifica token do header ou da query string"""
    if not WEBHOOK_SECRET:
        return True
    
    # Tentar pegar do header primeiro
    token = request.headers.get('X-Webhook-Secret')
    
    # Se não tiver no header, tentar pegar da URL
    if not token:
        token = request.args.get('token')
    
    # Verificar se é localhost (permitir sem token para testes locais)
    is_localhost = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
    
    # Se for localhost e não tiver token, permitir
    if is_localhost and not token:
        logger.info('Acesso local sem token permitido')
        return True
    
    # Verificar o token
    if token == WEBHOOK_SECRET:
        return True
    
    logger.warning(f'Token inválido ou ausente de {request.remote_addr}')
    return False

# ============================================
# ENDPOINTS ESPECÍFICOS PARA CADA TIPO DE NOTIFICAÇÃO
# ============================================

@app.route('/airbyte/failed', methods=['POST'])
def airbyte_failed_sync():
    """Endpoint para sincronizações que falharam"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Failed Sync: {json.dumps(data, indent=2)}')
    
    # Extrair emails ou usar padrão
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    # Preparar informações
    info = process_airbyte_data(data, 'failed')
    
    # Enviar email com subject específico
    subject = f"🔴 [FALHA] Sincronização Airbyte - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'failed')
    
    return jsonify({'status': 'success', 'type': 'failed_sync'}), 200

@app.route('/airbyte/success', methods=['POST'])
def airbyte_successful_sync():
    """Endpoint para sincronizações bem-sucedidas"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Successful Sync: {json.dumps(data, indent=2)}')
    
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    info = process_airbyte_data(data, 'success')
    
    subject = f"✅ [SUCESSO] Sincronização Airbyte - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'success')
    
    return jsonify({'status': 'success', 'type': 'successful_sync'}), 200

@app.route('/airbyte/update', methods=['POST'])
def airbyte_connection_update():
    """Endpoint para atualizações de conexão"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Connection Update: {json.dumps(data, indent=2)}')
    
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    info = process_airbyte_data(data, 'update')
    
    subject = f"🔄 [ATUALIZAÇÃO] Conexão Airbyte - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'update')
    
    return jsonify({'status': 'success', 'type': 'connection_update'}), 200

@app.route('/airbyte/action-required', methods=['POST'])
def airbyte_action_required():
    """Endpoint para atualizações que requerem ação"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Action Required: {json.dumps(data, indent=2)}')
    
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    info = process_airbyte_data(data, 'action_required')
    
    subject = f"⚠️ [AÇÃO NECESSÁRIA] Airbyte - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'action_required')
    
    return jsonify({'status': 'success', 'type': 'action_required'}), 200

@app.route('/airbyte/warning', methods=['POST'])
def airbyte_warning():
    """Endpoint para avisos de falhas repetidas"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Warning: {json.dumps(data, indent=2)}')
    
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    info = process_airbyte_data(data, 'warning')
    
    subject = f"⚠️ [AVISO] Falhas Repetidas - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'warning')
    
    return jsonify({'status': 'success', 'type': 'warning'}), 200

@app.route('/airbyte/disabled', methods=['POST'])
def airbyte_sync_disabled():
    """Endpoint para sincronização desabilitada"""
    if not verify_token_from_url_or_header(request):
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.get_json(force=True)
    logger.info(f'Airbyte Sync Disabled: {json.dumps(data, indent=2)}')
    
    recipients = extract_emails_from_data(data)
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    
    info = process_airbyte_data(data, 'disabled')
    
    subject = f"🚫 [DESABILITADO] Sincronização Airbyte - {info['connection_name']} - {info['timestamp']}"
    send_airbyte_email(info, recipients, subject, 'disabled')
    
    return jsonify({'status': 'success', 'type': 'sync_disabled'}), 200

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def process_airbyte_data(data, event_type):
    """Processa dados do Airbyte e extrai informações relevantes"""
    info = {
        'event_type': event_type,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'raw_data': data
    }
    
    # Extrair nome da conexão
    if 'connection' in data:
        info['connection_name'] = data['connection'].get('name', 'Conexão Desconhecida')
        info['connection_id'] = data['connection'].get('connectionId', 'N/A')
        info['source'] = data['connection'].get('source', {}).get('name', 'N/A')
        info['destination'] = data['connection'].get('destination', {}).get('name', 'N/A')
    else:
        info['connection_name'] = data.get('connectionName', 'Conexão Desconhecida')
        info['connection_id'] = data.get('connectionId', 'N/A')
        info['source'] = data.get('sourceName', 'N/A')
        info['destination'] = data.get('destinationName', 'N/A')
    
    # Informações do job
    if 'job' in data:
        info['job_id'] = data['job'].get('jobId', 'N/A')
        info['job_status'] = data['job'].get('status', 'N/A')
        info['start_time'] = data['job'].get('startTime', 'N/A')
        info['end_time'] = data['job'].get('endTime', 'N/A')
    
    # Estatísticas
    if 'summary' in data:
        info['records_synced'] = data['summary'].get('recordsSynced', 0)
        info['bytes_synced'] = data['summary'].get('bytesSynced', 0)
        info['duration'] = data['summary'].get('duration', 'N/A')
    
    # Informações de erro
    if 'error' in data:
        info['error'] = data.get('error')
        info['error_message'] = data.get('errorMessage', data.get('error'))
    
    # Workspace
    info['workspace_id'] = data.get('workspaceId', 'N/A')
    
    return info

def send_airbyte_email(info, recipients, subject, event_type):
    """Envia email formatado para notificações do Airbyte"""
    
    # Escolher cor e emoji baseado no tipo
    colors = {
        'failed': ('#FF4444', '🔴'),
        'success': ('#44BB44', '✅'),
        'update': ('#4444FF', '🔄'),
        'action_required': ('#FFA500', '⚠️'),
        'warning': ('#FF8C00', '⚠️'),
        'disabled': ('#808080', '🚫')
    }
    
    color, emoji = colors.get(event_type, ('#666666', '📢'))
    
    # Formatar bytes
    def format_bytes(bytes_val):
        try:
            b = float(bytes_val)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if b < 1024.0:
                    return f"{b:.2f} {unit}"
                b /= 1024.0
        except:
            return str(bytes_val)
    
    # HTML do email
    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; margin: 0;">
        <div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            
            <!-- Header com cor específica do evento -->
            <div style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%); color: white; padding: 25px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">
                    {emoji} Notificação Airbyte
                </h1>
                <p style="margin: 10px 0 0 0; opacity: 0.95; font-size: 14px;">
                    {event_type.replace('_', ' ').title()}
                </p>
            </div>
            
            <!-- Informações principais -->
            <div style="padding: 25px;">
                
                <!-- Badge de status -->
                <div style="text-align: center; margin-bottom: 25px;">
                    <span style="display: inline-block; background: {color}15; color: {color}; padding: 8px 20px; border-radius: 20px; font-weight: 600; border: 2px solid {color}30;">
                        {event_type.upper().replace('_', ' ')}
                    </span>
                </div>
                
                <!-- Detalhes da conexão -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px;">📊 Detalhes da Conexão</h3>
                    
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Conexão:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{info.get('connection_name', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Origem:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{info.get('source', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Destino:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{info.get('destination', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Data/Hora:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{info.get('timestamp', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
                
                {f'''
                <!-- Estatísticas (se disponíveis) -->
                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px;">📈 Estatísticas da Sincronização</h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center;">
                        <div>
                            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Registros</div>
                            <div style="font-size: 24px; font-weight: bold; color: #333;">
                                {info.get('records_synced', 0):,}
                            </div>
                        </div>
                        <div>
                            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Dados</div>
                            <div style="font-size: 24px; font-weight: bold; color: #333;">
                                {format_bytes(info.get('bytes_synced', 0))}
                            </div>
                        </div>
                        <div>
                            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Duração</div>
                            <div style="font-size: 24px; font-weight: bold; color: #333;">
                                {info.get('duration', 'N/A')}
                            </div>
                        </div>
                    </div>
                </div>
                ''' if info.get('records_synced') or info.get('bytes_synced') else ''}
                
                {f'''
                <!-- Mensagem de erro (se houver) -->
                <div style="background: #ffebee; border: 1px solid #ffcdd2; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #c62828; font-size: 16px;">❌ Erro Detectado</h3>
                    <p style="margin: 0; color: #333; font-family: monospace; font-size: 13px;">
                        {info.get('error_message', 'Erro não especificado')}
                    </p>
                </div>
                ''' if info.get('error') or info.get('error_message') else ''}
                
                <!-- IDs técnicos -->
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 12px; color: #666;">
                    <strong>IDs Técnicos:</strong><br>
                    Connection ID: <code>{info.get('connection_id', 'N/A')}</code><br>
                    Job ID: <code>{info.get('job_id', 'N/A')}</code><br>
                    Workspace ID: <code>{info.get('workspace_id', 'N/A')}</code>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="background: #f5f5f5; padding: 15px; text-align: center; color: #666; font-size: 12px;">
                Notificação automática do Airbyte via Webhook<br>
                Configurado em: cazouvilela@gmail.com
            </div>
            
        </div>
    </body>
    </html>
    """
    
    # Criar e enviar mensagem
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_body
    )
    
    # Versão texto
    msg.body = f"""
    Notificação Airbyte - {event_type.replace('_', ' ').title()}
    
    Conexão: {info.get('connection_name', 'N/A')}
    Origem: {info.get('source', 'N/A')} → Destino: {info.get('destination', 'N/A')}
    Data/Hora: {info.get('timestamp', 'N/A')}
    
    {f"Registros: {info.get('records_synced', 0):,}" if info.get('records_synced') else ''}
    {f"Dados: {format_bytes(info.get('bytes_synced', 0))}" if info.get('bytes_synced') else ''}
    {f"Erro: {info.get('error_message', '')}" if info.get('error') else ''}
    
    IDs: Connection {info.get('connection_id', 'N/A')} | Job {info.get('job_id', 'N/A')}
    """
    
    mail.send(msg)
    logger.info(f'Email Airbyte [{event_type}] enviado para: {", ".join(recipients)}')

# ============================================
# ENDPOINT DE TESTE GERAL
# ============================================

@app.route('/test-airbyte-all', methods=['GET'])
def test_all_airbyte_endpoints():
    """Testa todos os endpoints do Airbyte"""
    results = []
    
    endpoints = [
        ('failed', '🔴 Falha na Sincronização'),
        ('success', '✅ Sincronização Bem-sucedida'),
        ('update', '🔄 Atualização de Conexão'),
        ('action-required', '⚠️ Ação Necessária'),
        ('warning', '⚠️ Aviso de Falhas'),
        ('disabled', '🚫 Sincronização Desabilitada')
    ]
    
    for endpoint, description in endpoints:
        results.append({
            'endpoint': f'/airbyte/{endpoint}',
            'description': description,
            'url_with_token': f'http://localhost:5000/airbyte/{endpoint}?token={WEBHOOK_SECRET}',
            'test_curl': f'curl -X POST "http://localhost:5000/airbyte/{endpoint}?token={WEBHOOK_SECRET}" -H "Content-Type: application/json" -d \'{{"test": true}}\''
        })
    
    return jsonify({
        'message': 'Endpoints disponíveis para Airbyte',
        'endpoints': results,
        'token_configured': bool(WEBHOOK_SECRET)
    })

