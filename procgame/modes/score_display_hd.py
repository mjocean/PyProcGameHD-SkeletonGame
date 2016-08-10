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
    """ a 'notification' based GroupedLayer; it invokes a specific method 
        (`update_layer`) on the mode that owns it when next_frame() is called.
    """
    def __init__(self, width, height, mode):
        super(ScoreLayer, self).__init__(width, height, mode)
        self.mode = mode        
    def next_frame(self):
        """docstring for next_frame"""
        # Setup for the frame.
        self.mode.update_layer()
        return super(ScoreLayer, self).next_frame()


class ScoreDisplayHD(Mode):
    """:class:`ScoreDisplayHD` provides a YAML customizable generic template to display the scores of players.

    Most framework users will not need to instantiate :class:`ScoreDisplayHD` and add the instance to the mode queue,
    as this is handled in PyProcGame's :class:`BasicGame`.    A low priority is recommended otherwise the score layer
    may appear on top of the layers of other modes (blocking useful information).
    
    When the layer is asked for its :meth:`~procgame.dmd.Layer.next_frame` the DMD frame is built based on 
    the player score and ball information contained in the :class:`~procgame.game.GameController`.
    
    See the example file new_score.yaml to learn the new format.
    """
    
    score_muted = False

    def __init__(self, game, priority, left_players_justify="left"):
        super(ScoreDisplayHD, self).__init__(game, priority)

        yaml_file = "config/proposed_new_score.yaml"

        try:
            values = yaml.load(open(yaml_file, 'r'))
        except yaml.scanner.ScannerError, e:
            self.game.log('score_display: Error loading yaml file from %s; the file has a syntax error in it!\nDetails: %s' % (yaml_file, e))
            raise
        except Exception, e:
            self.game.log('score_display: Error loading yaml file from %s: %s' % (yaml_file, e))
            raise

        self.layer = ScoreLayer(self.game.dmd.width, self.game.dmd.height, self)


        # SINGLE PLAYER DISPLAY BUILDING
        self.single_player = dict()
        self.single_player_layers = list()
        # Make the SinglePlayer Credit Indicator TextLayer
        self.single_player["credit_layer"] = self.game.dmdHelper.generateTextLayerFromYaml(value_for_key(values,'ScoreLayout.CreditIndicator'))
        self.single_player_credit_template = value_for_key(values,'ScoreLayout.CreditIndicator.format', "FREE PLAY")
        
        self.single_player["credit_layer"].set_text(self.single_player_credit_template)

        self.single_player_layers.append(self.single_player["credit_layer"])

        # Make the SinglePlayer Ball Number Indicator TextLayer
        self.single_player["ball_number"] = self.game.dmdHelper.generateTextLayerFromYaml(value_for_key(values,'ScoreLayout.BallNumber'))
        self.single_player_ball_number_template = value_for_key(values,'ScoreLayout.BallNumber.format', "BALL _")
        
        if("_" in self.single_player_ball_number_template):
            self.single_player["ball_number"].set_text(self.single_player_ball_number_template.replace("_", "%d" % self.game.ball))

        self.single_player_layers.append(self.single_player["ball_number"])

        # Make the SinglePlayer Score Indicator TextLayer
        self.single_player["score"] = self.game.dmdHelper.generateTextLayerFromYaml(value_for_key(values,'ScoreLayout.SinglePlayer'))
        self.single_player_layers.append(self.single_player["score"])


        # MULTI PLAYER DISPLAY BUILDING
        self.multiplayer = dict()
        self.multiplayer_layers = list()

        # Make the Multiplayer Credit Indicator TextLayer - if omitted, we use the single player credit indicator and location
        credit_indicator_data = value_for_key(values,'ScoreLayout.MultiPlayer.CreditIndicator')
        if(credit_indicator_data is None):
            self.multiplayer["credit_layer"] = self.single_player["credit_layer"]
        else:
            self.multiplayer["credit_layer"] = self.game.dmdHelper.generateTextLayerFromYaml(credit_indicator_data)
            self.multiplayer_credit_template = value_for_key(values,'ScoreLayout.MultiPlayer.CreditIndicator.format', "FREE PLAY")
            self.multiplayer["credit_layer"].set_text(self.multiplayer_credit_template)

        self.multiplayer_layers.append(self.multiplayer["credit_layer"])

        # Make the Multiplayer Ball Number Indicator TextLayer
        ball_num_data = value_for_key(values,'ScoreLayout.MultiPlayer.BallNumber')        
        if(ball_num_data is None):
            self.multiplayer["ball_number"] = self.single_player["ball_number"]
            self.multiplayer_ball_number_template = self.single_player_ball_number_template
        else:
            self.multiplayer["ball_number"] = self.game.dmdHelper.generateTextLayerFromYaml(ball_num_data)
            self.multiplayer_ball_number_template = value_for_key(values,'ScoreLayout.MultiPlayer.BallNumber.format', "BALL _")
            if("_" in self.multiplayer_ball_number_template):
                self.multiplayer["ball_number"].set_text(self.multiplayer_ball_number_template.replace("_", "%d" % self.game.ball))
            else:
                self.multiplayer["ball_number"].set_text(self.multiplayer_ball_number_template)

        self.multiplayer_layers.append(self.multiplayer["ball_number"])

        # Make the MultiPlayer "Active" Score Indicator TextLayer
        self.multiplayer["score"] = self.game.dmdHelper.generateTextLayerFromYaml(value_for_key(values,'ScoreLayout.MultiPlayer.ActivePlayer'))
        self.multiplayer_layers.append(self.multiplayer["score"])

        for idx, playerName in enumerate(["PlayerOne", "PlayerTwo", "PlayerThree", "PlayerFour"]):
            # Make the Player# Score Indicator TextLayer
            self.multiplayer["p%d" % idx] = self.game.dmdHelper.generateTextLayerFromYaml(value_for_key(values,'ScoreLayout.MultiPlayer.%s' % playerName))
            self.multiplayer_layers.append(self.multiplayer["p%d" % idx])
            
        #     self.score_layer_player.append(dmd.HDTextLayer(pos[0], pos[1], font, justify=justify, vert_justify=vjustify, opaque=False, width=200, height=100, line_color=col, line_width=1, interior_color=col_int, fill_color=None))

        # bg = value_for_key(values, "ScoreLayout.MultiPlayer.Background")
        # if(bg is None):
        #     if("score_background" in self.game.animations):
        #         self.bgFrame = self.game.animations["score_background"]         
        #     else:
        #         self.bgFrame = dmd.SolidLayer(self.game.dmd.width, self.game.dmd.height, (0,0,0))
        # else:
        #     self.bgFrame = self.game.animations[bg]

        # bg = value_for_key(values, "ScoreLayout.ScoreInterior")
        # if(bg is None):
        #     if("score_interior" in self.game.animations):
        #         self.interior = self.game.animations["score_interior"]         
        #     else:
        #         self.interior = None
        # else:
        #     self.interior = self.game.animations[bg]

        self.layer.layers = self.single_player_layers

        self.last_num_players = 0
        self.last_player_idx = 0
        self.last_score = 0
        self.last_ball_num = -1 

        # if(self.interior is None):
        #     self.score_layer = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, 
        #                 self.font_for_score_single(0), "center", vert_justify="center",
        #                 line_color=(132,132,132), line_width=1, 
        #                 fill_color=None, 
        #                 width=self.game.dmd.width, height=self.game.dmd.height)
        # else:
        #     self.score_layer = dmd.AnimatedHDTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, 
        #                 self.font_for_score_single(0), "center", vert_justify="center",
        #                 line_color=(132,132,132), line_width=1, 
        #                 fill_color=None, fill_anim=self.interior, 
        #                 width=self.game.dmd.width, height=self.game.dmd.height)

        # for i in range(4): # pre-create score locations for four players
        #     score = 0
        #     is_active_player = False
        #     font = self.font_for_score(score=score, is_active_player=is_active_player)
        #     pos = self.pos_for_player(player_index=i, is_active_player=is_active_player)
        #     justify = self.justify_for_player(player_index=i)
        #     vjustify = "top" if i < 2 else "bottom"

        #     if(is_active_player):
        #         col = (132,132,132)
        #         col_int = (255,255,0)
        #     else:
        #         col = (82,82,0)
        #         col_int = (50,0,0)

        #     self.score_layer_player.append(dmd.HDTextLayer(pos[0], pos[1], font, justify=justify, vert_justify=vjustify, opaque=False, width=200, height=100, line_color=col, line_width=1, interior_color=col_int, fill_color=None))
        # pass


    def reset(self):
        """ call this when the machine is reset to also reset 
        the display state (from multiplayer back to 1), for example """
        self.layer.layers = self.single_player_layers
        self.last_num_players = 0
        self.last_player_idx = 0
        self.last_score = 0
        self.last_ball_num = -1


    def format_score(self, score):
        """Returns a string representation of the given score value.
        Override to customize the display of numeric score values."""
        if score == 0:
            return '00'
        else:
            return locale.format("%d", score, True)
    
    def update_layer(self):
        """Called by the layer to update the score layer for the present game state."""

        # check if we have any changes before we go on...
        # note, self.game.ball == 0 indicates no game in play; set to -1
        # to ensure the layer is updated once when first launched
        updates_needed = (self.last_ball_num != self.game.ball) or \
            (self.game.current_player() is not None) and \
            ( (self.last_num_players != len(self.game.players)) \
            or (self.last_player_idx != self.game.current_player_index) \
            or (self.last_score != self.game.current_player().score) )

        if(not updates_needed):
            return 

        if(self.score_muted==False):
            if len(self.game.players) <= 1:
                self.update_layer_1p()
            else:
                self.update_layer_4p()

        # record these changes for next time
        self.last_ball_num = self.game.ball
        self.last_num_players = len(self.game.players)
        self.last_player_idx = self.game.current_player_index
        self.last_score = 0
        
        if(self.game.current_player() is not None):
            self.last_score = self.game.current_player().score

    def update_layer_1p(self):
        if self.game.current_player() == None:
            score = 0 # Small hack to make *something* show up on startup.
        else:
            score = self.game.current_player().score
        
        self.single_player["score"].set_text(self.format_score(score))

        # note, self.game.ball == 0 indicates no game in play; set to -1
        if(self.game.ball > 0):
            if("_" in self.single_player_ball_number_template):
                self.single_player["ball_number"].set_text(self.single_player_ball_number_template.replace("_", "%d" % self.game.ball))
            else:
                self.single_player["ball_number"].set_text(self.single_player_ball_number_template)
        else:
            self.single_player["ball_number"].set_text("")

        self.single_player["credit_layer"].set_text(self.single_player_credit_template)

        self.layer.layers = self.single_player_layers
        
        # for i in range(0,4):
        #     self.score_layer_player[i].enabled = False

    def update_layer_4p(self):
        if self.game.current_player() == None:
            score = 0 # Small hack to make *something* show up on startup.
        else:
            score = self.game.current_player().score
        
        self.multiplayer["score"].set_text(self.format_score(score))

        # note, self.game.ball == 0 indicates no game in play; set to -1
        if(self.game.ball > 0):
            if("_" in self.single_player_ball_number_template):
                self.multiplayer["ball_number"].set_text(self.multiplayer_ball_number_template.replace("_", "%d" % self.game.ball))
            else:
                self.multiplayer["ball_number"].set_text(self.multiplayer_ball_number_template)
        else:
            self.multiplayer["ball_number"].set_text("")

        for i in range(len(self.game.players[:4])): # Limit to first 4 players for now.
            score = self.game.players[i].score
            self.multiplayer["p%d" % i].set_text(self.format_score(score))

        self.layer.layers = self.multiplayer_layers


    def deprecated_4p(self):
        self.layer.layers = [self.common]

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
        self.score_muted = muted
        

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