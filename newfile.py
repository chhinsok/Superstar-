import discord
from discord.ext import commands
import yt_dlp

# 1. Setup Intents
intents = discord.Intents.default()
intents.message_content = True

# 2. Setup Bot Prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. YTDL Configuration
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# 4. Audio Source Class
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# 5. Bot Commands
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='play', help='Plays audio from YouTube')
async def play(ctx, *, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel!")
        return
    
    channel = ctx.message.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'Now playing: **{player.title}**')
        except Exception as e:
            await ctx.send(f'An error occurred: {e}')

@bot.command(name='leave', help='Makes the bot leave the voice channel')
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I am not in a voice channel.")

# 6. Run the Bot
bot.run('MTUwNDczNDc5MjkxNzMxOTcyMQ.GuUxkN.uRX5UMOs8KejIB07euz1T2SzTCqGjBQreU6tI4')
