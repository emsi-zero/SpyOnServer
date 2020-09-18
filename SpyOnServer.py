import discord
from discord.ext import commands
import random

# game words
words = ['Physics' , 'Maths' , 'Chemistry']


# player. not users! user are linked to players in the Game object. 
class player:
    
    def __init__(self, name):
        self.name = name
        self.wins = 0.0
        self.spy = False
        self.suspicions = 0
        self.vote = False

    #adds to players wins for scoreboard
    def wins(self):
        self.wins += 1

    #reinitiates player spy status
    def replay(self):
        self.spy = False

    #sets the player as the spy
    def setSpy(self):
        self.spy = True    


#Game object. all the game properties are in stored in this object.
class Game:
    def __init__(self):
        self.GameStarted = False
        self.players = {}
        self.gameMessage = None
        self.startMessage = None
        self.channel = None
        self.votes = {}
        self.spy = None
        self.word = None
    
    #adds a player to the players list.
    async def addPlayer(self, member):
        self.players[member] = player(member.name)
        print(f'player {member.name} is added')

    # removes a player from players list.
    async def removePlayer(self , member):
        self.players.pop(member)
        print(f'player {member.name} is removed')


    #assign the spy by random from players list.
    async def assignSpy(self):
        self.spy = random.choice(list(self.players.values()))
        self.spy.setSpy()

    # finds and return the most suspicious player.
    def mostVoted(self):
        voted = player('sb')
        for culprit in self.players.values():
            if culprit.suspicions > voted.suspicions:
                voted = culprit
        
        return voted

    #sends all users DMs. the spy will recieve "you are the SPY" and the rest will recieve the game word
    async def sendUserMessages(self):
        for user in self.players.keys():
            if self.players[user] is self.spy:
                await user.send('You are the SPY!')
            else:
                await user.send('the word is ' + self.word)

    #re-initiates the game object, sends the gameMessage and start the game. 
    async def start(self):
        await self.channel.send('Beep! Beep! Beep!')
        self.word = random.choice(words)
        # checks if the game has begun and send relative message
        if self.GameStarted == False:
            self.GameStarted = True
            self.gameMessage = await self.channel.send('To All Agents! \nATTENTION! \nThere is a RAT among us! Find the culprit and bring him in ASAP!')

            await self.assignSpy()
            await self.sendUserMessages()
            listOfPlayers = 'Agents: \n'
            n = 0
            character= ['0️⃣', '1️⃣' , '2️⃣' , '3️⃣' , '4️⃣', '5️⃣' , '6️⃣' , '7️⃣' , '8️⃣' , '9️⃣', '🔟' ]
            for player in self.players.values():
                listOfPlayers += f'{n} : {player.name} \n'
                reaction = await self.gameMessage.add_reaction(character[n])
                self.votes[character[n]] = player
                n += 1

            await self.channel.send(listOfPlayers)

        else:
             await set.channel.send('The search has already begun! Continue to find the Spy!')


    #resets the game .
    def reset(self):
        self.spy = None
        self.GameStarted = False

    #finishes the game and reloads the game object.
    async def finishGame(self):
        if self.spy is self.mostVoted() :
            for player in self.players.values():
                await self.channel.send(f'The Spy is {self.spy.name}! Congratulations, Agent {player.name}! You are rewarded +0.5pts and the spy will lose 0.5 pts!')
                if not player.spy:
                    player.wins += 0.5
                else:
                    player.wins -= 0.5
        else :
            await self.channel.send(f'You have FAILED, Agent! The spy has won this time! {self.spy.name} was the culprit!')
            self.spy.wins += 1.0

        self.reset()
        

#creates the client
client = commands.Bot(command_prefix='/')

# a dictionary of games
games = {}

# resends the startMessage
async def callStartMessage(game):
    channel = game.channel
    game.startMessage = await channel.send('Are you ready, Agent?!')
    await game.startMessage.add_reaction('➕')

#This event makes sure that the bot is online
@client.event
async def on_ready():
    print('Bot is online!')
    

#this events triggers by adding reactions and handles the game joining and adding votes.
@client.event
async def on_raw_reaction_add(payload):
    guild = await client.fetch_guild(payload.guild_id)
    game = games[guild]
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = await client.fetch_user(payload.user_id)
    reaction = payload.emoji
    # print('reaction added')
    if message.id == game.startMessage.id :
        if not game.GameStarted :
            if not member.bot:
                await game.addPlayer(member)
            else:
                print('this player is a bot!!!!')
        else :
            await channel.send('The Game has already started!')
            await message.remove_reaction(reaction , member)

    elif message.id == game.gameMessage.id :
        if not member.bot and not game.players[member].vote :
            game.votes[reaction.name].suspicions += 1
            game.players[member].vote = True
        elif not member.bot and game.players[member].vote :
            for reactionCnt in message.reactions :
                if reactionCnt.emoji != reaction.name:
                    await message.remove_reaction(reactionCnt , member)
            
#this events triggers by removing reactions and handles the game leaving and removing votes.
@client.event
async def on_raw_reaction_remove(payload):
    guild = await client.fetch_guild(payload.guild_id)
    game = games[guild]
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = await client.fetch_user(payload.user_id)
    reaction = payload.emoji
    # print('reaction removed')
    if message.id == game.startMessage.id :
        if not game.GameStarted:
            if not member.bot:
                await game.removePlayer(member)
            else:
                print('this player is a bot!!!!')

    elif message.id == game.gameMessage.id :
        game.votes[reaction.name].suspicions -= 1
        game.players[member].vote = False
            


# makes the bot ready
@client.command()
async def SpyOnServer(ctx):
    guild = ctx.message.guild
    game = Game()
    games[guild] = game
    game.channel = await guild.create_text_channel('Top Secret Channel')
    everyoneRole = guild.get_role(guild.id)
    await game.channel.set_permissions(everyoneRole , read_messages = True , send_messages = False)
    await callStartMessage(game)


#Starts the Game
@client.command()
async def GameStart(ctx):
    guild = ctx.message.guild
    game = games[guild]

    await game.start()
    
#this command finishes and resets the game
@client.command()
async def finishGame(ctx):
    guild = ctx.message.guild
    game = games[guild]
    await game.finishGame()


        
    
token = open("token.txt" , "r")

client.run(token.readline())#recieves the token generated by discord as string. My token is regenarate! :D
