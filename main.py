import discord, asyncio, json, tokens
from discord.ext import commands
Client = discord.Client()

initial_extensions = ['cogs.misc', 'cogs.tasks', 'jishaku']

client = commands.Bot(
                    command_prefix=commands.when_mentioned_or('cl!'),
                    status=discord.Status.idle,
                    activity=discord.Activity(type=discord.ActivityType.watching, name='Github Repositories | cl!help'),
                    description='Hello! I watch your Github Repositories for Github Action Checks!\nLearn More at https://git.bduck.xyz',
                    case_insensitive=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                    reconnect=True,
                    intents=discord.Intents.default()
                    )

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            print(f'Code Linter: {extension} could not be loaded!\n{type(e).__name__}: {e}')

client.run(tokens.bot)
