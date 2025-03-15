import requests
import json
import telegram
from telegram import InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from telegram.error import TimedOut
from http.server import BaseHTTPRequestHandler, HTTPServer

# Token do seu bot (já fornecido)
TOKEN = '7359248793:AAEOyPPaHPZvEICuHXtzlgViUO3VP-Ubv7U'

# Função para obter o URL do vídeo a partir da URL do TikTok
def obter_url_video(video_url):
    try:
        response = requests.get(video_url, timeout=60)  # Aumentando o timeout para 60 segundos
        if response.status_code == 200:
            data = response.json()  # Parse da resposta JSON
            file_url = data.get('fileUrl', None)  # Obtém o fileUrl da resposta
            return file_url
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a URL do vídeo: {e}")
        return None

# Função para processar a URL do TikTok e enviar o vídeo para o usuário
async def processar_video(update, context):
    url_tiktok = update.message.text  # Pega a URL inserida pelo usuário

    # Envia a mensagem informando que está processando
    await update.message.reply_text("⏳ Espera aí, estou fazendo o download e já te mando...")

    # URL da API Tikdown
    api_url = "https://tikdown.com/proxy.php"

    # Payload com a URL do TikTok
    payload = {
        'url': url_tiktok
    }

    # Cabeçalhos necessários
    headers = {
        'Referer': 'https://tikdown.com',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        # Enviar a requisição POST
        response = requests.post(api_url, data=payload, headers=headers, timeout=60)  # Aumentando o timeout para 60 segundos

        if response.status_code == 200:
            data = response.json()  # Parse da resposta JSON
            video_url = data['api']['mediaItems'][0]['mediaUrl']  # URL do vídeo

            # Obter a URL de download do vídeo
            file_url = obter_url_video(video_url)

            if file_url:
                # Baixar o vídeo diretamente
                video_response = requests.get(file_url, timeout=60)  # Aumentando o timeout para 60 segundos
                if video_response.status_code == 200:
                    # Criar um arquivo temporário para enviar
                    with open('video.mp4', 'wb') as video_file:
                        video_file.write(video_response.content)

                    try:
                        # Enviar o vídeo de volta para o usuário
                        with open('video.mp4', 'rb') as video_file:
                            await context.bot.send_video(chat_id=update.message.chat_id, video=InputFile(video_file))

                    except TimedOut:
                        await update.message.reply_text("Desculpe, o envio do vídeo está demorando mais do que o esperado. Tente novamente mais tarde.")
                    except Exception as e:
                        await update.message.reply_text(f"Erro ao enviar o vídeo: {e}")

                    # Deletar o arquivo temporário
                    os.remove('video.mp4')

                else:
                    await update.message.reply_text("Erro ao baixar o vídeo.")
            else:
                await update.message.reply_text("Erro ao obter a URL de download do vídeo.")
        else:
            await update.message.reply_text(f"Erro ao processar a URL. Código de status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Erro ao conectar à API: {e}")

# Função para configurar o bot
async def start(update, context):
    await update.message.reply_text("Olá! Envie uma URL do TikTok para baixar o vídeo.")

# Função principal para configurar o bot
def bot_main(request):
    application = Application.builder().token(TOKEN).build()

    # Manipuladores de comandos e mensagens
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_video))

    # Iniciar o bot
    application.run_polling()

    return "Bot is running"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Defina a lógica aqui para a Vercel quando o bot for acionado
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def do_POST(self):
        # Aqui você pode tratar as requisições POST se necessário para o Telegram
        self.send_response(200)
        self.end_headers()

def run(server_class=HTTPServer, handler_class=Handler):
    server_address = ('', 8080)
    httpd = server_class(server_address, handler_class)
    print('Running server...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
