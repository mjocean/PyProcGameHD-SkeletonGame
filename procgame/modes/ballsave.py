from ..game import Mode
import logging

class BallSave(Mode):
    """Manages a game's ball save functionality by Keeping track of ball save timer and the number of balls to be saved.

    Parameters:

        'game': Parent game object.
        'lamp": Name of lamp to blink while ball save is active.
        'delayed_start_switch': Optional - Name of switch who's inactive event will cause the ball save timer to start (ie. Shooter Lane).
    """ 
    def __init__(self, game, lamp, delayed_start_switch='None'):
        super(BallSave, self).__init__(game, 3)
        self.logger = logging.getLogger('ballsave')
        self.lamp = lamp
        self.num_balls_to_save = 1
        self.mode_begin = 0
        self.allow_multiple_saves = False
        self.timer = 0
        self.tick_rate = 1
        self.timer_expired_callback = None
        self.timer_tick_callback = None

        if delayed_start_switch != 'None' and delayed_start_switch != 'none':
            self.add_switch_handler(name=delayed_start_switch, event_type='inactive', delay=1.0, handler=self.delayed_start_handler)

        """ Optional method to be called when a ball is saved.  Should be defined externally."""
        self.callback = None

        """ Optional method to be called to tell a trough to save balls.  Should be linked externally to an enable method for a trough."""
        self.trough_enable_ball_save = None

    def mode_stopped(self):
        self.disable()

    def launch_callback(self):
        """Disables the ball save logic when multiple saves are not allowed.  This is typically linked to a Trough object so the trough can notify this logic when a ball is being saved.  If 'self.callback' is externally defined, that method will be called from here."""        
        # call the callback prior to multiple saves check
        # otherwise not allowing multiple saves will stop
        # the callback even if this is the first save!
        if self.callback:
            self.callback()
        if not self.allow_multiple_saves:
            self.disable()

    def start_lamp(self):
        """Starts blinking the ball save lamp.  Oftentimes called externally to start blinking the lamp before a ball is plunged."""
        if(self.lamp is not None):
            self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)

    def update_lamps(self):
        if(self.lamp is None):
            return

        if self.timer > 5:
            self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)
        elif self.timer > 2:
            self.lamp.schedule(schedule=0x55555555, cycle_seconds=0, now=True)
        else:
            self.lamp.disable()

    def add(self, add_time, allow_multiple_saves=True):
        """Adds time to the ball save timer."""
        if self.timer >= 1:
            self.timer += add_time
            self.update_lamps()
        else:
            self.start(self.num_balls_to_save, add_time, True, allow_multiple_saves)

    def disable(self):
        """Disables the ball save logic."""
        if self.trough_enable_ball_save:
            self.trough_enable_ball_save(False)
        self.timer = 0
        if(self.lamp is not None):
            self.lamp.disable()
        # Note: this is commented out in ap's version too...  
        # self.callback = None

    def start(self, num_balls_to_save=1, time=12, now=True, allow_multiple_saves=False, tick_rate=1):
        """Activates the ball save logic.
            *time* : amount of time (in seconds) until the ball saver expires
            *now* : indicates the ballsaver should engage immediately 
                (if false, the activation of the *delayed_start_switch* will cause the saver to begin in 1s)
            *allow_multiple_saves* : if True the ballsaver will save continue to save balls until the timer expires
                if False, the ballsaver will be disabled (time depleted) after saving the first ball
            *tick_rate* : how frequently tick callbacks can occur.  A typical value is 1 (one per second),
                though a value of 0.1 could be used to generate tick events ten times per second.

            If you want tick or ball save expired events, set the .timer_tick_callback and .timer_expired_callback
            members to be the names of functions you want to call prior to starting the timer.  Example:

            class MyMode(..)
                ...
                def do_thing(self):
                    ...do something...

                def sw_shooter_inactive_for_250ms(self):
                    self.game.ball_save.timer_expired_callback = self.do_thing
                    self.game.enable_ball_saver()

        """
        self.tick_rate = tick_rate
        self.allow_multiple_saves = allow_multiple_saves
        self.num_balls_to_save = num_balls_to_save
        if time > self.timer: self.timer = time
        self.update_lamps()
        if now:
            self.cancel_delayed('ball_save_timer')
            self.delay(name='ball_save_timer', event_type=None, delay=self.tick_rate, handler=self.timer_countdown)
            if self.trough_enable_ball_save:
                self.trough_enable_ball_save(True)
        else:
            self.mode_begin = 1
            self.timer_hold = time

    def timer_countdown(self):
        self.timer -= self.tick_rate
        if (self.timer > 0):
            self.delay(name='ball_save_timer', event_type=None, delay=self.tick_rate, handler=self.timer_countdown)
            self.logger.debug("ball saver time left = %d" % self.timer)
            if(self.timer_tick_callback is not None):
                self.timer_tick_callback()
        else:
            self.logger.debug("ball saver disabled - timed out")
            self.disable()
            if(self.timer_expired_callback is not None):
                self.timer_expired_callback()

        self.update_lamps()

    def is_active(self):
        return self.timer > 0

    def get_num_balls_to_save(self):
        """Returns the number of balls that can be saved.  Typically this is linked to a Trough object so the trough can decide if a a draining ball should be saved."""
        return self.num_balls_to_save

    def saving_ball(self):
        if not self.allow_multiple_saves:
            self.timer = 1
            if(self.lamp is not None):
                self.lamp.disable()

    def delayed_start_handler(self, sw):
        if self.mode_begin:
            self.timer = self.timer_hold
            self.mode_begin = 0
            self.update_lamps()
            self.cancel_delayed('ball_save_timer')
            self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
            if self.trough_enable_ball_save:
                self.trough_enable_ball_save(True)

