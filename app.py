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

# --- BOT DURUMUNU DEĞİŞTİRME KOMUTU (YÖNETİCİLER İÇİN) ---

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


# --- SES KANALI İŞLEMLERİ ---

@bot.command()
@commands.has_permissions(administrator=True)
async def sestsustur(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı ses kanalında susturur (Server Mute)."""
    if not member.voice:
        await ctx.send(f"{member.mention} bir ses kanalında değil.")
        return

    try:
        await member.edit(mute=True, reason=neden)
        await ctx.send(f"🔇 **{member.display_name}** ses kanalında susturuldu. Neden: `{neden}`")
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
    """Kullanıcıyı süreli veya süresiz metin kanallarında susturur. 
    Kullanım: !metinsustur @kullanici 10s (saniye), 5m (dakika), 2h (saat) veya süre vermeden direkt."""
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
            
            # Arkaplanda süre sayımı başlatıyoruz
            await asyncio.sleep(seconds)
            
            # Süre bittiğinde kullanıcı hala sunucudaysa ve rolü üzerindeyse rolü geri al
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"💬🔊 Süre doldu! **{member.display_name}** adlı kullanıcının metin susturması otomatik olarak kaldırıldı.")
        else:
            # Süre belirtilmediyse normal sınırsız susturma
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
        await ctx.send("❌ Bu komutu kullanabilmek için **Yönetici (Administrator)** yetkisine sahip olmalısın!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Eksik argüman girdin! Lütfen komutun kullanımını kontrol et.")


bot.run(os.getenv("DISCORD_TOKEN"))