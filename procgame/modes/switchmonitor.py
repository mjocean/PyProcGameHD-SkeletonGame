import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from ..game import Mode
from procgame.game import SwitchStop, SwitchContinue
from .. import highscore


class SwitchMonitor(Mode):
    """A mode that monitors for specific switches and helps advance state as appropriate"""
    
    def __init__(self, game):
        super(SwitchMonitor, self).__init__(game=game, priority=12)
        pass


    # Enter service mode when the enter button is pushed.
    def sw_enter_active(self, sw):
        if not self.game.service_mode in self.game.modes:
            self.game.start_service_mode()
        return SwitchStop

    def sw_startButton_active(self, sw):
        for m in self.game.modes:
            if isinstance(m, highscore.HD_EntrySequenceManager):
                return SwitchContinue

        if(self.game.attract_mode in self.game.modes):
            self.game.modes.remove(self.game.attract_mode)
            # Initialize game   
            self.game.start_game()
            # Start_game takes care of adding the first player and starting a ball in SkelGame
        else:
            # not in attract mode; tell SkelGame to add another player
            if self.game.ball == 1:
                p = self.game.add_player()
                self.game.set_status(p.name + " added!")
            else:
                # probably in ball search mode...
                self.game.logger.info("switchmonitor: Start pressed, no players, no attract??  Ball search??")
                self.game.start_game()
        return SwitchStop


    # def sw_coinDoor_active_for_1s(self,sw):
    #     # disable coils
    #     pass

    # def sw_coinDoor_inactive_for_1s(self,sw):
    #     # enable coils
    #     pass

