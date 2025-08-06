import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import os

# Pobierz token bota, URI Mongo i guild ID ze zmiennych środowiskowych
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Połączenie z MongoDB
client = MongoClient(MONGO_URI)
db = client['erlc_database']  
dowody_col = db['dowody']
auta_col = db['auta']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}!')
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

# Komenda: wyrób dowód
@bot.tree.command(name="wyrób-dowód", description="Wyrob dowód osobisty", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nick_roblox="Nick Roblox",
    imie="Imię postaci",
    wiek="Wiek",
    pochodzenie="Pochodzenie",
    zdjecie_url="Link do zdjęcia"
)
async def wyrob_dowod(interaction: discord.Interaction, nick_roblox: str, imie: str, wiek: int, pochodzenie: str, zdjecie_url: str):
    if dowody_col.find_one({"nick_roblox": nick_roblox}):
        await interaction.response.send_message("Ten gracz ma już wyrobiony dowód!", ephemeral=True)
        return
    dowody_col.insert_one({
        "nick_roblox": nick_roblox,
        "imie": imie,
        "wiek": wiek,
        "pochodzenie": pochodzenie,
        "zdjecie_url": zdjecie_url
    })
    await interaction.response.send_message(f'Dowód wyrobiony dla {nick_roblox}!')

# Komenda: rejestracja auta
@bot.tree.command(name="rejestracja-auta", description="Zarejestruj auto", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    marka="Marka auta",
    model="Model auta",
    wlasciciel="Imię i nazwisko właściciela",
    tablice="Tablice rejestracyjne",
    zdjecie1="Zdjęcie przodu auta (link)",
    zdjecie2="Zdjęcie tyłu auta (link)",
    zdjecie3="Zdjęcie lewego boku auta (link)",
    zdjecie4="Zdjęcie prawego boku auta (link)"
)
async def rejestracja_auta(interaction: discord.Interaction, marka: str, model: str, wlasciciel: str, tablice: str, zdjecie1: str, zdjecie2: str, zdjecie3: str, zdjecie4: str):
    auta_col.insert_one({
        "marka": marka,
        "model": model,
        "wlasciciel": wlasciciel,
        "tablice": tablice,
        "zdjecia": [zdjecie1, zdjecie2, zdjecie3, zdjecie4]
    })
    await interaction.response.send_message(f'Auto {marka} {model} zarejestrowane!')

# Komenda: sprawdź dowód
@bot.tree.command(name="sprawdź-dowód", description="Sprawdź dowód po nicku Roblox", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick_roblox="Nick Roblox")
async def sprawdz_dowod(interaction: discord.Interaction, nick_roblox: str):
    dowod = dowody_col.find_one({"nick_roblox": nick_roblox})
    if not dowod:
        await interaction.response.send_message("Nie znaleziono dowodu dla tego nicku.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Dowód osobisty: {dowod['nick_roblox']}", color=discord.Color.blue())
    embed.add_field(name="Imię", value=dowod["imie"], inline=True)
    embed.add_field(name="Wiek", value=dowod["wiek"], inline=True)
    embed.add_field(name="Pochodzenie", value=dowod["pochodzenie"], inline=True)
    embed.set_image(url=dowod["zdjecie_url"])
    await interaction.response.send_message(embed=embed)

# Komenda: usuń dowód
@bot.tree.command(name="usuń-dowód", description="Usuń dowód z bazy", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick_roblox="Nick Roblox")
async def usun_dowod(interaction: discord.Interaction, nick_roblox: str):
    result = dowody_col.delete_one({"nick_roblox": nick_roblox})
    if result.deleted_count == 0:
        await interaction.response.send_message("Nie znaleziono takiego dowodu.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Dowód dla {nick_roblox} został usunięty.")

# Komenda: usuń auto
@bot.tree.command(name="usuń-auto", description="Usuń auto z bazy", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(tablice="Tablice rejestracyjne auta")
async def usun_auto(interaction: discord.Interaction, tablice: str):
    result = auta_col.delete_one({"tablice": tablice})
    if result.deleted_count == 0:
        await interaction.response.send_message("Nie znaleziono auta z takimi tablicami.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Auto z tablicami {tablice} zostało usunięte.")

# Komenda: sprawdź auto
@bot.tree.command(name="sprawdź-auto", description="Sprawdź auto po tablicach rejestracyjnych", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(tablice="Tablice rejestracyjne auta")
async def sprawdz_auto(interaction: discord.Interaction, tablice: str):
    auto = auta_col.find_one({"tablice": tablice})
    if not auto:
        await interaction.response.send_message("Nie znaleziono auta z takimi tablicami.", ephemeral=True)
        return
    embed = discord.Embed(title=f"AUTO: {auto['marka']} {auto['model']}", color=discord.Color.green())
    embed.add_field(name="Właściciel", value=auto["wlasciciel"], inline=True)
    embed.add_field(name="Tablice", value=auto["tablice"], inline=True)
    embed.set_image(url=auto["zdjecia"][0])  # pokazujemy pierwsze zdjęcie z listy
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)



