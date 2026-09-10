import os
import re
import discord
from discord.ext import commands
from flask import Flask
import threading

# --- KENDİ DİSCORD ID'N ---
SAHIP_ID = 85283991297966112

# Flask uygulamasını Gunicorn'un uyumlu görebileceği şekilde 'app' adıyla tanımlıyoruz
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
    if ctx.author.id != 852839991297966112:
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
    if ctx.author.id != 852839991297966112:
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
        await ctx.send(f"Ses kanalına bağlanırken hata oluştu (PyNaCl eksik olabilir): `{e}`")

@bot.command()
async def ayril(ctx):
    """Botun ses kanalından ayrılır."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Ses kanalından ayrıldım.")
    else:
        await ctx.send("Zaten bir ses kanalında değilim.")

@bot.command()
async def durdur(ctx):
    """Çalan müziği duraklatır."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Müzik duraklatıldı ⏸️")
    else:
        await ctx.send("Şu an çalan bir müzik yok.")

@bot.command()
async def devam(ctx):
    """Durdurulan müziği devam ettirir."""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Müzik devam ediyor ▶️")
    else:
        await ctx.send("Müzik duraklatılmış değil.")


@rolver.error
@rolal.error
async def rol_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Eksik argüman! Kullanım: `!rolver @Kullanici RolAdı` veya `!rolal @Kullanici RolAdı`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Belirtilen kullanıcı bulunamadı.")

# -----------------------------------------------

bot.run(os.getenv("DISCORD_TOKEN"))