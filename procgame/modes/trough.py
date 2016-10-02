from ..game import Mode
from ..game import SwitchContinue
import logging

class Trough(Mode):
    """Manages trough by providing the following functionality:

        - Keeps track of the number of balls in play
        - Keeps track of the number of balls in the trough
        - Launches one or more balls on request and calls a launch_callback when complete, if one exists.
        - calls a launched_callback when all pending balls have actually made it to the shooter lane
        - Auto-launches balls while ball save is active (if linked to a ball save object
        - Identifies when balls drain and calls a registered drain_callback, if one exists.
        - Maintains a count of balls locked in playfield lock features (if externally incremented) and adjusts the count of number of balls in play appropriately.  This will help the drain_callback distinguish between a ball ending or simply a multiball ball draining.

        Changes beyond the standard PyProcGame Trough:
            - supports autoplunge (see :meth:launch_and_autoplunge_balls()) if 'plunge_coilname' is provided to init()
            - tries to ensure a ball has successfully escaped the shooter lane before plunging another (see 'shooter_lane_inactivity_time')
        
        Notes: launch_callback is set either by reaching into the trough object and setting it,
            OR by passing a callback as a parameter to :meth:launch_balls().  Note the only
            way to _clear_ that callback is by reaching into the trouch object and setting it to None.

            This callback is useful for setting up ball save timer starts and what-not.  Note that
            for multiball, you probably want a different ball saver set up if you support autoplunge.
            (ball save with autoplunge vs. without)

            again, launched => got to the shooter lane
                    launch => intent to send to the shooter lane

    Parameters:

        'game': Parent game object.
        'position_switchnames': List of switchnames for each ball position in the trough.
        'eject_switchname': Name of switch in the ball position the feeds the shooter lane.
        'eject_coilname': Name of coil used to put a ball into the shooter lane.
        'early_save_switchnames': List of switches that will initiate a ball save before the draining ball reaches the trough (ie. Outlanes).
        'shooter_lane_switchname': Name of the switch in the shooter lane.  This is checked before a new ball is ejected.
        'drain_callback': Optional - Name of method to be called when a ball drains (and isn't saved).  
        'shooter_lane_inactivity_time':Optiona: - The amount of time the shooter lane should turn inactive for
            to imply a ball has been successfully launched and is away (i.e., failed plunge takes less than this time)
        'plunge_coilname': Optional - Name of a coil to be fired to autoplunge a ball if launch_and_autoplunge_balls() is called.
    """
    def __init__(self, game, position_switchnames, eject_switchname, eject_coilname, \
                     early_save_switchnames, shooter_lane_switchname, drain_callback=None, 
                     shooter_lane_inactivity_time=2.0, plunge_coilname=None):
        super(Trough, self).__init__(game, 90)
        self.logger = logging.getLogger('trough')

        self.position_switchnames = position_switchnames
        self.eject_switchname = eject_switchname
        self.eject_coilname = eject_coilname
        self.shooter_lane_switchname = shooter_lane_switchname
        self.drain_callback = drain_callback
        self.inactive_shooter_time = shooter_lane_inactivity_time
        self.plunge_coilname = plunge_coilname
        self.num_to_autoplunge = 0

        # if there is an outhole, add an auto-kickover
        outhole_sw_name = None
        if('outhole' in self.game.switches):
            outhole_sw_name = 'outhole'            
        else: 
            sa = self.game.switches.items_tagged('outhole')
            if(type(sa) is list and len(sa)==0):
                self.logger.info("No outhole switch found (name or tag).  If an outhole trough setup is preset, you should adjust names/tag in the machine yaml.")
            elif(type(sa) is list):
                outhole_sw_name = sa[0].name
                self.logger.warning("Multiple switches have been tagged 'outhole' -- since that makes no sense, only the first will be used.")
            else:
                outhole_sw_name = sa.name

        # at the point that there is an outhole switch, we need to find the outhole coil
        if(outhole_sw_name is not None):
            # find an outhole coilname
            self.outhole_coil = None
            if('outhole' in self.game.coils):
                self.outhole_coil = self.game.coils['outhole']
            else:
                sa = self.coils.items_tagged('outhole')
                if(type(sa) is list and len(sa)==0):
                    self.logger.eror("Outhole switch found but no 'outhole' coil found (name or tag).  If an outhole trough setup is preset, you should adjust names/tag in the machine yaml for switch and coil!")
                elif(type(sa) is list):
                    self.outhole_coil = sa[0]
                    self.logger.warning("Multiple coils have been tagged 'outhole' -- since that makes no sense, only the first will be used.")
                else:
                    self.outhole_coil = sa

            if(self.outhole_coil is not None):
                self.add_switch_handler(name=outhole_sw_name, event_type='active',\
                    delay=0.3, handler=self.outhole_handler)

        # Install switch handlers.
        # Use a delay of 750ms which should ensure balls are settled.
        for switch in position_switchnames:
            self.add_switch_handler(name=switch, event_type='active', \
                delay=None, handler=self.position_switch_handler)

        for switch in position_switchnames:
            self.add_switch_handler(name=switch, event_type='inactive', \
                delay=None, handler=self.position_switch_handler)

        # Install early ball_save switch handlers.
        for switch in early_save_switchnames:
            self.add_switch_handler(name=switch, event_type='active', \
                delay=None, handler=self.early_save_switch_handler)

        # install "successful feed" switch handler
        self.add_switch_handler(name=shooter_lane_switchname, event_type='active', \
                delay=None, handler=self.ball_in_shooterlane)

        # install autoplunge helper -- note 300ms rest time
        if(self.plunge_coilname is not None):
            self.add_switch_handler(name=shooter_lane_switchname, event_type='active', \
                    delay=0.3, handler=self.ball_in_shooterlane_for_autoplunge)
    
        # Reset variables
        self.num_balls_in_play = 0
        self.num_balls_locked = 0
        self.num_balls_to_launch = 0    # total number to be launched (incl. stealth balls)
        self.num_balls_to_stealth_launch = 0 # saved balls (won't change num_balls_in_play)
        self.launch_in_progress = False

        self.ball_save_active = False

        """ Callback called when a ball is saved.  Used optionally only when ball save is enabled (by a call to :meth:`Trough.enable_ball_save`).  Set externally if a callback should be used. """
        self.ball_save_callback = None

        """ Method to get the number of balls to save.  Set externally when using ball save logic."""
        self.num_balls_to_save = None

        """ Method to be called when a ball is queued up for launch """
        self.launch_callback = None

        """ Method to call when a ball has been successfully launched into the shooter lane """
        self.launched_callback = None

        # self.debug()

    def outhole_handler(self, sw):
        """ a method to auto pulse the outhole coil when the outhole switch is closed for a sufficiently
            long enough time for the ball to settle.  This is hard coded to 300ms but should almost certainly
            be programmatic... -- note, this method will be registered if the machine yaml includes a
            switch named outhole (or tag:outhole) and a coil named (or tagged) outhole.  Since the trough
            logic is based on the trough switches themselves, all this switch needs to do is move a ball
            into the trough for proper handling.  Since modern machines may not have an outhole trough setup,
            it is not an error to not have an outhole switch/coil pair. 
        """
        if(self.outhole_coil is not None):
            self.outhole_coil.pulse()
        return SwitchContinue

    def debug(self):
        self.game.set_status(str(self.num_balls()) + ":" + str(self.num_balls_in_play) + "," + str(self.num_balls_locked))
        self.delay(name='debug', event_type=None, delay=1.0, \
                       handler=self.debug)

    def enable_ball_save(self, enable=True):
        """Used to enable/disable ball save logic."""
        self.ball_save_active = enable

    def early_save_switch_handler(self, sw):
        if self.ball_save_active:
            # Only do an early ball save if a ball is ready to be launched.
            # Otherwise, let the trough switches take care of it.
            if self.game.switches[self.eject_switchname].is_active():
                self.launch_balls(1, self.ball_save_callback, \
                          stealth=True)

    def mode_stopped(self):
        self.cancel_delayed('check_switches')

    # Switches will change states a lot as balls roll down the trough.
    # So don't go through all of the logic every time.  Keep resetting a
    # delay function when switches change state.  When they're all settled,
    # the delay will call the real handler (check_switches).
    def position_switch_handler(self, sw):
        self.cancel_delayed('check_switches')
        self.delay(name='check_switches', event_type=None, delay=0.50, handler=self.check_switches)

    def check_switches(self):
        if self.num_balls_in_play > 0:
            # Base future calculations on how many balls the machine 
            # thinks are currently installed.
            num_current_machine_balls = self.game.num_balls_total
            temp_num_balls = self.num_balls()
            if self.ball_save_active:

                if self.num_balls_to_save:
                    num_balls_to_save = self.num_balls_to_save()
                else:
                    num_balls_to_save = 0
                
                # Calculate how many balls shouldn't be in the 
                # trough assuming one just drained
                num_balls_out = self.num_balls_locked + \
                    (num_balls_to_save - 1)
                # Translate that to how many balls should be in 
                # the trough if one is being saved.
                balls_in_trough = num_current_machine_balls - \
                          num_balls_out

                if (temp_num_balls - \
                    self.num_balls_to_launch) >= balls_in_trough:
                    self.launch_balls(1, self.ball_save_callback, \
                              stealth=True)
                else:
                    # If there are too few balls in the trough.  
                    # Ignore this one in an attempt to correct 
                    # the tracking.
                    return 'ignore'
            else:
                # Calculate how many balls should be in the trough 
                # for various conditions.
                num_trough_balls_if_ball_ending = \
                    num_current_machine_balls - self.num_balls_locked
                num_trough_balls_if_multiball_ending = \
                    num_trough_balls_if_ball_ending - 1
                num_trough_balls_if_multiball_drain = \
                    num_trough_balls_if_ball_ending - \
                    (self.num_balls_in_play - 1)


                # The ball should end if all of the balls 
                # are in the trough.

                if temp_num_balls == num_current_machine_balls or \
                   temp_num_balls == num_trough_balls_if_ball_ending:
                    self.num_balls_in_play = 0
                    if self.drain_callback:
                        self.drain_callback()
                # Multiball is ending if all but 1 ball are in the trough.
                # Shouldn't need this, but it fixes situations where 
                # num_balls_in_play tracking
                # fails, and those situations are still occuring.
                elif temp_num_balls == \
                     num_trough_balls_if_multiball_ending:
                    self.num_balls_in_play = 1
                    if self.drain_callback:
                        self.drain_callback()
                # Otherwise, another ball from multiball is draining 
                # if the trough gets one more than it would have if 
                # all num_balls_in_play are not in the trough.
                elif temp_num_balls ==  \
                     num_trough_balls_if_multiball_drain:
                    # Fix num_balls_in_play if too low.
                    if self.num_balls_in_play < 3:
                        self.num_balls_in_play = 2
                    # otherwise subtract 1
                    else:
                        self.num_balls_in_play -= 1
                    if self.drain_callback:
                        self.drain_callback()
        else: # there are no balls in play...
            if(self.is_full() and self.game.game_start_pending):
                self.game.your_search_is_over()

    # Count the number of balls in the trough by counting active trough switches.
    def num_balls(self):
        """Returns the number of balls in the trough."""
        ball_count = 0
        for switch in self.position_switchnames:
            if self.game.switches[switch].is_active():
                ball_count += 1
        return ball_count

    def is_full(self):
        return self.num_balls() == self.game.num_balls_total

    def launch_and_autoplunge_balls(self, num):
        if(self.plunge_coilname is None):
            raise ValueError, "trough cannot autoplunge when no autoplunge coil is defined!"

        if(self.launch_in_progress and self.num_to_autoplunge < 1): 
            # this would only happen if the game was currently trying to launch a non-autoplunge 
            # ball before this autoplunge request -- could happen? (probably programmer errror).
            # Anyway, we don't want to autoplunge a ball that was already going to launched some
            # other way, so we try again in a bit to see if the other balls are done
            self.delay(name="autoplunge",event_type="None", delay=0.5, handler=self.launch_and_autoplunge_balls, param=num)
            return

        # set auto-plunge function for shooter lane
        self.num_to_autoplunge += num

        # now launch a ball into the lane
        self.launch_balls(num, stealth=True)


    # Either initiate a new launch or add another ball to the count of balls
    # being launched.  Make sure to keep a separate count for stealth launches
    # that should not increase num_balls_in_play.
    def launch_balls(self, num, callback=None, stealth=False):
        """Launches balls into play.

            'num': Number of balls to be launched.  
            If ball launches are still pending from a previous request, 
            this number will be added to the previously requested number.

            'callback': If specified, the callback will be called once
            all of the requested balls have been launched.

            'stealth': Set to true if the balls being launched should NOT
            be added to the number of balls in play.  For instance, if
            a ball is being locked on the playfield, and a new ball is 
            being launched to keep only 1 active ball in play,
            stealth should be used.
        """

        self.num_balls_to_launch += num
        if stealth:
            self.num_balls_to_stealth_launch += num
            self.num_to_autoplunge += num
        if not self.launch_in_progress:
            self.launch_in_progress = True
            
            if callback: # set the launch callback if a new one has been specified
              self.launch_callback = callback

            self.common_launch_code()

    # This is the part of the ball launch code that repeats for multiple launches.
    def common_launch_code(self):
        # Only kick out another ball if the last ball is gone from the 
        # shooter lane. 
        # NOTE: a momentary check of the shooter lane may be insufficient
        #   probably best to adjust this to make sure the ball is really "away"
        if self.game.switches[self.shooter_lane_switchname].is_active() and \
           self.game.switches[self.shooter_lane_switchname].time_since_change() < self.inactive_shooter_time:
            # Wait 1 second before trying again.
            self.logger.info("Cannot feed ball as shooter lane isn't ready [pending=%d (stealth=%d)] --retry in 1s" % (self.num_balls_to_launch, self.num_balls_to_stealth_launch))
            # stalling for shooter lane clearance            
            self.delay(name='launch', event_type=None, delay=1.0, \
                   handler=self.common_launch_code)
        elif(self.num_balls()<1):
            self.logger.info("Cannot feed ball as shooter lane as trough is empty! [pending=%d (stealth=%d)] --retry in 1s" % (self.num_balls_to_launch, self.num_balls_to_stealth_launch))
            # we don't do anything else, because the trough handler will auto-call this when a ball drains
        else:
            # feed the shooter lane (via trough coil)
            self.game.coils[self.eject_coilname].pulse() 

            self.logger.debug("Feeding ball to shooter lane. [pending=%d|stealth=%d]" % (self.num_balls_to_launch, self.num_balls_to_stealth_launch))

            # if this is the last ball of a sequence to be launched, notify
            # that the ball has been FED (not the same as placed into shooter lane)
            if self.launch_callback and self.num_balls_to_launch==1:
                self.launch_callback() # call the callback for this launch


    def num_balls_requested(self):
        """ returns the number of balls that will be eventually "live", counted as the number of live
            balls currently plus the number of pending ejects """
        return self.num_balls + self.num_balls_to_launch

    def ball_in_shooterlane(self, sw):
        if(self.launch_in_progress):
            self.num_balls_to_launch -= 1

            # Only increment num_balls_in_play if there are no more 
            # stealth launches to complete.
            if self.num_balls_to_stealth_launch > 0:
                self.num_balls_to_stealth_launch -= 1
            else:
                self.num_balls_in_play += 1

            self.logger.debug("Fed ball to shooter lane. [pending=%d|stealth=%d]" % (self.num_balls_to_launch, self.num_balls_to_stealth_launch))

            # If more balls need to be launched, delay self.inactive_shooter_time second 
            if self.num_balls_to_launch > 0:
                self.delay(name='launch', event_type=None, delay=self.inactive_shooter_time, \
                   handler=self.common_launch_code)
            else:
                self.launch_in_progress = False

                # fire this because we have successfully launched ALL the balls 
                if self.launched_callback:
                    self.launched_callback() # call the callback for this successful launch

    def ball_in_shooterlane_for_autoplunge(self, sw):
        if(self.num_to_autoplunge > 0 and self.plunge_coilname is not None):
            self.num_to_autoplunge = max(self.num_to_autoplunge-1, 0)
            self.logger.info("Autoplunging ball; num left to autoplunge is %d" % self.num_to_autoplunge)
            self.game.coils[self.plunge_coilname].pulse()
        return SwitchContinue

