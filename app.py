from dotenv import load_dotenv
load_dotenv()

import os
import re
import asyncio
import discord
from discord.ext import commands
from flask import Flask
import threading

# Flask uygulaması
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run).start()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# --- KÜFÜR VE REKLAM ENGELLEME FİLTRESİ İÇİN KELİME LİSTESİ ---
# Buraya dilediğin yasaklı kelimeleri ekleyebilirsin
YASAKLI_KELIMELER = ["küfür1", "küfür2", "orospu", "amk", "sik", "discord.gg/", "http://", "https://"]

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

    # Mesajda yönetici izni varsa filtreye takılmasın (istiyorsan bu satırı silebilirsin)
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    # Mesaj içeriğini küçük harfe çevirerek kontrol et
    content_lower = message.content.lower()
    for kelime in YASAKLI_KELIMELER:
        if kelime in content_lower:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, bu sunucuda küfür veya reklam paylaşmak yasaktır!", delete_after=5)
                return
            except discord.Forbidden:
                pass
            break

    await bot.process_commands(message)

# --- BOT DURUMUNU DEĞİŞTİRME KOMUTU (YÖNETİCİler İÇİN) ---

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
            await asyncio.sleep(seconds)
            if member.voice and member.voice.mute:
                await member.edit(mute=False)
                await ctx.send(f"🔊 Ses süresi doldu! **{member.display_name}** adlı kullanıcının ses susturması otomatik olarak kaldırıldı.")
        else:
            await ctx.send(f"🔇 **{member.display_name}** ses kanalında süresiz susturuldu. Neden: `{neden}`")

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
            await asyncio.sleep(seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"💬🔊 Süre doldu! **{member.display_name}** adlı kullanıcının metin susturması otomatik olarak kaldırıldı.")
        else:
            await ctx.send(f"💬✍️ **{member.display_name}** metin kanallarında süresiz susturuldu. Neden: `{neden}`")
            
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
    except discord.Forbidden:
        await ctx.send("❌ Hata: Bu kullanıcıdan rolü almak için yetkim yetersiz veya 'Susturuldu' rolü benim rolümden üstte!")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")


# --- YENİ EKLENEN ÖZELLİKLER ---

# 1. TEMİZLİK / MESAJ SİLME KOMUTU (!sil <sayı>)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
    """Belirtilen miktarda mesajı kanaldan siler."""
    if miktar <= 0:
        await ctx.send("❌ Lütfen 0'dan büyük bir sayı gir.")
        return
    
    try:
        # Mesajı komutun kendisi de dahil olsun diye miktar + 1 silebiliriz veya direkt miktarı silebiliriz
        deleted = await ctx.channel.purge(limit=miktar + 1)
        msg = await ctx.send(f"🧹 Başarıyla **{len(deleted) - 1}** adet mesaj silindi.")
        await asyncio.sleep(3)
        await msg.delete()
    except discord.Forbidden:
        await ctx.send("❌ Mesajları silmek için 'Mesajları Yönet' yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

# 2. DİSCORD YERLEŞİK ZAMAN AŞIMI (TIMEOUT) KOMUTU (!timeout @kullanici 10m Sebep)
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
    except discord.Forbidden:
        await ctx.send("❌ Bu kullanıcıya zaman aşımı uygulamak için yetkim yetersiz.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

# 3. KULLANICI BİLGİ KOMUTU (!bilgi @kullanici)
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


# --- GENEL YASAKLAMA (BAN) İŞLEMLERİ ---

@bot.command()
@commands.has_permissions(administrator=True)
async def engelle(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı sunucudan yasaklar (Ban)."""
    try:
        await member.ban(reason=neden)
        await ctx.send(f"🔨 **{member.display_name}** sunucudan yasaklandı! Neden: `{neden}`")
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
    except discord.NotFound:
        await ctx.send("Bu ID'ye sahip yasaklı bir kullanıcı bulunamadı.")
    except discord.Forbidden:
        await ctx.send("Yasağı kaldırmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")


# --- YETKİ YOK HATASI YÖNETİMİ ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanabilmek için gerekli yetkiye sahip olmalısın!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Eksik argüman girdin! Lütfen komutun kullanımını kontrol et.")


bot.run(os.getenv("DISCORD_TOKEN"))