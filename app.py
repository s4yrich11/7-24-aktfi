from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
import asyncio
import discord
from discord.ext import commands
from flask import Flask
import threading
from gtts import gTTS

# --- LOG KANALI ID AYARI ---
LOG_KANAL_ID = 1546166612695056486  # Sunucudaki log kanal ID'si

# --- XP VE SEVİYE SİSTEMİ DOSYA VE ROL AYARLARI ---
XP_FILE = "xp.json"

# Seviyelere göre verilecek rollerin ID sözlüğü (Sunucundaki gerçek rol ID'leri ile değiştirmelisin)
LEVEL_ROLES = {
    5: 1546166452103684166,   # 5. seviye olunca verilecek rol ID
    10: 1546166450924953620,  # 10. seviye olunca verilecek rol ID
    15: 1546166449796808756,   # 15. seviye olunca verilecek rol ID
    20: 1546166447393480804,   # 20. seviye olunca verilecek rol ID
    25: 1546166441609265294,   # 25. seviye olunca verilecek rol ID
    30: 1546166440384659558,   # 30. seviye olunca verilecek rol ID
    35: 1546166439050739784,   # 35. seviye olunca verilecek rol ID
    40: 1546166436085501964,   # 40. seviye olunca verilecek rol ID
    45: 1546166433736556606,   # 45. seviye olunca verilecek rol ID
    50: 1546166432482725898,   # 50. seviye olunca verilecek rol ID
    55: 1546166431039750216,   # 55. seviye olunca verilecek rol ID
    60: 1546166429907419167,   # 60. seviye olunca verilecek rol ID
    65: 1546166429299118140,   # 65. seviye olunca verilecek rol ID
    70: 1546166427520729158,   # 70. seviye olunca verilecek rol ID
    75: 1546166425708920914,   # 75. seviye olunca verilecek rol ID
    80: 1546166421376208926,   # 80. seviye olunca verilecek rol ID
    85: 1546166419559813262,   # 85. seviye olunca verilecek rol ID
    90: 1546166418360246393,   # 90. seviye olunca verilecek rol ID
    95: 1546166417244684338,   # 95. seviye olunca verilecek rol ID
  100: 1546166415948521612,   # 100. seviye olunca verilecek rol ID


}

def load_xp():
    if os.path.exists(XP_FILE):
        with open(XP_FILE, "r") as f:
            return json.load(f)
    return {}

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def check_and_reward_role(message, current_level):
    """Kullanıcının seviyesine uygun bir rol ödülü olup olmadığını kontrol eder ve ekler."""
    if current_level in LEVEL_ROLES:
        role_id = LEVEL_ROLES[current_level]
        role = message.guild.get_role(role_id)
        
        if role and role not in message.author.roles:
            try:
                await message.author.add_roles(role)
                await message.channel.send(
                    f"🎉 Tebrikler {message.author.mention}! **{current_level}. Seviyeye** ulaştın ve {role.mention} rolünü kazandın!"
                )
            except discord.Forbidden:
                print("Botun bu üyeye rol vermek için yeterli yetkisi yok (Botun rolü ödül rolünden üstte olmalı).")
            except discord.HTTPException:
                print("Rol verme sırasında bir hata oluştu.")


# Flask uygulaması (Render vb. platformlarda 7/24 açık kalması için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run).start()

# Bot nesnesini tüm intent'lerle başlatıyoruz (Mesaj içeriği ve üyeler dahil)
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

# --- BİRLEŞTİRİLMİŞ ON_MESSAGE (FİLTRE + XP SİSTEMİ) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # 1. Küfür ve Reklam Kontrolü
    if not message.author.guild_permissions.administrator:
        content_lower = message.content.lower()
        for kelime in YASAKLI_KELİMELER:
            if kelime in content_lower:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, bu sunucuda küfür veya reklam paylaşmak yasaktır!", delete_after=5)
                    await log_gonder(message.guild, f"⚠️ **Filtre Yakaladı!** | Kullanıcı: {message.author.mention} | Kanal: {message.channel.mention} | Mesaj: `{message.content}`")
                    return
                except discord.Forbidden:
                    pass
                break

    # 2. XP ve Seviye Sistemi İşleyicisi
    xp_data = load_xp()
    user_id = str(message.author.id)

    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "level": 1}

    # Her mesaj başına 10 XP kazandır
    xp_data[user_id]["xp"] += 10
    current_xp = xp_data[user_id]["xp"]
    current_level = xp_data[user_id]["level"]

    # Her 100 XP'de bir seviye atlama eşiği
    next_threshold = current_level * 500
    if current_xp >= next_threshold:
        xp_data[user_id]["level"] += 1
        new_level = xp_data[user_id]["level"]
        
        await message.channel.send(f"🚀 Tebrikler {message.author.mention}, seviye atladın ve **{new_level}. seviye** oldun!")
        
        # Seviye rol ödülünü kontrol et
        await check_and_reward_role(message, new_level)

    save_xp(xp_data)

    # 3. Komutların çalışabilmesi için zorunlu satır
    await bot.process_commands(message)


# --- SEVİYE VE LADERBOARD KOMUTLARI ---

@bot.command(name="level", aliases=["seviye"], help="Kullanıcının mevcut seviyesini ve XP'sini gösterir.")
async def level_command(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)

    xp_data = load_xp()

    if user_id not in xp_data:
        await ctx.send(f"{target.name} henüz hiç XP kazanmamış!")
        return

    data = xp_data[user_id]
    current_xp = data["xp"]
    current_level = data["level"]
    next_level_xp = current_level * 100

    embed = discord.Embed(
        title=f"📊 {target.name} - Seviye Bilgisi",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Seviye", value=str(current_level), inline=True)
    embed.add_field(name="Toplam XP", value=str(current_xp), inline=True)
    embed.add_field(name="Sonraki Seviye", value=f"{current_xp} / {next_level_xp} XP", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["top", "siralama"], help="Sunucudaki en yüksek seviyeli kullanıcıları listeler.")
async def leaderboard_command(ctx):
    xp_data = load_xp()

    if not xp_data:
        await ctx.send("Henüz kayıtlı XP verisi bulunmuyor!")
        return

    # Toplam XP'ye göre büyükten küçüğe sırala
    sorted_users = sorted(xp_data.items(), key=lambda item: item[1]["xp"], reverse=True)
    top_users = sorted_users[:10]  # İlk 10 kişi

    embed = discord.Embed(
        title=f"🏆 {ctx.guild.name} - Seviye Sıralaması",
        color=discord.Color.gold(),
    )

    description = ""
    for index, (user_id, data) in enumerate(top_users, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.name if member else f"Kullanıcı ({user_id})"

        medal = "👑" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
        description += f"{medal} **{name}** — Seviye: `{data['level']}` | Toplam XP: `{data['xp']}`\n"

    embed.description = description
    embed.set_footer(text=f"Komutu kullanan: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)


# --- BOT ÜZERİNDEN BAŞKA KANALA YAZI YAZMA KOMUTU ---

@bot.command()
@commands.has_permissions(administrator=True)
async def yaz(ctx, kanal: discord.TextChannel, *, mesaj: str):
    """Belirttiğin kanala, senin komutunu silerek bot üzerinden mesaj gönderir."""
    try:
        await ctx.message.delete()
        await kanal.send(mesaj)
        await log_gonder(ctx.guild, f"📝 **Bot ile Mesaj Gönderildi** | Yetkili: {ctx.author.mention} | Hedef Kanal: {kanal.mention}")
    except discord.Forbidden:
        await ctx.send("❌ Belirtilen kanala mesaj göndermek veya mesaj silmek için yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")


# --- BOTA SES KANALINDAN KONUŞTURMA KOMUTLARI ---

YETKILI_IDLERI = [852839991297966112,1541880841993588760] 

async def id_kontrolu(ctx):
    return ctx.author.id in YETKILI_IDLERI

@bot.command()
@commands.check(id_kontrolu)
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
@commands.check(id_kontrolu)
async def ayril(ctx):
    """Botun ses kanalından çıkmasını sağlar."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Ses kanalından ayrıldım.")
    else:
        await ctx.send("❌ Zaten bir ses kanalında değilim.")

# --- BOT DURUMUNU DEĞİŞTİRME KOMUTU ---

@bot.command()
@commands.has_permissions(administrator=True)
async def durum(ctx, *, oyun_adi: str):
    """Botun oynuyor / durum mesajını anlık olarak değiştirir."""
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name=oyun_adi)
    )
    await ctx.send(f"✅ Botun durumu başarıyla **{oyun_adi}** olarak güncellendi!")


# --- ROL VERME VE ALMA KOMUTLARI ---

@bot.command()
@commands.has_permissions(administrator=True)
async def rolver(ctx, member: discord.Member, *, role_identifier: str):
    role = discord.utils.get(ctx.guild.roles, mention=role_identifier) or \
           discord.utils.get(ctx.guild.roles, name=role_identifier) or \
           ctx.guild.get_role(int(role_identifier[3:-1]) if role_identifier.startswith("<@&") and role_identifier.endswith(">") else 0)

    if not role:
        await ctx.send("Belirtilen rol bulunamadı. Lütfen rol adını veya etiketini doğru yaz.")
        return

    if role in member.roles:
        await ctx.send(f"{member.mention} zaten {role.name} rolüne sahip.")
        return
    
    try:
        await member.add_roles(role)
        await ctx.send(f"Başarılı! {member.mention} adlı kullanıcıya {role.name} rolü verildi.")
        await log_gonder(ctx.guild, f"➕ **Rol Verildi** | Kullanıcı: {member.mention} | Rol: {role.name} | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("Bu rolü vermek için yeterli yetkim yok veya rol benim rolümden üstte.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def rolal(ctx, member: discord.Member, *, role_identifier: str):
    role = discord.utils.get(ctx.guild.roles, mention=role_identifier) or \
           discord.utils.get(ctx.guild.roles, name=role_identifier) or \
           ctx.guild.get_role(int(role_identifier[3:-1]) if role_identifier.startswith("<@&") and role_identifier.endswith(">") else 0)

    if not role:
        await ctx.send("Belirtilen rol bulunamadı. Lütfen rol adını veya etiketini doğru yaz.")
        return

    if role not in member.roles:
        await ctx.send(f"{member.mention} zaten {role.name} rolüne sahip değil.")
        return
    
    try:
        await member.remove_roles(role)
        await ctx.send(f"Başarılı! {member.mention} adlı kullanıcıdan {role.name} rolü alındı.")
        await log_gonder(ctx.guild, f"➖ **Rol Alındı** | Kullanıcı: {member.mention} | Rol: {role.name} | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("Bu rolü almak için yeterli yetkim yok veya rol benim rolümden üstte.")
    except discord.HTTPException as e:
        await ctx.send(f"Hata oluştu: {e}")


# --- SES KANALI İŞLEMLERİ (SÜRELİ) ---

@bot.command()
@commands.has_permissions(administrator=True)
async def sestsustur(ctx, member: discord.Member, sure: str = None, *, neden="Belirtilmedi"):
    """Kullanıcıyı ses kanalında süreli veya süresiz susturur (Server Mute)."""
    if not member.voice:
        await ctx.send(f"{member.mention} bir ses kanalında değil.")
        return

    seconds = 0
    if sure:
        unit = sure[-1].lower()
        num = sure[:-1]
        if num.isdigit():
            num = int(num)
            if unit == 's':
                seconds = num
            elif unit == 'm':
                seconds = num * 60
            elif unit == 'h':
                seconds = num * 3600
            elif unit == 'd':
                seconds = num * 86400

    try:
        await member.edit(mute=True, reason=neden)
        if seconds > 0:
            await ctx.send(f"🔇 **{member.display_name}** ses kanalında **{sure}** süreyle susturuldu. Neden: `{neden}`")
            await log_gonder(ctx.guild, f"🔇 **Ses Susturma (Süreli)** | Kullanıcı: {member.mention} | Süre: {sure} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
            await asyncio.sleep(seconds)
            if member.voice and member.voice.mute:
                await member.edit(mute=False)
                await ctx.send(f"🔊 Ses süresi doldu! **{member.display_name}** adlı kullanıcının ses susturması otomatik olarak kaldırıldı.")
        else:
            await ctx.send(f"🔇 **{member.display_name}** ses kanalında süresiz susturuldu. Neden: `{neden}`")
            await log_gonder(ctx.guild, f"🔇 **Ses Susturma (Süresiz)** | Kullanıcı: {member.mention} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")

    except discord.Forbidden:
        await ctx.send("Kullanıcıyı susturmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def sestsusturac(ctx, member: discord.Member):
    """Kullanıcının ses kanalındaki susturmasını kaldırır (Server Unmute)."""
    if not member.voice:
        await ctx.send(f"{member.mention} bir ses kanalında değil.")
        return

    try:
        await member.edit(mute=False)
        await ctx.send(f"🔊 **{member.display_name}** adlı kullanıcının ses susturması kaldırıldı.")
        await log_gonder(ctx.guild, f"🔊 **Ses Susturma Kaldırıldı** | Kullanıcı: {member.mention} | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("Kullanıcının susturmasını kaldırmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def sesat(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı ses kanalından atar (Disconnect)."""
    if not member.voice:
        await ctx.send(f"{member.mention} herhangi bir ses kanalında değil.")
        return

    try:
        await member.move_to(None, reason=neden)
        await ctx.send(f"👢 **{member.display_name}** ses kanalından atıldı. Neden: `{neden}`")
        await log_gonder(ctx.guild, f"👢 **Ses Kanalından Atıldı** | Kullanıcı: {member.mention} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("Kullanıcıyı ses kanalından atmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")


# --- METİN KANALI İŞLEMLERİ (SÜRELİ) ---

@bot.command()
@commands.has_permissions(administrator=True)
async def metinsustur(ctx, member: discord.Member, sure: str = None, *, neden="Belirtilmedi"):
    """Kullanıcıyı süreli veya süresiz metin kanallarında susturur."""
    role = discord.utils.get(ctx.guild.roles, name="Susturuldu")
    
    if not role:
        await ctx.send("❌ Sunucuda tam olarak **Susturuldu** adında bir rol bulamadım. Lütfen rolün adını kontrol et.")
        return

    if role in member.roles:
        await ctx.send(f"{member.mention} zaten metin kanallarında susturulmuş durumda.")
        return

    seconds = 0
    if sure:
        unit = sure[-1].lower()
        num = sure[:-1]
        if num.isdigit():
            num = int(num)
            if unit == 's':
                seconds = num
            elif unit == 'm':
                seconds = num * 60
            elif unit == 'h':
                seconds = num * 3600
            elif unit == 'd':
                seconds = num * 86400

    try:
        await member.add_roles(role, reason=neden)
        if seconds > 0:
            await ctx.send(f"💬✍️ **{member.display_name}** metin kanallarında **{sure}** süreyle susturuldu. Neden: `{neden}`")
            await log_gonder(ctx.guild, f"💬 **Metin Susturma (Süreli)** | Kullanıcı: {member.mention} | Süre: {sure} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
            await asyncio.sleep(seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"💬🔊 Süre doldu! **{member.display_name}** adlı kullanıcının metin susturması otomatik olarak kaldırıldı.")
        else:
            await ctx.send(f"💬✍️ **{member.display_name}** metin kanallarında süresiz susturuldu. Neden: `{neden}`")
            await log_gonder(ctx.guild, f"💬 **Metin Susturma (Süresiz)** | Kullanıcı: {member.mention} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
            
    except discord.Forbidden:
        await ctx.send("❌ Hata: Bu kullanıcıya rol vermek için yetkim yetersiz veya 'Susturuldu' rolü benim rolümden üstte!")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def metinsusturac(ctx, member: discord.Member):
    """Kullanıcının 'Susturuldu' rolünü alarak metin susturmasını kaldırır."""
    role = discord.utils.get(ctx.guild.roles, name="Susturuldu")
    
    if not role:
        await ctx.send("❌ Sunucuda tam olarak **Susturuldu** adında bir rol bulunamadı.")
        return

    if role not in member.roles:
        await ctx.send(f"{member.mention} zaten metin kanallarında susturulmuş değil.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"💬🔊 **{member.display_name}** adlı kullanıcının metin susturması kaldırıldı.")
        await log_gonder(ctx.guild, f"💬 **Metin Susturması Kaldırıldı** | Kullanıcı: {member.mention} | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("❌ Hata: Bu kullanıcıdan rolü almak için yetkim yetersiz veya 'Susturuldu' rolü benim rolümden üstte!")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")


# --- TEMİZLİK VE DİĞER MODERASYON KOMUTLARI ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
    """Belirtilen miktarda mesajı kanaldan siler."""
    if miktar <= 0:
        await ctx.send("❌ Lütfen 0'dan büyük bir sayı gir.")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=miktar + 1)
        msg = await ctx.send(f"🧹 Başarıyla **{len(deleted) - 1}** adet mesaj silindi.")
        await log_gonder(ctx.guild, f"🧹 **Mesaj Temizliği** | Kanal: {ctx.channel.mention} | Silinen Adet: {len(deleted) - 1} | Yetkili: {ctx.author.mention}")
        await asyncio.sleep(3)
        await msg.delete()
    except discord.Forbidden:
        await ctx.send("❌ Mesajları silmek için 'Mesajları Yönet' yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, sure: str, *, neden="Belirtilmedi"):
    """Kullanıcıya Discord'un yerleşik zaman aşımını (timeout) uygular."""
    unit = sure[-1].lower()
    num = sure[:-1]
    
    if not num.isdigit():
        await ctx.send("❌ Geçersiz süre formatı! Örnek: `10s`, `5m`, `1h`")
        return
    
    num = int(num)
    delta = None
    if unit == 's':
        delta = discord.utils.timedelta(seconds=num)
    elif unit == 'm':
        delta = discord.utils.timedelta(minutes=num)
    elif unit == 'h':
        delta = discord.utils.timedelta(hours=num)
    elif unit == 'd':
        delta = discord.utils.timedelta(days=num)
    else:
        await ctx.send("❌ Geçersiz birim! Sadece `s`, `m`, `h`, `d` kullanabilirsin.")
        return

    try:
        await member.timeout(delta, reason=neden)
        await ctx.send(f"⏰ **{member.display_name}** adlı kullanıcıya **{sure}** süreyle zaman aşımı uygulandı. Neden: `{neden}`")
        await log_gonder(ctx.guild, f"⏰ **Timeout (Zaman Aşımı)** | Kullanıcı: {member.mention} | Süre: {sure} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("❌ Bu kullanıcıya zaman aşımı uygulamak için yetkim yetersiz.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def bilgi(ctx, member: discord.Member = None):
    """Etiketlenen kullanıcının detaylı bilgilerini gösterir."""
    if member is None:
        member = ctx.author

    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
    roles_str = ", ".join(roles) if roles else "Rolü yok"

    embed = discord.Embed(title=f"👤 Kullanıcı Bilgisi: {member.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="Kullanıcı Adı", value=str(member), inline=True)
    embed.add_field(name="Sunucu ID", value=member.id, inline=True)
    embed.add_field(name="Sunucuya Katılım Tarihi", value=member.joined_at.strftime("%d-%m-%Y %H:%M:%S") if member.joined_at else "Bilinmiyor", inline=False)
    embed.add_field(name="Hesap Oluşturma Tarihi", value=member.created_at.strftime("%d-%m-%Y %H:%M:%S"), inline=False)
    embed.add_field(name=f"Roller ({len(roles)})", value=roles_str, inline=False)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def engelle(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı sunucudan yasaklar (Ban)."""
    try:
        await member.ban(reason=neden)
        await ctx.send(f"🔨 **{member.display_name}** sunucudan yasaklandı! Neden: `{neden}`")
        await log_gonder(ctx.guild, f"🔨 **Yasaklama (Ban)** | Kullanıcı: {member.mention} | Neden: `{neden}` | Yetkili: {ctx.author.mention}")
    except discord.Forbidden:
        await ctx.send("Bu kullanıcıyı yasaklamak için yeterli yetkim yok veya rolü benim rolümden üstte.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def banliac(ctx, *, user_id: int):
    """ID'si verilen kullanıcının sunucu yasağını kaldırır (Unban)."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ **{user.name}** adlı kullanıcının yasağı kaldırıldı.")
        await log_gonder(ctx.guild, f"✅ **Yasak Kaldırma (Unban)** | Kullanıcı ID: {user_id} | Yetkili: {ctx.author.mention}")
    except discord.NotFound:
        await ctx.send("Bu ID'ye sahip yasaklı bir kullanıcı bulunamadı.")
    except discord.Forbidden:
        await ctx.send("Yasağı kaldırmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        print(f"Hata oluştu: {e}")

# --- YETKİ YOK HATASI YÖNETİMİ ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanabilmek için gerekli yetkiye sahip olmalısın!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Eksik argüman girdin! Lütfen komutun kullanımını kontrol et.")


# --- ÇEKİLİŞ SİSTEMİ ---
@bot.command()
@commands.has_permissions(administrator=True)
async def cekilis(ctx, sure: str, *, odul: str):
    """Süreye göre otomatik çekiliş başlatır (Örn: !cekilis 1m Nitro Ödülü)."""
    unit = sure[-1].lower()
    num = sure[:-1]
    
    if not num.isdigit():
        await ctx.send("❌ Geçersiz süre formatı! Örnek kullanım: `!cekilis 30s 100 TL`, `!cekilis 5m VIP Üyelik`")
        return
    
    num = int(num)
    seconds = 0
    if unit == 's':
        seconds = num
    elif unit == 'm':
        seconds = num * 60
    elif unit == 'h':
        seconds = num * 3600
    elif unit == 'd':
        seconds = num * 86400
    else:
        await ctx.send("❌ Geçersiz zaman birimi! Sadece `s` (saniye), `m` (dakika), `h` (saat), `d` (gün) kullanabilirsin.")
        return

    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ BAŞLADI! 🎉",
        description=f"🎁 **Ödül:** **{odul}**\n⏳ **Süre:** {sure}\n\nKatılmak için aşağıdaki 🎉 emojisine tıklaman yeterlidir!",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Düzenleyen: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    
    # Komut mesajını siliyoruz ve çekiliş mesajını atıyoruz
    await ctx.message.delete()
    cekilis_mesaji = await ctx.send(embed=embed)
    await cekilis_mesaji.add_reaction("🎉")

    # Belirtilen süre kadar bekliyoruz
    await asyncio.sleep(seconds)

    # Süre bittiğinde mesajı ve katılanları tekrar güncel alıyoruz
    try:
        yeni_mesaj = await ctx.channel.fetch_message(cekilis_mesaji.id)
        users = []
        for reaction in yeni_mesaj.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)
                break

        if users:
            import random
            kazanan = random.choice(users)
            
            kazanan_embed = discord.Embed(
                title="🏆 ÇEKİLİŞ SONUÇLANDI! 🏆",
                description=f"🎁 **Ödül:** **{odul}**\n🎉 **Kazanan:** {kazanan.mention}\nTebrikler!",
                color=discord.Color.red()
            )
            await ctx.send(f"🎊 Tebrikler {kazanan.mention}! **{odul}** çekilişini kazandın!", embed=kazanan_embed)
            await log_gonder(ctx.guild, f"🎁 **Çekiliş Sonucu** | Ödül: `{odul}` | Kazanan: {kazanan.mention}")
        else:
            await ctx.send(f"❌ **{odul}** çekilişine yeterli katılım olmadığından kazanan seçilemedi.")
            
    except Exception as e:
        print(f"Çekiliş sonlandırma hatası: {e}")


bot.run(os.getenv("DISCORD_TOKEN"))
