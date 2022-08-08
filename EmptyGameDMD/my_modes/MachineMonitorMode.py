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

    def evt_tilt(self, slam_tilt):
        self.game.sound.fadeout_music()
        self.game.sound.stop('tilt warning')

        if(slam_tilt):
            self.game.sound.play('slam_tilt')
            self.game.tilted_mode.layer = self.game.generateLayer('SLAM TILT')
        else:
            self.game.sound.play('tilt')
            self.game.tilted_mode.layer = self.game.generateLayer('TILT!!')

    def evt_tilt_warning(self, times):
        self.game.sound.stop('tilt warning')
        self.game.sound.play('tilt warning')
        self.game.displayText('Warning!!')

    def evt_initial_entry(self, category):
        self.game.displayText("Congrats on %s" % category, duration=2)
        return 2

    def evt_game_ended(self):
        pass
