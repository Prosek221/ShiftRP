import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import os

# Pobierz token i URI bazy z zmiennych środowiskowych
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Połączenie z MongoDB
client = MongoClient(MONGO_URI)
db = client['erlc_database']  # nazwa bazy
dowody_col = db['dowody']
auta_col = db['auta']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Zdefiniuj GUILD_ID, żeby komendy slash działały szybciej w testach
GUILD_ID = 1402608876356112404  # <- tutaj wpisz ID swojego serwera (int)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}!')
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)

# Komenda do wyrabiania dowodu
@bot.tree.command(name="wyrób-dowód", description="Wyrob dowód osobisty", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nick_roblox="Nick Roblox",
    imie="Imię postaci",
    wiek="Wiek",
    pochodzenie="Pochodzenie",
    zdjecie_url="Link do zdjęcia"
)
async def wyrob_dowod(interaction: discord.Interaction, nick_roblox: str, imie: str, wiek: int, pochodzenie: str, zdjecie_url: str):
    # Sprawdź, czy dowód już istnieje
    if dowody_col.find_one({"nick_roblox": nick_roblox}):
        await interaction.response.send_message("Ten gracz ma już wyrobiony dowód!", ephemeral=True)
        return

    # Wstaw do bazy
    dowody_col.insert_one({
        "nick_roblox": nick_roblox,
        "imie": imie,
        "wiek": wiek,
        "pochodzenie": pochodzenie,
        "zdjecie_url": zdjecie_url
    })
    await interaction.response.send_message(f'Dowód wyrobiony dla {nick_roblox}!')

# Komenda do rejestracji auta
@bot.tree.command(name="rejestracja-auta", description="Zarejestruj auto", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    marka="Marka auta",
    model="Model auta",
    wlasciciel="Imię i nazwisko właściciela",
    tablice="Tablice rejestracyjne",
    zdjecie1="Link do zdjęcia przodu auta",
    zdjecie2="Link do zdjęcia tyłu auta",
    zdjecie3="Link do zdjęcia lewego boku auta",
    zdjecie4="Link do zdjęcia prawego boku auta"
)
async def rejestracja_auta(interaction: discord.Interaction, marka: str, model: str, wlasciciel: str, tablice: str, zdjecie1: str, zdjecie2: str, zdjecie3: str, zdjecie4: str):
    # Każdy może zarejestrować wiele aut, więc nie blokujemy duplikatów
    auta_col.insert_one({
        "marka": marka,
        "model": model,
        "wlasciciel": wlasciciel,
        "tablice": tablice,
        "zdjecia": [zdjecie1, zdjecie2, zdjecie3, zdjecie4]
    })
    await interaction.response.send_message(f'Auto {marka} {model} zarejestrowane!')

# Komenda do wyszukiwania dowodu po nicku Roblox
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

# Komenda do usuwania dowodu (np. admin)
@bot.tree.command(name="usuń-dowód", description="Usuń dowód z bazy", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick_roblox="Nick Roblox")
async def usun_dowod(interaction: discord.Interaction, nick_roblox: str):
    result = dowody_col.delete_one({"nick_roblox": nick_roblox})
    if result.deleted_count == 0:
        await interaction.response.send_message("Nie znaleziono takiego dowodu.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Dowód dla {nick_roblox} został usunięty.")

# Analogicznie można dodać komendy do usuwania aut, listowania itp.

bot.run(DISCORD_TOKEN)

