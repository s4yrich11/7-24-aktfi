from dotenv import load_dotenv
load_dotenv()

import os
import re
import asyncio
import discord
from discord.ext import commands
from flask import Flask, render_template, request, jsonify
import threading
from gtts import gTTS

# --- LOG KANALI ID AYARI ---
LOG_KANAL_ID = 1546166612695056486  # Örn: 112233445566778899

# Flask uygulaması (Render vb. platformlarda 7/24 açık kalması ve Web Paneli için)
app = Flask(__name__)

# Bot nesnesini global olarak tanımlıyoruz ki Flask içinden erişebilelim
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@app.route('/')
def home():
    # templates klasörü içindeki index.html dosyasını web paneli olarak gösterir
    return render_template('index.html')

# --- WEB PANELİNDEN BOT DURUMUNU GÜNCELLEME API ROTOSU ---
@app.route('/api/durum-guncelle', methods=['POST'])
def api_durum_guncelle():
    veri = request.json
    yeni_oyun = veri.get('oyun')
    if not yeni_oyun:
        return jsonify({"durum": "hata", "mesaj": "Oyun adı boş olamaz!"}), 400

    try:
        # Discord botunun ana döngüsüne (event loop) güvenli bir şekilde görev gönderiyoruz
        future = asyncio.run_coroutine_threadsafe(
            bot.change_presence(
                status=discord.Status.dnd,
                activity=discord.Game(name=yeni_oyun)
            ), 
            bot.loop
        )
        future.result(timeout=5) # 5 saniye içinde güncellenmesini bekler
        return jsonify({"durum": "basarili", "mesaj": f"Durum '{yeni_oyun}' olarak güncellendi!"})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), use_reloader=False)

threading.Thread(target=run_flask).start()

# --- KÜFÜR VE REKLAM ENGELLEME FİLTRESİ İÇİN KELİME LİSTESİ ---
YASAKLI_KELİMELER = ["küfür1", "küfür2", "orospu", "amk", "sik", "discord.gg/", "http://", "https://"]

# --- ORTAK LOG GÖNDERME FONKSİYONU ---
async def log_gonder(guild, mesaj):
    kanal = guild.get_channel(LOG_KANAL_ID)
    if kanal:
        try:
            await kanal.send(mesaj)
        except Exception:
            pass

@bot.event
async def on_ready():
    print(f"Bot basariyla giris yapti: {bot.user}")
    
    # Bot açıldığında otomatik olarak Rahatsız Etmeyin (DND) ve aktiviteyi ayarlar
    await bot.change_presence(
        status=discord.Status.dnd,  
        activity=discord.Game(name="/premium | V8.18")  
    )

@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick or before.global_name != after.global_name:
        target_name = after.nick if after.nick else after.name

        match = re.search(r"\b(\d{1,2})\b", target_name)
        if match:
            age = int(match.group(1))

            role_18_plus = discord.utils.get(after.guild.roles, name="╭───𒌋𒀖 「🜲・ +18 ÜSTÜNDE」")
            role_18_minus = discord.utils.get(after.guild.roles, name="╭───𒌋𒀖 「🜲・+18 ALTINDA」")

            try:
                if age >= 18:
                    if role_18_plus and role_18_plus not in after.roles:
                        await after.add_roles(role_18_plus)
                    if role_18_minus and role_18_minus in after.roles:
                        await after.remove_roles(role_18_minus)
                else:
                    if role_18_minus and role_18_minus not in after.roles:
                        await after.add_roles(role_18_minus)
                    if role_18_plus and role_18_plus in after.roles:
                        await after.remove_roles(role_18_plus)
            except discord.Forbidden:
                print(f"Yetki Hatasi: Rol degistirme yetkim yok.")
            except discord.HTTPException as e:
                print(f"Hata olustu: {e}")

# --- OTOMATİK KÜFÜR VE REKLAM FİLTRESİ ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Küfür ve Reklam Kontrolü
    if not message.author.guild_permissions.administrator:
        content_lower = message.content.lower()
        for kelime in YASAKLI_KELİMELER:
            if kelime in content_lower:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, bu sunucuda küfür veya reklam paylaşmak yasaktır!", delete_after=5)
                    # Log kanalına bildir
                    await log_gonder(message.guild, f"⚠️ **Filtre Yakaladı!** | Kullanıcı: {message.author.mention} | Kanal: {message.channel.mention} | Mesaj: `{message.content}`")
                    return
                except discord.Forbidden:
                    pass
                break

    await bot.process_commands(message)


# --- BOTA SES KANALINDAN KONUŞTURMA KOMUTLARI ---

@bot.command()
@commands.has_permissions(administrator=True)
async def seskonus(ctx, *, metin: str):
    """Bot bulunduğun ses kanalına gelir ve yazdığın metni sesli olarak okur."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Önce herhangi bir ses kanalına girmelisin!")
        return

    kanal = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(kanal)
    else:
        await kanal.connect()

    try:
        tts = gTTS(text=metin, lang='tr', slow=False)
        ses_dosyasi = "konusma.mp3"
        tts.save(ses_dosyasi)

        source = discord.FFmpegPCMAudio(ses_dosyasi)
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(source, after=lambda e: os.remove(ses_dosyasi) if os.path.exists(ses_dosyasi) else None)
            await ctx.message.delete()
            await log_gonder(ctx.guild, f"🔊 **Sesli Okuma Yapıldı** | Yetkili: {ctx.author.mention} | Metin: `{metin}`")
        else:
            await ctx.send("⚠️ Zaten şu an bir şey okuyorum, bitmesini bekleyin.")
    except Exception as e:
        await ctx.send(f"❌ Sesli okuma sırasında bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ayril(ctx):
    """Botun ses kanalından çıkmasını sağlar."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Ses kanalından ayrıldım.")
    else:
        await ctx.send("❌ Zaten bir ses kanalında değilim.")


# --- DİĞER KOMUTLAR ---

@bot.command()
@commands.has_permissions(administrator=True)
async def durum(ctx, *, oyun_adi: str):
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=oyun_adi))
    await ctx.send(f"✅ Botun durumu başarıyla **{oyun_adi}** olarak güncellendi!")

# --- YETKİ YOK HATASI YÖNETİMİ ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanabilmek için gerekli yetkiye sahip olmalısın!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Eksik argüman girdin! Lütfen komutun kullanımını kontrol et.")


bot.run(os.getenv("DISCORD_TOKEN"))