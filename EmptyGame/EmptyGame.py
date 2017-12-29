##########################
# this is intended to be a very simple game from which
# to start a new game --use SampleGame or T2Game for examples
#
# The following imports add the "usual" stuff every game needs
import logging
import procgame
import procgame.game
import procgame.dmd
from procgame.game import SkeletonGame
from procgame import *
import os
from procgame.modes import Attract
from procgame.game.skeletongame import run_proc_game

# these are modes that you define, and probably store in
# a my_modes folder under this one....
import my_modes
from my_modes import BaseGameMode, MachineMonitorMode

# set up a few more things before we get started
# the logger's configuration and format
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
curr_file_path = os.path.dirname(os.path.abspath( __file__ ))

logging.getLogger('game.driver').setLevel(logging.INFO)
logging.getLogger('game.vdriver').setLevel(logging.INFO)

class MyGame(SkeletonGame):

    # constructor for the game object; called once
    def __init__(self):

        # THESE MUST BE DEFINED for SkeletonGame
        self.curr_file_path = curr_file_path

        # optional definition for 'auto-closed' switches
        # self.osc_closed_switches = ['trough2','trough3', 'trough4', 'trough5','trough6', 'trough7']

        # call the super class which makes the game and specify where to find
        # the 'machine (specific) yaml -CHANGE THIS!
        super(MyGame, self).__init__('config/JD.yaml', self.curr_file_path)

        self.base_game_mode = BaseGameMode(game=self)
        self.machine_monitor = MachineMonitorMode(game=self)

        # call reset (to reset the machine/modes/etc)
        self.reset()

    # called when you want to fully reset the game
    def reset(self):
        # EVERY SkeletonGame game should start its reset() with a call to super()
        super(MyGame,self).reset()

        # initialize the mode variables; the general form is:
        # self.varName = fileName.classModeName(game=self)
        # Note this creates the mode and causes the Mode's constructor
        # function --aka __init__()  to be run
        # self.some_non_advancedMode = ModeFile.MyMode(game=self)

        # add /some/ of the modes to the game's mode queue:
        # as soon as you add a mode, it is active/starts.
        # modes added here
        # e.g.,
        # self.modes.add(self.some_non_advancedMode)

        # EVERY SkeletonGame game should end its reset() with a call to start_attract_mode()
        self.start_attract_mode() # plays the attract mode and kicks off the game

## the following just set things up such that you can run Python EmptyGame.py
## and it will create an instance of the correct game objct and start running it!

if __name__ == '__main__':
    run_proc_game(MyGame)
