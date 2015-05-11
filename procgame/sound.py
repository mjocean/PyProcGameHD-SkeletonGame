#    _____ ____  __  ___   ______     __________  _   ____________  ____  __    __    __________ 
#   / ___// __ \/ / / / | / / __ \   / ____/ __ \/ | / /_  __/ __ \/ __ \/ /   / /   / ____/ __ \
#   \__ \/ / / / / / /  |/ / / / /  / /   / / / /  |/ / / / / /_/ / / / / /   / /   / __/ / /_/ /
#  ___/ / /_/ / /_/ / /|  / /_/ /  / /___/ /_/ / /|  / / / / _, _/ /_/ / /___/ /___/ /___/ _, _/ 
# /____/\____/\____/_/ |_/_____/   \____/\____/_/ |_/ /_/ /_/ |_|\____/_____/_____/_____/_/ |_|  
																							   
#
#All credit due to Josh Kugler, this is mostly his...
#
import random
import time
import logging
#from procgame import * 
from procgame.game import mode
from collections import deque
from math import ceil

try:
	logging.getLogger('game.sound').info("Initializing sound...")
	from pygame import mixer # This call takes a while.
except ImportError, e:
	logging.getLogger('game.sound').error("Error importing pygame.mixer; sound will be disabled!  Error: "+str(e))

import os.path

SNDCHL_DEFAULT_MUSIC = 0
SNDCHL_ANY = 0
SNDCHL_MUSIC = 1 
SNDCHL_SFX = 2
SNDCHL_VOICE = 3 

SND_IFAVAIL = 0
SND_FORCE = 1
SND_QUEUE = 2

class SoundController(mode.Mode):  #made this a mode since I want to use delay feature for audio queuing
	
	enabled = True
	
	def __init__(self,game,priority=1):
		super(SoundController, self).__init__(game,priority)
		self.logger = logging.getLogger('game.sound')

		try:
			self.sounds = {}
			self.music = {}
			self.queue = {}
			self.queue[SNDCHL_MUSIC]=deque() #for queing 
			self.music_track = mixer.Channel(SNDCHL_MUSIC)
			mixer.set_reserved(SNDCHL_MUSIC)

			self.queue[SNDCHL_SFX]=deque() #for queing             
			self.sfx_track = mixer.Channel(SNDCHL_SFX)
			mixer.set_reserved(SNDCHL_SFX)
			
			self.queue[SNDCHL_VOICE]=deque() #for queing             
			self.voice_track = mixer.Channel(SNDCHL_VOICE)
			mixer.set_reserved(SNDCHL_VOICE)

			# self.end_time[SNDCHL_VOICE] = 0
			# self.end_time[SNDCHL_MUSIC] = 0
			# self.end_time[SNDCHL_SFX] = 0

		except Exception, e:
			# The import mixer above may work, but init can still fail if mixer is not fully supported.
			self.enabled = False
			self.logger.error("pygame mixer init failed; sound will be disabled: "+str(e))
		self.music_volume_offset = 0
		self.set_volume(0.5)  #so this does not get saved, hmm

	def play_music(self, key, loops=0, start_time=0.0, channel=SNDCHL_DEFAULT_MUSIC):
		"""Start playing music at the given *key*."""
		if not self.enabled: return
		if key in self.music:
			if len(self.music[key]) > 0:
				random.shuffle(self.music[key])
			if channel > 0 :
				v = self.load_music(key, channel=channel)
				mixer.Channel(channel).set_volume(v)
				mixer.Channel(channel).music.play(loops,start_time)
			else:
				v = self.load_music(key)
				mixer.music.set_volume(v)
				mixer.music.play(loops,start_time)
				

	def stop_music(self, channel=SNDCHL_DEFAULT_MUSIC):
		"""Stop the currently-playing music."""
		if not self.enabled: return
		if channel == 0:
			mixer.music.stop()
		else:
			mixer.Channel(channel).music.stop()

	def fadeout_music(self, time_ms = 450, channel=SNDCHL_DEFAULT_MUSIC):
		""" """
		if not self.enabled: return
		if channel > 0:
			mixer.Channel(channel).fadeout(time_ms)
		else:
			mixer.music.fadeout(time_ms)

	def load_music(self, key, channel=SNDCHL_DEFAULT_MUSIC):
		""" """
		if not self.enabled: return
		if channel > 0:
			mixer.Channel(channel).music.load(self.music[key][0][0])
		else:
			mixer.music.load(self.music[key][0][0])
		return (self.music[key][0][1])

	def register_sound(self, key, sound_file, volume=.8):
		""" """
		#self.logger.info("Registering sound - key: %s, file: %s", key, sound_file)
		if not self.enabled: return
		if os.path.isfile(sound_file):
			self.new_sound = mixer.Sound(str(sound_file))
			self.new_sound.set_volume(self.volume)
			if key in self.sounds:
				if not self.new_sound in self.sounds[key]:
					self.sounds[key].append(self.new_sound)
			else:
				self.sounds[key] = [self.new_sound]
		else:
			self.logger.error("Sound registration error: file %s does not exist!", sound_file)


	def register_music(self, key, music_file, volume=0.5):
		""" """
		if not self.enabled: return
		if os.path.isfile(music_file):
			if key in self.music:
				if not music_file in self.music[key]:
					self.music[key].append([music_file,volume])
			else:
				self.music[key] = [[music_file,volume]]
		else:
			self.logger.error("Music registration error: file %s does not exist!", music_file)


	def play(self,key, loops=0, max_time=0, fade_ms=0, channel=SNDCHL_ANY, action=SND_IFAVAIL):
		""" """
		if not self.enabled: return

		if not key in self.sounds:
			return

		# time takes time...
		#current_time = time.time()
		
		# pre-compute duration and log it in the dict??
		duration = self.sounds[key][0].get_length() * (loops+1)

		if key in self.sounds:
			if(channel>0):
				if action==SND_IFAVAIL:
					if mixer.Channel(channel).get_busy():
						return 0
				elif action==SND_FORCE:  #we need to clear our queue and stop anything playing
					self.queue[channel].clear()
					mixer.Channel(channel).stop()
					mixer.Channel(channel).stop()  # incase there was something in the pygame queue?

				if mixer.Channel(channel).get_busy() and action != SND_FORCE:
					# print 'APPENDING TO QUEUE'
					self.queue[channel].append(key)
					#mixer.Channel(channel).queue(self.sounds[key][0])
					#w = self.end_time[channel].peekleft()
					#self.end_time[channel].append(duration + w) 
					return duration #+ w

				if len(self.sounds[key]) > 0:
					random.shuffle(self.sounds[key])
				mixer.Channel(channel).play(self.sounds[key][0],loops,max_time,fade_ms)
				
				if(channel>0):
					duration = duration +.01
					self.delay(delay=duration, handler=self.sound_finished, param=channel)

				return duration
			else:
				if len(self.sounds[key]) > 0:
					random.shuffle(self.sounds[key])
				self.sounds[key][0].play(loops,max_time,fade_ms)
		else:
			return 0

	def sound_finished(self,channel):
		#this gets called when a queued sound is completed, we then add the next item from our queue to be the
		#first/only item in the channels queue, which sould now be playing the last sound we queued
		# print("sound_finished, checking for next sound")
		if len(self.queue[channel]) > 0:
			key = self.queue[channel].popleft()
			if len(self.sounds[key]) > 0:
				random.shuffle(self.sounds[key])
			mixer.Channel(channel).queue(self.sounds[key][0])
			duration = self.sounds[key][0].get_length() 

			self.delay(delay=duration, handler=self.sound_finished, param=channel)


	def stop(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if not self.enabled: return
		if key in self.sounds:
			self.sounds[key][0].stop()

	def volume_up(self):
		""" """
		if not self.enabled: return
		if (self.volume < 0.8):
			self.set_volume(self.volume + 0.1)
		return self.volume*10

	def volume_down(self):
		""" """
		if not self.enabled: return
		if (self.volume > 0.2):
			self.set_volume(self.volume - 0.1)
		return self.volume*10

	def set_volume(self, new_volume):
		""" """
		if not self.enabled: return
		self.volume = new_volume
		mixer.music.set_volume (new_volume + self.music_volume_offset)
		for key in self.sounds:
			for sound in self.sounds[key]:
				sound.set_volume(self.volume)

	def beep(self):
		if not self.enabled: return
		pass
		#	self.play('chime')

def main():
	import os
	import procgame

	curr_file_path = os.path.dirname(os.path.abspath( __file__ ))

	game = procgame.game.BasicGame('pinproc.MachineTypeWPC')

	game.sound_path = curr_file_path + "/sound/"
	game.sfx_path = game.sound_path + "sfx/"


	game.reset()
	game.sound = SoundController(game)
	game.modes.add(game.sound)
	game.sound.register_sound('swing',game.sfx_path+'swing3.wav')
	game.sound.register_sound('hit',game.sfx_path+'hit-connects.wav')


	game.sound.play('swing', channel=SNDCHL_SFX, action=SND_QUEUE)
	game.sound.play('hit', channel=SNDCHL_SFX, action=SND_QUEUE)
	game.sound.play('well_done', channel=SNDCHL_SFX, action=SND_QUEUE)


if __name__ == '__main__':
	main()