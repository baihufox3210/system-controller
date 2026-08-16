import os, discord, traceback
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix = "♡", intents = intents
        )
        
    async def setup_hook(self):
        await self.load_extensions()
        await self.tree.sync()
    
    async def load_extensions(self):
        for root, _, files in os.walk("./cogs"):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    extension = rel_path.replace(os.sep, ".")[:-3]
                    
                    try: await super().load_extension(extension)
                    except Exception as e: pass
                    
    async def on_ready(slef): pass
    async def close(slef): await super().close()