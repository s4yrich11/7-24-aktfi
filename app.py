import asyncio
import json
import os
import random
import re
import threading
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import discord
import yt_dlp
from gtts import gTTS

load_dotenv()

# --- FLASK SUNUCUSU (Render'ın 7/24 açık tutması için) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot aktif ve çalışıyor!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# Flask'ı arka planda (thread içinde) başlatıyoruz
threading.Thread(target=run_flask, daemon=True).start()

# --- LOG KANALI ID AYARI ---
LOG_KANAL_ID = 1546166612695056486  # Sunucudaki log kanal ID'si

# --- XP VE SEVİYE SİSTEMİ DOSYA VE ROL AYARLARI ---
XP_FILE = "xp.json"

LEVEL_ROLES = {
    5: 1546166452103684166,
    10: 1546166450924953620,
    15: 1546166449796808756,
    20: 1546166447393480804,
    25: 1546166441609265294,
    30: 1546166440384659558,
    35: 1546166439050739784,
    40: 1546166436085501964,
    45: 1546166433736556606,
    50: 1546166432482725898,
    55: 1546166431039750216,
    60: 1546166429907419167,
    65: 1546166429299118140,
    70: 1546166427520729158,
    75: 1546166425708920914,
    80: 1546166421376208926,
    85: 1546166419559813262,
    90: 1546166418360246393,
    95: 1546166417244684338,
    100: 1546166415948521612,
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
  if current_level in LEVEL_ROLES:
    role_id = LEVEL_ROLES[current_level]
    role = message.guild.get_role(role_id)
    if role and role not in message.author.roles:
      try:
        await message.author.add_roles(role)
        await message.channel.send(
            f"🎉 Tebrikler {message.author.mention}! **{current_level}. Seviyeye**"
            f" ulaştın ve {role.mention} rolünü kazandın!"
        )
      except discord.Forbidden:
        print("Botun bu üyeye rol vermek için yeterli yetkisi yok.")
      except discord.HTTPException:
        print("Rol verme sırasında bir hata oluştu.")


# --- BOT NESNESİ VE INTENTS ---
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YASAKLI_KELİMELER = [
    "küfür1",
    "küfür2",
    "orospu",
    "amk",
    "sik",
    "discord.gg/",
    "http://",
    "https://",
]


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
  await bot.change_presence(
      status=discord.Status.dnd, activity=discord.Game(name="/premium | V8.18")
  )


@bot.event
async def on_member_update(before, after):
  if before.nick != after.nick or before.global_name != after.global_name:
    target_name = after.nick if after.nick else after.name
    match = re.search(r"\b(\d{1,2})\b", target_name)
    if match:
      age = int(match.group(1))
      role_18_plus = discord.utils.get(
          after.guild.roles, name="╭───𒌋𒀖 「🜲・ +18 ÜSTÜNDEJJ」"
      )
      role_18_minus = discord.utils.get(
          after.guild.roles, name="╭───𒌋𒀖 「🜲・+18 ALTINDA」"
      )
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
      except Exception as e:
        print(f"Yaş rol hatası: {e}")


@bot.event
async def on_message(message):
  if message.author.bot or not message.guild:
    return

  # Küfür ve Reklam Kontrolü
  if not message.author.guild_permissions.administrator:
    content_lower = message.content.lower()
    for kelime in YASAKLI_KELİMELER:
      if kelime in content_lower:
        try:
          await message.delete()
          await message.channel.send(
              f"⚠️ {message.author.mention}, bu sunucuda küfür veya reklam"
              " paylaşmak yasaktır!",
              delete_after=5,
          )
          await log_gonder(
              message.guild,
              f"⚠️ **Filtre Yakaladı!** | Kullanıcı: {message.author.mention} |"
              f" Kanal: {message.channel.mention} | Mesaj:"
              f" `{message.content}`",
          )
          return
        except discord.Forbidden:
          pass
        break

  # XP ve Seviye Sistemi
  xp_data = load_xp()
  user_id = str(message.author.id)
  if user_id not in xp_data:
    xp_data[user_id] = {"xp": 0, "level": 1}

  xp_data[user_id]["xp"] += 10
  current_xp = xp_data[user_id]["xp"]
  current_level = xp_data[user_id]["level"]

  next_threshold = current_level * 500
  if current_xp >= next_threshold:
    xp_data[user_id]["level"] += 1
    new_level = xp_data[user_id]["level"]
    await message.channel.send(
        f"🚀 Tebrikler {message.author.mention}, seviye atladın ve"
        f" **{new_level}. seviye** oldun!"
    )
    await check_and_reward_role(message, new_level)

  save_xp(xp_data)
  await bot.process_commands(message)


# --- SEVİYE VE LADERBOARD KOMUTLARI ---
@bot.command(
    name="level",
    aliases=["seviye"],
    help="Kullanıcının mevcut seviyesini ve XP'sini gösterir.",
)
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
      title=f"📊 {target.name} - Seviye Bilgisi", color=discord.Color.blue()
  )
  embed.set_thumbnail(url=target.display_avatar.url)
  embed.add_field(name="Seviye", value=str(current_level), inline=True)
  embed.add_field(name="Toplam XP", value=str(current_xp), inline=True)
  embed.add_field(
      name="Sonraki Seviye",
      value=f"{current_xp} / {next_level_xp} XP",
      inline=False,
  )
  await ctx.send(embed=embed)


@bot.command(
    name="leaderboard",
    aliases=["top", "siralama"],
    help="Sunucudaki en yüksek seviyeli kullanıcıları listeler.",
)
async def leaderboard_command(ctx):
  xp_data = load_xp()
  if not xp_data:
    await ctx.send("Henüz kayıtlı XP verisi bulunmuyor!")
    return
  sorted_users = sorted(
      xp_data.items(), key=lambda item: item[1]["xp"], reverse=True
  )
  top_users = sorted_users[:10]
  embed = discord.Embed(
      title=f"🏆 {ctx.guild.name} - Seviye Sıralaması",
      color=discord.Color.gold(),
  )
  description = ""
  for index, (user_id, data) in enumerate(top_users, start=1):
    member = ctx.guild.get_member(int(user_id))
    name = member.name if member else f"Kullanıcı ({user_id})"
    medal = (
        "👑"
        if index == 1
        else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
    )
    description += (
        f"{medal} **{name}** — Seviye: `{data['level']}` | Toplam XP:"
        f" `{data['xp']}`\n"
    )
  embed.description = description
  embed.set_footer(
      text=f"Komutu kullanan: {ctx.author.name}",
      icon_url=ctx.author.display_avatar.url,
  )
  await ctx.send(embed=embed)


# --- DİĞER YÖNETİM VE MODERASYON KOMUTLARI ---
@bot.command()
@commands.has_permissions(administrator=True)
async def yaz(ctx, kanal: discord.TextChannel, *, mesaj: str):
  await ctx.message.delete()
  await kanal.send(mesaj)
  await log_gonder(
      ctx.guild,
      f"📝 **Bot ile Mesaj Gönderildi** | Yetkili: {ctx.author.mention} | Hedef"
      f" Kanal: {kanal.mention}",
  )


YETKILI_IDLERI = [852839991297966112]


async def id_kontrolu(ctx):
  return ctx.author.id in YETKILI_IDLERI


@bot.command()
@commands.check(id_kontrolu)
async def seskonus(ctx, *, metin: str):
  if not ctx.author.voice or not ctx.author.voice.channel:
    await ctx.send("❌ Önce herhangi bir ses kanalına girmelisin!")
    return
  kanal = ctx.author.voice.channel
  if ctx.voice_client:
    await ctx.voice_client.move_to(kanal)
  else:
    await kanal.connect()
  try:
    tts = gTTS(text=metin, lang="tr", slow=False)
    ses_dosyasi = "konusma.mp3"
    tts.save(ses_dosyasi)
    source = discord.FFmpegPCMAudio(ses_dosyasi)
    if not ctx.voice_client.is_playing():
      ctx.voice_client.play(
          source,
          after=lambda e: (
              os.remove(ses_dosyasi) if os.path.exists(ses_dosyasi) else None
          ),
      )
      await ctx.message.delete()
      await log_gonder(
          ctx.guild,
          f"🔊 **Sesli Okuma Yapıldı** | Yetkili: {ctx.author.mention} | Metin:"
          f" `{metin}`",
      )
    else:
      await ctx.send("⚠️ Zaten şu an bir şey okuyorum.")
  except Exception as e:
    await ctx.send(f"❌ Hata: {e}")


@bot.command()
@commands.check(id_kontrolu)
async def ayril(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Ses kanalından ayrıldım.")
  else:
    await ctx.send("❌ Zaten bir ses kanalında değilim.")


@bot.command()
@commands.has_permissions(administrator=True)
async def durum(ctx, *, oyun_adi: str):
  await bot.change_presence(
      status=discord.Status.dnd, activity=discord.Game(name=oyun_adi)
  )
  await ctx.send(f"✅ Botun durumu başarıyla **{oyun_adi}** olarak güncellendi!")


@bot.command()
@commands.has_permissions(administrator=True)
async def rolver(ctx, member: discord.Member, *, role_identifier: str):
  role = (
      discord.utils.get(ctx.guild.roles, mention=role_identifier)
      or discord.utils.get(ctx.guild.roles, name=role_identifier)
      or ctx.guild.get_role(
          int(role_identifier[3:-1])
          if role_identifier.startswith("<@&") and role_identifier.endswith(">")
          else 0
      )
  )
  if not role:
    await ctx.send("Rol bulunamadı.")
    return
  await member.add_roles(role)
  await ctx.send(f"Başarılı! {member.mention} kullanıcısına {role.name} verildi.")


@bot.command()
@commands.has_permissions(administrator=True)
async def rolal(ctx, member: discord.Member, *, role_identifier: str):
  role = (
      discord.utils.get(ctx.guild.roles, mention=role_identifier)
      or discord.utils.get(ctx.guild.roles, name=role_identifier)
      or ctx.guild.get_role(
          int(role_identifier[3:-1])
          if role_identifier.startswith("<@&") and role_identifier.endswith(">")
          else 0
      )
  )
  if not role:
    await ctx.send("Rol bulunamadı.")
    return
  await member.remove_roles(role)
  await ctx.send(f"Başarılı! {member.mention} kullanıcısından {role.name} alındı.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
  if miktar <= 0:
    return
  deleted = await ctx.channel.purge(limit=miktar + 1)
  msg = await ctx.send(f"🧹 **{len(deleted) - 1}** adet mesaj silindi.")
  await asyncio.sleep(3)
  await msg.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def engelle(ctx, member: discord.Member, *, neden="Belirtilmedi"):
  await member.ban(reason=neden)
  await ctx.send(f"🔨 **{member.display_name}** yasaklandı. Neden: `{neden}`")


@bot.command()
@commands.has_permissions(administrator=True)
async def banliac(ctx, *, user_id: int):
  user = await bot.fetch_user(user_id)
  await ctx.guild.unban(user)
  await ctx.send(f"✅ **{user.name}** yasağı kaldırıldı.")


# --- MÜZİK SİSTEMİ (YT-DLP & FFMPEG) ---
ytdl_format_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
}

ffmpeg_options = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)
    self.data = data
    self.title = data.get("title")

  @classmethod
  async def from_url(cls, search, *, loop=None):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(search, download=False)
    )
    if "entries" in data:
      data = data["entries"][0]
    filename = data["url"]
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.command(name="çal", help="YouTube'dan isim veya link ile müzik çalar")
async def cal(ctx, *, arama: str):
  if not ctx.author.voice:
    await ctx.send("❌ Önce bir ses kanalına girmelisin!")
    return

  channel = ctx.author.voice.channel
  if ctx.voice_client is None:
    await channel.connect()
  else:
    await ctx.voice_client.move_to(channel)

  async with ctx.typing():
    try:
      player = await YTDLSource.from_url(arama, loop=bot.loop)
      ctx.voice_client.play(
          player, after=lambda e: print(f"Hata: {e}") if e else None
      )
    except Exception as e:
      await ctx.send(f"❌ Şarkı oynatılırken bir hata oluştu: {e}")
      return

  await ctx.send(f"🎶 Şu an çalınıyor: **{player.title}**")


@bot.command(name="durdur", help="Müziği duraklatır")
async def durdur(ctx):
  if ctx.voice_client and ctx.voice_client.is_playing():
    ctx.voice_client.pause()
    await ctx.send("⏸️ Müzik duraklatıldı.")


@bot.command(name="devam", help="Müziği devam ettirir")
async def devam(ctx):
  if ctx.voice_client and ctx.voice_client.is_paused():
    ctx.voice_client.resume()
    await ctx.send("▶️ Müzik devam ediyor.")


@bot.command(name="müzikçık", help="Botu ses kanalından çıkarır")
async def muzikitcikis(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Ses kanalından ayrıldım.")
  else:
    await ctx.send("❌ Zaten bir ses kanalında değilim.")


# Botu Çalıştır
bot.run(os.getenv("DISCORD_TOKEN"))