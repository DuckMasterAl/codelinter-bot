import discord, json, aiohttp, tokens, datetime, statcord, asyncio
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo_message.start()
        self.statkey = tokens.statcord
        self.statapi = statcord.Client(self.bot, self.statkey)
        self.statapi.start_loop()

    def cog_unload(self):
        self.repo_message.cancel()

    @tasks.loop(minutes=5.0)
    async def repo_message(self):
        await self.bot.wait_until_ready()
        File = open('/home/container/CodeLint/data.json').read()
        data = json.loads(File)
        for x in data:
            errors = []
            logging_information = []
            json_update = False
            for a in x['repo']:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.github.com/repos/{a["name"]}/actions/runs',
                    headers={'Authorization': f'token {x["token"]}'}) as r:
                        js = await r.json()
                        if r.status == 200:
                            if js['workflow_runs'] == [] or js['workflow_runs'][0]['event'] != 'push':
                                continue
                            elif (js['workflow_runs'][0]['conclusion'] == 'failure' and a['notified'] is False) or (js['workflow_runs'][0]['conclusion'] == 'success' and a['notified'] is True):
                                workflow = js['workflow_runs'][0]
                                message = workflow['head_commit']['message']
                                if message.__contains__('\n'):
                                    message = message.split('\n')[0]
                                message = f'[{discord.utils.escape_markdown(message)}](https://github.com/{workflow["repository"]["full_name"]}/commit/{workflow["head_sha"]})'
                                timestamp = datetime.datetime.strptime(workflow['head_commit']['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                                embed = discord.Embed(title=f'Bug Found in {workflow["repository"]["name"]}', description=f"Author: __{workflow['head_commit']['author']['name']}__\nLatest Commit: {message}", color=discord.Color.red(), url=f"{workflow['html_url']}", timestamp=timestamp)
                                embed.set_footer(text=f'Commit {workflow["head_sha"][0:7]}')
                                a['notified'] = True
                                json_update = True
                                if js['workflow_runs'][0]['conclusion'] == 'success' and a['notified'] is True:
                                    embed.title = f'Bug Fixed in {workflow["repository"]["name"]}'
                                    embed.color = discord.Color.green()
                                    a['notified'] = False
                                errors.append(embed)
                                logging_information.append(embed.title)
                        elif r.status == 404:
                            x['repo'].remove(a)
                            json_update = True
                            logging_information.append(f'Deleted {a["name"]} (404)')
                        else:
                            embed = discord.Embed(title='Github Down', description=f"Task: Repo Message Task\n**Status Code: {r.status}**\nUser: {x['id']}\nRepo: {a['name']}", color=discord.Color.red())
                            guild = self.bot.get_guild(739854607215230996)
                            channel = guild.get_channel(795395718998523925)
                            m = await channel.send(embed=embed)
                            logging_information.append(f'Github Down - [{r.status}]({m.jump_url})')

            if errors != []:
                user = await self.bot.fetch_user(x['id'])
                for e in errors:
                    try:
                        await user.send(embed=e)
                    except Exception as e:
                        logging_information.append(f'DM Fail - {e}')

            if json_update:
                with open('/home/container/CodeLint/data.json', 'w') as f:
                    json.dump(data, f, indent=2)

            if logging_information != []:
                guild = self.bot.get_guild(739854607215230996)
                channel = guild.get_channel(795398000645111848)
                logging = '\n> '.join(logging_information)
                embed = discord.Embed(title='Repo Task Logging', description=f'User: {user if errors != [] else x["id"]}\nUpdate JSON: {json_update}\n> {logging}', color=discord.Color.blurple())
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.author.bot is False and ctx.author.id not in [443217277580738571, 475117152106446849]:
            self.statapi.command_run(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.NoPrivateMessage) or isinstance(error, commands.PrivateMessageOnly):
            await ctx.reply(error)
            await asyncio.sleep(2)
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(f'{emotes.redx} You don\'t have permission to use this command!')
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id == 1:
                ctx.command.reset_cooldown(ctx)
                return await ctx.reinvoke()
            msg = await ctx.reply(error)
            await asyncio.sleep(error.retry_after)
            await msg.edit(content=f'You can now run `{ctx.message.content}`, {ctx.author.mention}', allowed_mentions=discord.AllowedMentions(users=True))
        else:
            if ctx.author.id == 44321727758073857:#1:
                e = discord.Embed(title=f'Error with {ctx.command.name}', description=str(error), color=discord.Color.red())
                return await ctx.reply(embed=e)
            guild = self.bot.get_guild(739854607215230996)
            log_channel = guild.get_channel(795395718998523925)
            new_line = '\n'
            e = discord.Embed(title=f'Error with {ctx.command.name}', description=f"Command: `{ctx.message.content}`\nError: **{error}**\nUser: {ctx.author} ({ctx.author.id})\nGuild: {f'{ctx.guild.name} ({ctx.guild.id}){new_line}Channel: {ctx.channel.name} ({ctx.channel.id}){new_line}[Jump to Message]({ctx.message.jump_url})' if ctx.guild is not None else 'DMs'}", color=discord.Color.red())
            await log_channel.send(embed=e)
            e2 = discord.Embed(title='Something went wrong when trying to run that command.', description='This error has been reported to a developer.', color=discord.Color.red())
            await ctx.reply(embed=e2)

def setup(bot):
    bot.add_cog(Tasks(bot))
