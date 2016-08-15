import pinproc
import struct
import time
import os
import locale
from procgame import dmd
from procgame.game import Mode
from procgame.yaml_helper import value_for_key
import yaml

class ScoreLayer(dmd.GroupedLayer):
    def __init__(self, width, height, mode):
        super(ScoreLayer, self).__init__(width, height, mode)
        self.mode = mode
    def next_frame(self):
        """docstring for next_frame"""
        # Setup for the frame.
        self.mode.update_layer()
        return super(ScoreLayer, self).next_frame()


class ScoreDisplay(Mode):
    """:class:`ScoreDisplay` is a mode that provides a DMD layer containing a generic 1-to-4 player score display.  
    To use :class:`ScoreDisplay` simply instantiate it and add it to the mode queue.  A low priority is recommended.
    
    When the layer is asked for its :meth:`~procgame.dmd.Layer.next_frame` the DMD frame is built based on 
    the player score and ball information contained in the :class:`~procgame.game.GameController`.
    
    :class:`ScoreDisplay` uses a number of fonts, the defaults of which are included in the shared DMD resources folder.
    If a font cannot be found then the score may not display properly
    in some states.  Fonts are loaded using :func:`procgame.dmd.font_named`; see its documentation for dealing with
    fonts that cannot be found.
    
    You can substitute your own fonts (of the appropriate size) by assigning the font attributes after initializing
    :class:`ScoreDisplay`.
    """
    
    font_common = None
    """Font used for the bottom status line text: ``'BALL 1  FREE PLAY'``.  Defaults to Font07x5.dmd."""
    font_single_player_10_digits = None
    """Defaults to Fontsingle_player_12.dmd."""
    font_single_player_11_digits = None
    """Defaults to Fontsingle_player_11.dmd."""
    font_single_player_12plus = None
    """Defaults to Fontsingle_player_10.dmd."""
    font_active_player_7_digits = None
    """Defaults to Fontactive_player_10.dmd."""
    font_active_player_8_digits = None
    """Defaults to Fontactive_player_9.dmd."""
    font_active_player_9plus = None
    """Defaults to Fontactive_player_8.dmd."""
    font_inactive_player_9plus = None
    """Defaults to Fontinactive_player_5.dmd."""
    font_inactive_player_8_digits = None
    """Defaults to Fontinactive_player_6.dmd."""
    font_inactive_player_7_digits = None
    """Defaults to Fontinactive_player_7.dmd."""
    
    credit_string_callback = None
    """If non-``None``, :meth:`update_layer` will call it with no parameters to get the credit string (usually FREE PLAY or CREDITS 1 or similar).
    If this method returns the empty string no text will be shown (and any ball count will be centered).  If ``None``, FREE PLAY will be shown."""
    
    scoreMuted = False

    def __init__(self, game, priority, left_players_justify="left"):
        super(ScoreDisplay, self).__init__(game, priority)

        yaml_file = "config/score_display.yaml"

        try:
            values = yaml.load(open(yaml_file, 'r'))
        except yaml.scanner.ScannerError, e:
            self.game.log('score_display: Error loading yaml file from %s; the file has a syntax error in it!\nDetails: %s' % (yaml_file, e))
            raise
        except Exception, e:
            self.game.log('score_display: Error loading yaml file from %s: %s' % (yaml_file, e))
            values = dict()

        self.layer = ScoreLayer(self.game.dmd.width, self.game.dmd.height, self)

        # if "ScoreLayout" in values:
        v = value_for_key(values,"ScoreLayout.Fonts")
        if(v is not None):
            key_single_player_10_digits = value_for_key(v,'single_player.10_digits.Font', 'score_1p')
            key_single_player_11_digits = value_for_key(v,'single_player.11_digits.Font', 'score_1p')
            key_single_player_12plus = value_for_key(v,'single_player.12plus.Font', 'score_1p')

            key_active_7_digits = value_for_key(v,'multiplayer.active.7_digits.Font', 'score_active')
            key_active_8_digits = value_for_key(v,'multiplayer.active.8_digits.Font', 'score_active')
            key_active_9plus = value_for_key(v,'multiplayer.active.9plus.Font', 'score_active')

            key_inactive_9plus = value_for_key(v,'multiplayer.inactive.7_digits.Font', 'score_inactive')
            key_inactive_8_digits = value_for_key(v,'multiplayer.inactive.8_digits.Font', 'score_inactive')
            key_inactive_7_digits = value_for_key(v,'multiplayer.inactive.9plus.Font', 'score_inactive')

            key_bottom_info = value_for_key(v,'bottom_info.Font', 'score_sub')
        else:
            key_single_player_10_digits = 'score_1p'
            key_single_player_11_digits = 'score_1p'
            key_single_player_12plus = 'score_1p'

            key_active_7_digits = 'score_active'
            key_active_8_digits = 'score_active'
            key_active_9plus = 'score_active'

            key_inactive_9plus = 'score_inactive'
            key_inactive_8_digits = 'score_inactive'
            key_inactive_7_digits = 'score_inactive'

            key_bottom_info = 'score_sub'

        bg = value_for_key(values, "ScoreLayout.Background")
        if(bg is None):
            if("score_background" in self.game.animations):
                self.bgFrame = self.game.animations["score_background"]         
            else:
                self.bgFrame = dmd.SolidLayer(self.game.dmd.width, self.game.dmd.height, (0,0,0))
        else:
            self.bgFrame = self.game.animations[bg]

        bg = value_for_key(values, "ScoreLayout.ScoreInterior")
        if(bg is None):
            if("score_interior" in self.game.animations):
                self.interior = self.game.animations["score_interior"]         
            else:
                self.interior = None
        else:
            self.interior = self.game.animations[bg]

        self.font_single_player_10_digits = self.game.fonts[key_single_player_10_digits]
        self.font_single_player_11_digits = self.game.fonts[key_single_player_11_digits]
        self.font_single_player_12plus = self.game.fonts[key_single_player_12plus]

        self.font_common = self.game.fonts[key_bottom_info]

        self.font_active_player_7_digits = self.game.fonts[key_active_7_digits]
        self.font_active_player_8_digits = self.game.fonts[key_active_8_digits]
        self.font_active_player_9plus = self.game.fonts[key_active_9plus]

        self.font_inactive_player_9plus = self.game.fonts[key_inactive_7_digits]
        self.font_inactive_player_8_digits = self.game.fonts[key_inactive_8_digits]
        self.font_inactive_player_7_digits = self.game.fonts[key_inactive_9plus]

        self.set_left_players_justify(left_players_justify)

        # self.bgFire = self.game.animations['flames']
        # self.bgFire.opaque=False
        self.bgFrame.opaque = True

        self.layer.layers = [self.bgFrame]

        if(self.interior is None):
            self.score_layer = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, 
                        self.font_for_score_single(0), "center", vert_justify="center",
                        line_color=(132,132,132), line_width=1, 
                        fill_color=None, 
                        width=self.game.dmd.width, height=self.game.dmd.height)
        else:
            self.score_layer = dmd.AnimatedHDTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, 
                        self.font_for_score_single(0), "center", vert_justify="center",
                        line_color=(132,132,132), line_width=1, 
                        fill_color=None, fill_anim=self.interior, 
                        width=self.game.dmd.width, height=self.game.dmd.height)

        self.layer.layers += [self.score_layer]

        # Common: Add the "BALL X ... FREE PLAY" footer.
        fs = value_for_key(values,"ScoreLayout.Fonts.bottom_info.FontStyle", None)
        if(fs is not None):
            fs = self.game.fontstyles[fs]

        self.common = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height, self.font_common, "center", vert_justify="bottom", width=self.game.dmd.width)
        self.common.style = fs
        # self.common.composite_op = "magentasrc"

        self.layer.layers += [self.common]

        self.score_layer_player = []

        for i in range(4): # pre-create score locations for four players
            score = 0
            is_active_player = False
            font = self.font_for_score(score=score, is_active_player=is_active_player)
            pos = self.pos_for_player(player_index=i, is_active_player=is_active_player)
            justify = self.justify_for_player(player_index=i)
            vjustify = "top" if i < 2 else "bottom"

            if(is_active_player):
                col = (132,132,132)
                col_int = (255,255,0)
            else:
                col = (82,82,0)
                col_int = (50,0,0)

            self.score_layer_player.append(dmd.HDTextLayer(pos[0], pos[1], font, justify=justify, vert_justify=vjustify, opaque=False, width=200, height=100, line_color=col, line_width=1, interior_color=col_int, fill_color=None))
        pass


    def reset(self):
        """ call this when the machine is reset to also reset 
        the display state (from multiplayer back to 1), for example """
        self.layer.layers = [self.bgFrame]
        self.layer.layers += [self.score_layer]
        self.layer.layers += [self.common]


    def format_score(self, score):
        """Returns a string representation of the given score value.
        Override to customize the display of numeric score values."""
        if score == 0:
            return '00'
        else:
            return locale.format("%d", score, True)
    
    def font_for_score_single(self, score):
        """Returns the font to be used for displaying the given numeric score value in a single-player game."""
        if score <   1e10:
            print "10"
            return self.font_single_player_10_digits
        elif score < 1e11:
            print "11"
            return self.font_single_player_11_digits
        else:
            print "12"
            return self.font_single_player_12plus
        
    def font_for_score(self, score, is_active_player):
        """Returns the font to be used for displaying the given numeric score value in a 2, 3, or 4-player game."""
        if is_active_player:
            if score < 1e7:
                return self.font_active_player_7_digits
            if score < 1e8:
                return self.font_active_player_8_digits
            else:
                return self.font_active_player_9plus
        else:
            if score < 1e7:
                return self.font_inactive_player_7_digits
            if score < 1e8:
                return self.font_inactive_player_8_digits
            else:
                return self.font_inactive_player_9plus

    def set_left_players_justify(self, left_players_justify):
        """Call to set the justification of the left-hand players' scores in a multiplayer game.
        Valid values for ``left_players_justify`` are ``'left'`` and ``'right'``."""
        if left_players_justify == "left":
            # score positions: True are positions for the respective player number when active
            # score positions: False are positions for the respective player number when INactive
            self.score_posns = { True: [(0, 0), (self.game.dmd.width, 0), (0, self.game.dmd.height), (self.game.dmd.width, self.game.dmd.height)], False: [(0, 0), (self.game.dmd.width, 0), (0, self.game.dmd.height), (self.game.dmd.width, self.game.dmd.height)] }
        elif left_players_justify == "right":
            self.score_posns = { True: [(self.game.dmd.width, 0), (self.game.dmd.width, 0), (self.game.dmd.width/2, self.game.dmd.height), (self.game.dmd.width, self.game.dmd.height)], False: [(self.game.dmd.width, 0), (self.game.dmd.width, 0), (self.game.dmd.width, self.game.dmd.height), (self.game.dmd.width,self.game.dmd.height)] }
        else:
            raise ValueError, "Justify must be right or left."
        self.score_justs = [left_players_justify, 'right', left_players_justify, 'right']

        #     self.score_posns = { True: [(0, -1), (450, -1), (0, 85), (450, 85)], False: [(0, -1), (450, -1), (0, 145), (450, 145)] }
        # elif left_players_justify == "right":
        #     self.score_posns = { True: [(75, 0), (450, 0), (75, 85), (450, 85)], False: [(52, -1), (450, -1), (52, 145), (450, 145)] }



    def pos_for_player(self, player_index, is_active_player):
        return self.score_posns[is_active_player][player_index]
    
    def justify_for_player(self, player_index):
        return self.score_justs[player_index]
    
    def update_layer(self):
        """Called by the layer to update the score layer for the present game state."""
        # self.layer.layers = [self.bgframe]
        # self.layer.layers = [self.bgFire]

        credit_str = 'FREE PLAY'
        if self.credit_string_callback:
            credit_str = self.credit_string_callback()
        if self.game.ball == 0:
            self.common.set_text(credit_str)
        elif len(credit_str) > 0:
            self.common.set_text("BALL %d      %s" % (self.game.ball, credit_str))
        else:
            self.common.set_text("BALL %d" % (self.game.ball))

        if(self.scoreMuted==False):
            if len(self.game.players) <= 1:
                self.update_layer_1p()
            else:
                self.update_layer_4p()


    def update_layer_1p(self):
        if self.game.current_player() == None:
            score = 0 # Small hack to make *something* show up on startup.
        else:
            score = self.game.current_player().score
        
        # self.score_layer.font = self.font_for_score_single(score)
        # print("%s,%d" % (self.score_layer.font.name, self.score_layer.font.font_size))

        self.score_layer.set_text(self.format_score(score))#, blink_frames=3)
        # layer.composite_op = "magentasrc"
    
        # self.layer.layers += [layer]
        

        for i in range(0,4):
            self.score_layer_player[i].enabled = False

    def update_layer_4p(self):
        self.layer.layers = [self.bgFrame]
        self.layer.layers += [self.common]

        for i in range(len(self.game.players[:4])): # Limit to first 4 players for now.
            score = self.game.players[i].score
            is_active_player = (self.game.ball > 0) and (i == self.game.current_player_index)
            font = self.font_for_score(score=score, is_active_player=is_active_player)
            pos = self.pos_for_player(player_index=i, is_active_player=is_active_player)
            justify = self.justify_for_player(player_index=i)
            vjustify = "top" if i < 2 else "bottom"
            
            if(is_active_player):
                col = (132,132,132)
                col_int = (255,255,0)
            else:
                col = (82,82,0)
                col_int = (50,0,0)

            force_update = False
            if(self.score_layer_player[i].font != font):
                self.score_layer_player[i].font = font
                force_update = True

            if(self.score_layer_player[i].x != pos[0]):
                self.score_layer_player[i].x = pos[0]
                force_update = True

            if(self.score_layer_player[i].y != pos[1]):
                self.score_layer_player[i].y = pos[1]
                force_update = True                

            self.score_layer_player[i].justify = justify
            self.score_layer_player[i].Vjustify = vjustify
            self.score_layer_player[i].set_text(self.format_score(score), style=
                dmd.HDFontStyle(interior_color=col_int, line_width=1, line_color=col, fill_color=None),
                force_update = force_update)

            self.score_layer_player[i].enabled = True

            self.layer.layers += [self.score_layer_player[i]]

        # turn off unused display elements
        for i in range(i+1,4):
            self.score_layer_player[i].enabled = False
        
        pass

    def mute_score(self, muted):
        self.scoreMuted = muted
        

    def mode_started(self):
        pass

    def mode_stopped(self):
        pass


class FreePoints(Mode):
    def __init__(self, game, priority):
        super(FreePoints, self).__init__(game, priority)

    def give_points(self):
        for i in xrange(0,len(self.game.players)):
            self.game.players[i].score += 20
            self.game.players[i].score *= 2
            
        self.delay(name='points',
         event_type=None,
         delay=1.0,
         handler=self.give_points)

    def mode_started(self):
        self.give_points()

    def sw_startButton_active(self, sw):
        p = self.game.add_player()
        self.game.set_status(p.name + " added!")


def main():
    import pinproc

    # add the directory one level up to the path and switch to it
    import os
    import sys
    sys.path.insert(1, os.path.join(sys.path[0], '..'))
    os.chdir(os.path.join(sys.path[0], '..'))

    # import your game class and instantiate it
    import ExampleGame
    game = ExampleGame.TEST_BuffyGame()

    # (BUT you don't want to?  Fine, so something like this...)
    # game = procgame.game.BasicGame(pinproc.MachineTypeWPC)
    # game.load_config('../sof.yaml') # in VP this is found in c:\P-ROC\shared\config\

    handler = None
    game.add_player() # can't test high-score entry without a player!

    game.ball=2
    mode = FreePoints(game=game,priority=99)
    game.modes.add(mode)
    # game.sound.play_music('attract-video')
    # mode.layer = dmd.MovieLayer( opaque=True, hold=False, repeat=False, frame_time=2, movie=dmd.Movie().load(game.dmd_path+'radioactive.mp4'))

    game.run_loop()

if __name__ == '__main__':
    main()      