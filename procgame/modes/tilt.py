# Defines the tilt mode.  Expects asset_list.yaml entries for:
# sounds: 'tilt warning' and 'tilt' 
# fonts: tilt_small and tilt_big

import procgame
from ..game import Mode
from ..game.advancedmode import AdvancedMode
from .. import dmd
import os

class Tilted(AdvancedMode):
    """docstring for Tilted mode - consumes all switch events to block scoring """
    def __init__(self, game):
        super(Tilted, self).__init__(game, priority=99999, mode_type=AdvancedMode.Manual)
        for sw in [x for x in self.game.switches if x.name not in self.game.trough.position_switchnames]:
            self.add_switch_handler(name=sw.name, event_type='active', delay=None, handler=self.ignore_switch)

        for sw_name in self.game.trough.position_switchnames:   
            self.add_switch_handler(name=sw_name, event_type='active', delay=0.5, handler=self.trough_switch)

    def ignore_switch(self, sw):
        self.game.log("tilted: ignoring switch '%s'" % sw.name)     
        return procgame.game.SwitchStop

    def trough_switch(self, sw):
        num_balls = 0
        for sw in self.game.trough.position_switchnames:    
            if(self.game.switches[sw].is_active()):
                num_balls += 1
        if(num_balls == self.game.balls_per_game):
            self.game.log("tilted: all balls back")     
            self.game.tilted_ball_end()
            self.game.modes.remove(self)
        else:
            self.game.log("tilted: %d balls back" % num_balls)                 
        return procgame.game.SwitchStop

class Tilt(AdvancedMode):
    """docstring for Tilt mode -- monitors tilt switches and sets game state accordingly"""
    def __init__(self, game, priority, font_big, font_small, tilt_sw=None, slam_tilt_sw=None):
        super(Tilt, self).__init__(game, priority, mode_type=AdvancedMode.Ball)
        self.font_big = font_big
        self.font_small = font_small
        self.text_layer = dmd.TextLayer(self.game.dmd_width/2, self.game.dmd_height/2, font_big, "center")
        self.tilt_sw = tilt_sw
        self.slam_tilt_sw = slam_tilt_sw

        if tilt_sw:
            self.add_switch_handler(name=tilt_sw, event_type='inactive', delay=None, handler=self.tilt_handler)
        if slam_tilt_sw:
            self.add_switch_handler(name=slam_tilt_sw, event_type='inactive', delay=None, handler=self.slam_tilt_handler)
        self.num_tilt_warnings = 2
        self.tilted = False

    def mode_started(self):
        self.times_warned = 0
        self.layer = None
        self.tilted = False
        self.tilt_status = 0

    def tilt_handler(self, sw):
        if self.times_warned == self.num_tilt_warnings:
            if not self.tilted:
                self.game.sound.stop('tilt warning')
                self.tilted = True
                self.game.sound.play('tilt')
                self.text_layer.set_text('TILT')
                self.tilt_callback()
        else:
            self.game.sound.stop('tilt warning')
            self.times_warned += 1
            self.game.sound.play('tilt warning')
            self.text_layer.set_text('Warning',3)
        self.layer = dmd.GroupedLayer(self.game.dmd_width, self.game.dmd_height, [self.text_layer])

    def slam_tilt_handler(self, sw):
        self.game.sound.play('slam_tilt')
        self.text_layer.set_text('SLAM TILT')
        self.slam_tilt_callback()
        self.layer = dmd.GroupedLayer(self.game.dmd_width, self.game.dmd_height, [self.text_layer])

    def tilt_delay(self, fn, secs_since_bob_tilt=2.0):
        """ calls the specified `fn` if it has been at least `secs_since_bob_tilt`
            (make sure the tilt isn't still swaying)
        """

        if self.tilt_sw.time_since_change() < secs_since_bob_tilt:
            self.delay(name='tilt_bob_settle', event_type=None, delay=secs_since_bob_tilt, handler=self.tilt_delay, param=fn)
        else:
            return fn()

    # Reset game on slam tilt
    def slam_tilt_callback(self):
        self.game.sound.fadeout_music()

        # Disable flippers so the ball will drain.
        self.game.enable_flippers(enable=False)

        # Make sure ball won't be saved when it drains.
        self.game.ball_save.disable()

        # Ensure all lamps are off.
        for lamp in self.game.lamps:
            lamp.disable()

        # Kick balls out of places it could be stuck.
        # TODO: ball search!!
        self.tilted = True
        self.tilt_status = 1

        self.game.tilted_mode = Tilted(game=self.game)  
        self.game.modes.add(self.game.tilted_mode)
        #play sound
        #play video
        self.game.slam_tilted()

        return True

    def tilt_callback(self):
        # Process tilt.
        # First check to make sure tilt hasn't already been processed once.
        # No need to do this stuff again if for some reason tilt already occurred.
        if self.tilt_status == 0:

            self.game.sound.fadeout_music()
            
            # Disable flippers so the ball will drain.
            self.game.enable_flippers(enable=False)

            # Make sure ball won't be saved when it drains.
            self.game.ball_save.disable()
            #self.game.modes.remove(self.ball_save)

            # Make sure the ball search won't run while ball is draining.
            #self.game.ball_search.disable()

            # Ensure all lamps are off.
            for lamp in self.game.lamps:
                lamp.disable()

            # Kick balls out of places it could be stuck.
            # TODO: ball search!!
            self.tilted = True
            self.tilt_status = 1

            self.game.tilted_mode = Tilted(game=self.game)  
            self.game.modes.add(self.game.tilted_mode)
            #play sound
            #play video
            self.game.tilted()
