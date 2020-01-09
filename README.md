# FluffyChatBot

Post on my site: https://www.maguro.one/2020/01/fluffy-chatbot.html

Custom twitch bot that identifies StarCraft II Co-op mutators and posts them in the chat. I also added support for intergration into my [MM] maps. You can affect the game with several supported commands (!join, !message, !spawn, !mutator, !resources)

Mutator identification would need to be modified to work at different resolutions and screen aspect ratios. I added a lightweight version that contains configurable commands and responses to them, together with integration to [MM] maps. Image recognition requires packages that would push the compiled size to around ~300MB.

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
