####
## Example of a blank mode

import procgame.game
from procgame.game import AdvancedMode
import logging

class ExBlankMode(procgame.game.AdvancedMode):
    """
    Example Mode
    """
    def __init__(self, game):
        """
        stuff in __init__ gets done EXACTLY once.
        happens when the "parent" Game creates this mode

        You _need_ to call the super class' init method:
        """
        super(ExBlankMode, self).__init__(game=game, priority=2, mode_type=AdvancedMode.Game) # 2 is lower than BGM
        # notice this mode has a mode_type of 'AdvancedMode.Game'
        # this means the mode is auto-added when a game starts and
        # removed when the last player finishes their game

        # useful to set-up a custom logger so it's easier to track debugging messages for this mode
        self.logger = logging.getLogger('ExBlankMode')
        pass
    
    def mode_started(self):
        self.logger.debug("My mode started")
        # because this mode is Game type, this method won't
        # get called more than once per game so it only gets
        # called on the first ball of the first player's game
    
    def mode_stopped(self): 
        self.logger.debug("My mode ended")
        # e.g., do cleanup of the mode here. 
  
    # Example of how to handle a switch hit
    def sw_target1_active(self, sw):
        # see if the player has hit it before, if not
        if(self.game.getPlayerState("EBM_Target1")==False):
            self.game.lamps.target1.enable()
            self.game.displayText("Target hit!")
            self.game.score(200) # award 200 points
            self.game.sound.play('sling')
            # if I want to keep the player's progress about this switch
            self.game.setPlayerState("EBM_Target1", True)
        else:
            self.game.sound.play('plink')
            self.game.score(10) # award 10 pity points
            
        #  return procgame.game.SwitchContinue
        # - or -
        return procgame.game.SwitchStop

    def evt_player_added(self, new_player):
        new_player.setState("EBM_Target1", False)
  
    def evt_ball_starting(self):
        # make sure the lamp reflects the player's progress
        if(self.game.getPlayerState("EBM_Target1")==True):
            self.game.lamps.target1.enable()
        else:
            self.game.lamps.target1.disable()

    def evt_ball_ending(self, (shoot_again, last_ball)):
        # don't show the target light between players/balls
        self.game.lamps.target1.disable()
 
  