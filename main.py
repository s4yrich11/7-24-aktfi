from dotenv import load_dotenv
load_dotenv()

import os
import re
import discord
import yt_dlp
from discord.ext import commands
from flask import Flask
import threading
import asyncio

# --- KENDİ DİSCORD ID'N ---
SAHIP_ID = 85283991297966112

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

@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick or before.global_name != after.global_name:
        target_name = after.nick if after.nick else after.name

        match = re.search(r"\b(\d{1,2})\b", target_name)
        if match:
            age = int(match.group(1))

            role_18_plus = discord.utils.get(after.guild.roles, name="18+")
            role_18_minus = discord.utils.get(after.guild.roles, name="18-")

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

# --- ROL VERME VE ALMA KOMUTLARI ---

@bot.command()
async def rolver(ctx, member: discord.Member, *, role_identifier: str):
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

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
async def rolal(ctx, member: discord.Member, *, role_identifier: str):
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

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


# --- MÜZİK AYARLARI ---
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

# --- MÜZİK / SES KOMUTLARI ---

@bot.command()
async def katil(ctx):
    """Botun ses kanalına katılır."""
    if not ctx.author.voice:
        await ctx.send("Önce bir ses kanalına girmelisin dostum!")
        return
    
    channel = ctx.author.voice.channel
    try:
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"🎤 {channel.name} kanalına bağlandım!")
    except Exception as e:
        await ctx.send(f"Ses kanalına bağlanırken hata oluştu: `{e}`")

@bot.command()
async def oynat(ctx, *, aranan: str):
    """YouTube'dan şarkı aratır veya linkten ses çalar."""
    if not ctx.author.voice:
        await ctx.send("Önce bir ses kanalına girmelisin!")
        return

    channel = ctx.author.voice.channel
    
    if not ctx.voice_client:
        try:
            await channel.connect()
        except Exception as e:
            await ctx.send(f"Kanala bağlanırken hata oluştu: {e}")
            return
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    await ctx.send(f"🔍 **{aranan}** aranıyor ve sese hazırlanıyor...")

    try:
        query = aranan if aranan.startswith("http") else f"ytsearch:{aranan}"

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            url2 = info['url']
            title = info.get('title', 'Bilinmeyen Şarkı')

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        
        await ctx.send(f"▶️ Çalınıyor: **{title}**")
        
    except Exception as e:
        await ctx.send(f"Şarkı çalınırken hata oluştu: `{e}`")


@bot.command()
async def sustur(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı ses kanalında susturur (Server Mute)."""
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

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
async def susturac(ctx, member: discord.Member):
    """Kullanıcının ses kanalındaki susturmasını kaldırır (Server Unmute)."""
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

    if not member.voice:
        await ctx.send(f"{member.mention} bir ses kanalında değil.")
        return

    try:
        await member.edit(mute=False)
        await ctx.send(f"🔊 **{member.display_name}** adlı kullanıcının susturması kaldırıldı.")
    except discord.Forbidden:
        await ctx.send("Kullanıcının susturmasını kaldırmak için yeterli yetkim yok.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

# --- SUNUCUDAN ATMA SUSTURMA ENGELLEME  ---

@bot.command()
async def at(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı ses kanalından atar (Disconnect)."""
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

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

@bot.command()
async def engelle(ctx, member: discord.Member, *, neden="Belirtilmedi"):
    """Kullanıcıyı sunucudan yasaklar (Ban)."""
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

    try:
        await member.ban(reason=neden)
        await ctx.send(f"🔨 **{member.display_name}** sunucudan yasaklandı! Neden: `{neden}`")
    except discord.Forbidden:
        await ctx.send("Bu kullanıcıyı yasaklamak için yeterli yetkim yok veya rolü benim rolümden üstte.")
    except discord.HTTPException as e:
        await ctx.send(f"Bir hata oluştu: {e}")

@bot.command()
async def banliac(ctx, *, user_id: int):
    """ID'si verilen kullanıcının sunucu yasağını kaldırır (Unban)."""
    if ctx.author.id != SAHIP_ID:
        await ctx.send("Bu komutu sadece botun sahibi kullanabilir!")
        return

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

bot.run(os.getenv("DISCORD_TOKEN"))