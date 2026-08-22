import discord
from discord.ext import commands
import urllib.request
import urllib.parse
import re
import random
import asyncio
import logging

logger = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.vc = None
        self.is_playing = False
        self.current_song = None
        self.connecting_lock = asyncio.Lock()

    def fetch_songs(self):
        try:
            html_url = "https://adimusic.vercel.app/library"
            req = urllib.request.Request(html_url, headers={'User-Agent': 'Mozilla/5.0'})
            html_resp = urllib.request.urlopen(req).read().decode('utf-8')
            js_file_matches = re.findall(r'src="(/assets/index-[^"]+\.js)"', html_resp)
            if not js_file_matches:
                return []
            
            js_url = "https://adimusic.vercel.app" + js_file_matches[0]
            js_req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
            js_resp = urllib.request.urlopen(js_req).read().decode('utf-8')
            mp3_matches = re.findall(r'"(https://[^"]+\.mp3)"', js_resp)
            return list(set(mp3_matches))
        except Exception as e:
            logger.error(f"Failed to fetch songs: {e}")
            return []

    def play_next(self, error=None):
        if error:
            logger.error(f"Player error: {error}")

        if len(self.queue) > 0 and self.vc and self.vc.is_connected():
            self.current_song = self.queue.pop(0)
            
            # Use FFmpeg to stream
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            
            audio_source = discord.FFmpegPCMAudio(self.current_song, **ffmpeg_options)
            
            self.is_playing = True
            self.vc.play(audio_source, after=self.play_next)
            
            # Print friendly name
            song_name = urllib.parse.unquote(self.current_song.split('/')[-1].replace('.mp3', ''))
            logger.info(f"Now playing: {song_name}")
        else:
            self.is_playing = False
            self.current_song = None
            if self.vc:
                # Optionally disconnect after queue finishes
                asyncio.run_coroutine_threadsafe(self.vc.disconnect(), self.bot.loop)

    @commands.command(name="play")
    async def play(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel first!")

        channel = ctx.author.voice.channel

        if not self.vc or not self.vc.is_connected():
            async with self.connecting_lock:
                if not self.vc or not self.vc.is_connected():
                    try:
                        self.vc = await channel.connect(timeout=60.0, self_deaf=True)
                    except Exception as e:
                        return await ctx.send(f"Failed to join voice channel: {e}")
        elif self.vc.channel != channel:
            await self.vc.move_to(channel)

        await ctx.send("Fetching songs from AdiMusic...")
        
        songs = await self.bot.loop.run_in_executor(None, self.fetch_songs)
        
        if not songs:
            return await ctx.send("Couldn't find any songs on the website!")

        random.shuffle(songs)
        
        # Add to queue
        self.queue.extend(songs)
        await ctx.send(f"Added {len(songs)} songs to the queue in shuffle mode! 🎶")

        if not self.is_playing and not self.vc.is_playing():
            self.play_next()

    @commands.command(name="skip")
    async def skip(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.stop() # This triggers the 'after' callback which plays the next song
            await ctx.send("Skipped to the next song! ⏭️")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        self.queue.clear()
        if self.vc:
            if self.vc.is_playing():
                self.vc.stop() # Callback will handle disconnect
            else:
                await self.vc.disconnect()
            self.vc = None
        self.is_playing = False
        await ctx.send("Stopped playing and cleared the queue. 🛑")

async def setup(bot):
    await bot.add_cog(Music(bot))
