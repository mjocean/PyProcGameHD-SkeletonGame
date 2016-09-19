#    _____ ____  __  ___   ______     __________  _   ____________  ____  __    __    __________ 
#   / ___// __ \/ / / / | / / __ \   / ____/ __ \/ | / /_  __/ __ \/ __ \/ /   / /   / ____/ __ \
#   \__ \/ / / / / / /  |/ / / / /  / /   / / / /  |/ / / / / /_/ / / / / /   / /   / __/ / /_/ /
#  ___/ / /_/ / /_/ / /|  / /_/ /  / /___/ /_/ / /|  / / / / _, _/ /_/ / /___/ /___/ /___/ _, _/ 
# /____/\____/\____/_/ |_/_____/   \____/\____/_/ |_/ /_/ /_/ |_|\____/_____/_____/_____/_/ |_|  
#
# authors: Josh Kugler, Michael Ocean
#
import random
import time
import logging
from procgame.game import mode
from collections import deque
from math import ceil

try:
    logging.getLogger('game.sound').info("Initializing sound...")
    from pygame import mixer # This call takes a while.
except ImportError, e:
    logging.getLogger('game.sound').error("Error importing pygame.mixer; sound will be disabled!  Error: "+str(e))

import os.path

# SPECIFIC RESERVED SOUND CHANNELS:
CH_MUSIC = 0      # standard streaming music audio - uses pygame music object (i.e. stream from disk on play)

# SOUND EFFECT CHANNEL
CH_SFX = -1    # this channel means "any free sound channel" - contrast with VOICE

# VOICE EFFECT CHANNEL 
CH_VOICE = 1    # voice effects are queued and a special channel reserved for them

# NON-STREAMING MUSIC CHANNELS
CH_MUSIC_1 = 2    # alternate music track 1 - uses pygame sound object (full load)
CH_MUSIC_2 = 3    # as above; note: these are useful if you want to pause music, start 
                  # another song playing (other channel) and later resume that first track
                    # NOTE: using these channels will cause your music to be treated like _sounds_
                    # and that means they will be fully loaded into memory instead of streamed
                    # from the disk.  Unlike sounds pre-loaded with the assetManager, so unless they
                    # are registered as non-streaming, they will be loaded at playback time, 
                    # which will introduce a delay

# this refers to all music channels which provides a default for
CH_ALL_MUSIC_CHANNELS = -2 # pause_music, unpause_music, stop_music, fadeout_music

# IF you add your own reserved channels, use numbers > 3 and < 8 
# (num channels == 8 unless you change mixer.set_num_channels(8))
# example : CH_SPINNER = 4 # doing this would ensure that your spinner doesn't 
#  eat all of your sound channels you would also need to add a 
#  mixer.set_reserved(CH_SPINNER) in the __init__() below, and be sure that
#  whenever you play() the spinner effect, you do so on this CH_SPINNER channel

# PLAYBACK "Priorities" for VOICE playback
# PLAY_SIMULTANEOUS = 1   # STANDARD METHOD USING SHARED CHANNEL (CH_SFX)
PLAY_QUEUED = 2         # ADD TO QUEUED CHANNEL (CH_VOICE)
PLAY_FORCE = 3          # STOP ANY SOUNDS PLAYING AND PLAY THIS
PLAY_NOTBUSY= 4         # only play or queue if nothing is currently playing
    
DUCKED_MUSIC_PERCENT = 0.5    # drops the music volume to this percentage when ducking for voice lines
# it not enabled by default for asset_manager loadeds sounds
# (because the way the pygame queue works, it has to be enabled for all voice calls or no voice calls).
# enable (from game code) via:
#   self.sound.enable_music_ducking(True)

class SoundController(mode.Mode):  #made this a mode since I want to use delay feature for audio queuing
    """Wrapper for pygame sound."""
    
    enabled = True
    

    def __init__(self,game,priority=10):
        super(SoundController, self).__init__(game,priority)
        self.logger = logging.getLogger('game.sound')
        try:
            mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)  #256 prev
            mixer.init()
            mixer.set_num_channels(8)
            
            self.queue=deque() #for queing up quotes
            
            mixer.set_reserved(CH_MUSIC_1)
            mixer.set_reserved(CH_MUSIC_2)
            mixer.set_reserved(CH_VOICE)

            #mixer.Channel(CH_VOICE).set_endevent(pygame.locals.USEREVENT)  -- pygame event queue really needs display and cause a ton of issues, creating own 
                            
        except Exception, e:
            self.logger.error("pygame mixer init failed; sound will be disabled: "+str(e))
            self.enabled = False

        self.ducking_enabled = False
        self.sounds = {}
        self.music = {}
        self.music_ducking_effect = 1.0 # no adjustment
        self.current_music_track_volume = 1.0
        self.set_volume(0.5)  # service mode should set the volume when it loads the last settings

    def play_music(self, key, loops=0, start_time=0.0, channel=CH_MUSIC):
        """Start playing music at the given *key*."""
        # self.logger.info("PLAY MUSIC " + str(key) + " on channel " + str(channel))
        if not self.enabled: return
        if key in self.music:
            if len(self.music[key]) > 1:
                # self.logger.info("Randomize Music")
                random.shuffle(self.music[key])

            if channel > 0 :                
                # playback music via regular "sound" mechanism
                if(start_time > 0):
                    raise ValueError, "play_music does not support start_time>0 for non standard channels"

                vol = self.music[key][0]["volume"]
                sound_file = self.music[key][0]["file"]
                mixer.Channel(channel).set_volume(self.volume * self.music_ducking_effect)
                
                if(self.music[key][0]["sound_obj"] is not None):
                    new_sound = self.music[key][0]["sound_obj"]
                else:
                    self.logger.warning("NOTE: Using non-streaming playback on music track [%s]; it is recommended you pre-load this track (change asset_manager entry to streaming_load:False)." % key)

                    new_sound = mixer.Sound(str(sound_file))
                    new_sound.set_volume(vol)

                self.logger.info("Music loaded, now telling to play")
                mixer.Channel(channel).play(new_sound, loops)
            else: 
                # playback on standard pyGame music object
                # get the volume
                self.current_music_track_volume = self.load_music(key)

                if(self.music[key][0]["sound_obj"] is not None):
                    self.logger.warning("NOTE: Using streaming playback on a pre loaded music track, [%s]; recommended you play to a different channel." % key)

                # self.logger.info("Music loaded, now setting volume and telling to play")
                mixer.music.set_volume (self.volume * self.music_ducking_effect*self.current_music_track_volume)

                mixer.music.play(loops,start_time)
                # self.logger.info("Play command issue, now unpause?")
                mixer.music.unpause()
                # self.logger.info("play music request complete")            
            
        
        else:
            self.logger.info("KEY NOT FOUND" + str(key))
                

    def stop_music(self, channel=CH_ALL_MUSIC_CHANNELS):
        """Stop the currently-playing music."""
        if not self.enabled: return

        if(channel==CH_ALL_MUSIC_CHANNELS):
            mixer.music.stop()
            mixer.Channel(CH_MUSIC_1).stop()
            mixer.Channel(CH_MUSIC_2).stop()
        elif channel == CH_MUSIC:
            mixer.music.stop()
        else:
            self.logger.info("stopping music on channel: %s" % channel)
            mixer.Channel(channel).stop()

    def fadeout_music(self, time_ms = 450, channel=CH_ALL_MUSIC_CHANNELS):
        """ """
        if not self.enabled: return
        
        if(channel==CH_ALL_MUSIC_CHANNELS):
            mixer.music.fadeout(time_ms)
            mixer.Channel(CH_MUSIC_1).fadeout(time_ms)
            mixer.Channel(CH_MUSIC_2).fadeout(time_ms)
        elif channel ==CH_MUSIC:
            mixer.music.fadeout(time_ms)
        else:
            mixer.Channel(channel).fadeout(time_ms)

    def load_music(self, key, channel=CH_MUSIC):
        """ """
        # self.logger.info("Handling load music for Key: " + str(key) + " and channel " + str(channel))
        if not self.enabled: return
        if channel == CH_MUSIC:
            mixer.music.load(self.music[key][0]["file"])
        else:
            """ note: this really doesn't do anything for alternate music channels """
            vol = self.music[key][0]["volume"]
            return vol
        return (self.music[key][0]["volume"])
        
    def register_sound(self, key, sound_file, channel=CH_SFX, volume=.4, is_voice=False):
        """ """
        self.logger.info("Registering sound - key: %s, file: %s", key, sound_file)
        if not self.enabled: return

        if os.path.isfile(sound_file):
            #if channel > 0:
            #    new_sound = mixer.Channel(channel).Sound(str(sound_file))
            #else:

            new_sound = mixer.Sound(str(sound_file))
            new_sound.set_volume(volume)
            
            if key in self.sounds:
                if not new_sound in self.sounds[key]['sound_list']:
                    self.sounds[key]['sound_list'].append(new_sound)
                    self.sounds[key]['is_voice'] = self.sounds[key]['is_voice'] or is_voice
            else:
                    self.sounds[key] = {'is_voice':is_voice, 'sound_list':[new_sound]}
        else:
            self.logger.error("Sound registration error: file %s does not exist!", sound_file)

    def register_music(self, key, music_file, volume=.4, streaming_load=True):
        """ """
        if not self.enabled: return
        if os.path.isfile(music_file):
            sound_obj = None
            if(not streaming_load):
                sound_obj = mixer.Sound(str(music_file))
                sound_obj.set_volume(volume)
            if key in self.music:
                if not music_file in self.music[key]:
                    self.music[key].append({'file':music_file,'volume':volume,'sound_obj':sound_obj})
            else:
                self.music[key] = [{'file':music_file,'volume':volume, 'sound_obj':sound_obj}]
        else:
            self.logger.error("Music registration error: file %s does not exist!", music_file)


    def check_voice_finished(self):
        """
        Voice playback uses a queue which is stored in self.queue but also makes use of pygame's own internal queue
        object to minimize delay between successive voice calls.  The pygame queue has length one, so it stores
        only a single sound to be played "next"

        This method gets called when a queued voice sound is completed (or when we think one should be), so we
        can add the next item from our queue (self.queue) to be the item in the pygame queue. Consider the picture
        below with sound items a, b, c, d.... a is currently playing, b will play next, then c, d, e...

        | a |   | b |        | c, d, e, ... |
        -----   -----        ----------------
        play    pyg.queue    self.queue

        we want to make sure that there is something in the pyg.queue before a finishes, which there is
        when b gets removed from the pygame queue (automatically, when playback of a finishes) we need to
        make sure c is moved into b's former spot some time before b completes playback.
        """
        #print "sound finished, the queue currently has :" + str(len(self.queue))

        # see if a voice call is already queued in PyGame
        queued_sound = mixer.Channel(CH_VOICE).get_queue() 
        self.logger.info("cvf: checking if voice playback is complete (pyg queue: %s)" % queued_sound)

        if (queued_sound):
            # we have a sound in the pyGame queue, so set a new delay; using too great a percentage to wait
            # (ie, waiting too long) could occur in the event that A is short and B is short, so we err on
            # the side of a few extra checks, checking again in 50% of the duration of B to see if A is done,
            # eventually it will be and we will catch this instant with at least 50% of B remaining:
            delay_length = 0.5 * queued_sound.get_length()

            self.logger.info("cvf: Found an element in the pygame audio queue - check again in %f" % delay_length)
            self.delay(delay=delay_length, handler=self.check_voice_finished, name="voice_finished")
            return

        # pygame sound queue is empty, so lets grab from our queue
        if len(self.queue) > 0:
            request = self.queue.popleft()
            key = request['key']
            
            if len(self.sounds[key]['sound_list']) > 0:
                random.shuffle(self.sounds[key]['sound_list'])
                
            # 'moving between queues sound: ' + key
            
            mixer.Channel(CH_VOICE).queue(self.sounds[key]['sound_list'][0])
            length = self.sounds[key]['sound_list'][0].get_length()
            #length = ceil(length * 100) / 100.0
            length = length -.02
            #print 'set up a sound finished handler with a delay of :' + str(length)
            self.delay(delay=length, handler=self.check_voice_finished, name="voice_finished")
            self.logger.info("cvf: Feeding an element from self.q into pygame audio queue (len(q)=%d)- check again in %f" % (len(self.queue),length))
            return 

        # otherwise?  Check if playback is just done!
        if(mixer.Channel(CH_VOICE).get_busy()):
            self.logger.info("cvf: No queued elements but sound still playing - stalling")
            self.delay(delay=0.1, handler=self.check_voice_finished, name="voice_finished")
        else:
            self.logger.info("cvf: voice playback complete.  Won't check until next play_voice()")
            self.__music_ducking(False)

    def play(self,key, loops=0, max_time=0, fade_ms=0, channel=None):
        """ plays the sound with the given *key* (as previously registered with register_sound)
            loops: number of _additional_ times it will play.  so 1 actually plays twice.  -1 is endless
            max_time: playback will stop after max_time millis
            fade_ms: playback fades in (from 0 volume) over fade_ms millis
            channel: the channel to play back on.  Specifying CH_VOICE will automatically call play_voice and 
                if other voice samples are currently playing, playback will be queued.
                If channel==None, CH_SFX is assumed _unless_ the sound file's  
                    .is_voice==True (was registered as a voice)
                To force a voice to play as a sound effect, pass CH_SFX as the channel arg
        """
        if not self.enabled: return
        if key in self.sounds:
            if len(self.sounds[key]['sound_list']) > 0:
                random.shuffle(self.sounds[key]['sound_list'])
            # print channel
            # print channel.__class__.__name__
            if channel is not None and channel.__class__.__name__== 'Channel':
                 channel.set_volume(self.volume)
                 channel.play(self.sounds[key]['sound_list'][0],loops,max_time,fade_ms)
                 return channel
            elif(channel == CH_VOICE) or (self.sounds[key]['is_voice']==True and channel==None):
                # call play_voice on behalf of the caller
                self.logger.info("playing [%s] as a voice!" % key)
                self.play_voice(key)
            elif channel is not None and channel > 0:
                mixer.Channel(channel).set_volume(self.volume)
                return mixer.Channel(channel).play(self.sounds[key]['sound_list'][0],loops,max_time,fade_ms)
            else:
                c = mixer.find_channel(True) # True means force
                c.set_volume(self.volume)
                c.play(self.sounds[key]['sound_list'][0],loops,max_time,fade_ms)
                return c
        else:
            self.logger.error("ERROR SOUND KEY NOT FOUND: %s", key)
            return 0

    def play_voice(self, key, action=PLAY_QUEUED, tag=None):
        """
        plays the sound that has been previously registered (register_sound) as a VOICE.

        Voice playback uses a queue which is stored in self.queue but also makes use of pygame's own internal queue
        object to minimize delay between successive voice calls.  The pygame queue has length one, so it stores
        only a single sound to be played "next"

        Consider the picture below with sound items { a, b, c, d, e }
        a is currently playing, b will play next, then c, d, e.

        | a |   | b |        | c, d, e, ... |
        -----   -----        ----------------
        play    pyg.queue    self.queue

        we want to make sure that there is something in the pyg.queue before a finishes, which there is
        when b gets removed from the pygame queue (automatically, when playback of a finishes) we need to
        make sure c is moved into b's former spot some time before b completes playback.
        """

        if not self.enabled: return 0

        self.logger.debug("play_voice(key=%s, action=%s)" % (key,action))

        # THIS ASSUMES THIS WAS REGISTERD AS A 'VOICE' and will play on the 'VOICE' channel

        if action==PLAY_NOTBUSY:
            if mixer.Channel(CH_VOICE).get_busy() or (mixer.Channel(CH_VOICE).get_queue() is not None):
                self.logger.debug("play_voice(key=%s, action=%s) - Voice module already busy - returning" % (key,action))
                return 0
        
        if key in self.sounds:
            if action==PLAY_FORCE:  #we need to clear our queue and stop anything playing
                # dump our queue
                self.logger.debug("play_voice(key=%s, action=%s) - FORCE requested, flushing queue" % (key,action))
                self.queue.clear()
                mixer.Channel(CH_VOICE).stop()
                mixer.Channel(CH_VOICE).stop()  # incase there was something in the pygame queue?
                # cancel sound completed callback, since it's no longer relevant
                self.cancel_delayed(name="voice_finished")
                
            # Check if there is a queue
            if (mixer.Channel(CH_VOICE).get_queue() or len(self.queue)>0): # PLAY_FORCE will have cleared the queue:
                # the delayed voice_finished for the currently playing track will
                # move this into playback for us eventually
                self.queue.append({'key':key,'tag':tag})
                length = 1
                self.logger.debug("play_voice(key=%s, action=%s) - queued to wait (len(q)=%d))" % (key,action,len(self.queue)))
            else:
                # there is no queue, so just play it now!
                if len(self.sounds[key]['sound_list']) > 0:
                    random.shuffle(self.sounds[key]['sound_list'])
                length = self.sounds[key]['sound_list'][0].get_length() * 0.98

                if action==PLAY_QUEUED:
                    # using queue since we are not 100% sure audio finsihed
                    mixer.Channel(CH_VOICE).queue(self.sounds[key]['sound_list'][0])
                    if(self.is_delayed('voice_finished')):
                        self.logger.debug("play_voice(key=%s, action=%s) - will play next (queue extended by %f)" % (key,action,length))
                        self.extend_delay_by('voice_finished', length)
                    else:
                        self.logger.debug("play_voice(key=%s, action=%s) - will play next (new queue check in %f)" % (key,action,length))
                        self.delay(delay=length, handler=self.check_voice_finished, name="voice_finished")
                elif action == PLAY_FORCE or action == PLAY_NOTBUSY:
                    # use play instead of queue since we want it to play now
                    # mixer.Channel(CH_VOICE).stop() # uncomment to use stop, if your driver won't force playback 
                    self.logger.debug("play_voice(key=%s, action=%s) - playing RIGHT NOW (next queue check in %f)" % (key,action,length))
                    mixer.Channel(CH_VOICE).play(self.sounds[key]['sound_list'][0]) 
                    self.delay(delay=length, handler=self.check_voice_finished, name="voice_finished")

            if(self.ducking_enabled):
                self.__music_ducking(True)

            return length
        else:
            self.logger.error("Voice sound with key '%s' not found" % key)
            return 0
        
    def voice_queued(self, key):
        #returns true if this sound is curently in our queue, but not if it is playing
        #or if it is queued in the channel to play, which we need to add to this somehow
        if key in self.queue:
            return True
        else:
            return False
        
    def empty_queue(self, tag='all'):
        if tag == 'all':
            self.queue.clear()
        else:
            for x in range(0,len(self.queue)):
                item = self.queue.popleft()
                if item['tag'] != tag:
                    self.queue.append(item)

    def stop(self, key, loops=0, max_time=0, fade_ms=0):
        """ """
        if not self.enabled: return
        if key in self.sounds:
            self.sounds[key]['sound_list'][0].stop()            
            # TODO: HOW DOES THIS WORK WITH VOICE?

    def pause_music(self, channel=CH_ALL_MUSIC_CHANNELS):
        if(channel==CH_ALL_MUSIC_CHANNELS):
            self.pause(CH_MUSIC)
            self.pause(CH_MUSIC_1)
            self.pause(CH_MUSIC_2)
        else:
            self.pause(channel)

    def unpause_music(self, channel=CH_ALL_MUSIC_CHANNELS):
        if(channel==CH_ALL_MUSIC_CHANNELS):
            self.unpause(CH_MUSIC)
            self.unpause(CH_MUSIC_1)
            self.unpause(CH_MUSIC_2)
        else:
            self.unpause(channel)

    #def play_voice_completed(self):
    #    pass
        ##this gets called when a queued sound is completed, we then add the next item from our queue to be the
        ##first/only item in the channels queue, which sould now be playing the last sound we queued
        #if len(self.queue) > 0:
        #    key = self.queue.popleft()
        #    if len(self.sounds[key]) > 0:
        #        random.shuffle(self.sounds[key])
        #    mixer.Channel(CH_VOICE).queue(self.sounds[key][0])

    def pause(self, channel=CH_MUSIC):
        """ this really only makes sense for CH_MUSIC, CH_MUSIC_1 and CH_MUSIC_2 """

        if channel==CH_MUSIC:
            mixer.music.pause()
        elif(channel < 0):
            # cannot possibly pause the randomly assigned sound effect channel and probably shouldn't anyway!
            raise ValueError, "Cannot pause randomly assigned SFX channels"
        else:
            mixer.Channel(channel).pause()
        # print 'pausing complete'

    def unpause(self, channel=CH_MUSIC):
        """ this really only makes sense for CH_MUSIC, CH_MUSIC_1 and CH_MUSIC_2 """

        # print "unpause mixer" + str(channel)
        if channel == CH_MUSIC:
            mixer.music.unpause()
        elif(channel < 0):
            # cannot unpause the randomly assigned sound effect channel and probably shouldn't anyway!
            raise ValueError, "Cannot unpause randomly assigned SFX channels"
        else:
            mixer.Channel(channel).unpause()
        # print 'Unpaused'

    def enable_music_ducking(self, enable):
        """ set this to true to turn ducking on, which drops the volume of
            music tracks when voices are played.  Disable to disable 
        """
        # if we are turning it off, make sure that we 
        # stop ducking in case we were already doing so
        if(self.ducking_enabled and enable==False):
            self.__music_ducking(False)
            
        self.ducking_enabled = enable

    def __music_ducking(self, enable):
        """ toggles internal ducking sound variables """
        if(not self.ducking_enabled):
            return

        if(enable):
            self.music_ducking_effect = DUCKED_MUSIC_PERCENT
            self.set_volume(self.volume)
        else:
            # stop ducking!
            self.music_ducking_effect = 1.0
            self.set_volume(self.volume)


    def volume_up(self):
        """ """
        if not self.enabled: return
        if (self.volume < 0.9):
            self.set_volume(self.volume + 0.1)
        return int(self.volume*10)

    def volume_down(self):
        """ """
        if not self.enabled: return
        if (self.volume > 0.1):
            self.set_volume(self.volume - 0.1)
        return int(self.volume*10)

    def set_volume(self, new_volume):
        """ """
        if not self.enabled: return
        self.volume = new_volume

        mixer.Channel(CH_VOICE).set_volume(self.volume)

        # adjust current Music mixer and Music channel volume level based on current track at new volume
        mixer.music.set_volume (new_volume * self.music_ducking_effect * self.current_music_track_volume)
        mixer.Channel(CH_MUSIC_1).set_volume (new_volume * self.music_ducking_effect) # for these, the sound file has 
        mixer.Channel(CH_MUSIC_2).set_volume (new_volume * self.music_ducking_effect) # self.current_music_track_volume

    def beep(self):
        if not self.enabled: return
        pass
        #   self.play('chime')

def testcase():
    """ run this testcase from the SampleGame folder (w/ sound asssets!), via:
        $ python ../procgame/sound.py 
    """
    import procgame

    curr_file_path = os.path.abspath("./") 
    print curr_file_path
    
    dots_w = 224
    dots_h = 112

    import procgame.game.skeletongame
    g = procgame.game.SkeletonGame('config/T2.yaml', curr_file_path)

    # if we don't wait until the game comes up, this won't work...
    def phase1(self):
        # self.game.sound.play_music('base-music-bgm', channel=CH_MUSIC)
        #self.game.sound.play_music('base-music-bgm', channel=CH_MUSIC_2)
        self.game.sound.play_music('base-music-bgm', channel=CH_MUSIC_2)

        # self.game.sound.play_voice('target_bank') 
        # self.game.sound.play_voice('target_bank') 
        # self.game.sound.play_voice('target_bank') 
        # self.game.sound.play_voice('target_bank') 
        self.game.sound.play('ss_missV')

    def phase2(self):
        #self.game.sound.stop_music(channel=CH_MUSIC_2)
        # self.game.sound.pause_music()
        # self.game.sound.play_voice('target_bank') 
        # self.game.sound.play_voice('target_bank') 
        self.game.sound.play_voice('ss_successV')
        self.game.sound.play('ss_successV')
        self.game.sound.play('ss_missV')
        # self.game.sound.play_voice('target_bank') 

    def phase3(self):
        # self.game.sound.stop_music()
        self.game.sound.fadeout_music()
    
    try:
        g.sound.enable_music_ducking(False)
        g.sound.delay(delay=1.0, handler=phase1, param=g.sound)
        g.sound.delay(delay=3.0, handler=phase2, param=g.sound)
        g.sound.delay(delay=12.0, handler=phase3, param=g.sound)
        g.modes.add(g.sound)

        g.run_loop()

    except Exception, e:
        import traceback
        print "=============FATAL=================="
        print e
        print e.__class__.__name__
        traceback.print_exc(e)
        print "===================================="
        g.end_run_loop()

if __name__ == '__main__':
    testcase()