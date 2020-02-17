
from gtts import gTTS

##
tts = gTTS('Hello! I am Maverick.', 'en')
tts.save('hello.mp3')

##
tts = gTTS('Please enable autonomy now.', 'en')
tts.save('please_enable_autonomy_now.mp3')

##
tts = gTTS('Stopped vehicle ahead!', 'en')
tts.save('stopped_vehicle_ahead_take_control_now.mp3')

##
tts = gTTS("Hey, this is an easy road." +
           "You don't need to worry about driving... " +
           "I will take care of it while you focus on finding the cues!!!.", 'en')
tts.save('SA_message.mp3')

##
tts = gTTS("Hey, this part of the road is not very easy." +
           "You can still find the cues, but please pay more attention to the road.", 'en')
tts.save('nudge_message.mp3')

##
tts = gTTS("Look! I told you! I do need your attention! " +
           "I can feel the road is terrible! I don't know if I can keep us totally safe!", 'en')
tts.save('Xnudge_message.mp3')
