##########################
# this is intended to be a very simple game from which 
# to learn SkeletonGame based PyProcGame programming
#
# The following imports add the "usual" stuff every PyProcGame needs
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
from my_modes import BaseGameMode, ExBlankMode

# set up a few more things before we get started 
# the logger's configuration and format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
curr_file_path = os.path.dirname(os.path.abspath( __file__ ))

class T2Game(SkeletonGame):

    # constructor for the game object; called once
    def __init__(self):

        # THESE MUST BE DEFINED for SkeletonGame
        self.curr_file_path = curr_file_path
        self.trough_count = 3

        # optional definition for 'auto-closed' switches
        self.osc_closed_switches = ['trough2','trough3']

        # call the super class which makes the game 
        # the so-called 'machine yaml; file must meet the following requirements:
        #    name the shooter-feeding coil 'trough'
        #    name trough switches numbered left-to-right trough1, trough2, trough3
        #    name the shooter lane switch 'shooter'
        super(T2Game, self).__init__('config/T2.yaml', self.curr_file_path)

        self.base_game_mode = BaseGameMode(game=self)
        self.blank_mode = ExBlankMode(game=self)

        # this is also a reasonable place to setup lists of lamps, switches, drivers, etc.
        # that might be useful in more than one mode.
        self.leftTargetLamps = [ self.lamps.target1, 
                        self.lamps.target2, 
                        self.lamps.target3,
                        self.lamps.target4,
                        self.lamps.target5]

        # call reset (to reset the machine/modes/etc)
        self.reset()

    # called when you want to fully reset the game
    def reset(self):
        # EVERY SkeletonGame game should start its reset() with a call to super()
        super(T2Game,self).reset()
        
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
        

    def do_ball_search(self, silent=False):
        """ If you don't want to use the full ball search mode
             --e.g., you can't figure out how to tag your yaml when you port 
                this to your own game, 
            you can use this much simpler ball_search implementation if you disable
            the ball_search in your config.yaml by setting 
                ball_search: False
            under the default_modes subheading.

        If ball_search is "disabled" it means SkeletonGame will default to calling a 
        method named *do_ball_search* instead of using it's built in tagging based
        mechanism.  The following is an example of an implementation of a manual search.
        """

        # always start by calling this:
        super(T2Game, self).do_ball_search(silent) 
        # this increases self.ball_search_tries; which you may want to check to
        # escalate the 'level' of your search.

        # this strategy is fire any coil that has the same name as a switch
        # that's active right now.  The delay is used to stagger pulses so we 
        # don't pop a fuse (or worse)
        time_to_fire = 0.0
        for sw in self.switches:
            if(sw.name in self.coils and (not sw.name.startswith('trough'))):
                if(sw.is_active):
                    self.switchmonitor.delay(delay=time_to_fire, 
                        handler=self.coils[sw.name].pulse)
                    time_to_fire+=0.5 
                    
## the following just set things up such that you can run Python ExampleGame.py
## and it will create an instance of the correct game objct and start running it!

if __name__ == '__main__':
    # change T2Game to be the class defined in this file!
    run_proc_game(T2Game)
