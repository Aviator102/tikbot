import requests
import json
import telegram
from telegram import InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut
import os

TOKEN = '7359248793:AAEOyPPaHPZvEICuHXtzlgViUO3VP-Ubv7U'

def obter_url_video(video_url):
    try:
        response = requests.get(video_url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            file_url = data.get('fileUrl', None)
            return file_url
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a URL do vídeo: {e}")
        return None

async def processar_video(update, context):
    url_tiktok = update.message.text
    await update.message.reply_text("⏳ Espera aí, estou fazendo o download e já te mando...")
    api_url = "https://tikdown.com/proxy.php"
    payload = {'url': url_tiktok}
    headers = {'Referer': 'https://tikdown.com', 'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(api_url, data=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            video_url = data['api']['mediaItems'][0]['mediaUrl']
            file_url = obter_url_video(video_url)
            if file_url:
                video_response = requests.get(file_url, timeout=60)
                if video_response.status_code == 200:
                    with open('video.mp4', 'wb') as video_file:
                        video_file.write(video_response.content)
                    try:
                        with open('video.mp4', 'rb') as video_file:
                            await context.bot.send_video(chat_id=update.message.chat_id, video=InputFile(video_file))
                    except TimedOut:
                        await update.message.reply_text("Desculpe, o envio do vídeo está demorando mais do que o esperado. Tente novamente mais tarde.")
                    except Exception as e:
                        await update.message.reply_text(f"Erro ao enviar o vídeo: {e}")
                    os.remove('video.mp4')
                else:
                    await update.message.reply_text("Erro ao baixar o vídeo.")
            else:
                await update.message.reply_text("Erro ao obter a URL de download do vídeo.")
        else:
            await update.message.reply_text(f"Erro ao processar a URL. Código de status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Erro ao conectar à API: {e}")

async def start(update, context):
    await update.message.reply_text("Olá! Envie uma URL do TikTok para baixar o vídeo.")

def handler(request):
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_video))
    return "Bot está rodando."
