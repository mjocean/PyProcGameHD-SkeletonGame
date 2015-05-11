import sys
import os
import pinproc
import procgame.game
import procgame.dmd
import procgame.dmd.font
import time
import logging

logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class PlayerGame(procgame.game.BasicGame):
	
	anim_layer = None
	
	def __init__(self, machine_type, width=128, height=32):
		super(PlayerGame, self).__init__(machine_type)
		f = procgame.dmd.font_named('Font07x5.dmd')
		self.dmd = procgame.dmd.DisplayController(self, width=width, height=height, message_font=f)
		self.anim_layer = procgame.dmd.AnimatedLayer()
		mode = procgame.game.Mode(game=self, priority=1)
		mode.layer = self.anim_layer
		self.modes.add(mode)
	
	def play(self, filename, repeat, hold=False, frametime=10):
		anim = procgame.dmd.Animation().load(filename)
		print("file has resolution (%d x %d)" % (anim.width, anim.height))
		self.anim_layer.frames = anim.frames
		self.anim_layer.repeat = repeat
		self.anim_layer.hold = hold
		self.anim_layer.frame_time = frametime
		if not repeat and not hold:
			self.anim_layer.add_frame_listener(-1, self.end_of_animation)
	
	def end_of_animation(self):
		self.end_run_loop()


def tool_populate_options(parser):
	parser.add_option('-m', '--machine-type', action='store', help='wpc, wpc95, stermSAM, sternWhitestar or custom (default)')
	parser.add_option('-r', '--repeat', action='store_true', help='Repeat the animation indefinitely')
	parser.add_option('-l', '--hold', action='store_true', help='Hold the last frame')
	parser.add_option('-f', '--frametime', type="int", dest='frametime', default=10, help='set the frame time')
	parser.add_option('-s', '--size', type="int", dest='size', nargs=2, metavar="WIDTH HEIGHT", default=(128,32), help='set the WIDTH and HEIGHT of the player (in dots)')

def tool_get_usage():
    return """<file.dmd>"""

def tool_run(options, args):
	if len(args) != 1:
		return False
	
	if options.machine_type:
		machine_type = pinproc.normalize_machine_type(options.machine_type)
	else:
		machine_type = pinproc.MachineTypeCustom
	
	game = PlayerGame(machine_type=machine_type,width=options.size[0], height=options.size[1])

	game.play(filename=args[0], repeat=options.repeat, hold=options.hold, frametime = options.frametime)
	
	game.run_loop()
	del game
	return True
