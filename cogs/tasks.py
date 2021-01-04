import discord, json, aiohttp, tokens, datetime
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo_message.start()

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
                            embed = discord.Embed(title='Github Down', description=f"Task: Repo Message Task\n**Status Code: {r.status}**\nUser: {x['id']}\nRepo: {a['name']}")
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

def setup(bot):
    bot.add_cog(Tasks(bot))
