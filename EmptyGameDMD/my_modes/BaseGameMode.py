import procgame.game
from procgame.game import AdvancedMode
import logging

class BaseGameMode(procgame.game.AdvancedMode):
    """
    The mode that is running during "normal" gameplay
    """

    def __init__(self, game):
        """
        The __init__ function is called automatically whenever an instance is created
        """

        # a call to 'super' is required
        # notice we set the mode type and the priority
        super(BaseGameMode, self).__init__(game=game, priority=5, mode_type=AdvancedMode.Game)

    def evt_player_added(self, player):
        """ an event that gets fired whenever a player is added to the game (presses start);
            the player argument is the newly created player who has just been added tot he game
            (but may not yet be playing)
        """
        self.game.displayText(player.name + " added!")
        self.game.sound.play("click")
        player.setState('multiplier', 0)

    def evt_ball_starting(self):
        """ an event that gets fired when a ball is starting (for any player) """

        # since we might actually want to account for time spent in the trough,
        # let's reset the timer when the shooter lane goes inactive.
        self.game.sound.fadeout_music()
        self.game.sound.play_music('base-music-bgm')

    def evt_ball_saved(self):
        """ this event is fired to notify us that a ball has been saved
        """
        self.game.log("BaseGameMode: BALL SAVED from Trough callback")
        self.game.sound.play('ball_saved')
        self.game.displayText('Ball Saved!')
        # Do NOT tell the trough to launch balls!  It's handled automatically!
        # self.game.trough.launch_balls(1)

    def mode_started(self):
        """
        the mode_started method is called whenever this mode is added
        to the mode queue; this might happen multiple times per game,
        depending on how the Game itself adds/removes it.  B/C this is
        an advancedMode, we know when it will be added/removed.
        """
        pass

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
        """
        #match lamps to player states...
        pass

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


