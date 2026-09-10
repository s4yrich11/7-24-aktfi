import os
import re
import discord
from discord.ext import commands
from flask import Flask
import threading

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

bot.run(os.getenv("DISCORD_TOKEN"))