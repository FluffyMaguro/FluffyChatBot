import socket
import string
import time
import threading
import cv2
import numpy as np
import pyautogui
import os
import pandas as pd
import xml.etree.ElementTree as ET
import configparser

### Set up is loaded from a config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

BANKFILE = config['CONFIG']['BANKFILE'] #location of bank file, for example: 'C:\\Users\\Maguro\\Documents\\StarCraft II\\Accounts\\114803619\\1-S2-1-4189373\\Banks\\1-S2-1-4189373\\MMTwitchIntegration.SC2Bank'
CHANNEL = config['CONFIG']['CHANNEL'] #channel name where bot operates (all lowercase)
NICK = config['CONFIG']['NICK'] #bot name (all lowercase)
PASS = config['CONFIG']['PASS'] #twitch API you get for your bot: "oauth:r7x5n................."
HOST = config['CONFIG']['HOST'] #for twitch: "irc.twitch.tv"
PORT = int(config['CONFIG']['PORT']) #port, for twitch: "6667"

### Init some variables
findingActivated = True
postCurrent = False
mutatorsFound = False
CommandNumber = np.random.randint(1,1000000) #just add this number to each command, so the same commands don't have the same name
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
    GMActive = False 
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
                    response = sendGameMessage('join', user) 
                    print('user joined:', user)

            #other commands      

            if "@VeryFluffyBot" in line and not(console(line)):
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'*little fluffy bot likes tuna*')

            if "!tuna" == first_word:
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'*munches* thunk you! ')

            if "!stop" == first_word and user == CHANNEL: 
                findingActivated = False
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'No catching little mutator things, fine! *yawns*')

            if "!start" == first_word and user == CHANNEL:
                postCurrent = False 
                findingActivated = True
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'Find them all, got it! *sniffs*')

            if "!website" == first_word or "!site" == first_word or "!blog" == first_word:
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'www.maguro.one')

            if "!twitter" == first_word:
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'twitter.com/FluffyMaguro')

            if "!mutators" == first_word:
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'www.maguro.one/p/mutators.html')

            if "!commands" == first_word:
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,'!website, !twitter, !mutators, !current')

            if "!current" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if findingActivated == False or mutatorsFound == False:
                    sendMessage(s,'cannot do that right now')
                else:
                    sendMessage(s,'let me see...')
                    postCurrent = True

        time.sleep(1)

def getBrutalPlus (diff):
        level = 'undefined'
        if 0 < diff < 4:
            level = 'Too easy for Brutal+'
        if 4 <= diff <= 6:
            level = 'Brutal+1'
        if 7 <= diff <= 8:
            level = 'Brutal+2'
        if 9 <= diff <= 10:
            level = 'Brutal+3'
        if 11 <= diff <= 12:
            level = 'Brutal+4'
        if 13 <= diff <= 14:
            level = 'Brutal+4.5'
        if 15 <= diff <= 16:
            level = 'Brutal+5'
        if 17 <= diff <= 18:
            level = 'Brutal+5.5'
        if 19 <= diff <= 20:
            level = 'Brutal+6'
        if  diff > 20:
            level = 'Harder than any Brutal+'
        return level


def FindMutators():
    global postCurrent
    global mutatorsFound

    MutatorDescriptions = {"Concussive Attacks": "Player units are slowed by all enemy attacks.", "Eminent Domain": "Enemies gain control of your structures after destroying them.", "Evasive Maneuvers": "Enemy units teleport a short distance away upon taking damage.", "Life Leech": "Enemy units and structures steal life or shields whenever they do damage.", "Orbital Strike": "Enemy Orbital Strikes are periodically fired throughout the map.", "Photon Overload": "All enemy structures attack nearby hostile units.", "Shortsighted": "Player units and structures have reduced vision range.", "Temporal Field": "Enemy Temporal Fields are periodically deployed throughout the map.", "Time Warp": "Enemy Time Warps are periodically deployed throughout the map.", "Alien Incubation": "All enemy units spawn Broodlings upon death.", "Barrier": "Enemy units and structures gain a temporary shield upon the first time they take damage.", "Darkness": "Previously explored areas remain blacked out on the minimap while outside of player vision.", "Hardened Will": "Enemy Heroic units reduce all incoming damage to a maximum of 10 when any non-heroic enemy unit is near them.", "Inspiration": "Enemy Heroic units increase the attack speed and armor of all enemies within a small range. ", "Laser Drill": "An enemy Laser Drill constantly attacks player units within enemy vision.", "Long Range": "Enemy units and structures have increased weapon and vision range.", "Mineral Shields": "Mineral clusters at player bases are periodically encased in a shield which must be destroyed for gathering to continue.", "Moment of Silence": "When a Heroic enemy dies, all player units around it will reflect on their transgressions, leaving them unable to attack or use abilities.", "Purifier Beam": "An enemy Purifier Beam moves across the map toward nearby player units.", "Scorched Earth": "Enemy units set the terrain on fire upon death.", "Speed Freaks": "Enemy units have increased movement speed.", "Twister": "Tornadoes move across the map, damaging and knocking back player units in their path.", "Walking Infested": "Enemy units spawn Infested Terran upon death in numbers according to the unit's life.", "Aggressive Deployment": "Additional enemy units are periodically deployed onto the battlefield.", "Diffusion": "Damage dealt to enemies is split evenly across all nearby units, including your own.", "Double-Edged": "Your units also receive all the damage they deal, but they are healed over time.", "Fatal Attraction": "When enemy units and structures die, any of your nearby units are pulled to their location.", "Fear": "Player units will occasionally stop attacking and run around in fear upon taking damage.", "Going Nuclear": "Nukes are launched at random throughout the map.", "Lava Burst": "Lava periodically bursts from the ground at random locations and deals damage to player air and ground units.", "Missile Command": "Endless missile bombardments target your structures and must be shot down throughout the mission.", "Outbreak": "Enemy Infested Terrans spawn continuously around the map.", "Self Destruction": "Enemy units explode and deal damage to nearby player units upon death.", "We Move Unseen": "All enemy units are permanently cloaked.", "Mag-nificent": "Mag Mines are deployed throughout the map at the start of the mission.", "Blizzard": "Storm clouds move across the map, damaging and freezing player units in their path.", "Avenger": "Enemy units gain increased attack speed, movement speed, armor, life, and life-regeneration when nearby enemy units die.", "Micro Transactions": "Giving commands to your units costs resources based on the unit's cost.", "Mutually Assured Destruction": "Enemy Hybrid units detonate a Nuke upon death.", "Power Overwhelming": "All enemy units have energy and use random abilities.", "Slim Pickings": "Player worker units gather resources at a reduced rate, but resource pickups spawn throughout the map.", "Void Reanimators": "Void Reanimators wander the battlefield, bringing your enemies back to life.", "Kill Bots": "Offensive robots of a mysterious origin have been unleashed on the Koprulu sector, intent on destruction. Through cunning engineering, they are invincible until their pre-programmed kill counter has been filled. After that occurs, they will shut down. But can you survive for that long?", "Minesweeper": "Groups of Widow Mines and Spider Mines are buried throughout the battlefield.", "Black Death": "Some enemy units carry a plague that deals damage over time and spreads to other nearby units. The plague spreads to your units when the enemy unit is killed.", "Just Die!": "Enemy units are automatically revived upon death.", "Polarity": "Each enemy unit is immune to either your units or your ally's units.", "Transmutation": "Enemy units have a chance to transform into more powerful units whenever they deal damage.", "Propagators": "Shapeless lifeforms creep toward your base, transforming all of the units and structures they touch into copies of themselves.", "Heroes from the Storm": "Attack waves will be joined by heroes of increasing power.", "Void Rifts": "Void Rifts periodically appear in random locations and spawn enemy units until destroyed."}
    MutatorDiffScore = {"Concussive Attacks": "1", "Eminent Domain": "1", "Evasive Maneuvers": "1", "Life Leech": "1", "Orbital Strike": "1", "Photon Overload": "1", "Shortsighted": "1", "Temporal Field": "1", "Time Warp": "1", "Alien Incubation": "2", "Barrier": "2", "Darkness": "2", "Hardened Will": "2", "Inspiration": "2", "Laser Drill": "2", "Long Range": "2", "Mineral Shields": "2", "Moment of Silence": "2", "Purifier Beam": "2", "Scorched Earth": "2", "Speed Freaks": "2", "Twister": "2", "Walking Infested": "2", "Aggressive Deployment": "3", "Diffusion": "3", "Double-Edged": "3", "Fatal Attraction": "3", "Fear": "3", "Going Nuclear": "3", "Lava Burst": "3", "Missile Command": "3", "Outbreak": "3", "Self Destruction": "3", "We Move Unseen": "3", "Mag-nificent": "4", "Blizzard": "4", "Avenger": "5", "Micro Transactions": "5", "Mutually Assured Destruction": "5", "Power Overwhelming": "5", "Slim Pickings": "5", "Void Reanimators": "5", "Kill Bots": "6", "Minesweeper": "6", "Black Death": "7", "Just Die!": "7", "Polarity": "7", "Transmutation": "7", "Propagators": "8", "Heroes from the Storm": "10", "Void Rifts": "10"}

    PATH = 'Mutator Icons'
    INTERVAL = 3 #seconds
    PreviousMutators = []  
    colors = ['Red', 'Blue']
    currentColor = 0  

    while True:

        if findingActivated == False: #skip if the function is deactivated via chat command (temporarily)
            time.sleep(INTERVAL)
            print('//mutator find disabled')
            continue

        MutatorDF = pd.DataFrame(columns=['Mutator', 'Description', 'Y','X','Max_val'])
        NewMutators = []
        a = 0
        FewMutators = False #these prevent doing more work than necessary, if it's either small or big, the checks only those later
        ManyMutators = False
        entries = os.scandir(PATH) #for some reason this needs to be rescaned
        
        img = pyautogui.screenshot(region=(1810,380, 110, 480))
        img_rgb = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        for entry in entries:
            if entry.is_file() and entry.name.endswith('.png'):

                if len(entry.name.split('_')) > 1 and FewMutators: #tells whether to load small or not
                    continue
                if len(entry.name.split('_')) == 1 and ManyMutators:
                    continue

                template = cv2.imread(PATH +'/'+ entry.name,1)

                res = cv2.matchTemplate(img_rgb,template,cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                threshold = 0.9
                loc = np.where( res >= threshold) #array with values where res > threshold
                        
                if np.count_nonzero(loc)>0:
                    mutatorsFound = True
                    if ManyMutators == False and FewMutators == False:
                        if len(entry.name.split('_')) > 1: #was it a small of big one?
                            ManyMutators = True
                        else:
                            FewMutators = True

                    NewMutators.append(entry.name.split('.')[0]) #add to pd frames to sort later by position (x,y)
                    MutatorDF.loc[a] = [entry.name.split('.')[0].split('_')[0]]+[MutatorDescriptions[entry.name.split('.')[0].split('_')[0]]]+[round(max_loc[1]/10,0)]+[round(max_loc[0]/10,0)]+[round(max_val,3)]
                    a += 1

        MutatorsNotChanged = len(set(PreviousMutators) & set(NewMutators)) >= len(NewMutators)  

        if MutatorsNotChanged and postCurrent == False:
            pass
        else:
            postCurrent = False
            PreviousMutators = NewMutators
            
            if not(MutatorsNotChanged): #sort & save only if mutations changed, and not when using !current command
                SortedMutatorDF = MutatorDF.sort_values(by=['Y','X'], ascending=True).reset_index()
                MutatorDF['Mutator'].to_csv('MutatorLog.csv', mode='a', header=False, sep ='\t')

            currentColor += 1
            if currentColor >= len(colors): #loop back if max
                currentColor = 0               

            MutationDifficulty = 0
            Message = '/color ' + colors[currentColor]
            sendMessage(s,Message)

            for index, row in SortedMutatorDF.iterrows():
                print(index, row['Mutator'],' ', row['Max_val'])
                Message = row['Mutator'] + ' ('+ MutatorDiffScore[row['Mutator']] +') - ' + row['Description'] #'/me : '
                sendMessage(s,Message)
                MutationDifficulty += int(MutatorDiffScore[row['Mutator']])

            sendMessage(s,'Total difficulty score: ' + str(MutationDifficulty) +' ('+getBrutalPlus(MutationDifficulty)+')')

        time.sleep(INTERVAL)

#start the bot
if (__name__ == "__main__"):
    s = openSocket()
    joinRoom(s)
    t1 = threading.Thread(target = FindMutators)
    t1.start()
    t2 = threading.Thread(target = pingsAndMessages)
    t2.start()
    