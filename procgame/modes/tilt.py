# Defines the tilt mode.  Expects asset_list.yaml entries for:
# sounds: 'tilt warning' and 'tilt' 
# fonts: tilt_small and tilt_big

import logging
import procgame
from ..game import Mode
from ..game.advancedmode import AdvancedMode
from .. import dmd
import time
import os

class Tilted(AdvancedMode):
    """docstring for Tilted mode - consumes all switch events to block scoring """
    def __init__(self, game):
        super(Tilted, self).__init__(game, priority=99999, mode_type=AdvancedMode.Manual)
        always_seen_switches = self.game.switches.items_tagged('tilt_visible')
        always_seen_switches.append(self.game.switches.items_tagged('trough'))
        for sw in [x for x in self.game.switches if x.name not in self.game.trough.position_switchnames and x.name not in always_seen_switches]:
            self.add_switch_handler(name=sw.name, event_type='active', delay=None, handler=self.ignore_switch)

    def ignore_switch(self, sw):
        self.game.log("tilted: ignoring switch '%s'" % sw.name)     
        return procgame.game.SwitchStop

    def mode_stopped(self):
        self.game.game_tilted = False
        self.game.tilt_mode.tilt_reset()

class TiltMonitorMode(AdvancedMode):
    """docstring for Tilt mode -- monitors tilt switches and sets game state accordingly"""
    def __init__(self, game, priority, tilt_sw=None, slam_tilt_sw=None):
        super(TiltMonitorMode, self).__init__(game, priority, mode_type=AdvancedMode.Ball)
        self.logger = logging.getLogger('TiltMonitorMode')
        self.tilt_sw = tilt_sw
        self.slam_tilt_sw = slam_tilt_sw
        self.game.tilted_mode = None

        if tilt_sw:
            self.add_switch_handler(name=tilt_sw, event_type='active', delay=None, handler=self.tilt_handler)
        if slam_tilt_sw:
            self.add_switch_handler(name=slam_tilt_sw, event_type='active', delay=None, handler=self.slam_tilt_handler)
        self.num_tilt_warnings = 2
        self.tilt_bob_settle_time = 2.0
        self.tilted = False

    def tilt_reset(self):
        self.times_warned = 0
        self.tilted = False
        self.tilt_status = 0
        self.previous_warning_time = None

    def mode_started(self):
        self.tilt_reset()
        if self.game.tilted_mode is None:
            self.game.tilted_mode = Tilted(game=self.game)  

    def tilt_handler(self, sw):
        now = time.time()
        self.logger.info('tilt bob switch active [%d]' % now)
        if(self.previous_warning_time is not None) and ((now - self.previous_warning_time) < self.tilt_bob_settle_time):
            self.logger.info('tilt bob still swinging from previous warning')
            return
        else:
            self.previous_warning_time = now
            self.logger.info('about to issue warning %d of %d' % (self.times_warned+1, self.num_tilt_warnings+1))

        if self.times_warned == self.num_tilt_warnings:
            if not self.tilted:
                self.logger.info('TILTED')
                self.tilted = True
                self.tilt_callback()
            else:
                self.logger.info('(ALREADY/STILL) TILTED')
        else:
            self.times_warned += 1
            self.game.tilt_warning(self.times_warned)

    def slam_tilt_handler(self, sw):
        self.slam_tilt_callback()

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

            # self.game.tilted_mode = Tilted(game=self.game)  
            self.game.modes.add(self.game.tilted_mode)
            #play sound
            #play video
            self.game.tilted()
