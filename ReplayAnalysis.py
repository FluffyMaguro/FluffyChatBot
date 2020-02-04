import os
import sc2reader
from UnitNameDict import UnitNameDict

amon_forces = ['Amon','Infested','Salamander','Void Shard','Hologram','Moebius', "Ji'nara" ]
duplicating_units = ['HotSRaptor']
skip_strings = ['placement', 'placeholder', 'dummy','cocoon']
revival_types = {'KerriganReviveCocoon':'K5Kerrigan', 'AlarakReviveBeacon':'AlarakCoop','ZagaraReviveCocoon':'ZagaraVoidCoop','DehakaCoopReviveCocoonFootPrint':'DehakaCoop','NovaReviveBeacon':'NovaCoop','ZeratulCoopReviveBeacon':'ZeratulCoop'}


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
    unit_type_dict_amon = {}
    print('Analysing:',filepath)

    try:
        replay = sc2reader.load_replay(filepath,load_level=3)

    except:
        print(f'ERROR: Failed to load replay ({filepath})')
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

    #get result
    game_result = 'Defeat'
    for team in replay.teams:
        for player in team:
            if player.result == 'Win':
                game_result = 'Victory'
            break

    unit_dict = {}
    #structure: {unit_id : [UnitType, Owner]}

    #go through game events
    for event in replay.events:  
        if event.name == 'UnitBornEvent' or event.name == 'UnitInitEvent':
            #save into unit dict
            try:
                unit_dict[str(event.unit_id)] = [event.unit_type_name,str(event.unit_controller)[7]]
            except:
                #unit created without for no player
                pass

            #certain hero units don't die, instead lets track their revival beacons/cocoons. Let's assume they will finish reviving.
            if event.unit_type_name in revival_types and main_player == event.control_pid and event.second > 0:
                unit_type_dict_maguro[revival_types[event.unit_type_name]][1] += 1
                unit_type_dict_maguro[revival_types[event.unit_type_name]][0] += 1

            #save stats for units created
            if main_player == event.control_pid:
                unit_type = event.unit_type_name

                if contains_skip_strings(unit_type):
                    continue

                if unit_type in unit_type_dict_maguro:
                    unit_type_dict_maguro[unit_type][0] += 1
                else:
                    unit_type_dict_maguro[unit_type] = [1,0,0,0]

            if event.control_pid in amon_players:
                unit_type = event.unit_type_name

                if contains_skip_strings(unit_type):
                    continue

                if unit_type in unit_type_dict_amon:
                    unit_type_dict_amon[unit_type][0] += 1
                else:
                    unit_type_dict_amon[unit_type] = [1,0,0,0]


        if event.name == 'UnitTypeChangeEvent' and str(event.unit_id) in unit_dict:
                #update unit_dict
                old_unit_type = unit_dict[str(event.unit_id)][0]
                unit_dict[str(event.unit_id)][0] = str(event.unit_type_name)

                #add to created units
                unit_type = event.unit_type_name
                if unit_type in UnitNameDict and old_unit_type in UnitNameDict:
                    if UnitNameDict[unit_type] != UnitNameDict[old_unit_type]: #don't add into created units if it's just a morph

                        owner = int(unit_dict[str(event.unit_id)][1])
                        # #increase unit type created for controlling player 
                        if main_player == owner:
                            if unit_type in unit_type_dict_maguro:
                                unit_type_dict_maguro[unit_type][0] += 1
                            else:
                                unit_type_dict_maguro[unit_type] = [1,0,0,0]

                        if owner in amon_players:
                            if unit_type in unit_type_dict_amon:
                                unit_type_dict_amon[unit_type][0] += 1
                            else:
                                unit_type_dict_amon[unit_type] = [1,0,0,0]


        if event.name == 'UnitOwnerChangeEvent' and str(event.unit_id) in unit_dict:
            unit_dict[str(event.unit_id)][1] = str(event.control_pid)



        if event.name == 'UnitDiedEvent':    
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

                if main_player == losing_player and event.second > 0: #don't count deaths on game init
                    unit_type_dict_maguro[killed_unit_type][1] += 1

                if losing_player in amon_players and event.second > 0:
                    unit_type_dict_amon[killed_unit_type][1] += 1           
            except:
                pass
                #some units aren't created

   
    #Get messages
    replay_report = f"{game_result}! ({replay.map_name})."

    #Player kills
    sorted_maguro = {k:v for k,v in sorted(unit_type_dict_maguro.items(), reverse = True, key=lambda item: item[1][2])} #sorts by number of create (0), lost (1), kills (2), K/D (3)
    sorted_maguro = switch_names(sorted_maguro)
    temp_string_init = f" {main_player_name}'s most effective units were"
    temp_string = ''
    message_count = 0

    maxUnits = 0
    for key in sorted_maguro:
        if sorted_maguro[key][2] > 0:
            maxUnits +=1

    maxUnits = min(maxUnits, 3)

    for key in sorted_maguro:
        if sorted_maguro[key][2] > 0 and message_count < maxUnits:
            message_count +=1
            if message_count == 1:
                temp_string = f'{temp_string} {key}: {sorted_maguro[key][2]} kills ({sorted_maguro[key][0]} created/{sorted_maguro[key][1]} lost),' 
            elif message_count == maxUnits:
                temp_string = f'{temp_string} and {key}: {sorted_maguro[key][2]} kills ({sorted_maguro[key][0]}/{sorted_maguro[key][1]}).'
                break
            else:
                temp_string = f'{temp_string} {key}: {sorted_maguro[key][2]} kills ({sorted_maguro[key][0]}/{sorted_maguro[key][1]}),'   

    if temp_string != '':
        temp_string = temp_string[:-1]+'.'
        replay_report = replay_report + temp_string_init + temp_string

    #Amon lost
    sorted_amon = {k:v for k,v in sorted(unit_type_dict_amon.items(), reverse = True, key=lambda item: item[1][1])}
    sorted_amon = switch_names(sorted_amon)
    message_count = 0
    temp_string_init = " Amon has lost"
    temp_string = ''
    for key in sorted_amon:  
        if sorted_amon[key][1] > 0 and not('droppod' in key.lower()):
            message_count += 1
            if message_count > 4:
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

# file_path = 'C:/Users/Maguro/Documents/StarCraft II/Accounts/114803619/1-S2-1-4189373/Replays/Multiplayer/[MM] Temple of the Past - Terran (74).SC2Replay'
# file_path = 'C:/Users/Maguro/Documents/StarCraft II/Accounts/114803619/1-S2-1-4189373/Replays/Multiplayer/Scythe of Amon (226).SC2Replay'

# PLAYERNAME = 'Maguro'
# replay_message = analyse_replay(file_path,PLAYERNAME)
# print(replay_message)