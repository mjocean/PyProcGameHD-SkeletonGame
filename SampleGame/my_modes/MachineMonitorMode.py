import procgame.game
from procgame.game import AdvancedMode
import logging

class MachineMonitorMode(procgame.game.AdvancedMode):
    """
    The mode that is ALWAYS running; monitors events that are beyond the scope of
    an individual game and responds to them (e.g., volume up, volume down, ball search)
    """

    def __init__(self, game):
        # Mode type is System --> Persists even if a game is not in play!
        super(MachineMonitorMode, self).__init__(game=game, priority=5, mode_type=AdvancedMode.System)

    def evt_volume_down(self, vol):
        self.game.displayText("Volume Down : %d" % int(vol))        

    def evt_volume_up(self, vol):
        self.game.displayText("Volume Up : %d" % int(vol))        

    def evt_balls_missing(self):
        self.game.displayText("Balls Missing, Please Wait", opaque=True)
