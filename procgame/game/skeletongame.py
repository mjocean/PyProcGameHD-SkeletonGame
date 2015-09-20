# Using SkeletonGame:

# 1. Your filesystem should be set up with assets/dmd and assets/sound sub-folders
# 2. Your game class should inheriet from SkeletonGame
# 3. Your config.yaml (which may be in this directory) must define
#   information about the dmd resolution, fps, etc.  See the example.
# 4. Your game class should implement the following helpful methods:
#   doBallSearch()
# 5. Your modes should handle the following events:
#   game_started
#   ball_starting
#   ball_ended
#   game_ended
# 6. your assets.yaml should define:
#       font: default_msg
#
##########################

from . import GameController
from . import BasicGame
from . import Player
from .advancedmode import AdvancedMode
from ..dmd import HDDisplayController, font_named, sdl2_DisplayManager
from ..dmd.layers import SolidLayer, GroupedLayer
from ..modes import ScoreDisplay
from ..modes import Trough, ballsave, BallSearch
from ..modes import osc
from ..modes import DMDHelper, SwitchMonitor
from ..modes import score_display, bonusmode, service, Attract, Tilt, Tilted

from .. import sound
from .. import config
from .. import auxport
from .. import alphanumeric
from .. import lamps
from .. import assetmanager
from .. import highscore
import pinproc
import time
import datetime
import traceback
import inspect

import pygame
from pygame import mixer
import time
import pinproc
import os
import logging
import locale
import random
import re
import weakref

from game import config_named

# set up a few more things before we get started 
# the logger's configuration and format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

try:
    # Mac/Linux version
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8") # This is used to put commas in the score
except Exception, e:
    # Windows
    locale.setlocale(locale.LC_ALL, "") # This is used to put commas in the score

def cleanup():
    import sdl2.ext
    sdl2.ext.quit()
    from procgame.modes.osc import OSC_INST
    global OSC_INST
    if(OSC_INST is not None):
        OSC_INST.OSC_shutdown()

def run_proc_game(game_class):
    import sys

    game = None
    exc_info = None

    try:
        game = game_class()
        game.run_loop() 
    except Exception, e:
        # back up the exception
        exc_info = sys.exc_info()        
    finally:
        if(game is not None):
            game.end_run_loop()
        else:
            cleanup()

        if(exc_info is not None):
            raise exc_info[0], exc_info[1], exc_info[2]
            print "---------"


class GameEventHandler(object):
    def __init__(self, name, mode, handler, param=None):
        self.name = name
        self.handler = handler
        self.param = param
        self.mode = weakref.ref(mode) # use a weak reference

    def __str__(self):
        return '<name=%s handler=%s mode=%s>' % (self.name, self.handler, self.mode())


class SkeletonGame(BasicGame):
    """ SkeletonGame is intended to be the new super-class for your game class.  It provides
        more of the functionality that one expects to be in a 'generic' 'modern' pinball machine
    """
    def __init__(self, machineYamlFile, curr_file_path, machineType=None):
        try:
            random.seed()
            pygame.mixer.pre_init(44100,-16,2,512)

            self.curr_file_path = curr_file_path

            if(machineType is None):
                self.config = config_named(machineYamlFile)
                if not self.config:
                    raise ValueError, 'machineType not set in SkeletonGame() init.' % (filename)

                machineType = self.config['PRGame']['machineType']
            
            machine_type = pinproc.normalize_machine_type(machineType)
            if not machine_type:
                raise ValueError, 'machine config(filename="%s") did not set machineType, and not set in SkeletonGame() init.' % (filename)

            super(SkeletonGame, self).__init__(machine_type)

            self.dmd_width = config.value_for_key_path('dmd_dots_w', 480)
            self.dmd_height = config.value_for_key_path('dmd_dots_h', 240) 
            self.dmd_fps = config.value_for_key_path('dmd_framerate', 30) 

            # load the machine config yaml
            self.load_config(machineYamlFile)
            self.max_players = 4

            # used to hold the 'fonts' dictionary
            fonts = {}
            animations = {}

            self.lampshow_path = config.value_for_key_path('lampshow_path', curr_file_path + "/assets/lampshows/")
            self.dmd_path = config.value_for_key_path('dmd_path', curr_file_path + "/assets/dmd/")
            self.sound_path = config.value_for_key_path('sound_path', curr_file_path + "/assets/sound/")
            
            self.voice_path = self.sound_path + config.value_for_key_path('voice_dir', "voice/")
            self.sfx_path = self.sound_path + config.value_for_key_path('sfx_dir', "sfx/")
            self.music_path = self.sound_path + config.value_for_key_path('music_dir', "music/")
            
            self.hdfont_path = config.value_for_key_path('hdfont_dir', curr_file_path + "/assets/fonts/")

            self.known_modes = {}
            self.known_modes[AdvancedMode.System] = []
            self.known_modes[AdvancedMode.Ball] = []
            self.known_modes[AdvancedMode.Game] = []
            self.known_modes[AdvancedMode.Manual] = []
            
            self.event_handlers = dict()
            # the evt_ methods:
            self.known_events = ['tilt', 'ball_ending', 'ball_starting', 'game_ending', 'game_starting', 'tilt_ball_ending', 'player_added']
            for e in self.known_events:
                self.event_handlers[e] = list()

            self.game_tilted = False # indicates if any kind of tilt has occured; tilt, slam_tilt
            
            # create a sound controller (self.game.sound from within modes)
            self.sound = sound.SoundController(self)

            self.settings = []

            # create a lamp controller for lampshows
            self.lampctrl = lamps.LampController(self)

            # call load_assets function to load fonts, sounds, etc.
            self.load_assets()

            t1 = SolidLayer(self.dmd_width-16, self.dmd_height/2-16, (128,128,128,192))
            t1.set_target_position(4,4)
            t1.opaque=False
            t2 = SolidLayer(self.dmd_width-8, self.dmd_height/2-8, (255,196,0,255))
            self.animations['status_bg'] = GroupedLayer(self.dmd_width-8, self.dmd_height/2-8,[t2,t1])
            self.animations['status_bg'].set_target_position(4,self.dmd_height/4+4)

            self.dmd = HDDisplayController(self)

            self.use_stock_scoredisplay = config.value_for_key_path('default_modes.score_display', True)
            self.use_stock_bonusmode = config.value_for_key_path('default_modes.bonus_tally', True)
            self.use_stock_attractmode = config.value_for_key_path('default_modes.attract', True)
            self.use_osc_input = config.value_for_key_path('default_modes.osc_input', True)
            self.use_stock_servicemode = config.value_for_key_path('default_modes.service_mode', True)
            self.use_stock_tiltmode = config.value_for_key_path('default_modes.tilt_mode', True)
            self.use_ballsearch_mode = config.value_for_key_path('default_modes.ball_search', True)


            if(self.use_stock_scoredisplay):
                self.score_display = score_display.ScoreDisplay(self,0)
            if(self.use_stock_bonusmode):
                self.bonus_mode = bonusmode.BonusMode(game=self)

            if(self.use_stock_tiltmode):
                self.tilt_mode = Tilt(game=self, priority=98, font_big=self.fonts['tilt-font-big'], 
                    font_small=self.fonts['tilt-font-small'], tilt_sw='tilt', slam_tilt_sw='slamTilt')

            self.ball_save = ballsave.BallSave(self, lamp=self.lamps.shootAgain, delayed_start_switch='shooter')

            trough_switchnames = []
            # Note - Game specific item:
            # This range should include the number of trough switches for 
            # the specific game being run.  In range(1,x), x = last number + 1.
            self.trough_count = self.config['PRGame']['numBalls']
            for i in range(1,self.trough_count+1):
                trough_switchnames.append('trough' + str(i))

            # early_save_switchnames = ['outlaneR', 'outlaneL']

            # Note - Game specific item:
            # Here, trough6 is used for the 'eject_switchname'.  This must
            # be the switch of the next ball to be ejected.  Some games
            # number the trough switches in the opposite order; so trough1
            # might be the proper switchname to user here.
            trough_coil_name = None
            if('trough' in self.coils):
                trough_coil_name = 'trough'
            else:
                for c in self.coils:
                    if(c.name.startswith("trough")):
                        trough_coil_name = c.name
                        break
                if(trough_coil_name is None):
                    raise ValueError, "machine YAML must define a coil named 'Trough' or that starts with"
            self.trough = Trough(self,trough_switchnames, trough_switchnames[-1], trough_coil_name, [], 'shooter', self.__ball_drained_callback)
        
            # Link ball_save to trough
            self.trough.ball_save_callback = self.ball_save.launch_callback
            self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
            self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save


            self.game_start_pending = False
            bs_stopSwitches = list()
            bs_resetSwitches = list()
            self.ball_search_tries = 0

            if(self.use_ballsearch_mode):
                # add ball search options as per config.yaml
                bs_stopSwitches = [sw for sw in self.switches if (hasattr(sw,'ballsearch') and (sw.ballsearch == 'stop' or 'stop' in sw.ballsearch))]
                bs_resetSwitches = [sw for sw in self.switches if (hasattr(sw,'ballsearch') and (sw.ballsearch == 'reset' or 'reset' in sw.ballsearch))]
                
                self.ballsearch_resetSwitches = dict()
                for sw in bs_resetSwitches:
                    v = 'closed' if sw.type == 'NC' or sw.type == 'nc' else 'open'
                    self.ballsearch_resetSwitches[sw.name]=v

                self.ballsearch_stopSwitches = dict()
                for sw in bs_stopSwitches:
                    v = 'active' if sw.type == 'NC' or sw.type == 'nc' else 'closed'
                    self.ballsearch_stopSwitches[sw.name]=v

                self.ballsearch_coils = [dr.name for dr in self.coils if (hasattr(dr,'ballsearch') and dr.ballsearch == True)]

                if(len(bs_stopSwitches) == 0 and len(bs_resetSwitches) == 0):
                    self.log("Could not use Ball search mode as there were no ballsearch tags (reset/stop) on any game switches in the yaml. ")
                    self.log(" -- will default to using your games: do_ball_search() method...")
                    self.use_ballsearch_mode = False

            # create it anyway; if the switches are empty it will nerf itself.                
            self.ball_search = BallSearch(self, priority=100, \
                                 countdown_time=10, coils=self.ballsearch_coils, \
                                 reset_switches=self.ballsearch_resetSwitches, \
                                 stop_switches=self.ballsearch_stopSwitches, \
                                 special_handler_modes=[])

            if(self.use_osc_input):
                try:
                    self.osc_closed_switches
                    # or getattr(self, 'big_object')
                except AttributeError:                
                    self.osc_closed_switches = []
                self.osc = osc.OSC_Mode(game=self, priority=1, closed_switches=self.osc_closed_switches)
                self.modes.add(self.osc)

            self.dmdHelper = DMDHelper(game=self)
            self.modes.add(self.dmdHelper)

            self.switchmonitor = SwitchMonitor(game=self)
            self.modes.add(self.switchmonitor)

            self.load_settings_and_stats()

            # # call reset (to reset the machine/modes/etc)

            self.genLayerFromYAML = self.dmdHelper.genLayerFromYAML

            self.notify_list = None
            self.curr_delayed_by_mode = None

        except Exception, e:
            if(hasattr(self,'osc') and self.osc is not None):
                self.osc.OSC_shutdown()
            raise

    def end_run_loop(self):
        cleanup()
        super(SkeletonGame,self).end_run_loop()        


    def clear_status(self):
        self.dmdHelper.layer = None

    def set_status(self, msg, duration=2.0):
        """ a helper used to display a message on the DMD --low-tech version of displayText """
        self.displayText(msg, font_key='default_msg', background_layer='status_bg', flashing=8, duration=duration)

    def displayText(self, msg, background_layer=None, font_key=None, font_style=None, opaque=False, duration=2.0, flashing=False):
        """ a helper to show a specified message on the display for duration seconds.  Calling 
            showMessage twice in rapid successioin will result in replacing the first message with
            the contents of the second.

            msg may be a single string or a list of strings.  A single string will show centered
            vertically.  A list will be spaced out across the vertical space of the dmd height

            the message will appear on top of the animation/layer asset with a key matching the
            background_layer parameter.  If background_layer is a list, then the elements will be
            arranged in a grouped layer and the message will appear on top of that stack of frames

            the font_key argument refers to the key (i.e., name) of the font as defined in the asset_yaml
            If None is passed then the default message font is used: the font named 'med' in the yaml file

            the font_style argument is an instance of HDFontStyle (allowing the caller to set
                the border size, border color and fill color of the text)

            opaque indicates whether or not the contents below this message will be visible when shown

            duration is the maximum number of seconds that this message will be visible on the screen
        """
        self.dmdHelper.showMessage(msg, background_layer, font_style, opaque, duration, font_key=font_key, flashing=flashing)
    
    def generateLayer(self, msg, background_layer=None, font_style=None, font_key=None, opaque=False):
        """ a helper to generate a frame containing a specified message on top of an image/animation

            msg may be a single string or a list of strings.  A single string will show centered
            vertically.  A list will be spaced out across the vertical space of the dmd height

            the message will appear on top of the animation/layer asset with a key matching the
            background_layer parameter.  If background_layer is a list, then the elements will be
            arranged in a grouped layer and the message will appear on top of that stack of frames

            the font_key argument refers to the key (i.e., name) of the font as defined in the asset_yaml
            If None is passed then the default message font is used: the font named 'med' in the yaml file

            the font_style argument is an instance of HDFontStyle (allowing the caller to set
                the border size, border color and fill color of the text)

            opaque indicates whether or not the contents below this message will be visible when shown

            duration is the maximum number of seconds that this message will be visible on the screen
        """

        return self.dmdHelper.genMsgFrame(msg, background_layer, font_style, font_key, opaque)

    def ball_saver_enable(self, num_balls_to_save=1, time=5, now=True, allow_multiple_saves=False, callback=None):
        """ use this to turn on the ball_saver! """
        self.ball_save.callback = callback
        self.ball_save.start(num_balls_to_save, time, now, allow_multiple_saves)

    def ball_saver_disable(self):
        """ use this to end the ball saver, early! """
        self.ball_save.disable()

    def get_highscore_data(self):
        return highscore.get_highscore_data(self.highscore_categories)

    def notifyOfNewMode(self,new_mode):
        self.known_modes[new_mode.mode_type].append(new_mode)
        self.log("Skel: Known advanced modes added '%s'" % new_mode)

        # Format: evt_name(self):
        handler_func_re = re.compile('evt_(?P<name>[a-zA-Z0-9_]+)?')
        for item in dir(new_mode):
            m = handler_func_re.match(item)
            if m == None:
                continue
            handlerfn = getattr(new_mode, item)
            evt_name = m.group('name')
            self.add_evt_handler(new_mode, evt_name, handler=handlerfn)

    def notifyNextMode(self):
        if(len(self.notify_list)==0):
            self.curr_delayed_by_mode = None
            if(self.event_complete_fn is not None):
                self.log("Skel: completing event '%s' by calling '%s'" % (self.event, self.event_complete_fn))
                self.event_complete_fn()
            else:
                self.log("Skel: completing event '%s'." % (self.event))
            return

        # otherwise there are more modes awaiting notification
        next_handler = self.notify_list.pop()

        self.log("Skel: calling mode '%s' event handler for event '%s'" % (next_handler.mode(), self.event))

        if(self.args is None):
            d = next_handler.handler()
        else:
            d = next_handler.handler(self.args)

        if(d is not None and type(d) is int and d > 0):
            self.curr_delayed_by_mode = next_handler.mode()
            self.switchmonitor.delay(name='notifyNextMode',
               event_type=None, 
               delay=d, 
               handler=self.notifyNextMode)            
        elif(type(d) is tuple):
            if(d[1] == True): # flag to stop event propegation and jump to the event 
                self.notify_list = list() # zero out the list so the next 'notifyNext' call will just call the final event handler
                self.log("Skel: Mode '%s' indivates event '%s' is now complete.  Blocking further propegation" % (next_handler.mode(), self.event))
            if(d[0] > 0):
                self.curr_delayed_by_mode = next_handler.mode()
                self.switchmonitor.delay(name='notifyNextMode',
                   event_type=None, 
                   delay=d[0], 
                   handler=self.notifyNextMode)            
            else: # no delay specified
                self.notifyNextMode() # note: next call will either fire event or notify next mode accordingly
        else:
            self.notifyNextMode()


    def add_evt_handler(self, mode, evt_name, handler):
        if(evt_name not in self.event_handlers):
            raise ValueError, "Mode: %s defined a function named '%s' which is not known to the Event System" % (mode, evt_name)
        ge = GameEventHandler(evt_name, mode, handler)
        self.event_handlers[evt_name].append(ge)
        
    def notifyNextModeNow(self, caller_mode):
        if(caller_mode == self.curr_delayed_by_mode):
            # okay to notify next
            self.log("Skel: notifyNextModeNow called by %s..." % (caller_mode))
            self.switchmonitor.cancel_delayed(name='notifyNextMode')
            self.notifyNextMode()
        else:
            # not okay, wrong caller!!
            self.log("Skel: notifyNextModeNow called by %s, but currently blocked by %s!?" % (caller_mode, self.curr_delayed_by_mode))

    def notifyModes(self, event, args=None, event_complete_fn=None):
        delay = 0
        self.notify_list = list()
        self.event_complete_fn = event_complete_fn
        self.args = args
        if(event.startswith('evt_')):
            self.event = event[4:]

        self.log("Skel: preparing to notify modes of event %s." % event)

        only_active_handlers = [h for h in self.event_handlers[self.event] if h.mode() is not None and h.mode() in self.modes]
        for h in only_active_handlers:
            self.log("Skel: event handler queuing handler in mode [%s]" % (h.mode()))
            self.notify_list.append(h)

        # note this sort is in reverse priority order because we pop 
        # off the back!
        self.notify_list.sort(lambda x, y: x.mode().priority - y.mode().priority)

        self.notifyNextMode()

    # called when you want to fully reset the game
    def reset(self):
        self.log("Skel: RESET()")

        super(SkeletonGame,self).reset()
        self.ball_search_tries = 0

        self.game_start_pending = False

        # try to set the game up to be in a clean state from the outset:
        if(self.trough.num_balls() < self.num_balls_total):
            self.log("Skel: RESET: trough isn't full [%d of %d] -- requesting search" % (self.trough.num_balls(), self.num_balls_total))
            if(self.use_ballsearch_mode):
                self.ball_search.perform_search(5, silent=True)
            else:
                self.do_ball_search(silent=True)

        # handle modes that need to be alerted of the game reset!
        for m in self.known_modes[AdvancedMode.System]:
            self.modes.add(m)

        self.modes.add(self.trough)
        self.modes.add(self.ball_save)
        if(self.use_stock_scoredisplay):
            self.score_display.reset()
            self.modes.add(self.score_display)

        self.modes.add(self.ball_search)
        if(self.use_ballsearch_mode):
            self.ball_search.disable()

        # initialize the mode variables; the general form is:
        # self.varName = fileName.classModeName(game=self)
        # Note this creates the mode and causes the Mode's constructor
        # function --aka __init__()  to be run
        
        if(self.use_osc_input):
            self.modes.modes.append(self.osc)

        if(self.use_stock_servicemode):
            self.service_mode = service.ServiceMode(self, 99, self.fonts['settings-font-small'], extra_tests=[])        
        self.modes.add(self.dmdHelper)
        self.modes.add(self.switchmonitor)

        if(self.use_stock_attractmode):
            self.attract_mode = Attract(game=self)
        
    def start_attract_mode(self):
        self.attract_mode.reset()
        self.modes.add(self.attract_mode) # plays the attract mode and kicks off the game


    def enable_alphanumeric_flippers(self, enable):
        """ overrides the defaults in game.py so that the flipper-relay is checked from the
            machine.yaml.  If not present, the default value of '79' is used """
        # 79 corresponds to the circuit on the power/driver board.  It will be 79 for all WPCAlphanumeric machines.
        self.log("AN Flipper enable in SkelGame.py called")

        if('flipperEnable' in self.coils):
            if enable:
                self.coils.flipperEnable.pulse(0)
            else:
                self.coils.flipperEnable.disable()
        else:
            self.log("WARNING: No flipperEnable entry in PRCoils section of machine yaml")


    def process_config(self):
        """Called by :meth:`load_config` and :meth:`load_config_stream` to process the values in :attr:`config`."""
        super(SkeletonGame,self).process_config()
        
        # if ('arduino' in self.config['PRGame'] and self.config['PRGame']['arduino'] != False) :
        #     comport = self.config['PRGame']['arduino']
        #     self.arduino_client = ArduinoClient(comport, baud_rate=14400,timeout=1)

        sect_dict = self.config['PRSwitches']
        for name in sect_dict:
            item_dict = sect_dict[name]

            if ('ballsearch' in item_dict):
                self.switches[name].ballsearch = item_dict['ballsearch']


        sect_dict = self.config['PRCoils']
        for name in sect_dict:
            item_dict = sect_dict[name]

            if ('ballsearch' in item_dict):
                self.coils[name].ballsearch = item_dict['ballsearch']


    def load_settings_and_stats(self):
        self.load_game_data('game_default_data.yaml','game_user_data.yaml')

        self.load_settings('game_default_settings.yaml','game_user_settings.yaml')

        self.balls_per_game = self.user_settings['Machine (Standard)']['Balls Per Game']

        ## high score stuff:
        self.highscore_categories = []

        cat = highscore.HighScoreCategory()
        cat.game_data_key = 'ClassicHighScores'
        cat.titles = ['Grand Champion', 'High Score 1', 'High Score 2', 'High Score 3', 'High Score 4']
        self.highscore_categories.append(cat)

        self.last_score = 0

        for category in self.highscore_categories:
            category.load_from_game(self)

    def save_settings(self, filename=None):
        if(filename is None):
            filename = 'game_user_settings.yaml'
        super(SkeletonGame, self).save_settings(os.path.join('config/' + filename))

    def save_game_data(self, filename):
        super(SkeletonGame, self).save_game_data(os.path.join('config/' + filename))

    def load_game_data(self, file_default, file_game):
        super(SkeletonGame, self).load_game_data(os.path.join('config/' + file_default),os.path.join('config/' + file_game))

    def load_settings(self, file_default, file_game):
        super(SkeletonGame, self).load_settings(os.path.join('config/' + file_default),os.path.join('config/' + file_game))

    def load_assets(self):
        """ function to clean up code/make things easier to read; 
            this handles reading/loading of all assets (sounds, dmd images,
            dmd fonts, lightshows) from the file system
        """
        self.asset_mgr = assetmanager.AssetManager(game=self)
        self.animations = self.asset_mgr.animations
        self.fontstyles = self.asset_mgr.fontstyles
        self.fonts = self.asset_mgr.fonts
        
    def ball_starting(self):
        """ this is auto-called when the ball is actually starting 
            (so happens 3 or more times a game) """

        self.log("Skel: BALL STARTING")

        for m in self.known_modes[AdvancedMode.Ball]:
            self.modes.add(m)

        self.notifyModes('evt_ball_starting', args=None, event_complete_fn=self.actually_start_ball)

    def actually_start_ball(self):
        super(SkeletonGame, self).ball_starting()

        # eject a ball into the shooter lane
        self.trough.launch_balls(1)

        self.enable_flippers(True)
        self.enable_alphanumeric_flippers(True)

        if(self.use_ballsearch_mode):
            self.ball_search.enable()

    def __ball_drained_callback(self):
        if self.trough.num_balls_in_play == 0:
            shoot_again = False
            last_ball = False
            if self.current_player().extra_balls > 0:
                shoot_again = True
            if self.ball >= self.balls_per_game:
                last_ball = True

            self.ball_end_time = time.time()

            # Calculate ball time and save it because the start time
            # gets overwritten when the next ball starts.
            self.ball_time = self.get_ball_time()
            self.current_player().game_time += self.ball_time

            self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
            self.game_data['Audits']['Balls Played'] += 1
            # can't save here as file might still be open on game end...
            # self.save_game_data('game_user_data.yaml')

            if(self.use_ballsearch_mode):
                self.ball_search.disable()
            self.notifyModes('evt_ball_ending', args=(shoot_again,last_ball), event_complete_fn=self.end_ball)

    def your_search_is_over(self):
        """ all balls have been accounted for --if you were blocking a game start, stop that. """
        if(self.game_start_pending):
            if(self.use_ballsearch_mode):
                self.ball_search.full_stop()
            self.game_start_pending = False
            self.clear_status()
            self.game_started()

    def add_player(self):
        player = super(SkeletonGame, self).add_player()
        self.notifyModes('evt_player_added', args=(player), event_complete_fn=None)
        return player

    def slam_tilted(self):
        self.b_slam_tilted = True
        self.game_tilted = True
        self.tilted()

    def slam_tilt_complete(self):
        self.b_slam_tilted = False
        self.game_tilted = False
        self.end_ball()
        self.end_game()
        self.reset()

    def tilted(self):
        """ called by the 'Tilted' mode to indicate the machine has been tilted;
            because evt_ball_ending isn't fired, bonus mode will not be tallied
        """
        self.b_slam_tilted = False
        self.game_tilted = True
        self.notifyModes('evt_tilt', args=None, event_complete_fn=None)

    def tilted_ball_end(self):
        """ called by the 'Tilted' mode to indicate the machine has been 
            tilted and all balls are back in the trough -- in essence, this 
            signals a evt_tilt_ball_ending, which is a variant of evt_ball_ending;
            because evt_ball_ending isn't fired, bonus mode will not be tallied
        """
        self.game_tilted = False
        if(not self.b_slam_tilted):
            self.notifyModes('evt_tilt_ball_ending', args=None, event_complete_fn=self.end_ball)
        else:
            self.notifyModes('evt_tilt_ball_ending', args=None, event_complete_fn=self.slam_tilt_complete)

    def ball_ended(self):
        """ Subclassed by implementor to react to the ball being completely over
            automatically invoked by end_ball(). At this point the ball is over """
        self.log("Skel: BALL ENDED")

        # turn off the flippers
        self.enable_flippers(False)
        # self.enable_alphanumeric_flippers(False)
        if(self.use_ballsearch_mode):
            self.ball_search.disable() # possibly redundant if ball ends normally, but not redundant when slam tilted

        super(SkeletonGame, self).ball_ended()
        for m in self.known_modes[AdvancedMode.Ball]:
            self.modes.remove(m)

    def reset_search(self):
        if(self.game_start_pending):
            if(self.trough.num_balls() >= self.num_balls_total):
                self.game_start_pending = False
                self.game_started()        
            else: # insufficient balls to start
                # wait 3s before trying again
                if(self.use_ballsearch_mode):
                    self.ball_search.perform_search(3,  completion_handler=self.reset_search)
                    # self.ball_search.delay(name='ballsearch_start_delay',
                    #    event_type=None, 
                    #    delay=3, 
                    #    handler=self.game_started)            
                else:
                    self.do_ball_search(silent=False)
                    self.ball_search.delay(name='ballsearch_start_delay', event_type=None, delay=3.0, handler=self.reset_search)
        else:
            # game started on it's own.  Continue living
            pass

    def game_started(self):
        """ this happens after start_game but before start_ball/ball_starting"""
        self.log("Skel:GAME STARTED")

        # check trough and potentially do a ball search first
        if(self.game_start_pending):
            self.log("Skel: game_started: PLEASE WAIT!! -- TROUGH STATE is still BLOCKING GAME START!")
            self.set_status("Balls STILL Missing: PLEASE WAIT!!", 3.0)
            return

        if(self.trough.num_balls() < self.num_balls_total):
            self.game_start_pending=True
            self.log("Skel: game_started: trough isn't full [%d of %d] -- requesting search" % (self.trough.num_balls(), self.num_balls_total))
            if(self.use_ballsearch_mode):
                self.ball_search.perform_search(3,  completion_handler=self.reset_search)
                self.log("Skel: game_started: TROUGH STATE BLOCKING GAME START!  Will AUTOMATICALLY Retry again in 5s if not resolved")
            else:
                self.do_ball_search(silent=False)
                self.ball_search.delay(name='ballsearch_start_delay', event_type=None, delay=3.0, handler=self.reset_search)
            return
        else: # we have the right number of balls
            self.game_start_pending=False
            if(self.use_ballsearch_mode):
                self.ball_search.cancel_delayed(name='ballsearch_start_delay')

        super(SkeletonGame, self).game_started()

        for m in self.known_modes[AdvancedMode.Game]:
            self.modes.add(m)

        self.ball_search_tries = 0
        self.game_data['Audits']['Games Started'] += 1
        self.save_game_data('game_user_data.yaml')

        self.notifyModes('evt_game_starting', args=None, event_complete_fn=self.actually_start_game)

    def actually_start_game(self):
        # Add the first player
        self.add_player()
        # Start the ball.  This includes ejecting a ball from the trough.
        self.start_ball()

    def end_game(self):
        """Called by the implementor to mark notify the game that the game has ended."""
        # Handle stats for last ball here
        self.ball = 0
        self.log("Skel: 'GAME ENDED")
        self.last_score = self.current_player().score
        self.log("Skel: 'players score %s" % self.last_score)

        self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
        
        # Also handle game stats.
        for i in range(0,len(self.players)):
            game_time = self.get_game_time(i)
            self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string( self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
            self.game_data['Audits']['Games Played'] += 1

        for i in range(0,len(self.players)):
            self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
        self.save_game_data('game_user_data.yaml')

        # show any animations you want in ball_ending
        self.notifyModes('evt_game_ending', args=None, event_complete_fn=self.game_ended)

    def game_ended(self):
        super(SkeletonGame, self).game_ended()
        self.disableAllLamps()

        # remove Game-duration modes
        for m in self.known_modes[AdvancedMode.Game]:
            self.modes.remove(m)
        pass

        seq_manager = highscore.HD_EntrySequenceManager(game=self, priority=2)
        seq_manager.finished_handler = self.high_score_entry_completed
        seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
        self.modes.add(seq_manager)


    def high_score_entry_completed(self, mode):
        self.save_game_data('game_user_data.yaml')
        self.modes.remove(mode)
        self.reset()        

    def calc_time_average_string(self, prev_total, prev_x, new_value):
        prev_time_list = prev_x.split(':')
        prev_time = (int(prev_time_list[0]) * 60) + int(prev_time_list[1])
        avg_game_time = int((int(prev_total) * int(prev_time)) + int(new_value)) / (int(prev_total) + 1)
        avg_game_time_min = avg_game_time/60
        avg_game_time_sec = str(avg_game_time%60)
        if len(avg_game_time_sec) == 1:
            avg_game_time_sec = '0' + avg_game_time_sec

        return_str = str(avg_game_time_min) + ':' + avg_game_time_sec
        return return_str

    def calc_number_average(self, prev_total, prev_x, new_value):
        avg_game_time = int((prev_total * prev_x) + new_value) / (prev_total + 1)
        return int(avg_game_time)

    def dmd_event(self):
        self.dmd.update()       

    def start_service_mode(self):
        self.disableAllLamps()

        for m in self.modes:
            self.modes.remove(m)

        self.modes.add(self.service_mode)

    def service_mode_ended(self):
        self.save_settings()
        self.reset()

    def disableAllLamps(self):
        # turn off all the lamps
        for lamp in self.lamps:
            lamp.disable()

    def create_player(self, name):
        # do NOT call the super class, we replace the
        # player with our own 'advancedPlayerRecord'
        #
        # super(SkeletonGame,self).create_player(name)
        return AdvPlayer(name)

    def setPlayerState(self, key, val):
        if (self.ball != 0):
            self.p = self.current_player()
            self.p.setState(key,val)

    def adjPlayerState(self, key, delta):
        if (self.ball != 0):
            self.p = self.current_player()
            self.p.adjState(key, delta)

    def getPlayerState(self, key):
        if (self.ball != 0):
            self.p = self.current_player()
            return self.p.getState(key)

    def bonus(self, name, quantity=1):
        if (self.ball != 0):
            self.p = self.current_player()
            self.p.awardBonus(name,quantity)

    def run_loop(self, min_seconds_per_cycle=None):
        #sdl2_DisplayManager.inst().show_window(True)
        super(SkeletonGame, self).run_loop(min_seconds_per_cycle)

    def do_ball_search(self, silent=False):
        self.ball_search_tries += 1
        if(not silent):
            self.set_status("Balls Missing: PLEASE WAIT!!", 3.0)

class AdvPlayer(Player):
    """Represents a player in the game.
    The game maintains a collection of players in :attr:`GameController.players`."""
    
    # parent class tracks: score, name, extra_balls, and game_time
    # this class adds:

    state_tracking = {}
    """ player-specific mode progress variables (owned by the specific player and
        kept between balls, across players """

    bonus_records = None
    """ the information about bonuses awarded to the player on this ball (or held over) """

    def __init__(self, name):
        super(AdvPlayer, self).__init__(name)

        self.bonuses = BonusRecord()

        self.state_tracking = {}

    def awardBonus(self, name, quantity=1):
        self.bonuses.award(name,quantity)

    def getBonusList(self):
        t = self.bonuses.earned_list
        if(not self.bonuses.bonus_held):
            self.bonuses.earned_list = []
        return t

    def setState(self, key, val):
        self.state_tracking[key] = val

    def adjState(self, key, delta):
        v = self.state_tracking[key]
        v = v + delta
        self.state_tracking[key] = v

    def getState(self, key):
        return self.state_tracking[key]

        
class BonusRecord(object):
    """ represents a list of the bonuses awarded to the player, as well as 
        all possible bonuses, their display order (in ball_end animation) 
        and the bonus types (award: once, many, max); this is used by the
        ball_end animation Mode: BonusTally to show the player their bonus """

    bonus_held = False

    master_list = []
    """ a list of all possible bonuses and their orders """

    earned_list = []
    """ list of key/val pairs (dict) mapping bonus name to the current number awarded for this player
        values should be 0 (not awarded!?), 1 (once only), 2, ..., N 
        """
    def award(self, name, quantity=1):
        master = find_in_list(name, self.master_list)
        if(master is None):
            logging.getLogger('Bonus').warning("trying to award bonus ['%s'] which is not defined in master list" % name)
            master = {  'name':name, 
                        'points': 1000, 
                        'min':0, 
                        'max':float('inf'), 
                        'order':len(self.master_list)}
            self.master_list.append(master)
        prev_award = find_in_list(name, self.earned_list)
        if(prev_award is None):
            prev_award = {'name':name, 'count':0}
            self.earned_list.append(prev_award)

        if(prev_award['count'] < master['max']):
            prev_award['count'] = prev_award['count'] + 1
        else:
            logging.getLogger('Bonus').info("Bonus ['%s'] at max!" % name)

        print("==================")
        print("%s" % self.earned_list)
        print("%s" % self.master_list)
        print("==================")

    def parse_from_file(self):
        # read a yaml fie and load all the bonuses
        pass


def find_in_list(name, list):
    found_item = next((tmpItem for tmpItem in list if tmpItem["name"] == name), None)
    return found_item

## the following just set things up such that you can run Python ExampleGame.py
# and it will create an instance of the correct game objct and start running it!
def main():
    # initialize the sound playback hardware
    pygame.mixer.pre_init(44100,-16,2,512)
    # print pygame.mixer.get_init()

    game = None
    game = SkeletonGame()
    game.run_loop()
    del game

if __name__ == '__main__':
    main()