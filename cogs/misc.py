import discord, json, time, aiohttp, tokens, asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

async def github_offline(self, ctx, status):
    embed = discord.Embed(title='Github is Down!', description='Github seems to be offline! You can [check their website for updates.](https://www.githubstatus.com/)\nIf Github is not down, [report this to a developer.](https://discord.gg/FZHUWdF8HX)', color=discord.Color.blurple())
    await ctx.send(embed=embed)
    newline = '\n'
    embed2 = discord.Embed(title='Github Down', description=f"Command: `{ctx.message.content}`\n**Status Code: {status}**\nAuthor: {ctx.author} ({ctx.author.id})\n{f'Guild: {ctx.guild.name} ({ctx.guild.id}){newline}Channel: {ctx.channel.name} ({ctx.channel.id}){newline}[Jump to Message]({ctx.message.jump_url})' if ctx.guild is not None else 'Guild: DMs'}")
    guild = self.bot.get_guild(739854607215230996)
    channel = guild.get_channel(795395718998523925)
    await channel.send(embed=embed2)

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 2.5, BucketType.user)
    async def ping(self, ctx):
        """ Ping Pong! Check the bot's latency. """
        start = time.perf_counter()
        message = await ctx.send(f":ping_pong: Pong!\n:heart: {round(self.bot.latency * 1000)}ms")
        end = time.perf_counter()
        await message.edit(content=f"{message.content}\n:pencil2: {round((end - start) * 1000)}ms")

    @commands.command()
    @commands.cooldown(1, 2.5, BucketType.user)
    async def setup(self, ctx):
        """ Get Setup Instructions """
        embed = discord.Embed(title='Setup your Account', color=discord.Color.green())
        embed.add_field(name='1) Get Your Code', value='Copy your code [from our website.](https://git.bduck.xyz/oauth)', inline=False)
        embed.add_field(name='2) Link Your Accounts', value=f'Run the `{ctx.clean_prefix}link <code>` command.', inline=False)
        embed.add_field(name='3) Activate Repos', value=f'Run the `{ctx.clean_prefix}repo <repo>` command.', inline=False)
        embed.set_footer(text=f'{self.bot.user.name} is not affiliated or endorced by Github and/or Discord.')
        await ctx.send(embed=embed)

    @commands.command()
    # @commands.cooldown(1, 2.5, BucketType.user)
    async def link(self, ctx, *, code):
        """ Link your Github Account! """
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://github.com/login/oauth/access_token?client_id=eb8d5d1d67f9e842e89b&client_secret={tokens.github}&code={code}') as r:
                if r.status == 200:
                    text = await r.text()
                    if text.startswith("error=bad_verification_code"):
                        embed = discord.Embed(title='Invalid Code!', description='You seem to have provided an invalid code.\nCodes have a one time use and expire after 10 mintues.\nPlease get a new token [here.](https://git.bduck.xyz/new)', color=discord.Color.dark_orange())
                        embed.set_thumbnail(url='https://code-linter.elixi.re/i/72qm.png?raw=1')
                        return await ctx.send(embed=embed)
                    params = text.split('&')
                    token = params[0].replace('access_token=', '')
                    scope = params[1].replace('scope=', '')
                    if 'repo' not in scope.split('%2C'):
                        embed = discord.Embed(title='Missing Permissions!', description='You didn\'t give us access to Workflow/Repo permissions!\nPlease [re-authorize](https://git.bduck.xyz/new) with the proper permissions.', color=discord.Color.dark_orange())
                        embed.set_thumbnail(url='https://code-linter.elixi.re/i/72qm.png?raw=1')
                        return await ctx.send(embed=embed)
                else:
                    return await github_offline(self, ctx, r.status)

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/user', headers={"Authorization": f"token {token}"}) as r:
                if r.status == 200:
                    js = await r.json()
                    embed = discord.Embed(title='Confirm your Account', description=f"Are you sure you want to link your account to **{js['login']}**?", color=discord.Colour.blue(), url=str(js['html_url']))
                    embed.set_thumbnail(url=str(js['avatar_url']))
                    msg = await ctx.send(embed=embed)
                else:
                    return await github_offline(self, ctx, r.status)

        check = '\U00002705'
        redx = '\U0000274c'
        await msg.add_reaction(check)
        await msg.add_reaction(redx)

        def reaction_check(reaction, user2):
            if ctx.author == user2 and reaction.message.id == msg.id and reaction.emoji in [check, redx]:
                return True
            return False

        try:
            reaction, user2 = await self.bot.wait_for('reaction_add', timeout=60.0, check=reaction_check)
        except asyncio.TimeoutError:
            embed.color = discord.Color.dark_grey()
            embed.description = f'{embed.description}\n:notepad_spiral: You took to long to respond! Please run this command again.'
            return await msg.edit(embed=embed)
        else:
            if reaction.emoji == redx:
                embed.color = discord.Color.red()
                embed.title = 'Cancelled Linking'
                embed.description = f'Not linking you account to **{js["login"]}**'
                return await msg.edit(embed=embed)

        embed.color = discord.Color.green()
        embed.description = f"Your account has been linked to **{js['login']}**"
        embed.title = 'Linked your Account'
        File = open('/home/container/CodeLint/data.json').read()
        data = json.loads(File)
        for x in data:
            if x['id'] == ctx.author.id:
                x['token'] = token
                return await msg.edit(embed=embed)
        data.append({"id": ctx.author.id, "token": token, 'donator': False, 'repo': []})
        with open('/home/container/CodeLint/data.json', 'w') as f:
            json.dump(data, f, indent=2)
        await msg.edit(embed=embed)

    @commands.command()
    async def repo(self, ctx, repo):
        """ Start Watching a Repository for Github Action Checks """
        await ctx.trigger_typing()
        File = open('/home/container/CodeLint/data.json').read()
        data = json.loads(File)
        for x in data:
            if x['id'] == ctx.author.id:
                for a in x['repo']:
                    if a['name'] == str(repo):
                        x['repo'].remove(a)
                        with open('/home/container/CodeLint/data.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        embed = discord.Embed(title='No Longer Watching Repository', description=f"No longer watching **{repo}** for Github Action Checks!", color=discord.Color.red(), url=f'https://github.com/{repo}')
                        return await ctx.send(embed=embed)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.github.com/repos/{repo}/actions/runs', headers={"Authorization": f"token {x['token']}"}) as r:
                        js = await r.json()
                        if r.status == 200:
                            x['repo'].append({"name": str(repo), "notified": False})
                            with open('/home/container/CodeLint/data.json', 'w') as f:
                                json.dump(data, f, indent=2)
                            embed = discord.Embed(title='Now Watching Repository', description=f"**{repo}** is now being watched for Github Action Checks!", color=discord.Color.green(), url=f'https://github.com/{repo}')
                            await ctx.send(embed=embed)
                        elif r.status == 404:
                            msg = """ I could not find that repository! Make sure of the following things:
                            > You entered the repository in the format owner/name - For example [quacky-bot/quacky-support](https://github.com/quacky-bot/quacky-support)
                            > If the repository is private, you have given us access to the organization/your account's private repos.
                            If these steps don't help [contact our Support Team!](https://discord.gg/FZHUWdF8HX)
                            """
                            embed = discord.Embed(title='404 • Repo not found!', description=msg, color=discord.Color.dark_orange())
                            return await ctx.send(embed=embed)
                        else:
                            return await github_offline(self, ctx, r.status)

    @commands.command()
    async def privacy(self, ctx):
        """ Read our Privacy Policy! """
        await ctx.send(f'You can view {self.bot.user.name}\'s Privacy Policy at https://git.bduck.xyz/privacy')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(f'cool an error - {error}')

def setup(bot):
    bot.add_cog(Misc(bot))