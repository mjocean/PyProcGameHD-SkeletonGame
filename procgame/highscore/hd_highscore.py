##################################################
#     __        __     __    _       __                            
#    / /_  ____/ /    / /_  (_)___ _/ /_  ______________  ________ 
#   / __ \/ __  /    / __ \/ / __ `/ __ \/ ___/ ___/ __ \/ ___/ _ \
#  / / / / /_/ /    / / / / / /_/ / / / (__  ) /__/ /_/ / /  /  __/
# /_/ /_/\__,_/____/_/ /_/_/\__, /_/ /_/____/\___/\____/_/   \___/ 
#            /_____/       /____/                                  
#
##################################################
# An alternate high-score entry and display manager for
# the HdDMD PyProcGame "fork"
#
# Instructions for use are mostly the same as the stock
# http://pyprocgame.pindev.org/ref/highscore.html
#
#
# 1. Put this somewhere, and import it in your Game class
# 2. in the game Class's __init__ add the following:
#
#		## load your score files
#		self.load_game_data('game_default_data.yaml','game_user_data.yaml')
#
#		## high score stuff:
#		self.highscore_categories = []
#
#		cat = highscore.HighScoreCategory()
#		cat.game_data_key = 'ClassicHighScores'
#		cat.titles = ['Grand Champion', 'High Score 1', 'High Score 2', 'High Score 3', 'High Score 4']
#		self.highscore_categories.append(cat)
#
# 3. in the game class's game_ended() method add the following:
# 	def game_ended(self):
#
#		seq_manager = HD_EntrySequenceManager(game=self, priority=2)
#		seq_manager.finished_handler = self.highscore_entry_finished
#		seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
#		self.modes.add(seq_manager)
#
# 4. note this refers to a method called 'highscore_entry_finished' -- define that in the Class, too:
#
#	def highscore_entry_finished(self, mode):
#		self.modes.remove(mode)
#		super(BuffyGame, self).game_ended()
#
#		# Do clean up stuff, e.g., turn off all the lamps
#		for lamp in self.lamps:
#			lamp.disable()
#
#		# remove active game modes and re-add the sttract mode
#		self.modes.add(self.attract_mode)
#		self.reset()
#
# 5. change the sizes in the code below
#
# 6. change the fonts in the code below
#
# Enjoy..?


import math
from procgame.game import Mode
from procgame import dmd
from procgame import highscore

class HD_InitialEntryMode(Mode):
	"""Mode that prompts the player for their initials.
	
	*left_text* and *right_text* are strings or arrays to be displayed at the
	left and right corners of the display.  If they are arrays they will be
	rotated.
	
	:attr:`entered_handler` is called once the initials have been confirmed.
	
	This mode does not remove itself; this should be done in *entered_handler*."""
	
	### LOOK HERE: change the following to suit your game and tastes... 
	# set these to your display's width and height
	display_width = 450
	display_height = 225

	# change this to the number of chars wide you want your character selection palette to be
	columns_of_chars_in_palette = 8

	# the number of dots to encompass each character in the palette (includes surrounding space!)
	space_per_char = 25 # make sure your font is smaller than this!

	entered_handler = None
	"""Method taking two parameters: `mode` and `inits`."""
	
	char_back =  '<'
	char_done =  '>'
	
	init_font = None
	font = None
	letters_font = None
	
	def __init__(self, game, priority, left_text, right_text, entered_handler):
		super(HD_InitialEntryMode, self).__init__(game, priority)
		
		self.entered_handler = entered_handler
		
		# self.init_font = dmd.font_named('Font09Bx7.dmd')
		# self.font = dmd.font_named('Font07x5.dmd')
		# self.letters_font = dmd.font_named('Font07x5.dmd')

		## YOU almost CERTAINLY need to change these...
		self.init_font = self.game.fonts['large']
		self.text_font = self.game.fonts['small']
		self.letters_font = self.game.fonts['mono-tiny']
		self.letters_font_mini = self.game.fonts['mono-micro']

		self.init_font_height = self.init_font.size("Z")[1]
		
		self.text_font_height = self.text_font.size(left_text)[1]

		self.layer = dmd.GroupedLayer(self.display_width, self.display_height)
		self.layer.opaque = True
		self.layer.layers = []
		
		if type(right_text) != list:
			right_text = [right_text]
		if type(left_text) != list:
			left_text = [left_text]
		
		seconds_per_text = 1.5
		
		script = []
		mh = 0
		for text in left_text:
			words = text.split()
			h = self.text_font_height*len(words)
			mh = max(h, mh)
			frame = dmd.Frame(width=self.display_width, height=h)
			i = 0
			for w in words:
				self.text_font.draw(frame, w, 0, i*self.text_font_height)
				i+=1
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_left_layer = dmd.ScriptedLayer(width=self.display_width, height=mh, script=script)
		topthird_left_layer.composite_op = 'blacksrc'
		topthird_left_layer.target_y = self.display_height/2 - mh/2
		topthird_left_layer.target_x = 10
		self.layer.layers += [topthird_left_layer]
		
		script = []
		mh = 0
		for text in right_text:
			words = text.split()
			h = self.text_font_height*len(words)
			mh = max(h, mh)
			frame = dmd.Frame(width=self.display_width, height=h)
			i = 0
			for w in words:
				self.text_font.draw(frame, w, self.display_width-(self.text_font.size(w)[0]), i*self.text_font_height)
				i+=1
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_right_layer = dmd.ScriptedLayer(width=self.display_width, height=mh, script=script)
		topthird_right_layer.composite_op = 'blacksrc'
		topthird_right_layer.target_y = self.display_height/2 - mh/2
		topthird_right_layer.target_x = -10
		self.layer.layers += [topthird_right_layer]

		# the entered initials so far		
		self.inits_layer = dmd.HDTextLayer(self.display_width/2, self.init_font_height/2+5, self.init_font, "center", vert_justify="center", line_color=(128,128,255), line_width=1, interior_color=(0,0,192),fill_color=(0,0,0)).set_text("")
		self.inits_layer.set_target_position(0, self.text_font_height+2)
		self.layer.layers += [self.inits_layer]

		
		self.letters = []
		for idx in range(26):
			self.letters += [chr(ord('A')+idx)]
		self.letters += [' ', '.', self.char_back, self.char_done]
		self.current_letter_index = 0
		self.inits = self.letters[self.current_letter_index]

		# Draw my fancy rows
        w = self.space_per_char*(self.columns_of_chars_in_palette+1)
        h = self.space_per_char*(30/self.columns_of_chars_in_palette+1.5)
        print("About to create a frame with w=" + str(w) + "; h=" + str(h))
		self.char_optsF = dmd.Frame(width=w, height=h)
		for index in range(30):
			x = index % self.columns_of_chars_in_palette 
			y = index / self.columns_of_chars_in_palette 
			(w,h) = self.letters_font.size(self.letters[index])
			if(index<28):
				self.letters_font.draw(self.char_optsF, self.letters[index], (x+1) * self.space_per_char - w/2, (y+1) * self.space_per_char - h/2)
			elif(index==28):
				(w,h) = self.letters_font_mini.size("DEL")
				self.letters_font_mini.draw(self.char_optsF, "DEL", (x+1) * self.space_per_char - w/2, (y+1) * self.space_per_char - h/2)
			elif(index==29):
				(w,h) = self.letters_font_mini.size("END")
				self.letters_font_mini.draw(self.char_optsF, "END", (x+1) * self.space_per_char - w/2, (y+1) * self.space_per_char - h/2)

		self.char_opts_layer = dmd.FrameLayer(opaque=False, frame=self.char_optsF)
		self.char_opts_layer.set_target_position((self.display_width-(self.columns_of_chars_in_palette+1) * self.space_per_char)/2, self.init_font_height)
		# self.char_opts_layer.composite_op = "blacksrc"
		self.layer.layers += [self.char_opts_layer]

		fbox = dmd.Frame(width=self.space_per_char, height=self.space_per_char)
		fbox.fill_rect(0, 0, self.space_per_char, self.space_per_char, (128,128,255))
		fbox.fill_rect(2, 2, self.space_per_char-4, self.space_per_char-4, (0,0,128))
		self.selection_box_layer = dmd.FrameLayer(opaque=False, frame=fbox)
		self.selection_box_layer.composite_op = "max"
		self.layer.layers += [self.selection_box_layer]


		self.animate_to_index(0)
	
	def mode_started(self):
		pass
		
	def mode_stopped(self):
		pass
				
	def animate_to_index(self, new_index, inc = 0):
		x = new_index % self.columns_of_chars_in_palette 
		y = new_index / self.columns_of_chars_in_palette 
		(bx, by) =   (self.char_opts_layer.target_x,self.char_opts_layer.target_y)
		self.selection_box_layer.set_target_position( x * self.space_per_char + bx + self.space_per_char/2, y * self.space_per_char + by + self.space_per_char/2)
		print("moving box to:", self.selection_box_layer.target_x, ",", self.selection_box_layer.target_y)

		self.current_letter_index = new_index

		# Now draw the initials, being careful to change the display based on which option is highlighted:
		if(self.letters[self.current_letter_index]==self.char_back):
			self.inits_layer.set_text(self.inits[:-2])
		elif(self.letters[self.current_letter_index]==self.char_done):
			self.inits_layer.set_text(self.inits[:-1], blink_frames = 15)
		else:
			self.inits_layer.set_text(self.inits)
		
	def letter_increment(self, inc):
		new_index = (self.current_letter_index + inc)
		if new_index < 0:
			new_index = len(self.letters) + new_index
		elif new_index >= len(self.letters):
			new_index = new_index - len(self.letters)
		#print("letter_increment %d + %d = %d" % (self.current_letter_index, inc, new_index))
		self.inits = self.inits[:-1] + self.letters[new_index]
		self.animate_to_index(new_index, inc)
	
	def letter_accept(self):
		# TODO: Add 'back'/erase/end
		letter = self.letters[self.current_letter_index]
		if letter == self.char_back:
			if len(self.inits) > 0:
				self.inits = self.inits[:-1]
		elif letter == self.char_done or len(self.inits) > 10:
			self.inits = self.inits[:-1] # Strip off the done character
			if self.entered_handler != None:
				self.entered_handler(mode=self, inits=self.inits)
			else:
				self.game.logger.warning('InitialEntryMode finished but no entered_handler to notify!')
		else:
			self.inits += letter
		self.letter_increment(0)
	
	def sw_flipperLwL_active(self, sw):
		self.periodic_left()
		return False
	def sw_flipperLwL_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def sw_flipperLwR_active(self, sw):
		self.periodic_right()
		return False
	def sw_flipperLwR_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def periodic_left(self):
		self.letter_increment(-1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_left)
	def periodic_right(self):
		self.letter_increment(1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_right)
		
	def sw_startButton_active(self, sw):
		self.letter_accept()
		return True

####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################

### This is the old, scrolling mode from Adam, that I tried to adapt to be more 
# flexible with fonts and sizes. I bailed on it, but leave this here if you want
# to try to track this down (e.g., if your display isn't as huge as mine)
class HD_InitialEntryMode_old(Mode):
	"""Mode that prompts the player for their initials.
	
	*left_text* and *right_text* are strings or arrays to be displayed at the
	left and right corners of the display.  If they are arrays they will be
	rotated.
	
	:attr:`entered_handler` is called once the initials have been confirmed.
	
	This mode does not remove itself; this should be done in *entered_handler*."""
	
	entered_handler = None
	"""Method taking two parameters: `mode` and `inits`."""
	
	char_back = '<'
	char_done = '='
	
	init_font = None
	font = None
	letters_font = None
	
	def __init__(self, game, priority, left_text, right_text, entered_handler):
		super(HD_InitialEntryMode, self).__init__(game, priority)
		
		self.entered_handler = entered_handler
		
		# self.init_font = dmd.font_named('Font09Bx7.dmd')
		# self.font = dmd.font_named('Font07x5.dmd')
		# self.letters_font = dmd.font_named('Font07x5.dmd')

		self.init_font = self.game.fonts['small']
		self.text_font = self.game.fonts['large']
		self.letters_font = self.game.fonts['med']

		self.init_font_height = self.init_font.size("Z")[1]
		self.text_font_height = self.text_font.size("Z")[1]

		self.layer = dmd.GroupedLayer(480, 240)
		self.layer.opaque = True
		self.layer.layers = []
		
		if type(right_text) != list:
			right_text = [right_text]
		if type(left_text) != list:
			left_text = [left_text]
		
		seconds_per_text = 1.5
		
		script = []
		for text in left_text:
			frame = dmd.Frame(width=450, height=self.text_font_height)
			self.text_font.draw(frame, text, 0, 0)
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_left_layer = dmd.ScriptedLayer(width=480, height=self.text_font_height, script=script)
		topthird_left_layer.composite_op = 'blacksrc'
		self.layer.layers += [topthird_left_layer]
		
		script = []
		for text in right_text:
			frame = dmd.Frame(width=480, height=self.text_font_height)
			self.text_font.draw(frame, text, 480-(self.text_font.size(text)[0]), 0)
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_right_layer = dmd.ScriptedLayer(width=480, height=self.text_font_height, script=script)
		topthird_right_layer.composite_op = 'blacksrc'
		self.layer.layers += [topthird_right_layer]
		
		self.inits_frame = dmd.Frame(width=480, height=self.init_font_height)
		inits_layer = dmd.FrameLayer(opaque=False, frame=self.inits_frame)
		inits_layer.set_target_position(0, self.text_font_height+2)
		self.layer.layers += [inits_layer]
		
		self.lowerhalf_layer = dmd.FrameQueueLayer(opaque=False, hold=True)
		self.lowerhalf_layer.set_target_position(0, self.init_font_height+self.text_font_height)
		self.layer.layers += [self.lowerhalf_layer]
		
		self.letters = []
		for idx in range(26):
			self.letters += [chr(ord('A')+idx)]
		self.letters += [' ', '.', self.char_back, self.char_done]
		self.current_letter_index = 0
		self.inits = self.letters[self.current_letter_index]
		self.animate_to_index(0)
	
	def mode_started(self):
		pass
		
	def mode_stopped(self):
		pass
				
	def animate_to_index(self, new_index, inc = 0):
		letter_spread = 20
		letter_width = self.letters_font_width
		if inc < 0:
			rng = range(inc * letter_spread, 1)
		elif inc > 0:
			rng = range(inc * letter_spread)[::-1]
		else:
			rng = [0]
		#print rng
		for x in rng:
			frame = dmd.Frame(width=450, height=self.init_font_height+2)
			for offset in range(-7, 8):
				index = new_index - offset
				#print "Index %d  len=%d" % (index, len(self.letters))
				if index < 0:
					index = len(self.letters) + index
				elif index >= len(self.letters):
					index = index - len(self.letters)
				(w, h) = self.letters_font.size(self.letters[index])
				#print "Drawing %d w=%d" % (index, w)
				self.letters_font.draw(frame, self.letters[index], 450/2 - offset * letter_spread - letter_width/2 + x, 0)
			frame.fill_rect(64-5, 0, 1, self.init_font_height+2, 1)
			frame.fill_rect(64+5, 0, 1, self.init_font_height+2, 1)
			self.lowerhalf_layer.frames += [frame]
		self.current_letter_index = new_index
		
		# Prune down the frames list so we don't get too far behind while animating
		x = 0
		while len(self.lowerhalf_layer.frames) > 15 and x < (len(self.lowerhalf_layer.frames)-1):
			del self.lowerhalf_layer.frames[x]
			x += 2
		
		# Now draw the top right panel, with the selected initials in order:
		self.inits_frame.clear()
		init_spread = self.init_font_width + 3
		x_offset = self.inits_frame.width/2 - len(self.inits) * init_spread / 2
		for x in range(len(self.inits)):
			self.init_font.draw(self.inits_frame, self.inits[x], x * init_spread + x_offset, 0)
		self.inits_frame.fill_rect((len(self.inits)-1) * init_spread + x_offset, 9, 8, 1, 1)
		
	def letter_increment(self, inc):
		new_index = (self.current_letter_index + inc)
		if new_index < 0:
			new_index = len(self.letters) + new_index
		elif new_index >= len(self.letters):
			new_index = new_index - len(self.letters)
		#print("letter_increment %d + %d = %d" % (self.current_letter_index, inc, new_index))
		self.inits = self.inits[:-1] + self.letters[new_index]
		self.animate_to_index(new_index, inc)
	
	def letter_accept(self):
		# TODO: Add 'back'/erase/end
		letter = self.letters[self.current_letter_index]
		if letter == self.char_back:
			if len(self.inits) > 0:
				self.inits = self.inits[:-1]
		elif letter == self.char_done or len(self.inits) > 10:
			self.inits = self.inits[:-1] # Strip off the done character
			if self.entered_handler != None:
				self.entered_handler(mode=self, inits=self.inits)
			else:
				self.game.logger.warning('InitialEntryMode finished but no entered_handler to notify!')
		else:
			self.inits += letter
		self.letter_increment(0)
	
	def sw_flipperLwL_active(self, sw):
		self.periodic_left()
		return False
	def sw_flipperLwL_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def sw_flipperLwR_active(self, sw):
		self.periodic_right()
		return False
	def sw_flipperLwR_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def periodic_left(self):
		self.letter_increment(-1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_left)
	def periodic_right(self):
		self.letter_increment(1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_right)
		
	def sw_startButton_active(self, sw):
		self.letter_accept()
		return True

class HD_EntrySequenceManager(highscore.EntrySequenceManager):
	def create_highscore_entry_mode(self, left_text, right_text, entered_handler):
		"""Subclasses can override this to supply their own entry handler."""
		return HD_InitialEntryMode(game=self.game, priority=self.priority+1, left_text=left_text, right_text=right_text, entered_handler=entered_handler)


#### 
# The following allows me to test just the high score entry mode, and does so
# with this hd_highscore.py file in a sub-directory of my game directory
# You likely need to change this...

def main():
	import pinproc

	# add the directory one level up to the path and switch to it
	import os
	import sys
	sys.path.insert(1, os.path.join(sys.path[0], '..'))
	os.chdir(os.path.join(sys.path[0], '..'))

	# import your game class and instantiate it
	import ExampleGame
	game = ExampleGame.TEST_BuffyGame()

	# (BUT you don't want to?  Fine, so something like this...)
	# game = procgame.game.BasicGame(pinproc.MachineTypeWPC)
	# game.load_config('../sof.yaml') # in VP this is found in c:\P-ROC\shared\config\

	handler = None
	game.add_player() # can't test high-score entry without a player!

	mode = HD_InitialEntryMode(game, 3, "Player 1", "Grand Champion", handler)
	game.modes.add(mode)

	game.run_loop()

if __name__ == '__main__':
	main()	