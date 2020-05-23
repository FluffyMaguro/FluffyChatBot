import os
import traceback
import sys
import mpyq
import json

import sc2reader
from UnitNameDict import UnitNameDict

amon_forces = ['Amon','Infested','Salamander','Void Shard','Hologram','Moebius', "Ji'nara" ]
duplicating_units = ['HotSRaptor']
skip_strings = ['placement', 'placeholder', 'dummy','cocoon']
revival_types = {'KerriganReviveCocoon':'K5Kerrigan', 'AlarakReviveBeacon':'AlarakCoop','ZagaraReviveCocoon':'ZagaraVoidCoop','DehakaCoopReviveCocoonFootPrint':'DehakaCoop','NovaReviveBeacon':'NovaCoop','ZeratulCoopReviveBeacon':'ZeratulCoop'}


class logclass:
    """ used for logging purposes """
    def __init__(self,name,showtype,level):
        self.name = name
        self.showtype = showtype
        self.level = level

    def debug(self,message):
        if self.level > 0:
            return
        mtype = ' (D)' if self.showtype else ''
        print(f'{self.name}{mtype}: {message}\n')

    def info(self,message):
        if self.level > 1:
            return
        mtype = ' (I)' if self.showtype else ''
        print(f'{self.name}{mtype}: {message}\n')

    def error(self,message):
        if self.level > 2:
            return
        mtype = ' (E)' if self.showtype else ''
        print(f'{self.name}{mtype}: {message}\n')


logger = logclass('RepAnalysis',False,1)



def contains_skip_strings(pname):
    """ checks if any of skip strings is in the pname """
    lowered_name = pname.lower()
    for item in skip_strings:
        if item in lowered_name:
            return True
    return False


def check_amon_forces(alist, string):
    """ Checks if any word from the list is in the string """
    for item in alist:
        if item in string:
            return True
    return False


def calculate_KD(pdit):
    """ Calculates K/D, """
    for item in pdit:
        if pdit[item][1] != 0:
            pdit[item][3] = pdit[item][2]/pdit[item][1]
        else:
            pdit[item][3] = float(pdit[item][2])  

                    
def save_dict(pdict,pname,sep):
    """ Saves dictionary into text file """
    temp_string = f'Unit type{sep}created{sep}died{sep}kills{sep}K/D'
    for key in pdict:
        temp_string = f'{temp_string}\n{key}{sep}{pdict[key][0]}{sep}{pdict[key][1]}{sep}{pdict[key][2]}{sep}{pdict[key][3]}'

    with open(pname, 'w') as file:       
        file.write(temp_string)


def switch_names(pdict):
    """ Changes names to that in unit dictionary, sums duplicates"""
    temp_dict = {}
    for key in pdict:
        name = key
        if key in UnitNameDict:
            name = UnitNameDict[key]

        if name in temp_dict:
            for a in range(0,len(temp_dict[name])):
                temp_dict[name][a] += pdict[key][a]
        else:
            temp_dict[name] = pdict[key]

    return temp_dict



def analyse_replay(filepath, playernames):
    """ Analyses the replay and returns message into the chat"""
    main_player_name = playernames[0]
    #structure: {unitType : [#created, #died, #kills, #KD]}
    unit_type_dict_maguro = {}
    unit_type_dict_ally = {}
    unit_type_dict_amon = {}
    logger.info(f'Analysing: {filepath}')

    #APM
    archive = mpyq.MPQArchive(filepath)
    metadata = json.loads(archive.read_file('replay.gamemetadata.json'))

    try:
        replay = sc2reader.load_replay(filepath,load_level=3)
    except:
        logger.error(f'ERROR: SC2reader failed to load replay ({filepath})')
        return ''

    is_coop_map = False
    main_player = 1
    amon_players = []

    for per in replay.person:
        #find main player
        for playeriter in playernames:
            if playeriter in str(replay.person[per]): 
                main_player = per
                main_player_name = playeriter
                break

        #find Amon players
        if check_amon_forces(amon_forces,str(replay.person[per])) and per > 2:
            amon_players.append(per)

    ally_player = 1 if main_player==2 else 2
    ally_player_name = str(replay.person[ally_player]).split(' - ')[1].replace(' (Zerg)', '').replace(' (Terran)', '').replace(' (Protoss)', '')

    logger.debug(f'{main_player_name=} | {main_player=} | {ally_player_name=} | {ally_player=} | {amon_players=}')

    map_data = dict()
    logger.debug(f'{metadata=}')

    for player in metadata["Players"]:
        if player["PlayerID"] == main_player:
            map_data[main_player] = player["APM"]
        elif player["PlayerID"] == ally_player:
            map_data[ally_player] = player["APM"]

    logger.debug(f'{map_data=}')

    #get result
    game_result = 'Defeat'
    for team in replay.teams:
        for player in team:
            if player.result == 'Win':
                game_result = 'Victory'
            break

    unit_dict = {} #structure: {unit_id : [UnitType, Owner]}
    DT_HT_Ignore = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] #ignore certain amount of DT/HT deaths after archon is initialized. DT_HT_Ignore[player]
    killcounts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    #go through game events
    for event in replay.events:  
        if event.name == 'UnitBornEvent' or event.name == 'UnitInitEvent':
            
            unit_dict[str(event.unit_id)] = [event.unit_type_name, event.control_pid]
            unit_type = event.unit_type_name

            #certain hero units don't die, instead lets track their revival beacons/cocoons. Let's assume they will finish reviving.
            if event.unit_type_name in revival_types and event.control_pid in [1,2] and event.second > 0:
                if event.control_pid == main_player:
                    unit_type_dict_maguro[revival_types[event.unit_type_name]][1] += 1
                    unit_type_dict_maguro[revival_types[event.unit_type_name]][0] += 1
                if event.control_pid == ally_player:
                    unit_type_dict_ally[revival_types[event.unit_type_name]][1] += 1
                    unit_type_dict_ally[revival_types[event.unit_type_name]][0] += 1


            #save stats for units created
            if event.control_pid in [1,2]:
                if contains_skip_strings(unit_type):
                    continue

                if main_player == event.control_pid:
                    if unit_type in unit_type_dict_maguro:
                        unit_type_dict_maguro[unit_type][0] += 1
                    else:
                        unit_type_dict_maguro[unit_type] = [1,0,0,0]

                if ally_player == event.control_pid:
                    if unit_type in unit_type_dict_ally:
                        unit_type_dict_ally[unit_type][0] += 1
                    else:
                        unit_type_dict_ally[unit_type] = [1,0,0,0]


            if event.control_pid in amon_players:
                if contains_skip_strings(unit_type):
                    continue

                if unit_type in unit_type_dict_amon:
                    unit_type_dict_amon[unit_type][0] += 1
                else:
                    unit_type_dict_amon[unit_type] = [1,0,0,0]


        #ignore some DT/HT deaths caused by Archon merge
        if event.name == "UnitInitEvent" and event.unit_type_name == "Archon":
            DT_HT_Ignore[event.control_pid] += 2

        if event.name == 'UnitTypeChangeEvent' and str(event.unit_id) in unit_dict:
                #update unit_dict
                old_unit_type = unit_dict[str(event.unit_id)][0]
                unit_dict[str(event.unit_id)][0] = str(event.unit_type_name)

                #add to created units
                if unit_type in UnitNameDict and old_unit_type in UnitNameDict:
                    event.control_pid = int(unit_dict[str(event.unit_id)][1])
                    if UnitNameDict[unit_type] != UnitNameDict[old_unit_type]: #don't add into created units if it's just a morph

                        # #increase unit type created for controlling player 
                        if main_player == event.control_pid:
                            if unit_type in unit_type_dict_maguro:
                                unit_type_dict_maguro[unit_type][0] += 1
                            else:
                                unit_type_dict_maguro[unit_type] = [1,0,0,0]

                        if ally_player == event.control_pid:
                            if unit_type in unit_type_dict_ally:
                                unit_type_dict_ally[unit_type][0] += 1
                            else:
                                unit_type_dict_ally[unit_type] = [1,0,0,0]

                        if event.control_pid in amon_players:
                            if unit_type in unit_type_dict_amon:
                                unit_type_dict_amon[unit_type][0] += 1
                            else:
                                unit_type_dict_amon[unit_type] = [1,0,0,0]
                    else:
                        if main_player == event.control_pid and not(unit_type in unit_type_dict_maguro):
                            unit_type_dict_maguro[unit_type] = [0,0,0,0] 

                        if ally_player == event.control_pid and not(unit_type in unit_type_dict_ally):
                            unit_type_dict_ally[unit_type] = [0,0,0,0] 

                        if event.control_pid in amon_players and not(unit_type in unit_type_dict_amon):
                            unit_type_dict_amon[unit_type] = [0,0,0,0]    


        if event.name == 'UnitOwnerChangeEvent' and str(event.unit_id) in unit_dict:
            unit_dict[str(event.unit_id)][1] = str(event.control_pid)


        if event.name == 'UnitDiedEvent':
            try:
                losing_player = int(unit_dict[str(event.unit_id)][1])
                if losing_player != event.killing_player_id and not(event.killing_player_id in [1,2] and losing_player in [1,2]): #don't count team kills
                    killcounts[event.killing_player_id] += 1
            except:
                pass


        if event.name == 'UnitDiedEvent' and str(event.unit_id) in unit_dict:    
            try:
                killing_unit_id = str(event.killing_unit_id)
                killed_unit_type = unit_dict[str(event.unit_id)][0]
                losing_player = int(unit_dict[str(event.unit_id)][1])

                if killing_unit_id in unit_dict:
                    killing_unit_type = unit_dict[killing_unit_id][0]
                else:
                    killing_unit_type = 'NoUnit'

                if contains_skip_strings(killed_unit_type): #skip placeholders, dummies, cocoons
                    continue   
            
                #update kills
                if (killing_unit_id in unit_dict) and (killing_unit_id != str(event.unit_id)) and losing_player != event.killing_player_id:
                  
                    if main_player == event.killing_player_id:
                        if killing_unit_type in unit_type_dict_maguro:
                            unit_type_dict_maguro[killing_unit_type][2] += 1
                        else:
                            unit_type_dict_maguro[killing_unit_type] = [0,0,1,0]

                    if ally_player == event.killing_player_id:
                        if killing_unit_type in unit_type_dict_ally:
                            unit_type_dict_ally[killing_unit_type][2] += 1
                        else:
                            unit_type_dict_ally[killing_unit_type] = [0,0,1,0]

                    if event.killing_player_id in amon_players:  
                        if killing_unit_type in unit_type_dict_amon:
                            unit_type_dict_amon[killing_unit_type][2] += 1
                        else:
                            unit_type_dict_amon[killing_unit_type] = [0,0,1,0]
               
                #update unit deaths
                #fix for raptors that are counted each time they jump (as death and birth)
                if main_player == losing_player and event.second > 0 and killed_unit_type in duplicating_units and killed_unit_type == killing_unit_type and losing_player == event.killing_player_id:
                    unit_type_dict_maguro[killed_unit_type][0] -= 1
                    continue

                if ally_player == losing_player and event.second > 0 and killed_unit_type in duplicating_units and killed_unit_type == killing_unit_type and losing_player == event.killing_player_id:
                    unit_type_dict_ally[killed_unit_type][0] -= 1
                    continue

                # in case of death caused by Archon merge, ignore these kills
                if (killed_unit_type == 'HighTemplar' or killed_unit_type == 'DarkTemplar') and DT_HT_Ignore[losing_player] > 0:
                    DT_HT_Ignore[losing_player] -= 1
                    continue

                if main_player == losing_player and event.second > 0: #don't count deaths on game init
                    if killed_unit_type in unit_type_dict_maguro:
                        unit_type_dict_maguro[killed_unit_type][1] += 1
                    else:
                        unit_type_dict_maguro[killed_unit_type] = [0,1,0,0]

                if ally_player == losing_player and event.second > 0: #don't count deaths on game init
                    if killed_unit_type in unit_type_dict_ally:
                        unit_type_dict_ally[killed_unit_type][1] += 1
                    else:
                        unit_type_dict_ally[killed_unit_type] = [0,1,0,0]

                if losing_player in amon_players and event.second > 0:
                    if killed_unit_type in unit_type_dict_amon:
                        unit_type_dict_amon[killed_unit_type][1] += 1  
                    else:
                        unit_type_dict_amon[killing_unit_type] = [0,1,0,0]  
                               
            except Exception as e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_tb)
                pass

    logger.debug(f'{unit_type_dict_maguro=}')
    logger.debug(f'{unit_type_dict_ally=}')
    logger.debug(f'{killcounts=}')


    #Get messages
    replay_report = f"{game_result}! ({replay.map_name})."


    def playermessage(playername,player,pdict):

        #Player kills
        sorted_dict = {k:v for k,v in sorted(pdict.items(), reverse = True, key=lambda item: item[1][2])} #sorts by number of create (0), lost (1), kills (2), K/D (3)
        sorted_dict = switch_names(sorted_dict)
        temp_string = f" {playername}'s ({killcounts[player]} kills, {map_data[player]:.0f} APM) most effective units were"
        message_count = 0

        maxUnits = 0
        for key in sorted_dict:
            if sorted_dict[key][2] > 0:
                maxUnits +=1

        maxUnits = min(maxUnits, 3)

        for key in sorted_dict:
            if sorted_dict[key][2] > 0 and message_count < maxUnits:
                message_count +=1
                if message_count == 1:
                    temp_string = f'{temp_string} {key}: {sorted_dict[key][2]} kills ({sorted_dict[key][0]} created/{sorted_dict[key][1]} lost),' 
                elif message_count == maxUnits:
                    temp_string = f'{temp_string} and {key}: {sorted_dict[key][2]} kills ({sorted_dict[key][0]}/{sorted_dict[key][1]}).'
                    break
                else:
                    temp_string = f'{temp_string} {key}: {sorted_dict[key][2]} kills ({sorted_dict[key][0]}/{sorted_dict[key][1]}),' 

        #add comma
        if temp_string != '':
            temp_string = temp_string[:-1]+'.'

        if message_count == 0:
            return ''

        return temp_string  

    replay_report = replay_report + playermessage(main_player_name, main_player, unit_type_dict_maguro) + playermessage(ally_player_name, ally_player, unit_type_dict_ally)


    #Amon lost
    sorted_amon = {k:v for k,v in sorted(unit_type_dict_amon.items(), reverse = True, key=lambda item: item[1][1])}
    sorted_amon = switch_names(sorted_amon)
    message_count = 0
    temp_string_init = " Amon has lost"
    temp_string = ''
    for key in sorted_amon:  
        if sorted_amon[key][1] > 0 and not('droppod' in key.lower()) and not('larva' in key.lower()):
            message_count += 1
            if message_count > 2:
                temp_string = f'{temp_string} and {sorted_amon[key][1]} {key}s.' 
                break
            else:   
                temp_string = f'{temp_string} {sorted_amon[key][1]} {key}s,' 

    if temp_string != '':
        temp_string = temp_string[:-1]+'.'
        replay_report = replay_report + temp_string_init + temp_string

    #Amon kills
    message_count = 0
    sorted_amon = {k:v for k,v in sorted(unit_type_dict_amon.items(), reverse = True, key=lambda item: item[1][2])}
    sorted_amon = switch_names(sorted_amon)
    temp_string_init = " Amon's most effective units were"
    temp_string = ''

    for key in sorted_amon:  
        if sorted_amon[key][2] > 0:
            message_count += 1
            if message_count > 1:
                temp_string = f'{temp_string} and {key} with {sorted_amon[key][2]} kills.' 
                break
            else:   
                temp_string = f'{temp_string} {key} with {sorted_amon[key][2]} kills,' 

    if temp_string != '':
        temp_string = temp_string[:-1]+'.'
        replay_report = replay_report + temp_string_init + temp_string

    return replay_report


#DEBUG
if __name__ == "__main__":
    PLAYERNAME = 'Maguro'

    folder_path = 'C:\\Users\\Maguro\\Desktop\\TEST'
    file_list = os.listdir(folder_path)

    # for file in file_list:
    #     file_path = os.path.join(folder_path,file)
    #     replay_message = analyse_replay(file_path,[PLAYERNAME])
    #     logger.info(f'{replay_message=}')

    file_path = 'C:/Users/Maguro/Documents/StarCraft II/Accounts\\452875987\\2-S2-1-7503439\\Replays\\Multiplayer\\Oblivion Express (19).SC2Replay'
    replay_message = analyse_replay(file_path,[PLAYERNAME])
    logger.info(f'{replay_message=}')

    
    
    