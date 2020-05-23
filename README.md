# FluffyChatBot

Post on my site: https://www.maguro.one/2020/01/fluffy-chatbot.html

* Basic bot stuff - configurable responses
* Indentifies mutators that are being played and posts the in the chat
* Calculates mutation difficulty score and equivalent Brutal+ difficulty and posts it into the chat

![Summary](https://github.com/FluffyMaguro/FluffyChatBot/blob/master/2019-12-31_183302.png)

* Post game summary

![Summary](https://raw.githubusercontent.com/FluffyMaguro/FluffyChatBot/master/BotReplayAnalysis.png)

* Game integration into my [MM] maps. You can affect the game with several supported commands (!join, !message, !spawn, !mutator, !resources).

![Summary](https://github.com/FluffyMaguro/FluffyChatBot/blob/master/party.jpg)

Mutator identification would need to be modified to work at different resolutions and screen aspect ratios. I added a lightweight version that supports only basic bot functionality and twitch intergration into my maps.

# How to use the lightweight bot

1. Create a twitch account for the bot
2. Get twich API oauth key for the bot (https://twitchapps.com/tmi/)
3. Download the config file and .exe (or python script and run/compile it yourself).
4. Change channel name, bot name, oauth key, bank locations (and optionally responses) in the config file.
5. Run the bot while playing

Commands for the streamer: 
* !gm → enables partial game integration (!join, !message). But it's on by default already.
* !gm full → enables full game integration (!mutator, !spawn, !resources)
* !gm stop → disables all game integration

Editing responses:

* You add or remove them as you wish (except "RESPONSE", removing that one might throw an error)
* For example if you add `SNOW = It's snowing!`, if someone writes "!snow", the bot will say "It's snowing!"
