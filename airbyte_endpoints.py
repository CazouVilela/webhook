#!/usr/bin/env python3
"""
Endpoints Airbyte V2 - Processamento Detalhado de Webhooks
Versão otimizada para emails informativos com base na estrutura oficial do Airbyte
"""

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
            <div style="background: #FFF3CD; border-left: 4px solid #FFC107; padding: 12px; margin: 15px 0; border-radius: 6px;">
                <h4 style="margin: 0 0 8px 0; color: #856404; font-size: 14px;">⚠️ Perda de Dados Detectada</h4>
                <p style="margin: 0; color: #856404; font-size: 13px;">
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
                    <td style="padding: 6px; color: #666;"><strong>{origin_icon} Origem:</strong></td>
                    <td style="padding: 6px; color: #333;"><strong>{origin_name}</strong> ({error_origin})</td>
                </tr>
                """

            error_section = f"""
            <div style="background: #F8D7DA; border-left: 4px solid #DC3545; padding: 15px; margin: 15px 0; border-radius: 6px;">
                <h3 style="color: #721C24; margin-top: 0; font-size: 16px;">
                    {error_info['icon']} {error_info['title']}
                </h3>
                <table style="width: 100%; font-size: 13px;">
                    <tr>
                        <td style="padding: 6px; color: #666; width: 35%;"><strong>📝 Mensagem:</strong></td>
                        <td style="padding: 6px; color: #333; font-weight: bold; word-break: break-word;">{error_message or 'Erro sem mensagem específica'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px; color: #666;"><strong>🏷️ Tipo:</strong></td>
                        <td style="padding: 6px; color: #333;">{error_type or 'Não especificado'}</td>
                    </tr>
                    {origin_text}
                    <tr>
                        <td style="padding: 6px; color: #666;"><strong>💡 Descrição:</strong></td>
                        <td style="padding: 6px; color: #555; font-style: italic; font-size: 12px;">{error_info['description']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px; color: #666;"><strong>🔧 Ação:</strong></td>
                        <td style="padding: 6px; color: #333; background: #FFF3CD; border-radius: 3px; font-size: 12px;">
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
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 8px; background: #F5F7FA;">
            <div style="max-width: 650px; width: 100%; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

                <!-- Header -->
                <div style="background: linear-gradient(135deg, {config['color']} 0%, {config['color']}DD 100%); color: white; padding: 20px 15px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">
                        {config['emoji']} Airbyte Notification
                    </h1>
                    <h2 style="margin: 8px 0 0 0; font-size: 16px; font-weight: normal; opacity: 0.95;">
                        {config['label']}
                    </h2>
                    <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 6px 12px; border-radius: 15px; margin-top: 12px;">
                        <span style="font-size: 12px; font-weight: bold;">Prioridade: {config['priority']}</span>
                    </div>
                </div>

                <div style="padding: 15px;">

                    <!-- Informações da Conexão -->
                    <div style="background: #F8F9FA; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid {config['color']};">
                        <h3 style="color: #333; margin-top: 0; font-size: 16px;">
                            🔗 Informações da Conexão
                        </h3>
                        <table style="width: 100%; font-size: 13px;">
                            <tr>
                                <td style="padding: 6px 0; color: #666; width: 35%;"><strong>Nome:</strong></td>
                                <td style="padding: 6px 0; color: #333; font-weight: bold; font-size: 14px;">
                                    {connection.get('name', 'N/A')}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #666;"><strong>📥 Fonte:</strong></td>
                                <td style="padding: 6px 0; color: #333;">{source.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #666;"><strong>📤 Destino:</strong></td>
                                <td style="padding: 6px 0; color: #333;">{destination.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #666;"><strong>🏢 Workspace:</strong></td>
                                <td style="padding: 6px 0; color: #333;">{workspace.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #666;"><strong>🔢 Job ID:</strong></td>
                                <td style="padding: 6px 0; color: #333; font-family: monospace; font-size: 11px; word-break: break-all;">{job_id}</td>
                            </tr>
                        </table>

                        {f'''
                        <div style="margin-top: 12px; text-align: center;">
                            <a href="{connection.get('url', '#')}"
                               style="display: inline-block; background: {config['color']}; color: white; padding: 8px 16px;
                                      text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 13px;">
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
                    <div style="background: #E7F3FF; padding: 15px; border-radius: 6px; margin: 15px 0;">
                        <h3 style="color: #333; margin-top: 0; font-size: 16px;">📊 Métricas de Sincronização</h3>

                        <table style="width: 100%; margin-bottom: 12px;" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="width: 48%; padding-right: 2%;">
                                    <div style="background: white; padding: 12px; border-radius: 5px; text-align: center;">
                                        <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 5px;">📝 Registros</div>
                                        <div style="font-size: 22px; font-weight: bold; color: #007BFF; margin: 8px 0;">
                                            {records_committed:,}
                                        </div>
                                        <div style="color: #999; font-size: 11px;">
                                            de {records_emitted:,} emitidos
                                        </div>
                                    </div>
                                </td>
                                <td style="width: 48%; padding-left: 2%;">
                                    <div style="background: white; padding: 12px; border-radius: 5px; text-align: center;">
                                        <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 5px;">💾 Volume</div>
                                        <div style="font-size: 22px; font-weight: bold; color: #28A745; margin: 8px 0;">
                                            {bytes_committed}
                                        </div>
                                        <div style="color: #999; font-size: 11px;">
                                            de {bytes_emitted} emitidos
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </table>

                        <table style="width: 100%; font-size: 13px; background: white; border-radius: 5px; padding: 10px;">
                            <tr>
                                <td style="padding: 6px; color: #666; width: 35%;"><strong>⏰ Início:</strong></td>
                                <td style="padding: 6px; color: #333; font-size: 12px;">{started_at}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px; color: #666;"><strong>✅ Término:</strong></td>
                                <td style="padding: 6px; color: #333; font-size: 12px;">{finished_at}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px; color: #666;"><strong>⏱️ Duração:</strong></td>
                                <td style="padding: 6px; color: #333; font-weight: bold;">
                                    {duration_formatted if isinstance(duration_formatted, str) else f'{duration_formatted} segundos'}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 6px; color: #666;"><strong>✔️ Status:</strong></td>
                                <td style="padding: 6px;">
                                    <span style="background: {'#D4EDDA' if success else '#F8D7DA'};
                                                 color: {'#155724' if success else '#721C24'};
                                                 padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 12px;">
                                        {'✅ Sucesso' if success else '❌ Falha'}
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Links Rápidos -->
                    <div style="background: #FFF9E6; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #FFC107;">
                        <h3 style="color: #333; margin-top: 0; font-size: 16px;">🔗 Links Rápidos</h3>
                        <table style="width: 100%;" cellpadding="5" cellspacing="0">
                            {f'<tr><td><a href="{workspace.get("url", "#")}" style="display: block; background: white; color: #007BFF; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #007BFF; font-weight: bold; font-size: 13px;">🏢 Workspace</a></td></tr>' if workspace.get('url') else ''}
                            {f'<tr><td><a href="{source.get("url", "#")}" style="display: block; background: white; color: #28A745; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #28A745; font-weight: bold; font-size: 13px;">📥 Fonte</a></td></tr>' if source.get('url') else ''}
                            {f'<tr><td><a href="{destination.get("url", "#")}" style="display: block; background: white; color: #DC3545; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; border: 2px solid #DC3545; font-weight: bold; font-size: 13px;">📤 Destino</a></td></tr>' if destination.get('url') else ''}
                        </table>
                    </div>

                    <!-- Payload Completo (colapsável) -->
                    <details style="margin: 15px 0;">
                        <summary style="cursor: pointer; color: #007BFF; font-weight: bold; padding: 12px; background: #F8F9FA; border-radius: 5px; border: 1px solid #DEE2E6; font-size: 13px;">
                            🔍 Payload Completo (clique para expandir)
                        </summary>
                        <pre style="background: #F8F9FA; padding: 12px; border-radius: 5px; margin-top: 8px; font-size: 10px; overflow-x: auto; border: 1px solid #DEE2E6; max-height: 300px; overflow-y: auto;">
{json.dumps(data, indent=2, ensure_ascii=False)}
                        </pre>
                    </details>

                    <!-- Footer -->
                    <hr style="border: none; border-top: 1px solid #E9ECEF; margin: 20px 0 15px 0;">

                    <div style="text-align: center; color: #6C757D; font-size: 11px;">
                        <p style="margin: 4px 0;">
                            🤖 Notificação automática gerada por <strong>Airbyte Webhook Server</strong>
                        </p>
                        <p style="margin: 4px 0;">
                            📧 Configurado por: <strong>{app.config['MAIL_USERNAME']}</strong>
                        </p>
                        <p style="margin: 4px 0;">
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
