import socket
import string
import time
import xml.etree.ElementTree as ET
import configparser
import random

### Set up is loaded from a config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

local_test = False #for local testing, different bank file & no mutator log saving

if local_test == True:
	BANKFILE = config['CONFIG']['LOCALBANKFILE']
else:
	BANKFILE = config['CONFIG']['BANKFILE'] #location of bank file, for example: 'C:\\Users\\Maguro\\Documents\\StarCraft II\\Accounts\\114803619\\1-S2-1-4189373\\Banks\\1-S2-1-4189373\\MMTwitchIntegration.SC2Bank'

CHANNEL = config['CONFIG']['CHANNEL'] #channel name where bot operates (all lowercase)
NICK = config['CONFIG']['NICK'] #bot name (all lowercase)
PASS = config['CONFIG']['PASS'] #twitch API you get for your bot: "oauth:r7x5n................."
HOST = config['CONFIG']['HOST'] #for twitch: "irc.twitch.tv"
PORT = int(config['CONFIG']['PORT']) #port, for twitch: "6667"

### Init some variables
CommandNumber = random.randint(1,1000000) #just add this number to each command, so the same commands don't have the same name
MutatorList = ['walking infested', 'outbreak', 'darkness', 'time warp', 'speed freaks', 'mag-nificent', 'mineral shields', 'barrier', 'avenger', 'evasive maneuvers', 'scorched earth', 'lava burst', 'self destruction', 'aggressive deployment', 'alien incubation', 'laser drill', 'long range', 'shortsighted', 'mutually assured destruction', 'we move unseen', 'slim pickings', 'concussive attacks', 'just die!', 'temporal field', 'void rifts', 'twister', 'orbital strike', 'purifier beam', 'blizzard', 'fear', 'photon overload', 'minesweeper', 'void reanimators', 'going nuclear', 'life leech', 'power overwhelming', 'micro transactions', 'missile command', 'vertigo', 'polarity', 'transmutation', 'afraid of the dark', 'trick or treat', 'turkey shoot', 'sharing is caring', 'diffusion', 'black death', 'eminent domain', 'gift exchange', 'naughty list', 'extreme caution', 'heroes from the storm', 'inspiration', 'hardened will', 'fireworks', 'lucky envelopes', 'double-edged', 'fatal attraction', 'propagators', 'moment of silence', 'kill bots', 'boom bots', 'the mist', 'the usual suspects', 'supreme commander', 'shapeshifters', 'rip field generators', 'repulsive field', 'old times', 'nuclear mines', 'necronomicon', 'mothership', 'matryoshka', 'level playing field', 'infestation station', 'i collect, i change', 'great wall', 'endurance', 'dark mirror', 'bloodlust']


def openSocket():
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
    s.send("JOIN #{}\r\n".format(CHANNEL).encode("utf-8"))
    return s

def joinRoom(s):
    readbuffer_join = "".encode()
    Loading = True
    while Loading:
        readbuffer_join = s.recv(1024)
        readbuffer_join = readbuffer_join.decode()
        temp = readbuffer_join.split("\n")
        readbuffer_join = readbuffer_join.encode()
        readbuffer_join = temp.pop()

        for line in temp:
            Loading = loadingComplete(line)

    print("VeryFluffyBot has joined the chat")
    sendMessage(s,'/color green')

def loadingComplete(line):
    if ("End of /NAMES list" in line):
        return False
    else:
        return True

def getUser(line):
    separate = line.split(":", 2)
    user = separate[1].split("!", 1)[0]
    return user

def getMessage(line):
    separate = line.split(":", 2)
    message = separate[2]
    return message

def console(line):
    if "PRIVMSG" in line:
        return False
    else:
        return True    

def sendMessage(s, message):
    messageTemp = "PRIVMSG #" + CHANNEL + " :" + message
    print("(sent: " + message+')')
    try:
        s.send("{}\r\n".format(messageTemp).encode("utf-8"))
    except BrokenPipeError:
        s = openSocket()
        s.send("{}\r\n".format(messageTemp).encode("utf-8"))


def sendGameMessage(type, message):
    global CommandNumber
    try:
	    tree = ET.parse(BANKFILE) #reload to account for new changes
	    root = tree.getroot()

	    if type == 'mutator':
	        message = message.lower()
	        if not(message in MutatorList):     
	            print('ERROR, mutator not in the list')
	            return '{incorrect mutator name}'
	    
	    for child in root: 
	        if child.attrib['name'] == 'Commands':
	            CommandNumber += 1
	            child.append((ET.fromstring('<Key name="' + type + ' ' + str(CommandNumber) + '"><Value string="'+ message +'" /></Key>')))
	            tree.write(BANKFILE)
	            return '{request sent}'
    except:
    	print('ERROR – bank not loaded properly, message not sent')
         

def pingsAndMessages():
    global findingActivated
    global postCurrent
    # global CommandNumber
    GMActive = True 
    GMActiveFull = False 
    chatColor = 'green'
    
    while True:
        try:
            readbuffer = s.recv(1024)
            readbuffer = readbuffer.decode()
            temp = readbuffer.split("\n")
            readbuffer = readbuffer.encode()
            readbuffer = temp.pop()
        except:
            temp = ""

        for line in temp:
            if line == "":
                break
            
            if "PING" in line and console(line):
                msgg = "PONG :tmi.twitch.tv\r\n".encode()
                s.send(msgg)
                print(msgg)
                break

            #Commands
            user = getUser(line) 
            message = getMessage(line)
            first_word = message.split()[0]
            try:
                following_words = message.split(' ',1)[1].rstrip() #rstrip strips the end (spaces, breaks) from the string
            except:
                following_words = ''
            print(user + ": " + message.rstrip())

            #twitch integration into the game

            if "!gm" == first_word and user == CHANNEL: 
                sendMessage(s,'/color ' + chatColor)
                if 'full' in following_words:
                    GMActive = True
                    GMActiveFull = True
                    sendMessage(s,'{Full game integration} !mutator, !spawn, and !resources commands enabled') #mutators, spawning, resources
                elif 'stop' in following_words:
                    GMActive = False
                    GMActiveFull = False
                    sendMessage(s,'{Game integration disabled}') #mutators, spawning, resources
                else:
                    GMActive = True
                    GMActiveFull = False
                    sendMessage(s,'{Partial game integration} !join and !message commands active') #mutators, spawning, resources

            if "!message" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActive == False:
                    sendMessage(s,'{Game integration inactive}')
                else:
                    print('message sent:',user,following_words)
                    sendGameMessage('message', user +': ' + following_words)

            if "!mutator" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('mutator', following_words) 
                    print('mutator started:',following_words)

            if "!spawn" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('spawn', following_words) 
                    print('unit spawned:',following_words)

            if "!resources" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('resources', following_words) 
                    print('resources given:',following_words)

            if "!join" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActive == False:
                    sendMessage(s,'{Game integration inactive}')
                else:
                    response = sendGameMessage('join', user + ' %' + following_words) 
                    print('user joined:', user)

            #other commands      
            if "@VeryFluffyBot" in line and not(console(line)):
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,config['RESPONSES']['RESPONSE'])

            after_command = first_word.replace('!','') #strip of "!"

            if after_command in config['RESPONSES'].keys(): 
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,config['RESPONSES'][after_command])

        time.sleep(1)


#start the bot
if (__name__ == "__main__"):
    s = openSocket()
    joinRoom(s)
    pingsAndMessages()
    