import socket
import string
import time
import threading
# import cv2
# import numpy as np
# import pyautogui
import os
# import pandas as pd
import xml.etree.ElementTree as ET
import configparser
import random
import datetime
# import requests
# from ReplayAnalysis import analyse_replay

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
ACCOUNTDIR = config['CONFIG']['ACCOUNTDIR']
PORT = int(config['CONFIG']['PORT']) #port, for twitch: "6667"

PLAYER_NAMES = []
for player in config['CONFIG']['PLAYERNAME'].split(','):
    PLAYER_NAMES.append(player)

try:
    RESIZECOEF = float(config['CONFIG']['RESIZECOEF'])
except:
    RESIZECOEF = 1

BannedMutators = []
for mutator in config['CONFIG']['BANNEDMUTATORS'].split(','):
    BannedMutators.append(mutator.lower().rstrip().lstrip())

OtherCommands = []
for command in config['CONFIG']['OTHERCOMMANDS'].split(','):
    com = command.lower().rstrip().lstrip()
    if com != "":
        OtherCommands.append(command.lower().rstrip().lstrip())


### Init some variables
findingActivated = True
postCurrent = False
mutatorsFound = False
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
    if not('/color' in message):
        print("(sent: " + message+')')
    try:
        s.send("{}\r\n".format(messageTemp).encode("utf-8"))
    except BrokenPipeError:
        s = openSocket()
        s.send("{}\r\n".format(messageTemp).encode("utf-8"))


def sendGameMessage(type, message, user):
    global CommandNumber
    try:
        tree = ET.parse(BANKFILE) #reload to account for new changes
        root = tree.getroot()

        if type == 'mutator':
            message = message.lower()
            mutator = message.replace(' disable','')
            if not(mutator in MutatorList):     
                print('ERROR, mutator not in the list')
                return '{incorrect mutator name}'

            if mutator in BannedMutators:
                print('Mutator is banned!')
                return '{this mutator is banned from use and will not be activated!}'
        
        for child in root: 
            if child.attrib['name'] == 'Commands':
                CommandNumber += 1
                child.append((ET.fromstring('<Key name="' + type + ' ' + str(CommandNumber) +' #'+ user +'"><Value string="'+ message +'" /></Key>')))
                tree.write(BANKFILE)
                return ''
    except:
        print('ERROR – bank not loaded properly, message not sent')
         

def saveMessage(user,message):
    with open('ChatLog.txt', 'a') as file:
        time_now = str(datetime.datetime.now())[:-7]
        file.write('\n({})\t{}:\t{}'.format(time_now,user,message.rstrip()))


def pingsAndMessages():
    global findingActivated
    global postCurrent
    # global CommandNumber
    GMActive = True 
    GMActiveFull = False 
    chatColor = 'green'
    GreetedUsers = []

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
            first_word = message.split()[0].lower()
            saveMessage(user,message)
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
                    sendGameMessage('message', user +': ' + following_words,user)

            if "!mutator" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('mutator', following_words,user) 
                    print('mutator started:',following_words)
                    if response != "":
                        sendMessage(s,response)

            if "!spawn" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('spawn', following_words,user) 
                    print('unit spawned:',following_words)

            if "!resources" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActiveFull == False:
                    sendMessage(s,'{Full game integration inactive}')
                else:
                    response = sendGameMessage('resources', following_words,user) 
                    print('resources given:',following_words)

            if "!join" == first_word:
                sendMessage(s,'/color ' + chatColor)
                if GMActive == False:
                    sendMessage(s,'{Game integration inactive}')
                else:
                    response = sendGameMessage('join', following_words, user) 
                    print('user joined:', user)

            if first_word[1:] in OtherCommands: #this is for future command that can be added later
                sendGameMessage(first_word[1:], following_words, user) 

            #other commands      
            if "@VeryFluffyBot" in line and not(console(line)):
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,config['RESPONSES']['RESPONSE'])

            #general responses configurable in config.ini    
            after_command = first_word.replace('!','') #strip of "!"

            if after_command in config['RESPONSES'].keys(): 
                sendMessage(s,'/color ' + chatColor)
                sendMessage(s,config['RESPONSES'][after_command])


            if user in config['GREETINGS'].keys() and not(user in GreetedUsers):
                try:
                    GreetedUsers.append(user)
                    sendMessage(s,'/color ' + chatColor)
                    possibleresponses = list(config['GREETINGS'][user].split("/ ")) 
                    sendMessage(s,random.choice(possibleresponses))
                except:
                    pass

            #commands controlling mutators
            # if "!stop" == first_word and user == CHANNEL: 
            #     findingActivated = False
            #     sendMessage(s,'/color ' + chatColor)
            #     sendMessage(s,'No catching little mutator things, fine! *yawns*')

            # if "!start" == first_word and user == CHANNEL:
            #     postCurrent = False 
            #     findingActivated = True
            #     sendMessage(s,'/color ' + chatColor)
            #     sendMessage(s,'Find them all, got it! *sniffs*')
             
            # if "!current" == first_word:
            #     sendMessage(s,'/color ' + chatColor)
            #     if findingActivated == False or mutatorsFound == False:
            #         sendMessage(s,'cannot do that right now')
            #     else:
            #         sendMessage(s,'let me see...')
            #         postCurrent = True

        time.sleep(1)


# def getBrutalPlus (diff):
#         level = 'undefined'
#         if 0 < diff < 4:
#             level = 'Too easy for Brutal+'
#         if 4 <= diff <= 6:
#             level = 'Brutal+1'
#         if 7 <= diff <= 8:
#             level = 'Brutal+2'
#         if 9 <= diff <= 10:
#             level = 'Brutal+3'
#         if 11 <= diff <= 12:
#             level = 'Brutal+4'
#         if 13 <= diff <= 14:
#             level = 'Brutal+4.5'
#         if 15 <= diff <= 16:
#             level = 'Brutal+5'
#         if 17 <= diff <= 18:
#             level = 'Brutal+5.5'
#         if 19 <= diff <= 20:
#             level = 'Brutal+6'
#         if  diff > 20:
#             level = 'Harder than any Brutal+'
#         return level


# def check_replays():
#     """ Checks every 10s for new replays  """

#     already_opened_replays = []
#     while True:      
#         for root, directories, files in os.walk(ACCOUNTDIR):
#             for file in files:
#                 if file.endswith('.SC2Replay') and not(file in already_opened_replays):
#                     file_path = os.path.join(root,file)
#                     try:
#                         if (time.time() - os.stat(file_path).st_mtime < 60) :                            
#                             replay_message = analyse_replay(file_path,PLAYER_NAMES)
#                             if replay_message != '' and not(file in already_opened_replays):
#                                 already_opened_replays.append(file)
#                                 sendMessage(s,replay_message)
#                             else:
#                                 print(f'ERROR: No output from replay analysis ({file})') 
#                             break
#                     except:
#                         print(f'ERROR: Failed at something with replays({file})')                                
#         time.sleep(10)     


# def FindMutators():
#     global postCurrent
#     global mutatorsFound

#     MutatorDescriptions = {"Walking Infested": "Enemy units spawn Infested Terran upon death in numbers according to the unit's life.", "Outbreak": "Enemy Infested Terrans spawn continuously around the map.", "Darkness": "Previously explored areas remain blacked out on the minimap while outside of player vision.", "Time Warp": "Enemy Time Warps are periodically deployed throughout the map.", "Speed Freaks": "Enemy units have increased movement speed.", "Mag-nificent": "Mag Mines are deployed throughout the map at the start of the mission.", "Mineral Shields": "Mineral clusters at player bases are periodically encased in a shield which must be destroyed for gathering to continue.", "Barrier": "Enemy units and structures gain a temporary shield upon the first time they take damage.", "Avenger": "Enemy units gain increased attack speed, movement speed, armor, life, and life-regeneration when nearby enemy units die.", "Evasive Maneuvers": "Enemy units teleport a short distance away upon taking damage.", "Scorched Earth": "Enemy units set the terrain on fire upon death.", "Lava Burst": "Lava periodically bursts from the ground at random locations and deals damage to player air and ground units.", "Self Destruction": "Enemy units explode and deal damage to nearby player units upon death.", "Aggressive Deployment": "Additional enemy units are periodically deployed onto the battlefield.", "Alien Incubation": "All enemy units spawn Broodlings upon death.", "Laser Drill": "An enemy Laser Drill constantly attacks player units within enemy vision.", "Long Range": "Enemy units and structures have increased weapon and vision range.", "Shortsighted": "Player units and structures have reduced vision range.", "Mutually Assured Destruction": "Enemy Hybrid units detonate a Nuke upon death.", "We Move Unseen": "All enemy units are permanently cloaked.", "Slim Pickings": "Player worker units gather resources at a reduced rate, but resource pickups spawn throughout the map.", "Concussive Attacks": "Player units are slowed by all enemy attacks.", "Just Die!": "Enemy units are automatically revived upon death.", "Temporal Field": "Enemy Temporal Fields are periodically deployed throughout the map.", "Void Rifts": "Void Rifts periodically appear in random locations and spawn enemy units until destroyed.", "Twister": "Tornadoes move across the map, damaging and knocking back player units in their path.", "Orbital Strike": "Enemy Orbital Strikes are periodically fired throughout the map.", "Purifier Beam": "An enemy Purifier Beam moves across the map toward nearby player units.", "Blizzard": "Storm clouds move across the map, damaging and freezing player units in their path.", "Fear": "Player units will occasionally stop attacking and run around in fear upon taking damage.", "Photon Overload": "All enemy structures attack nearby hostile units.", "Minesweeper": "Groups of Widow Mines and Spider Mines are buried throughout the battlefield.", "Void Reanimators": "Void Reanimators wander the battlefield, bringing your enemies back to life.", "Going Nuclear": "Nukes are launched at random throughout the map.", "Life Leech": "Enemy units and structures steal life or shields whenever they do damage.", "Power Overwhelming": "All enemy units have energy and use random abilities.", "Micro Transactions": "Giving commands to your units costs resources based on the unit's cost.", "Missile Command": "Endless missile bombardments target your structures and must be shot down throughout the mission.", "Vertigo": "Your camera randomly changes positions.", "Polarity": "Each enemy unit is immune to either your units or your ally's units.", "Transmutation": "Enemy units have a chance to transform into more powerful units whenever they deal damage.", "Afraid of the Dark": "Vision provided by all sources is extremely limited except when in view of your camera.", "Trick or Treat": "Civilians visit your Candy Bowl looking for treats, which are generated by spending minerals. If no treats are available, the civilians transform into random enemy units.", "Turkey Shoot": "Supply can only be generated by killing turkeys that wander throughout the map. Doing so may anger the turkeys that remain.", "Sharing Is Caring": "Supply is shared between you and your partner, and units from both armies contribute to your combined supply cap.", "Diffusion": "Damage dealt to enemies is split evenly across all nearby units, including your own.", "Black Death": "Some enemy units carry a plague that deals damage over time and spreads to other nearby units. The plague spreads to your units when the enemy unit is killed.", "Eminent Domain": "Enemies gain control of your structures after destroying them.", "Gift Exchange": "Gifts are periodically deployed around the map.  If you don't claim them, Amon will!", "Naughty List": "Player units and structures take increased damage for each enemy they've killed.", "Extreme Caution": "Your units will not obey any command placed in areas they cannot see.", "Heroes from the Storm": "Attack waves will be joined by heroes of increasing power.", "Inspiration": "Enemy Heroic units increase the attack speed and armor of all enemies within a small range. ", "Hardened Will": "Enemy Heroic units reduce all incoming damage to a maximum of 10 when any non-heroic enemy unit is near them.", "Fireworks": "Enemies launch a dazzling fireworks display upon death, dealing damage to your nearby units.", "Lucky Envelopes": "Festive envelopes containing resource pickups are dropped at random throughout the map.", "Double-Edged": "Your units also receive all the damage they deal, but they are healed over time.", "Fatal Attraction": "When enemy units and structures die, any of your nearby units are pulled to their location.", "Propagators": "Shapeless lifeforms creep toward your base, transforming all of the units and structures they touch into copies of themselves.", "Moment of Silence": "When a Heroic enemy dies, all player units around it will reflect on their transgressions, leaving them unable to attack or use abilities.", "Kill Bots": "Offensive robots of a mysterious origin have been unleashed on the Koprulu sector, intent on destruction. Through cunning engineering, they are invincible until their pre-programmed kill counter has been filled. After that occurs, they will shut down. But can you survive for that long?", "Boom Bots": "Uncaring automatons carry a nuclear payload toward your base. One player must discern the disarming sequence and the other player must enter it.", "The Mist": "Mists roll over battlefield while unseen terrors lurk inside. Desperate warriors will fall and rise again.", "The Usual Suspects": "Enemy attacks will be led by dark reflections of Heroes in the service of Amon", "Supreme Commander": "Massive units gain 25% life and are bigger, the rest of units have 25% less life and are smaller. All units gain +2 weapon range.", "Shapeshifters": "Shapeshifters spawn with enemy attacks and in enemy bases. These creatures can transform into any unit of yours.", "Rip Field Generators": "Rip-Field Generators are deployed throughout the map. They will burn any unit that comes into their range.", "Repulsive Field": "Enemy attacks will push your units away.", "Old Times": "We are traveling back in time. Unit selection is limited to 12 units. There is no worker auto-mine, no smart cast, no multiple building select, etc.", "Nuclear Mines": "Nuclear Mines have been placed around the battlefield.", "Necronomicon": "Killed player units will rise again at enemy bases.", "Mothership": "Enemy Mothership roams the map and attacks player units.", "Matryoshka": "Enemy units will spawn mini-self upon death. This can trigger several times for larger units.", "Level Playing Field": "All weapons and abilities can hit both air and ground targets.", "Infestation Station": "Damaging any structure can cause infestation.", "I Collect, I Change": "When a non-heroic unit kills a hostile unit, it becomes the unit it killed. Units can only evolve into more expensive units.", "Great Wall": "Enemy begins massive effort to construct defensive structures around the battlefield.", "Endurance": "Player and enemy units and structures have 3x more health and shields.", "Dark Mirror": "Enemy attack waves will contain player units.", "Bloodlust": "Enemy units gain increased attack speed, movement speed, acceleration and damage reduction as their health gets lower."}
#     MutatorDiffScore = {"Walking Infested": "2", "Outbreak": "3", "Darkness": "2", "Time Warp": "1", "Speed Freaks": "2", "Mag-nificent": "4", "Mineral Shields": "2", "Barrier": "2", "Avenger": "5", "Evasive Maneuvers": "1", "Scorched Earth": "2", "Lava Burst": "3", "Self Destruction": "3", "Aggressive Deployment": "3", "Alien Incubation": "2", "Laser Drill": "2", "Long Range": "2", "Shortsighted": "1", "Mutually Assured Destruction": "5", "We Move Unseen": "3", "Slim Pickings": "5", "Concussive Attacks": "1", "Just Die!": "7", "Temporal Field": "1", "Void Rifts": "10", "Twister": "2", "Orbital Strike": "1", "Purifier Beam": "2", "Blizzard": "4", "Fear": "3", "Photon Overload": "1", "Minesweeper": "6", "Void Reanimators": "5", "Going Nuclear": "3", "Life Leech": "1", "Power Overwhelming": "5", "Micro Transactions": "5", "Missile Command": "3", "Vertigo": "0", "Polarity": "7", "Transmutation": "7", "Afraid of the Dark": "0", "Trick or Treat": "0", "Turkey Shoot": "0", "Sharing Is Caring": "0", "Diffusion": "3", "Black Death": "7", "Eminent Domain": "1", "Gift Exchange": "0", "Naughty List": "0", "Extreme Caution": "0", "Heroes from the Storm": "10", "Inspiration": "2", "Hardened Will": "2", "Fireworks": "0", "Lucky Envelopes": "0", "Double-Edged": "3", "Fatal Attraction": "3", "Propagators": "8", "Moment of Silence": "2", "Kill Bots": "6", "Boom Bots": "0", "The Mist": "3", "The Usual Suspects": "5", "Supreme Commander": "0", "Shapeshifters": "4", "Rip Field Generators": "3", "Repulsive Field": "1", "Old Times": "0", "Nuclear Mines": "2", "Necronomicon": "1", "Mothership": "2", "Matryoshka": "2", "Level Playing Field": "0", "Infestation Station": "4", "I Collect, I Change": "-2", "Great Wall": "5", "Endurance": "3", "Dark Mirror": "0", "Bloodlust": "1"}

#     PATH = 'Mutator Icons'
#     INTERVAL = 3 #seconds
#     PreviousMutators = []  
#     colors = ['Red', 'Blue']
#     currentColor = 0  
#     threshold = 0.9

#     while True:
#         if findingActivated == False: #skip if the function is deactivated via chat command (temporarily)
#             time.sleep(INTERVAL)
#             print('//mutator find disabled')
#             continue

#         game_response = requests.get('http://localhost:6119/game') #SC2 returns simple response with player names and races (or random)
#         game_response = game_response.json()
#         if 'isReplay' in game_response:
#             isReplay =  game_response['isReplay']
#             if isReplay:
#                 time.sleep(INTERVAL)
#                 continue
#         else:
#             print('game not running? no reponse')

#         MutatorDF = pd.DataFrame(columns=['Mutator', 'Description', 'Y','X','Max_val'])
#         NewMutators = []
#         a = 0
#         FewMutators = False #these prevent doing more work than necessary, if it's either small or big, the checks only those later
#         ManyMutators = False
#         entries = os.scandir(PATH) #for some reason this needs to be rescaned
        
#         img = pyautogui.screenshot(region=(1810,380, 110, 480))
#         img_rgb = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

#         # cv2.imshow("orig image", img_rgb)
#         # cv2.waitKey(0)
#         # cv2.destroyAllWindows()

#         #RESIZING (resize screenshot, if yes, lower threshold since accuracy will take a hit)
#         if RESIZECOEF != 1:
#             img_rgb = cv2.resize(img_rgb,(int(110*RESIZECOEF),int(480*RESIZECOEF)), interpolation = cv2.INTER_AREA)
#             threshold = 0.7
#             # cv2.imshow("resized image", img_rgb)
#             # cv2.waitKey(0)
#             # cv2.destroyAllWindows()

#         for entry in entries:
#             if entry.is_file() and entry.name.endswith('.png'):

#                 if len(entry.name.split('_')) > 1 and FewMutators: #tells whether to load small or not
#                     continue
#                 if len(entry.name.split('_')) == 1 and ManyMutators:
#                     continue

#                 template = cv2.imread(PATH +'/'+ entry.name,1)

#                 res = cv2.matchTemplate(img_rgb,template,cv2.TM_CCOEFF_NORMED)
#                 min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#                 loc = np.where( res >= threshold) #array with values where res > threshold
                        
#                 if np.count_nonzero(loc)>0:
#                     mutatorsFound = True
#                     if ManyMutators == False and FewMutators == False:
#                         if len(entry.name.split('_')) > 1: #was it a small of big one?
#                             ManyMutators = True
#                         else:
#                             FewMutators = True

#                     NewMutators.append(entry.name.split('.')[0]) #add to pd frames to sort later by position (x,y)
#                     MutatorDF.loc[a] = [entry.name.split('.')[0].split('_')[0]]+[MutatorDescriptions.get(entry.name.split('.')[0].split('_')[0])]+[round(max_loc[1]/10,0)]+[round(max_loc[0]/10,0)]+[round(max_val,3)]
#                     a += 1

#         MutatorsNotChanged = len(set(PreviousMutators) & set(NewMutators)) >= len(NewMutators)  

#         if MutatorsNotChanged and postCurrent == False:
#             pass
#         else:
#             postCurrent = False
#             PreviousMutators = NewMutators
            
#             if not(MutatorsNotChanged): #sort & save only if mutations changed, and not when using !current command
#                 SortedMutatorDF = MutatorDF.sort_values(by=['Y','X'], ascending=True).reset_index()
#                 if local_test == False:
#                     MutatorDF['Mutator'].to_csv('MutatorLog.csv', mode='a', header=False, sep ='\t')

#             currentColor += 1
#             if currentColor >= len(colors): #loop back if max
#                 currentColor = 0               

#             MutationDifficulty = 0
#             Message = '/color ' + colors[currentColor]
#             sendMessage(s,Message)

#             for index, row in SortedMutatorDF.iterrows():
#                 print(index, row['Mutator'],' ', row['Max_val'])
#                 Message = row['Mutator'] + ' ('+ MutatorDiffScore.get(row['Mutator']) +') - ' + row['Description'] #'/me : '
#                 sendMessage(s,Message)
#                 MutationDifficulty += int(MutatorDiffScore.get(row['Mutator']))

#             p1name =  game_response['players'][0]['name']
#             p2name =  game_response['players'][1]['name']

#             sendMessage(s,f'{p1name} and {p2name} will face a mutation with total difficulty score of {str(MutationDifficulty)} ({getBrutalPlus(MutationDifficulty)})')

#         time.sleep(INTERVAL)

#start the bot
if (__name__ == "__main__"):
    s = openSocket()
    joinRoom(s)
    pingsAndMessages()
    # t1 = threading.Thread(target = FindMutators)
    # t1.start()
    # t2 = threading.Thread(target = pingsAndMessages)
    # t2.start()
    # t3 = threading.Thread(target = check_replays)
    t3.start()
    