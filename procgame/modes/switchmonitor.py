import logging

from ..game import Mode
from procgame.game import SwitchStop, SwitchContinue
from .. import highscore


class SwitchMonitor(Mode):
    """A mode that monitors for specific switches and helps advance state as appropriate"""
    
    def __init__(self, game):
        super(SwitchMonitor, self).__init__(game=game, priority=32767)
        pass

    # Enter service mode when the enter button is pushed.
    def sw_enter_active(self, sw):
        self.game.log("starting service mode")
        if not self.game.service_mode in self.game.modes:
            self.game.start_service_mode()
            return SwitchStop
        return SwitchContinue

    def sw_startButton_active_for_2s(self, sw):
        if(self.game.ball > 1):
            self.game.reset()

    def sw_startButton_active(self, sw):
        for m in self.game.modes:
            if isinstance(m, highscore.HD_EntrySequenceManager):
                return SwitchContinue

        if(self.game.attract_mode in self.game.modes):
            # Initialize game   
            self.game.start_game()
            # Start_game takes care of adding the first player and starting a ball in SkelGame
        else:
            # not in attract mode; tell SkelGame to add another player
            if self.game.ball == 1:
                self.game.request_additional_player()
            elif self.game.ball > 1:
                self.game.logger.info("switchmonitor: Start pressed after ball 1")
            else:
                # either in ball search mode or ball 2 maybe?  Either way ignore!
                self.game.logger.info("switchmonitor: Start pressed, no players, no attract??  Ball search??")
                #self.game.start_game()
        return SwitchStop

    def sw_down_closed(self, sw):
        if not self.game.service_mode in self.game.modes:
            self.game.volume_down()
            return SwitchStop
        return SwitchContinue

    def sw_up_closed(self, sw):
        if not self.game.service_mode in self.game.modes:
            self.game.volume_up()
            return SwitchStop
        return SwitchContinue

    # def sw_coinDoor_active_for_1s(self,sw):
    #     # disable coils
    #     pass

    # def sw_coinDoor_inactive_for_1s(self,sw):
    #     # enable coils
    #     pass

