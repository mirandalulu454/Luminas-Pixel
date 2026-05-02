import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, UnidentifiedImageError
import io
import os
from flask import Flask
from threading import Thread

# ==========================================
# 1. TRUCO ANTI-APAGADO (Página web escondida)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Luminas Pixel está en línea y monitoreando 24/7."

def run_server():
    # Render asigna un puerto dinámico a través de la variable de entorno PORT
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# ==========================================
# 2. CONFIGURACIÓN DEL BOT Y SEGURIDAD
# ==========================================
TOKEN = os.environ.get('TELEGRAM_TOKEN')

if not TOKEN:
    raise ValueError("❌ FATAL ERROR: No se encontró el TELEGRAM_TOKEN en las variables de entorno.")

bot = telebot.TeleBot(TOKEN)
FORMATOS_SALIDA = ['JPG', 'PNG', 'WEBP', 'PDF', 'BMP', 'TIFF', 'ICO', 'GIF']

# ==========================================
# 3. LÓGICA PRINCIPAL DE LUMINAS PIXEL
# ==========================================
@bot.message_handler(content_types=['photo', 'document'])
def handle_image(message):
    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id 
            file_name = "imagen_telegram.jpg" 
        else:
            file_id = message.document.file_id
            file_name = message.document.file_name

        msg_temp = bot.reply_to(message, "🔍 *Analizando estructura del archivo...*", parse_mode='Markdown')

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_stream = io.BytesIO(downloaded_file)
        
        try:
            img = Image.open(image_stream)
            formato_real = img.format if img.format else "Desconocido"
        except (IOError, UnidentifiedImageError):
            bot.edit_message_text("❌ El archivo enviado no es una imagen reconocible o está dañado.", chat_id=message.chat.id, message_id=msg_temp.message_id)
            return

        peso_mb = round(len(downloaded_file) / (1024 * 1024), 2)

        markup = InlineKeyboardMarkup(row_width=3)
        botones = [InlineKeyboardButton(text=f"A {fmt}", callback_data=f"convert_{fmt}") for fmt in FORMATOS_SALIDA]
        markup.add(*botones)

        texto_respuesta = (
            f"⚡ **Luminas Pixel - Listo**\n\n"
            f"📁 **Archivo:** `{file_name}`\n"
            f"👁️ **Formato Original:** `{formato_real}`\n"
            f"⚖️ **Peso:** `{peso_mb} MB`\n\n"
            f"👇 **Selecciona el formato de salida:**"
        )

        bot.edit_message_text(texto_respuesta, chat_id=message.chat.id, message_id=msg_temp.message_id, reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Error de lectura. Detalle: `{e}`", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('convert_'))
def callback_query(call):
    try:
        formato_destino = call.data.split('_')[1]
        
        bot.answer_callback_query(call.id, f"Procesando a {formato_destino}...")
        
        bot.edit_message_text(f"⏳ Ensamblando imagen en **{formato_destino}**...\n_Procesando en RAM..._", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id, 
                              parse_mode='Markdown')
        
        mensaje_original = call.message.reply_to_message
        
        if mensaje_original.content_type == 'photo':
            file_id = mensaje_original.photo[-1].file_id
            nombre_base = "luminas_pixel"
        else:
            file_id = mensaje_original.document.file_id
            nombre_base = mensaje_original.document.file_name.rsplit('.', 1)[0]
            
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        img_stream = io.BytesIO(downloaded_file)
        img = Image.open(img_stream)
        
        if formato_destino in ['JPG', 'JPEG', 'BMP']:
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255)) 
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3]) 
                else:
                    background.paste(img)
                img = background
                
        if formato_destino == 'ICO':
            img.thumbnail((256, 256))
            
        formato_guardado = 'JPEG' if formato_destino == 'JPG' else formato_destino
            
        output_stream = io.BytesIO()
        
        if formato_guardado == 'PDF':
            img.save(output_stream, format='PDF', resolution=100.0)
        else:
            img.save(output_stream, format=formato_guardado)
            
        output_stream.seek(0)
        nuevo_nombre = f"{nombre_base}.{formato_destino.lower()}"
        
        bot.send_document(chat_id=call.message.chat.id, 
                          document=(nuevo_nombre, output_stream),
                          reply_to_message_id=mensaje_original.message_id,
                          caption=f"✅ **Luminas Pixel**\nConversión a **{formato_destino}** completada.",
                          parse_mode='Markdown')
                          
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error interno en la conversión a {formato_destino}.\nDetalle: `{e}`",
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              parse_mode='Markdown')

# ==========================================
# 4. INICIO DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    # Primero encendemos la página web invisible
    keep_alive()
    print("🌐 Servidor web oculto encendido.")
    
    # Luego encendemos el bot de Telegram
    print("🤖 Luminas Pixel inicializado. Conectado a Telegram...")
    bot.polling(none_stop=True)