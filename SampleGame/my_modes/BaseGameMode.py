import procgame.game
from procgame.game import AdvancedMode
import logging

class BaseGameMode(procgame.game.AdvancedMode):
    """
    An example of a mode that runs whenever the GAME is in progress.
    Notice the super() function call in __init__ below specifies 
     the mode_type is set to AdvancedMode.Game.  This means:
    - it is automatically added when a game starts
        (mode_started will be called once per game)
    - it is automatically removed when a game ends
        (mode_stopped will be called once per game)

    NOTE: a second player does not cause a second game
        (confusing, no doubt).  When a new player is
        added, an evt_player_added will fire.  When
        a new ball starts, that's a good time to ensure
        our data comes from that player and sync up
        lamps via a call to update_lamps.  Read on...
    """

    def __init__(self, game):
        """ 
        The __init__ function is called automatically whenever an instance 
        of this object is created --e.g., whenever the code:
                something = new BaseGameMode() 
        is executed, this __init__ function is called
        """

        # a call to 'super' call's the parent object's __init__ method
        # in this case, it calls the procgame.game.Mode's init()
        super(BaseGameMode, self).__init__(game=game, priority=5, mode_type=AdvancedMode.Game)

        # You might be used to storing data, right in the mode, like as follows:
        # self.multiplier = 0
        # self.standupSwitchL = False
        # self.standupSwitchC = False
        # self.standupSwitchR = False
        # self.idle_balls = 0
        # self.leftTargets = [False, False, False, False, False]
        # self.kickbackEnabled = False

        # you CAN do this, and it's OK to do so, but these are properties 
        #  of the PLAYER not the mode, so if there's more than one player, 
        #  when the player number changes, these are no longer valid, but we
        #  may want to restore them when this player's turn resumes.

        #  We need to store some data per player.  Fortunately, that's
        #  what the player object lets us do!

    def evt_player_added(self, player):
        """ an event that gets fired whenever a player is added to the game (presses start);
            the player argument is the newly created player who has just been added
        """
        player.setState('multiplier', 0)
        player.setState('standupSwitchL', False) 
        player.setState('standupSwitchC', False) 
        player.setState('standupSwitchR', False) 
        player.setState('idle_balls', 0)
        player.setState('leftTargets', [False, False, False, False, False])
        player.setState('kickbackEnabled', False)
        
        
        """
        Notice that progress is stored in the player object, so check with:
            self.game.getPlayerState(key)
        which is a wrapper around:
            self.game.get_current_player().getState(key)
        """
        
    def evt_ball_starting(self):
        """ an event that gets fired when a ball is starting (for any player) """

        # since we might actually want to account for time spent in the trough, 
        # let's reset the timer when the shooter lane goes inactive.

        self.game.sound.fadeout_music()
        self.game.sound.play_music('base-music-bgm')

    def sw_shooter_inactive_for_250ms(self, sw):
        # ball saver syntax has changed.  We no longer need to supply a callback
        # method instead, evt_ball_saved() will be called if a ball is saved.
        # to enable it, use this 
        # (defaults are 1 ball, save time length is based on service mode setting)

        self.game.enable_ball_saver()
        

    def evt_ball_saved(self):
        """ this event is fired to notify us that a ball has been saved
        """
        self.game.log("BaseGameMode: BALL SAVED from Trough callback")
        self.game.sound.play('ball_saved')
        self.game.displayText('Ball Saved!')
        self.game.coils.flasherShootAgain.pulse()
        # Do NOT tell the trough to launch balls!  It's handled automatically!
        # self.game.trough.launch_balls(1)

    def mode_started(self):
        """
        the mode_started method is called whenever this mode is added
        to the mode queue; this might happen multiple times per game,
        depending on how the Game itself adds/removes it.  B/C this is 
        an advancedMode, we know when it will be added/removed.
        """
        self.game.coils.dropTarget.pulse()

    def mode_stopped(self): 
        """
        the mode_stopped method is called whenever this mode is removed
        from the mode queue; this might happen multiple times per game,
        depending on how the Game itself adds/removes it
        """
        pass

    def update_lamps(self):
        """ 
        update_lamps is a very important method -- you use it to set the lamps
        to reflect the current state of the internal mode progress variables.
        This function is called after a lampshow is played so that the state
        variables are correct after the lampshow is done.  It's also used other
        times.

        Notice that progress is stored in the player object, so check with:
            self.game.getPlayerState(key)
        which is a wrapper around:
            self.game.get_current_player().getState(key)
        """
        if(self.game.getPlayerState('kickbackEnabled')==True):
                self.game.lamps.kickback.enable()
        else:
                self.game.lamps.kickback.disable()      

        if(self.game.getPlayerState('multiplier') == 2):
            self.game.lamps.mult2x.enable()
        else:
            self.game.lamps.mult2x.disable()

         # standupMid target states
        if(self.game.getPlayerState('standupSwitchL')):
            self.game.lamps.standupMidL.enable()
        else:
            self.game.lamps.standupMidL.disable()

        if(self.game.getPlayerState('standupSwitchC')): 
            self.game.lamps.standupMidC.enable()
        else:
            self.game.lamps.standupMidC.disable()

        if(self.game.getPlayerState('standupSwitchR')): 
            self.game.lamps.standupMidR.enable()
        else:
            self.game.lamps.standupMidR.disable()

        # here's an example of using an array (list) of lamps
        # defined in the game (look at T2Game's __init__ method)
        # and an array of player states to make quick work of syncing
        # several lamps to target states:
        leftTargetStates = self.game.getPlayerState('leftTargets')

        for target,lamp in zip(leftTargetStates,self.game.leftTargetLamps):
            if(target):
                lamp.enable()
            else:
                lamp.disable()                        

    """ The following are the event handlers for events broadcast by SkeletonGame.  
        handling these events lets your mode give custom feedback to the player
        (lamps, dmd, sound, etc)
    """

    def evt_ball_ending(self, (shoot_again, last_ball)):
        """ this is the handler for the evt_ball_ending event.  It shows    
            the player information about the specific event.  You can optionally
            return a number, which is the number of seconds that you are requesting
            to delay the commitment of the event.  For example, if I wanted to show
            a message for 5 seconds before the ball actually ended (and bonus mode
            began), I would return 5.  Returning 0 (or None) would indicate no delay.
        """
        self.game.log("base game mode trough changed notification ('ball_ending - again=%s, last=%s')" % (shoot_again,last_ball))

        # stop any music as appropriate
        # self.game.sound.fadeout_music()
        self.game.sound.play('ball_drain')
        self.game.sound.play_music('sonic')
        self.game.displayText('BGM Ball Ended!')
        return 2.0

    def evt_game_ending(self):
        self.game.log("base game mode game changed notification ('game_ending')")

        self.game.displayText("GAME ENDED", 'gameover')

        # Do NOT call game_ended any more!!!!!
        # not now or later!

        return 2


    """
    this is an example of a timed switch handler
         sw_      : indicates a switch handler
         outhole  : the name of the switch
         active   : the state (could be inactive, open, closed)
         for_200ms: how long that the switch must be detected
                                in this state before this handler is called

    in this case, if the controller sees this switch closed
    for 200ms, then this function is called; waiting 200ms
    will wait for long enough for the ball to settle in the
    slot before responding
    """
    def sw_outhole_active_for_200ms(self,sw):
            self.game.coils.outhole.pulse()
        
    def sw_ballPopper_active_for_200ms(self, sw):
        # ballPopper is the vertical up kicker (VUK) in the Skull.
        # note that blindly kicking the ball up is unwise...
        
        # check via something like:
        #if(self.game.gun_mode.clearToLaunchFromSkull()):
        #    self.game.coils.ballPopper.pulse()
        self.game.coils.ballPopper.pulse()

        # either way, reset the droptarget
        self.game.lamps.dropTarget.pulse()
        return procgame.game.SwitchStop

    def sw_lockLeft_active_for_200ms(self, sw):
        self.game.coils.lockLeft.pulse()
        return procgame.game.SwitchStop

    def sw_lockTop_active_for_200ms(self, sw):
        self.game.coils.lockTop.pulse()
        return procgame.game.SwitchStop

    def sw_rampRightEnter_active(self, sw):       
        # self.game.displayText("Right Ramp Enter")    
        return procgame.game.SwitchStop

    def rampRightMade_active(self, sw):
        self.game.score(500)
        # self.game.displayText("Right Ramp Made")    
        return procgame.game.SwitchStop

    def sw_rampLeftEnter_active(self, sw):    
        # self.game.displayText("Left Ramp Enter")    
        return procgame.game.SwitchStop

    def sw_rampLeftMade_active(self, sw):
        self.game.score(500)
        # self.game.displayText("Left Ramp Made")    
        return procgame.game.SwitchStop

    def kickback_disabler(self):
        self.game.setPlayerState('kickbackEnabled',False)
        self.game.lamps.kickback.disable()

    def sw_outlaneL_active(self, sw):
        if(self.game.getPlayerState('kickbackEnabled')):
            self.game.coils.kickback.pulse()
            self.game.score(100)
            self.game.displayText("Kickback!!!")
            self.game.lamps.kickback.schedule(schedule=0xff00ff00)
            self.delay(name='disable_kickback',
                                 delay=3.0,
                                 handler=self.kickback_disabler)
        else:
            self.game.displayText("Too bad")

        return procgame.game.SwitchContinue   

    """ The following methods illustrate handling a bank of related
        targets.  Notice that the logical state of the switch is 
        stored in the player's object.  Each of these functions
        are VERY similar, and that might be annoying to you
        (and should be).  An example of a 'better way' follows these.
    """
    def sw_standupMidL_active(self, sw): 
        self.game.setPlayerState('standupSwitchL',True)
        self.game.lamps.standupMidL.enable()
        self.game.bonus("loop")
        self.checkAllSwitches()
        return procgame.game.SwitchContinue 
        
    def sw_standupMidC_active(self, sw):
        self.game.setPlayerState('standupSwitchC',True)
        self.game.lamps.standupMidC.enable()
        self.game.bonus("reverb")
        self.checkAllSwitches()
        return procgame.game.SwitchContinue
        
    def sw_standupMidR_active(self, sw):
        self.game.setPlayerState('standupSwitchR',True)
        self.game.lamps.standupMidR.enable()
        self.checkAllSwitches()
        return procgame.game.SwitchContinue

    def checkAllSwitches(self):
        """ called by each of the standupMid? handlers to 
            determine if the bank has been completed """
        if((self.game.getPlayerState('standupSwitchL') == True) and
            (self.game.getPlayerState('standupSwitchC') == True) and
            (self.game.getPlayerState('standupSwitchR') == True)): # all three are True
                self.game.displayText("All Targets Hit")
                self.game.score(1000)
                self.game.sound.play('target_bank')
                self.game.lamps.standupMidL.disable()
                self.game.lamps.standupMidC.disable()
                self.game.lamps.standupMidR.disable()
                self.game.setPlayerState('standupSwitchL', False)
                self.game.setPlayerState('standupSwitchC', False)
                self.game.setPlayerState('standupSwitchR', False)
        else:
                self.game.score(10)
                self.game.sound.play('target')

    """ An alternate way of handling a bank of related switches
        using lists (for switch states and lamps) we can have
        every switch handler call a single function.  Removes
        redundancy, makes maintanence easier, life better, etc.
    """
    def leftTargetHitHelper(self, targetNum):
        """ called by each of the target active functions
            the targetNums are actually 0..4 to coincide
            with the indexes in the arrays, not their numbers
        """
        vals = self.game.getPlayerState('leftTargets')
        vals[targetNum] = True
        if(False in vals):
            self.game.setPlayerState('leftTargets',vals)
            self.game.score(5000)
            self.game.leftTargetLamps[targetNum].enable()
            self.game.sound.play('target')
        else:
            self.game.setPlayerState('leftTargets',vals)            
            self.game.score(50000)
            self.game.sound.play('target_bank')
            self.game.displayText("LEFT TARGETS COMPLETE!", 'explosion')
            self.game.setPlayerState('leftTargets',[False]*5)

        return procgame.game.SwitchContinue    

    def sw_target1_active(self, sw):
        return self.leftTargetHitHelper(0)        

    def sw_target2_active(self, sw):
        return self.leftTargetHitHelper(1)        

    def sw_target3_active(self, sw):
        return self.leftTargetHitHelper(2)        

    def sw_target4_active(self, sw):
        return self.leftTargetHitHelper(3)        

    def sw_target5_active(self, sw):
        return self.leftTargetHitHelper(4)        

    def sw_slingL_active(self, sw):
        self.game.score(100)
        self.game.sound.play('sling')
        return procgame.game.SwitchContinue

    def sw_slingR_active(self, sw):
        self.game.score(100)
        self.game.sound.play('sling')
        return procgame.game.SwitchContinue

    def sw_dropTarget_active(self,sw):
        self.game.displayText("STAY OUT!")
        self.game.coils.dropTarget.pulse()
        self.game.lamps.dropTarget.pulse(20)
        return procgame.game.SwitchStop  

    def sw_gripTrigger_active(self, sw):
        if self.game.switches.shooter.is_active():
            self.game.coils.plunger.pulse()
            self.game.sound.play('sling')
        return procgame.game.SwitchStop
