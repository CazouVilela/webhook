#!/usr/bin/env python3
"""
Webhook Server com Envio de Email
Servidor Flask que recebe webhooks e envia notificações por email
Suporta token no header ou URL para compatibilidade com Airbyte
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

# Email destinatário padrão
DEFAULT_RECIPIENT = os.getenv('DEFAULT_RECIPIENT_EMAIL', 'cazouvilela@gmail.com')

# Token de segurança
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'webhook_pessoal_secret_token')

def verify_token():
    """Verifica token do header OU da query string"""
    if not WEBHOOK_SECRET:
        return True
    
    # Tentar pegar do header primeiro
    token_header = request.headers.get('X-Webhook-Secret')
    
    # Se não tiver no header, tentar pegar da URL
    token_url = request.args.get('token')
    
    # Se for localhost, permitir sem token
    is_local = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
    
    # Verificar o token
    token = token_header or token_url
    
    if token == WEBHOOK_SECRET:
        return True
    elif is_local and not token:
        logger.info('Acesso local sem token permitido')
        return True
    else:
        logger.warning(f'Token inválido ou ausente de {request.remote_addr}')
        return False

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
    
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return emails
    
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
            if isinstance(value, str) and validate_email(value):
                emails.append(value)
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
                    'X-Webhook-Secret': 'seu-token-secreto (ou use ?token=seu-token na URL)'
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
            'airbyte_examples': {
                'failed': '/webhook/failed?token=seu-token',
                'success': '/webhook/success?token=seu-token',
                'update': '/webhook/update?token=seu-token'
            }
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal do webhook"""
    try:
        # Verificar token
        if not verify_token():
            return jsonify({'error': 'Não autorizado'}), 401
        
        # Obter dados do webhook
        data = request.get_json(force=True)
        
        # Log da requisição recebida
        logger.info(f'Webhook recebido: {json.dumps(data, indent=2)}')
        
        # Extrair emails de destino
        recipient_emails = extract_emails_from_data(data)
        if not recipient_emails:
            recipient_emails = [DEFAULT_RECIPIENT]
        
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
    """Endpoint do webhook com ação específica - Compatível com Airbyte"""
    try:
        # Verificar token (aceita header ou URL)
        if not verify_token():
            return jsonify({'error': 'Não autorizado'}), 401
        
        # Obter dados
        data = request.get_json(force=True)
        
        # Log da ação
        logger.info(f'Webhook com ação "{action}" recebido')
        logger.info(f'Dados: {json.dumps(data, indent=2)}')
        
        # Extrair emails de destino
        recipient_emails = extract_emails_from_data(data)
        if not recipient_emails:
            recipient_emails = [DEFAULT_RECIPIENT]
        
        # Mapear ações para emojis e labels (suporte ao Airbyte)
        action_map = {
            'failed': ('🔴', 'FALHA'),
            'success': ('✅', 'SUCESSO'),
            'update': ('🔄', 'ATUALIZAÇÃO'),
            'action-required': ('⚠️', 'AÇÃO NECESSÁRIA'),
            'warning': ('⚠️', 'AVISO'),
            'disabled': ('🚫', 'DESABILITADO'),
            # Ações customizadas
            'login': ('👤', 'LOGIN'),
            'pedido': ('🛒', 'PEDIDO'),
            'alerta': ('🚨', 'ALERTA'),
            'erro': ('❌', 'ERRO'),
            'info': ('ℹ️', 'INFO')
        }
        
        emoji, label = action_map.get(action, ('📢', action.upper()))
        
        # Extrair nome da conexão (para Airbyte)
        connection_name = ''
        if 'connection' in data:
            if isinstance(data['connection'], dict):
                connection_name = data['connection'].get('name', '')
            else:
                connection_name = str(data['connection'])
        
        # Preparar informações
        webhook_info = {
            'acao': action,
            'label': label,
            'emoji': emoji,
            'connection_name': connection_name,
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
        # Preparar assunto com suporte ao Airbyte
        if action:
            emoji = webhook_info.get('emoji', '📢')
            label = webhook_info.get('label', action.upper())
            connection = webhook_info.get('connection_name', '')
            
            if connection:
                subject = f'{emoji} [{label}] {connection} - {webhook_info["timestamp"]}'
            else:
                subject = f'{emoji} [{label}] Webhook - {webhook_info["timestamp"]}'
        else:
            subject = f'📢 [Webhook] Notificação - {webhook_info["timestamp"]}'
        
        # Determinar cor baseada na ação
        color_map = {
            'failed': '#FF4444',
            'success': '#44BB44', 
            'update': '#4444FF',
            'warning': '#FFA500',
            'disabled': '#808080',
            'alerta': '#FF6B6B',
            'erro': '#DC3545'
        }
        header_color = color_map.get(action, '#667eea')
        
        # Preparar corpo do email
        body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; margin: 0;">
            <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                
                <!-- Header com cor dinâmica -->
                <div style="background: linear-gradient(135deg, {header_color} 0%, {header_color}CC 100%); color: white; padding: 30px;">
                    <h1 style="margin: 0; font-size: 28px;">
                        {webhook_info.get('emoji', '🔔')} Notificação de Webhook
                    </h1>
                    {f'<p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.95;">Ação: {webhook_info.get("label", action)}</p>' if action else ''}
                    {f'<p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Conexão: {webhook_info.get("connection_name")}</p>' if webhook_info.get("connection_name") else ''}
                </div>
                
                <div style="padding: 30px;">
                    <!-- Informações Gerais -->
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">📊 Informações Gerais</h3>
                        <table style="width: 100%; font-size: 14px;">
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>📅 Data/Hora:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{webhook_info.get('timestamp')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>🌐 IP de Origem:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{webhook_info.get('ip_origem')}</td>
                            </tr>
                            {f'''<tr>
                                <td style="padding: 8px 0; color: #666;"><strong>⚡ Ação:</strong></td>
                                <td style="padding: 8px 0; color: #333; font-weight: bold;">{webhook_info.get("acao")}</td>
                            </tr>''' if webhook_info.get('acao') else ''}
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>📧 Enviado para:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{', '.join(webhook_info.get('destinatarios', []))}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Dados Recebidos -->
                    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">📦 Dados Recebidos</h3>
                        <pre style="background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 13px; max-height: 400px; overflow-y: auto;">
{json.dumps(dados_limpos, indent=2, ensure_ascii=False)}
                        </pre>
                    </div>
                    
                    <!-- Headers (colapsável) -->
                    <details style="margin-bottom: 20px;">
                        <summary style="cursor: pointer; color: #667eea; font-weight: bold; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                            🔧 Headers da Requisição (clique para expandir)
                        </summary>
                        <pre style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 10px; font-size: 12px; overflow-x: auto;">
{json.dumps(webhook_info.get('headers', {}), indent=2, ensure_ascii=False)}
                        </pre>
                    </details>
                    
                    <!-- Footer -->
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0 20px 0;">
                    
                    <p style="color: #888; font-size: 12px; text-align: center; margin: 0;">
                        Este é um email automático enviado pelo Webhook Server.<br>
                        Configurado por: cazouvilela@gmail.com
                    </p>
                </div>
                
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
        {'Conexão: ' + webhook_info.get('connection_name') if webhook_info.get('connection_name') else ''}
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
        # Permitir especificar email de teste
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

# ============================================
# ENDPOINTS PARA AIRBYTE - VERSÃO 2.0 MELHORADA
# ============================================

@app.route('/airbyte/<string:event_type>', methods=['POST', 'GET'])
def airbyte_universal(event_type):
    """
    Endpoint universal otimizado para Airbyte com emails detalhados
    Processa a estrutura oficial: workspace, connection, source, destination, métricas
    """
    try:
        # Log do método da requisição
        logger.info(f'Airbyte {event_type} - Method: {request.method}')

        # Para requisições GET (teste do Airbyte)
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'message': f'Webhook {event_type} está funcionando',
                'method': 'GET',
                'endpoint': f'/airbyte/{event_type}'
            }), 200

        # Para requisições POST
        # Verificar token apenas se configurado
        if WEBHOOK_SECRET:
            token = request.args.get('token') or request.headers.get('X-Webhook-Secret')
            is_local = request.remote_addr in ['127.0.0.1', 'localhost', '::1']

            if not is_local and token != WEBHOOK_SECRET:
                logger.warning(f'Token inválido de {request.remote_addr}')
                return jsonify({'status': 'success', 'note': 'token invalid'}), 200

        # Obter payload completo
        payload = request.get_json(silent=True) or {}
        logger.info(f'Payload Airbyte [{event_type}]: {json.dumps(payload, indent=2)}')

        # Extrair seção 'data' do payload do Airbyte
        data = payload.get('data', payload)

        # Determinar destinatários
        recipients = extract_emails_from_data(data) or [DEFAULT_RECIPIENT]

        # Processar e enviar email detalhado
        success_count = send_airbyte_detailed_email(event_type, data, recipients)

        logger.info(f'Email Airbyte [{event_type}] enviado para: {", ".join(recipients)}')

        return jsonify({
            'status': 'success',
            'event_type': event_type,
            'recipients': recipients,
            'emails_sent': success_count
        }), 200

    except Exception as e:
        logger.error(f'Erro no airbyte/{event_type}: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'status': 'success', 'error': str(e)}), 200


def send_airbyte_detailed_email(event_type, data, recipients):
    """
    Envia email detalhado e informativo para eventos do Airbyte
    Processa todos os campos do payload oficial do Airbyte
    """
    try:
        # Configuração de evento
        event_configs = {
            'failed': {
                'emoji': '🔴',
                'label': 'FALHA NA SINCRONIZAÇÃO',
                'color': '#DC3545',
                'priority': 'ALTA'
            },
            'success': {
                'emoji': '✅',
                'label': 'SINCRONIZAÇÃO CONCLUÍDA',
                'color': '#28A745',
                'priority': 'NORMAL'
            },
            'update': {
                'emoji': '🔄',
                'label': 'ATUALIZAÇÃO DE CONEXÃO',
                'color': '#17A2B8',
                'priority': 'MÉDIA'
            },
            'action-required': {
                'emoji': '⚠️',
                'label': 'AÇÃO NECESSÁRIA',
                'color': '#FFC107',
                'priority': 'ALTA'
            },
            'warning': {
                'emoji': '⚠️',
                'label': 'AVISO - FALHAS REPETIDAS',
                'color': '#FF6B6B',
                'priority': 'ALTA'
            },
            'disabled': {
                'emoji': '🚫',
                'label': 'SINCRONIZAÇÃO DESABILITADA',
                'color': '#6C757D',
                'priority': 'CRÍTICA'
            }
        }

        config = event_configs.get(event_type, {
            'emoji': '📢',
            'label': event_type.upper(),
            'color': '#6C757D',
            'priority': 'NORMAL'
        })

        # Extrair informações do payload
        workspace = data.get('workspace', {})
        connection = data.get('connection', {})
        source = data.get('source', {})
        destination = data.get('destination', {})

        # Informações do Job
        job_id = data.get('jobId', 'N/A')
        started_at = data.get('startedAt', 'N/A')
        finished_at = data.get('finishedAt', 'N/A')
        duration_formatted = data.get('durationFormatted', data.get('durationInSeconds', 'N/A'))

        # Métricas de dados
        records_emitted = data.get('recordsEmitted', 0)
        records_committed = data.get('recordsCommitted', 0)
        bytes_emitted = data.get('bytesEmittedFormatted', data.get('bytesEmitted', 'N/A'))
        bytes_committed = data.get('bytesCommittedFormatted', data.get('bytesCommitted', 'N/A'))

        # Status e erros
        success = data.get('success', True)
        error_message = data.get('errorMessage', '')
        error_type = data.get('errorType', '')
        error_origin = data.get('errorOrigin', '')

        # Preparar assunto do email
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        connection_name = connection.get('name', 'Conexão Desconhecida')
        subject = f"{config['emoji']} [{config['label']}] {connection_name} - {timestamp}"

        # Determinar se há perda de dados
        data_loss = ''
        if records_emitted > 0 and records_committed < records_emitted:
            loss_percentage = ((records_emitted - records_committed) / records_emitted) * 100
            data_loss = f"""
            <div style="background: #FFF3CD; border-left: 4px solid #FFC107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">⚠️ Perda de Dados Detectada</h4>
                <p style="margin: 0; color: #856404;">
                    <strong>{records_emitted - records_committed} registros</strong> não foram confirmados
                    ({loss_percentage:.1f}% de perda)
                </p>
            </div>
            """

        # Criar seção de erro detalhada (apenas para falhas)
        error_section = ''
        if event_type == 'failed' or not success or error_message:
            error_type_info = {
                'config_error': {
                    'icon': '⚙️',
                    'title': 'Erro de Configuração',
                    'description': 'Problema nas configurações da fonte ou destino',
                    'action': 'Verifique as credenciais e configurações de conexão'
                },
                'transient_error': {
                    'icon': '🔄',
                    'title': 'Erro Temporário',
                    'description': 'Problema temporário que pode se resolver automaticamente',
                    'action': 'Aguarde e monitore as próximas tentativas'
                },
                'system_error': {
                    'icon': '🖥️',
                    'title': 'Erro do Sistema',
                    'description': 'Problema interno do sistema Airbyte',
                    'action': 'Verifique os logs do Airbyte para mais detalhes'
                }
            }

            error_info = error_type_info.get(error_type, {
                'icon': '❌',
                'title': 'Erro Desconhecido',
                'description': 'Tipo de erro não classificado',
                'action': 'Verifique os logs para mais informações'
            })

            origin_text = ''
            if error_origin:
                origin_icon = '📥' if error_origin == 'source' else '📤'
                origin_name = source.get('name', 'Fonte') if error_origin == 'source' else destination.get('name', 'Destino')
                origin_text = f"""
                <tr>
                    <td style="padding: 10px; color: #666;"><strong>{origin_icon} Origem do Erro:</strong></td>
                    <td style="padding: 10px; color: #333;"><strong>{origin_name}</strong> ({error_origin})</td>
                </tr>
                """

            error_section = f"""
            <div style="background: #F8D7DA; border-left: 5px solid #DC3545; padding: 20px; margin: 25px 0; border-radius: 5px;">
                <h3 style="color: #721C24; margin-top: 0;">
                    {error_info['icon']} {error_info['title']}
                </h3>
                <table style="width: 100%; font-size: 14px;">
                    <tr>
                        <td style="padding: 10px; color: #666; width: 30%;"><strong>📝 Mensagem:</strong></td>
                        <td style="padding: 10px; color: #333; font-weight: bold;">{error_message or 'Erro sem mensagem específica'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; color: #666;"><strong>🏷️ Tipo de Erro:</strong></td>
                        <td style="padding: 10px; color: #333;">{error_type or 'Não especificado'}</td>
                    </tr>
                    {origin_text}
                    <tr>
                        <td style="padding: 10px; color: #666;"><strong>💡 Descrição:</strong></td>
                        <td style="padding: 10px; color: #555; font-style: italic;">{error_info['description']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; color: #666;"><strong>🔧 Ação Recomendada:</strong></td>
                        <td style="padding: 10px; color: #333; background: #FFF3CD; border-radius: 3px;">
                            {error_info['action']}
                        </td>
                    </tr>
                </table>
            </div>
            """

        # HTML do email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #F5F7FA;">
            <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

                <!-- Header -->
                <div style="background: linear-gradient(135deg, {config['color']} 0%, {config['color']}DD 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 32px;">
                        {config['emoji']} Airbyte Notification
                    </h1>
                    <h2 style="margin: 10px 0 0 0; font-size: 20px; font-weight: normal; opacity: 0.95;">
                        {config['label']}
                    </h2>
                    <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 16px; border-radius: 20px; margin-top: 15px;">
                        <span style="font-size: 14px; font-weight: bold;">Prioridade: {config['priority']}</span>
                    </div>
                </div>

                <div style="padding: 30px;">

                    <!-- Informações da Conexão -->
                    <div style="background: #F8F9FA; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid {config['color']};">
                        <h3 style="color: #333; margin-top: 0; display: flex; align-items: center;">
                            🔗 Informações da Conexão
                        </h3>
                        <table style="width: 100%; font-size: 14px;">
                            <tr>
                                <td style="padding: 8px 0; color: #666; width: 30%;"><strong>Nome:</strong></td>
                                <td style="padding: 8px 0; color: #333; font-weight: bold; font-size: 16px;">
                                    {connection.get('name', 'N/A')}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>📥 Fonte:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{source.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>📤 Destino:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{destination.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>🏢 Workspace:</strong></td>
                                <td style="padding: 8px 0; color: #333;">{workspace.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>🔢 Job ID:</strong></td>
                                <td style="padding: 8px 0; color: #333; font-family: monospace;">{job_id}</td>
                            </tr>
                        </table>

                        {f'''
                        <div style="margin-top: 15px; text-align: center;">
                            <a href="{connection.get('url', '#')}"
                               style="display: inline-block; background: {config['color']}; color: white; padding: 10px 20px;
                                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                                🔗 Ver Conexão no Airbyte
                            </a>
                        </div>
                        ''' if connection.get('url') else ''}
                    </div>

                    <!-- Seção de Erro (se houver) -->
                    {error_section}

                    <!-- Perda de Dados (se houver) -->
                    {data_loss}

                    <!-- Métricas de Sincronização -->
                    <div style="background: #E7F3FF; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <h3 style="color: #333; margin-top: 0;">📊 Métricas de Sincronização</h3>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="background: white; padding: 15px; border-radius: 5px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                <div style="color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 5px;">📝 Registros</div>
                                <div style="font-size: 28px; font-weight: bold; color: #007BFF; margin: 10px 0;">
                                    {records_committed:,}
                                </div>
                                <div style="color: #999; font-size: 12px;">
                                    de {records_emitted:,} emitidos
                                </div>
                            </div>

                            <div style="background: white; padding: 15px; border-radius: 5px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                <div style="color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 5px;">💾 Volume</div>
                                <div style="font-size: 28px; font-weight: bold; color: #28A745; margin: 10px 0;">
                                    {bytes_committed}
                                </div>
                                <div style="color: #999; font-size: 12px;">
                                    de {bytes_emitted} emitidos
                                </div>
                            </div>
                        </div>

                        <table style="width: 100%; font-size: 14px; background: white; border-radius: 5px; padding: 15px;">
                            <tr>
                                <td style="padding: 10px; color: #666;"><strong>⏰ Início:</strong></td>
                                <td style="padding: 10px; color: #333;">{started_at}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; color: #666;"><strong>✅ Término:</strong></td>
                                <td style="padding: 10px; color: #333;">{finished_at}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; color: #666;"><strong>⏱️ Duração:</strong></td>
                                <td style="padding: 10px; color: #333; font-weight: bold;">
                                    {duration_formatted if isinstance(duration_formatted, str) else f'{duration_formatted} segundos'}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; color: #666;"><strong>✔️ Status:</strong></td>
                                <td style="padding: 10px;">
                                    <span style="background: {'#D4EDDA' if success else '#F8D7DA'};
                                                 color: {'#155724' if success else '#721C24'};
                                                 padding: 5px 15px; border-radius: 15px; font-weight: bold;">
                                        {'✅ Sucesso' if success else '❌ Falha'}
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Links Rápidos -->
                    <div style="background: #FFF9E6; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #FFC107;">
                        <h3 style="color: #333; margin-top: 0;">🔗 Links Rápidos</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                            {f'<a href="{workspace.get("url", "#")}" style="flex: 1; min-width: 150px; background: white; color: #007BFF; padding: 12px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #007BFF; font-weight: bold;">🏢 Workspace</a>' if workspace.get('url') else ''}
                            {f'<a href="{source.get("url", "#")}" style="flex: 1; min-width: 150px; background: white; color: #28A745; padding: 12px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #28A745; font-weight: bold;">📥 Fonte</a>' if source.get('url') else ''}
                            {f'<a href="{destination.get("url", "#")}" style="flex: 1; min-width: 150px; background: white; color: #DC3545; padding: 12px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #DC3545; font-weight: bold;">📤 Destino</a>' if destination.get('url') else ''}
                        </div>
                    </div>

                    <!-- Payload Completo (colapsável) -->
                    <details style="margin: 25px 0;">
                        <summary style="cursor: pointer; color: #007BFF; font-weight: bold; padding: 15px; background: #F8F9FA; border-radius: 5px; border: 1px solid #DEE2E6;">
                            🔍 Payload Completo do Webhook (clique para expandir)
                        </summary>
                        <pre style="background: #F8F9FA; padding: 20px; border-radius: 5px; margin-top: 10px; font-size: 12px; overflow-x: auto; border: 1px solid #DEE2E6; max-height: 400px; overflow-y: auto;">
{json.dumps(data, indent=2, ensure_ascii=False)}
                        </pre>
                    </details>

                    <!-- Footer -->
                    <hr style="border: none; border-top: 2px solid #E9ECEF; margin: 30px 0 20px 0;">

                    <div style="text-align: center; color: #6C757D; font-size: 12px;">
                        <p style="margin: 5px 0;">
                            🤖 Notificação automática gerada por <strong>Airbyte Webhook Server</strong>
                        </p>
                        <p style="margin: 5px 0;">
                            📧 Configurado por: <strong>{app.config['MAIL_USERNAME']}</strong>
                        </p>
                        <p style="margin: 5px 0;">
                            🕐 Recebido em: <strong>{timestamp}</strong>
                        </p>
                    </div>

                </div>

            </div>
        </body>
        </html>
        """

        # Versão texto simples
        text_body = f"""
        {config['emoji']} AIRBYTE NOTIFICATION - {config['label']}
        Prioridade: {config['priority']}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CONEXÃO
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Nome: {connection.get('name', 'N/A')}
        Fonte: {source.get('name', 'N/A')}
        Destino: {destination.get('name', 'N/A')}
        Workspace: {workspace.get('name', 'N/A')}
        Job ID: {job_id}

        {'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' if error_message else ''}
        {'ERRO' if error_message else ''}
        {'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' if error_message else ''}
        {f'Mensagem: {error_message}' if error_message else ''}
        {f'Tipo: {error_type}' if error_type else ''}
        {f'Origem: {error_origin}' if error_origin else ''}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        MÉTRICAS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Registros: {records_committed:,} de {records_emitted:,}
        Volume: {bytes_committed} de {bytes_emitted}
        Duração: {duration_formatted}
        Status: {'Sucesso' if success else 'Falha'}

        Início: {started_at}
        Término: {finished_at}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Notificação automática do Airbyte Webhook Server
        Recebido em: {timestamp}
        """

        # Criar e enviar mensagem
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body
        )

        mail.send(msg)
        logger.info(f'Email detalhado do Airbyte enviado para: {", ".join(recipients)}')

        return len(recipients)

    except Exception as e:
        logger.error(f'Erro ao enviar email detalhado do Airbyte: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        raise


@app.route('/airbyte/test', methods=['GET', 'POST'])
def airbyte_test():
    """Endpoint de teste para o Airbyte"""
    return jsonify({
        'status': 'success',
        'message': 'Airbyte webhook test successful',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    }), 200

# FIM DOS ENDPOINTS DO AIRBYTE V2.0

if __name__ == '__main__':
    # Verificar configurações essenciais
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        logger.error('MAIL_USERNAME e MAIL_PASSWORD devem ser configurados!')
        logger.error('Verifique o arquivo .env')
        exit(1)
    
    # Mostrar configuração atual
    logger.info('=== Configuração do Webhook Server ===')
    logger.info(f'Email remetente: {app.config["MAIL_USERNAME"]}')
    logger.info(f'Servidor SMTP: {app.config["MAIL_SERVER"]}:{app.config["MAIL_PORT"]}')
    logger.info(f'Email padrão para notificações: {DEFAULT_RECIPIENT}')
    logger.info(f'Token de segurança configurado: {"Sim" if WEBHOOK_SECRET else "Não"}')
    logger.info('=====================================')
    
    # Iniciar servidor
    logger.info('Iniciando webhook server na porta 7000...')
    logger.info('Acesse http://localhost:7000 para verificar o status')
    logger.info('Use http://localhost:7000/help para ver a documentação')

    app.run(
        host='0.0.0.0',  # Escutar em todas as interfaces
        port=7000,        # Porta do webhook
        debug=False       # Mudar para True para desenvolvimento
    )
