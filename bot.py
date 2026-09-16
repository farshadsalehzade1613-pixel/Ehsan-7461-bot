import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک ویدیو از سایت مورد نظرت رو بفرست تا بررسی و دانلود کنم.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return
    
    msg = await update.message.reply_text("در حال استخراج اطلاعات ویدیو...")
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        loop = asyncio.get_running_loop()
        
        def get_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        info = await loop.run_in_executor(None, get_info)
        
        title = info.get('title', 'بدون عنوان')
        direct_url = info.get('url', '')
        filesize = info.get('filesize') or info.get('filesize_approx') or 0
        
        filesize_mb = filesize / (1024 * 1024) if filesize else 0
        
        if filesize_mb > 50 or filesize_mb == 0:
            text = (
                f"🎬 **عنوان:** {title}\n"
                f"📦 **حجم فایل:** {f'{filesize_mb:.1f} MB' if filesize_mb else 'نامشخص'}\n\n"
                f"⚠️ *حجم ویدیو بیش از ۵۰ مگابایت است.* برای دانلود از لینک مستقیم زیر استفاده کنید:\n\n"
                f"🔗 [برای دانلود مستقیم اینجا کلیک کنید]({direct_url})"
            )
            await msg.edit_text(text, parse_mode='Markdown', disable_web_page_preview=True)
            return

        await msg.edit_text("حجم ویدیو کمتر از ۵۰ مگابایت است. در حال دانلود و ارسال به تلگرام...")
        
        download_opts = {
            'format': 'best',
            'outtmpl': f'video_{update.message.message_id}.mp4',
            'max_filesize': 50 * 1024 * 1024,
        }
        
        def download():
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([url])
                
        await loop.run_in_executor(None, download)
        
        filename = f'video_{update.message.message_id}.mp4'
        
        await msg.edit_text("در حال آپلود ویدیو به تلگرام...")
        with open(filename, 'rb') as video:
            await update.message.reply_video(video=video, caption=f"🎬 {title}")
        
        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ خطا در پردازش لینک.\nجزئیات: {str(e)[:150]}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.run_polling()

if __name__ == "__main__":
    main()
