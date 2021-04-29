# bot.py
from discord.utils import get
from math import ceil
from math import floor
import asyncio
import os
import discord
import json
import random
import time

XP_RATE = 0.3
TIME = 90
with open('pepemusic.txt', 'r') as file:
    SONG = file.read()
with open('jokes.json', 'r') as jokes:
    JOKES = json.load(jokes)


def scaling(x):
    return x * x

class Player:
    def __init__(self, name, userid, url):
        self.name = name
        self.id = userid
        self.url = url
        self.xp = 0
        self.level = 1
        self.humor = 0
        self.credits = 0
        self.secrets = {}

    def update_url(self, url):
        self.url = url

    def import_data(self, save_dict):
        self.name = save_dict['name']
        self.id = save_dict['id']
        self.xp = save_dict['xp']
        self.level = save_dict['level']
        self.humor = save_dict['humor']
        self.secrets = save_dict['secrets']
        self.credits = save_dict['credits']

    def export_data(self):
        save_dict = {'xp': self.xp, 'level': self.level,
                     'humor': self.humor, 'name': self.name,
                     'id': self.id, 'secrets': self.secrets,
                     'credits': self.credits}
        return save_dict
        

    def gain_xp(self, xp):
        self.xp = max([scaling(self.level - 1), self.xp + xp])
        if self.xp > scaling(self.level):
            while self.xp > scaling(self.level):
                self.level += 1
            return True
        return False
    
    def get_secret(self, secret):
        self.secrets[secret['opcode']] = secret

    def gain_humor(self, i):
        self.humor += i

    def gain_credits(self, i):
        self.credits += i

    def level_up(self, amount):
        for i in range(amount):
            self.gain_xp(scaling(self.level) - self.xp)
        return True

    def stats(self):
        stats = discord.Embed(title=f'{self.name}\'s stats')
        stats.set_thumbnail(url=self.url)
        stats.description = f'xp: {self.xp}\nnivel: {self.level}\nhumor: {self.humor}\ncredits: {self.credits}'
        return stats

    def get_secrets(self):
        secret_list = discord.Embed(title=f'{self.name}\'s secrets')
        titles = '\n'.join([s['title'] for s in self.secrets.values()])
        opcodes = '\n'.join([s['opcode'] for s in self.secrets.values()])
        secret_list.description = opcodes
        secret_list.set_footer(text=titles)
        return secret_list

    def view_secret(self, opcode):
        opcode_string = f'OPCODE:{opcode}'
        if opcode_string in self.secrets:
            s = self.secrets[opcode_string]
            secret = discord.Embed(title=opcode_string)
            secret.description = s['text']
            secret.set_footer(text=s['title'])
        else:
            secret = discord.Embed(title=f'classified')
        return secret

with open('dev.json', 'r') as f:
    PROBLEMS = json.load(f)

categories = {}
for p in PROBLEMS:
    if not p['category'] in categories:
        categories[p['category']] = []
    categories[p['category']].append(p)

async def level_up_message(channel, player):
    await channel.send('---------------------\n' +
                       f'{player.name} ahora es nivel {player.level}!', embed=player.stats())

async def get_problem(channel, user_id, flags):
    letter_to_index = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4}
    emojis = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]

    cat = random.choice(list(categories.keys()))
    if flags != None:
        for c in categories.keys():
            print(c)
            if c.startswith(flags):
                cat = c
                break
    problem = random.choice(categories[cat])
    #['a ) 5 ', ' b ) 6.25 ', ' c ) 6.75 ', ' d ) 6.87 ', ' e ) 7.25']
    text = f'Category: {cat}\n' + problem['Problem'] + '\n' + problem['options']
    correct = problem['correct']
    print(correct)

    msg = await channel.send(text)
    for i in range(5):
        await msg.add_reaction(emojis[i])
    correct_emoji = emojis[letter_to_index[correct]]

    try:
        t0 = time.time()
        payload = await client.wait_for('raw_reaction_add',
                                        timeout=TIME,
                                        check = lambda payload:
                                            payload.message_id == msg.id and
                                            payload.member.id == user_id and
                                            str(payload.emoji) in emojis)
    except asyncio.TimeoutError:
        await msg.channel.send(f'se acabo el tiempo')
    else:
        t1 = time.time()
        total = (TIME - (t1-t0)) / 3
        print(total)
        player = PLAYERS[user_id]
        if str(payload.emoji) == correct_emoji:
            gain = random.randint(ceil(total - (XP_RATE * total)), ceil(total + (XP_RATE * total)))
            await msg.channel.send(f'{payload.member.name} ha contestado correctamente! +{gain}xp')
            await msg.channel.send(f'```+1 credit```')
            player.gain_credits(1)
            if player.gain_xp(gain):
                await level_up_message(channel, player)

        else:
            total = total / 5
            loss = -1 * random.randint(floor(total - (XP_RATE * total)), floor(total + (XP_RATE * total)))
            await msg.channel.send(f'contestacion incorrecta! {loss}xp')
            player.gain_xp(loss)
    
async def get_joke(channel):
    options = ['👍', '👎']
    reactions = ['😂', '😒']
    msg = await channel.send('Quieres escuchar un chiste?')
    for e in options:
        await msg.add_reaction(e)
    try:
        payload = await client.wait_for('raw_reaction_add',
                                        timeout=45,
                                        check = lambda payload:
                                            payload.message_id == msg.id and
                                            payload.member.id != client.user.id and
                                            str(payload.emoji) in options)
    except asyncio.TimeoutError:
        ignored_msg = await msg.channel.send('Esta bien, pichea.')
        time.sleep(5)
        await msg.delete()
        await ignored_msg.delete()
    else:
        if str(payload.emoji) == '👍':
            category = random.choice(list(JOKES.keys()))
            joke = random.choice(JOKES[category])

            embed = discord.Embed(title=joke['title'])
            embed.description = joke['text']
            embed.set_footer(text=f'categoria: {category}')
            if 'image' in joke:
                embed.set_image(url=joke['image'])
                embed.description += joke['image'] #add url to text
            m = await channel.send('', embed=embed)

            for e in reactions:
                await m.add_reaction(e)
            try:
                payload = await client.wait_for('raw_reaction_add',
                                                timeout=30,
                                                check = lambda payload:
                                                    payload.message_id == m.id and
                                                    payload.member.id != client.user.id and
                                                    str(payload.emoji) in reactions)
            except asyncio.TimeoutError:
                await m.channel.send('Wow, tan malo estaba? Pichea.')

            else:
                if str(payload.emoji) == '😂':
                    to_gain = 1
                    await msg.channel.send(f'Si {payload.member.name}, soy muy graciosito.')
                else:
                    to_gain = -1
                    await msg.channel.send(f'Que sabes tu? {payload.member.name} el comediante? ')

                if payload.member.id in PLAYERS:
                    player = PLAYERS[payload.member.id]
                    player.gain_humor(to_gain)
        else:
            await msg.channel.send('Esta bien, no digo nada.')
    save(PLAYERS)

async def get_secret(channel):
    msg = await channel.send('Tengo un secreto. Quieres saberlo?')
    await msg.add_reaction('✅')
    time.sleep(1)
    try:
        payload = await client.wait_for('raw_reaction_add',
                                        timeout=10,
                                        check = lambda payload:
                                            payload.message_id == msg.id and
                                            payload.member.id != client.user.id and
                                            str(payload.emoji) == '✅')
    except asyncio.TimeoutError:
        await msg.channel.send('Ah, ya se me olvido.')
    else:
        secret = random.choice(VISIONS)
        VISIONS.remove(secret)
        
        title = secret[0:15]
        opcode = f'{secret[16:23]}{random.randint(0, 999999)}'
        text = secret[30:]

        secret = {'title': title, 'opcode':opcode, 'text': text}

        player = PLAYERS[payload.member.id]
        player.get_secret(secret)
        
        await msg.channel.send('Interesante, verdad?')
        await msg.channel.send(f'```{len(VISIONS)}/100 restantes```')

        with open('vis.json', 'w') as v:
            json.dump(VISIONS, v)
        save(PLAYERS)

PLAYERS = {}

def save(PLAYERS):
    with open('PLAYERS.json', 'w') as f:
        json.dump([p.export_data() for p in PLAYERS.values()], f)

def load():
    with open('PLAYERS.json', 'r') as f:
        prelim = json.load(f)
        for p in prelim:
            player = Player('', 0, '')
            player.import_data(p)
            PLAYERS[p['id']] = player


with open('TOKEN.txt', 'r') as t:
    TOKEN = t.read()

with open('vis.json', 'r') as v:
    VISIONS = json.load(v)
    print(len(VISIONS))

client = discord.Client()

@client.event
async def on_ready():
    bot_channels = [ch for ch in client.get_all_channels() if 'bot' in ch.name.lower()]

    try:
        load()
        print('data loaded')
    except:
        print('no valid prior data')

    while True:
        await asyncio.sleep(random.randint(1600-300, 1600+300))
        if random.randint(0, 20) == 0:
            await get_secret(random.choice(bot_channels))
        else:
            await get_joke(random.choice(bot_channels))
    

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 283595771377614850:
        if message.content == '&save':
            save(PLAYERS)
        elif message.content == '&joketest':
            await get_joke(message.channel)
        elif message.content == '&secrettest':
            await get_secret(message.channel)
        elif message.content == '&players':
            for p in PLAYERS.values():
                await message.channel.send(p.name)

    if message.content == '&info':
        info_embed = discord.Embed(title='info')
        info_embed.description = ("-&join para matricularse\n"
                                  "-&stats para stats\n"
                                  "-&pCATEGORY para problema nuevo\n"
                                  "-&pepe para musica\n"
                                  "-&joke para un chiste (cuesta 1 credit)\n"
                                  "-&secrets para ver tus secretos\n"
                                  "-&vsCODE para ver un secreto\n\n"
                                  "Digo chistes de vez en cuando. (solo en canales con nombre 'bot')\n\n"
                                  "categories:\n"
                                  "physics, probability, geometry, general, other.")
        await message.channel.send('', embed=info_embed)

    if message.author.id in PLAYERS:
        player = PLAYERS[message.author.id]
        
        if message.content == '&stats':
            url = message.author.avatar_url
            player.update_url(url)
            await message.channel.send('', embed=player.stats())

        elif message.content == '&secrets':
            await message.channel.send('', embed=player.get_secrets())
            
        elif message.content.startswith('&vs'):
            opcode = None
            if len(message.content) > 2:
                opcode = message.content[3:]
                print(opcode)
                await message.channel.send('', embed=player.view_secret(opcode))

        elif message.content == '&pepe':
            song = discord.Embed(title='Pepe pepe pepe')
            song.description = SONG
            song.set_thumbnail(url='https://img.youtube.com/vi/qbkwE-XgZPI/default.jpg')
            await message.channel.send('https://www.youtube.com/watch?v=qbkwE-XgZPI', embed=song)

        elif message.content.startswith('&p') and message.content != '&players':
            flags = None
            if len(message.content) > 2:
                flags = message.content[2:]
            print(flags)
            await get_problem(message.channel, message.author.id, flags)
            save(PLAYERS)

        #credit ops
        elif message.content == '&joke':
            if player.credits > 0:
                minus = -1
                await message.channel.send(f'```{minus} credit```')
                player.gain_credits(minus)
                await get_joke(message.channel)
            else:
                await message.channel.send(f'```insufficient credits```')

    else:
        if message.content == '&join':
            p = message.author
            role = get(message.guild.roles, name='Mosca Scholar')
            await p.add_roles(role)
            PLAYERS[p.id] = Player(p.name, p.id, p.avatar_url)
            await message.channel.send(f'<@{message.author.id}> ahora es un Mosca Scholar')
            save(PLAYERS)

client.run(TOKEN)
