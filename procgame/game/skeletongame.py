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
from ..modes import ScoreDisplay, ScoreDisplayHD
from ..modes import Trough, ballsave, BallSearch
from ..modes import osc
from ..modes import DMDHelper, SwitchMonitor
from ..modes import bonusmode, service, Attract, TiltMonitorMode, Tilted
#from ..modes import serviceHD

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
import yaml
from procgame.yaml_helper import value_for_key

# from weakref import WeakValueDictionary

from game import config_named
from procgame.modes.rgbshow import RgbShowPlayer

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
        game.run_loop(.0001)
    except Exception, e:
        # back up the exception
        exc_info = sys.exc_info()
    finally:
        # if the game crashes, end_run_loop might not be called
        if(game is not None):
            game.end_run_loop()
        else:
            cleanup()

        if(exc_info is not None):
            raise exc_info[0], exc_info[1], exc_info[2]
            print "---------"


class SkeletonGame(BasicGame):
    """ SkeletonGame is intended to be the new super-class for your game class.  It provides
        more of the functionality that one expects to be in a 'generic' 'modern' pinball machine
    """
    def __init__(self, machineYamlFile, curr_file_path, machineType=None):
        try:
            self.cleaned_up = False
            random.seed()
            pygame.mixer.pre_init(44100,-16,2,512)

            self.curr_file_path = curr_file_path

            if(machineType is None):
                self.config = config_named(machineYamlFile)
                if not self.config:
                    raise ValueError, 'Yaml file "%s" could not be loaded and machineType not passed as arg to SkeletonGame() init.' % (machineYamlFile)

                machineType = self.config['PRGame']['machineType']

            machine_type = pinproc.normalize_machine_type(machineType)
            if not machine_type:
                raise ValueError, 'machine config(filename="%s") did not set machineType, and not set in SkeletonGame() init.' % (machineYamlFile)

            self.dmd_width = config.value_for_key_path('dmd_dots_w', 480)
            self.dmd_height = config.value_for_key_path('dmd_dots_h', 240)
            self.dmd_fps = config.value_for_key_path('dmd_framerate', 30)

            try:
                super(SkeletonGame, self).__init__(machine_type)
            except IOError, e:
                self.log("Error connecting to P-ROC -- running virtual mode")
                sdl2_DisplayManager.inst().clear((0,0,0,0))
                if self.dmd_width > 128:
                    s = "Hardware connection failed."
                    tx = sdl2_DisplayManager.inst().font_render_text(s, font_alias=None, size=None, width=int(0.9*self.dmd_width), color=(255,128,0,0), bg_color=None)
                    sdl2_DisplayManager.inst().screen_blit(tx, x=int(0.1 * self.dmd_width), y=int(0.33*self.dmd_height), expand_to_fill=False)
                    s = "Ensure boards have power and USB cable is secure."
                    tx2 = sdl2_DisplayManager.inst().font_render_text(s, font_alias=None, size=None, width=int(0.9*self.dmd_width), color=(255,128,0,0), bg_color=None)
                    sdl2_DisplayManager.inst().screen_blit(tx2, x=int(0.1 * self.dmd_width), y=int(0.33*self.dmd_height), expand_to_fill=False)
                    sdl2_DisplayManager.inst().flip()
                    from time import sleep
                    sleep(15)
                exit(-1)

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

            # known_modes are all AdvancedModes that have been created; they are stored by type
            # what is stored is a weakref to each, so we don't mess up reference counts/garbage collection
            self.known_modes = {}
            self.known_modes[AdvancedMode.System] = []
            self.known_modes[AdvancedMode.Ball] = []
            self.known_modes[AdvancedMode.Game] = []
            self.known_modes[AdvancedMode.Manual] = []

            # event hanlders are lists of AdvancedModes (again, weakref) that care about these specific
            # events (i.e., these classes define functions to handle these specific events)
            self.event_handlers = {}
            # the evt_ methods:
            self.known_events = [ 'evt_tilt', 'evt_shoot_again', 'evt_single_ball_play', \
                                    'evt_ball_ending', 'evt_ball_starting', 'evt_ball_saved', \
                                    'evt_game_ending', 'evt_game_starting', 'evt_tilt_ball_ending', \
                                    'evt_player_added', 'evt_balls_missing', 'evt_balls_found',
                                    'evt_volume_up', 'evt_volume_down', 'evt_tilt_warning', \
                                    'evt_game_ended', 'evt_initial_entry', 'evt_mb_drain']

            for e in self.known_events:
                self.event_handlers[e] = []

            self.sg_event_queue = [] # if a known event fires while still processing another, this will
            # hold the queue of out-standing SG events

            self.event = None # the current SG event being processed

            self.game_tilted = False # indicates if any kind of tilt has occured; tilt, slam_tilt

            # create a sound controller (self.game.sound from within modes)
            self.sound = sound.SoundController(self)
            self.modes.add(self.sound)

            self.settings = []

            # create a lamp controller for lampshows
            self.lampctrl = lamps.LampController(self)

            ### the rgb show player is a player for rgb lamps
            self.rgbshow_player = RgbShowPlayer(game=self, priority=50)
            self.modes.add(self.rgbshow_player)
            self.rgbshow_player.reset()

            # call load_assets function to load fonts, sounds, etc.
            self.load_assets()

            self.dmd = HDDisplayController(self)

            self.use_stock_scoredisplay = config.value_for_key_path('default_modes.score_display', True)
            self.use_stock_bonusmode = config.value_for_key_path('default_modes.bonus_tally', True)
            self.use_stock_attractmode = config.value_for_key_path('default_modes.attract', True)
            self.use_osc_input = config.value_for_key_path('default_modes.osc_input', True)
            self.use_stock_servicemode = config.value_for_key_path('default_modes.service_mode', True)
            #self.use_HD_servicemode = config.value_for_key_path('default_modes.service_mode_HD', True)
            self.use_stock_tiltmode = config.value_for_key_path('default_modes.tilt_mode', True)
            self.use_ballsearch_mode = config.value_for_key_path('default_modes.ball_search', True)
            self.use_multiline_score_entry = config.value_for_key_path('default_modes.multiline_highscore_entry', False)
            self.ballsearch_time = config.value_for_key_path('default_modes.ball_search_delay', 30)

            self.dmdHelper = DMDHelper(game=self)
            self.modes.add(self.dmdHelper)

            if(self.use_stock_scoredisplay is True):
                self.score_display = ScoreDisplay(self,0)
            elif(self.use_stock_scoredisplay=='HD'):
                self.score_display = ScoreDisplayHD(self, 0)

            if(self.use_stock_bonusmode):
                self.bonus_mode = bonusmode.BonusMode(game=self)

            self.load_settings_and_stats()

            #if(self.use_HD_servicemode):
            #    self.service_mode = serviceHD.ServiceModeHD(self, 99, self.fonts['settings-font-small'], self.fonts['settings-font-small'], extra_tests=[])
            #elif(self.use_stock_servicemode):
            self.service_mode = service.ServiceMode(self, 99, self.fonts['settings-font-small'], extra_tests=[])

            if(self.use_stock_tiltmode):
                # find a tilt switch
                tilt_sw_name = self.find_item_name('tilt',self.switches)
                slamtilt_sw_name = self.find_item_name('slamTilt',self.switches)
                self.tilt_mode = TiltMonitorMode(game=self, priority=99998,
                    tilt_sw=tilt_sw_name, slam_tilt_sw=slamtilt_sw_name)

            shoot_again = self.lamps.item_named_or_tagged('shoot_again')
            shooter_lane_sw_name = self.find_item_name('shooter',self.switches)
            self.ball_save = ballsave.BallSave(self, lamp=shoot_again, delayed_start_switch=shooter_lane_sw_name)

            # Note - Game specific item:
            trough_switchnames = self.switches.items_tagged('trough')
            # This range should include the number of trough switches for
            # the specific game being run.  In range(1,x), x = last number + 1.

            if(len(trough_switchnames)==0):
                logging.getLogger('Trough').warning("No switches have been tagged 'trough'.  Switches with names that start Trough will be used.")
                trough_switchnames = [t.name for t in self.switches if t.name.startswith("trough") ]
            else:
                trough_switchnames = [t.name for t in trough_switchnames]

            if(len(trough_switchnames)==0):
                logging.getLogger('Trough').error("No switches have been tagged 'trough' and no switch names start with 'trough'")
                raise ValueError("Machine YAML must contain switches either tagged 'trough' or with names that start with 'trough'")

            early_save_switchnames = [save_sw.name for save_sw in self.switches.items_tagged('early_save')]

            # Added auto-config for auto plunger
            plunge_coilname = self.find_item_name('autoPlunger', self.coils)

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

            if(hasattr(self,'autoplunge_settle_time')):
                autoplunge_settle_time = self.autoplunge_settle_time
            else:
                autoplunge_settle_time = 0.3

            if(hasattr(self,'trough_settle_time')):
                trough_settle_time = self.trough_settle_time
            else:
                trough_settle_time = 0.5

            if(shooter_lane_sw_name is None):
                raise ValueError, "machine YAML must define a switch named 'shooter' or tagged 'shooter'"
            self.trough = Trough(self,trough_switchnames, trough_switchnames[-1], trough_coil_name, \
                early_save_switchnames, shooter_lane_sw_name, drain_callback=None, plunge_coilname=plunge_coilname, \
                autoplunge_settle_time=autoplunge_settle_time, trough_settle_time=trough_settle_time)

            # Only once the ball is fed to the shooter lane is it possible for the ball
            # drain to actually end a ball
            self.trough.drain_callback = None
            self.trough.launch_callback = None
            self.trough.launched_callback = self.__install_drain_logic

            # Link ball_save to trough
            self.trough.ball_save_callback = self.ball_save.launch_callback
            self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
            self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

            self.game_start_pending = False
            bs_stopSwitches = list()
            bs_resetSwitches = list()
            self.ball_search_tries = 0

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

            if(self.use_ballsearch_mode):
                if(len(bs_stopSwitches) == 0 and len(bs_resetSwitches) == 0):
                    self.logger.error("Could not use Ball search mode as there were no ballsearch tags (reset/stop) on any game switches in the yaml.\n -- will default to using your games: do_ball_search() method...")
                    self.use_ballsearch_mode = False

            # create it anyway; if the switches are empty it will nerf itself.
            self.ball_search = self.create_ball_search()

            if(self.use_osc_input):
                try:
                    self.osc_closed_switches
                    # or getattr(self, 'big_object')
                except AttributeError:
                    self.osc_closed_switches = []
                self.osc = osc.OSC_Mode(game=self, priority=1, closed_switches=self.osc_closed_switches)
                self.modes.add(self.osc)


            self.switchmonitor = self.create_switch_monitor()
            self.modes.add(self.switchmonitor)

            # # call reset (to reset the machine/modes/etc)

            self.genLayerFromYAML = self.dmdHelper.genLayerFromYAML

            self.notify_list = None
            self.curr_delayed_by_mode = None

            if(self.use_stock_attractmode):
                start_lamp = self.lamps.item_named_or_tagged('start_button')
                self.attract_mode = Attract(game=self, start_button_lamp=start_lamp)

        except Exception, e:
            if(hasattr(self,'osc') and self.osc is not None):
                self.osc.OSC_shutdown()
            raise

    def create_switch_monitor(self):
        return SwitchMonitor(game=self)

    def create_ball_search(self):
        return BallSearch(self, priority=100, \
                         countdown_time=self.ballsearch_time, coils=self.ballsearch_coils, \
                         reset_switches=self.ballsearch_resetSwitches, \
                         stop_switches=self.ballsearch_stopSwitches, \
                         special_handler_modes=[])

    def __install_drain_logic(self):
        """ do not install the "ball drained" logic until we know we have
            successfully fed the ball into the shooter lane """
        self.logger.debug("drain logic installed to trough")
        self.trough.drain_callback = self.__ball_drained_callback
        self.trough.launch_callback = None
        self.trough.launched_callback = None

    def cleanup(self):
        """ stub incase subclass doesn't provide an implementation """
        pass

    def end_run_loop(self):
        if(not self.cleaned_up): # if the game hasn't crashed, this might be called twice
            cleanup()
            if(hasattr(self,'cleanup')):
                self.logger.info("calling cleanup")
                self.cleanup()
            super(SkeletonGame,self).end_run_loop()
            self.cleaned_up = True
        else:
            pass
            # self.logger.info("suppressing second call to cleanup")

    def define_bonuses(self, file_name):
        """ given a yaml file that defines bonus records will init the list of known
            bonuses and their respective values """
        BonusRecord.parse_from_file(file_name)

    def find_item_name(self, identifier, group):
        """ returns the name of a switch either named or tagged with the given tag """
        tmp = group.item_named_or_tagged(identifier)
        if(tmp is None):
            return tmp
        return tmp.name

    def clear_status(self):
        self.dmdHelper.layer = None

    def set_status(self, msg, duration=2.0):
        """ a helper used to display a message on the DMD --low-tech version of displayText """
        self.displayText(msg, font_key=self.status_font_name, background_layer='status_bg', font_style=self.status_font_style, flashing=8, duration=duration)

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

        """

        return self.dmdHelper.genMsgFrame(msg, background_layer, font_style, font_key, opaque)

    def ball_saver_enable(self, num_balls_to_save=1, time=5, now=True, allow_multiple_saves=False, callback=None):
        import warnings
        message = "'ball_saver_enable' has been phased out. Replace with a call to 'enable_ball_saver()' and handle the 'evt_ball_saved' event for notification."
        warnings.simplefilter("error")
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        # raise NameError, message

    def enable_ball_saver(self, num_balls_to_save=1, time=None, now=True, allow_multiple_saves=False, tick_rate=1):
        """ turns on the ball saver -- omit time to use the setting from the service menu
            --note, if this happens 'too early' in your game, just enable the saver again at
            a later point to extend the timer """
        if(self.game_tilted):
            self.logger.debug("ball saver enable() request DENIED -- game is tilted")
            return

        if(time is None):
            time = self.user_settings['Gameplay (Feature)']['Ball Save Timer']

        self.logger.debug("ball saver enabled balls=[%d], time left=[%d]" % (num_balls_to_save,time))
        self.ball_save.start(num_balls_to_save, time, now, allow_multiple_saves, tick_rate)
        self.ball_save.callback = self.__ball_saved

    def __ball_saved(self):
        self.notifyModes('evt_ball_saved', args=None, event_complete_fn=None)

    def disable_ball_saver(self):
        """ use this to end the ball saver early """
        self.logger.debug("ball saver disabled")
        self.ball_save.disable()

    def get_highscore_data(self):
        return highscore.get_highscore_data(self.highscore_categories)

    def notifyOfNewMode(self,new_mode):
        """ let the skeletongame instance know about the new mode.  Use weakref to
            record information about the new mode so we don't accidentally keep it
            around longer than needed.  learning of the new mode happens whenever
            an advancedMode is created, and allows skeletongame to handle auto-add/remove
            of a mode based on the specified mode_type.

            NOTE: if a second instance of the same mode type is created, this raises an error.
            Do not re create modes in reset(), just reset() the mode itself
        """
        if(weakref.ref(new_mode) in self.known_modes[new_mode.mode_type]):
            self.logger.warning("Skel: A second instance of an already known mode has been created '%s'" % new_mode)
            raise ValueError, "This cannot happen. Someone notified us of the same mode instance twice!"

        for m in self.known_modes[new_mode.mode_type]:
            if type(m())==type(new_mode):
                raise ValueError, "Your code attempted to create a second instance of the Mode '%s' --this is likely an error." % type(new_mode)

        self.known_modes[new_mode.mode_type].append(weakref.ref(new_mode))
        self.logger.debug("Skel: Known advanced modes added '%s'" % new_mode)

        # import sys
        # for thing in self.known_modes[new_mode.mode_type]:
        #     self.logger.debug("skel: mode='%s' ref_ct=%d'" % (thing, sys.getrefcount(thing)))

        # # Format: evt_name(self):
        # handler_func_re = re.compile('evt_(?P<name>[a-zA-Z0-9_]+)?')
        # for item in dir(new_mode):
        #     m = handler_func_re.match(item)
        #     if m == None:
        #         continue
        #     handlerfn = getattr(new_mode, item)
        #     evt_name = m.group('name')
        #     self.add_evt_handler(new_mode, evt_name, handler=handlerfn)

    def add_evt_handler(self, mode, evt_name):
        if(evt_name not in self.event_handlers):
            raise ValueError, "Mode: %s defined a function named '%s' which is not known to the Event System" % (mode, evt_name)

        self.event_handlers[evt_name].append(weakref.ref(mode))

    def notifyNextMode(self):
        self.curr_delayed_by_mode = None
        if(len(self.notify_list)==0):
            self.event = None
            if(self.event_complete_fn is not None):
                self.logger.debug("Skel: completing event '%s' by calling '%s'" % (self.event, self.event_complete_fn))
                self.event_complete_fn()
            else:
                self.logger.debug("Skel: completing event '%s'." % (self.event))
            self.checkOutstandingSGEvents()
            return

        # otherwise there are more modes awaiting notification
        next_handler = self.notify_list.pop()

        self.logger.debug("Skel: calling mode '%s' event handler for event '%s'" % (next_handler, self.event))

        d = next_handler.handle_game_event(self.event,params=self.args)
        # if(self.args is None):
        #     d = evt_handler()
        # else:
        #     d = evt_handler(self.args)

        if(d is not None and (type(d) is int or type(d) is float)):
            if(d == 0):
                self.notifyNextMode()
            else:
                self.curr_delayed_by_mode = next_handler
                if(d > 0):
                    self.switchmonitor.delay(name='notifyNextMode',
                       event_type=None,
                       delay=d,
                       handler=self.notifyNextMode)
                # else, handler will need to handle the event itself (self.force_event_next())
        elif(type(d) is tuple):
            if(d[1] == True): # flag to stop event propegation and jump to the event
                self.notify_list = list() # zero out the list so the next 'notifyNext' call will just call the final event handler
                self.logger.info("Skel: Mode '%s' indicates event '%s' is now complete.  Blocking further propegation" % (next_handler, self.event))
            if(d[0] > 0):
                self.curr_delayed_by_mode = next_handler
                self.switchmonitor.delay(name='notifyNextMode',
                   event_type=None,
                   delay=d[0],
                   handler=self.notifyNextMode)
            elif(d[0]==0):
                # no delay specified
                self.notifyNextMode()
            else:
                # time reported is less than zero (e.g., -1) --user is saying they do not
                # want to return a bound on how long they need to handle the event, so
                # the mode is responsible for indicating the completion of handling (self.force_event_next())
                self.curr_delayed_by_mode = next_handler
        else:
            # returning None from an event handler (or not returning at all) means no delay will be given
            self.notifyNextMode()

    def notifyNextModeNow(self, caller_mode):
        if(caller_mode == self.curr_delayed_by_mode):
            # okay to notify next
            self.logger.info("Skel: notifyNextModeNow called by %s..." % (caller_mode))
            self.switchmonitor.cancel_delayed(name='notifyNextMode')
            self.notifyNextMode()
        else:
            # not okay, wrong caller!!
            self.logger.critical("Skel: notifyNextModeNow called by %s, but this mode is not blocking this event! (%s is)!?" % (caller_mode, self.curr_delayed_by_mode))

    def checkOutstandingSGEvents(self):
        if(len(self.sg_event_queue)>0):
            self.logger.info("Processing SG Event Queue: contains %d events" % len(self.sg_event_queue))
            evt = self.sg_event_queue.pop()
            self.notifyModes(evt.name, evt.args, evt.on_complete_fn, evt.only_active_modes)
        else:
            self.logger.info("SG Event Queue -- All Clear")

    def notifyModes(self, event, args=None, event_complete_fn=None, only_active_modes=True):
        """ this method will notify all AdvencedMode derived modes of the given event.  Modes
            will be notified in priority order and notifications happen over time -- that is,
            the next mode will be notified after the previous mode has completed dealing with this
            notification.  To facilitate this, modes that handle the event (by defining a
            method of the same name as the event) should respond to notifications by returning a
            number of seconds required to complete the handling of this event.  Should a method
            complete handling of the event earlier than originally anticipated (e.g., a user
            skips an animation sequence), that mode should call the AdvancedMode method:
            self.force_event_next()

            Setting the only_active_modes=False will notify _all_ known modes, not just active
            modes.  This will be of _very_ limited utility, however is useful for events such as
            evt_player_added.
        """

        if(self.event is not None):
            #We are still processing an event
            self.logger.error("Trying to notify modes about new event [%s] while [%s] is still being processed!!" % (event, self.event))

            self.sg_event_queue.append(SGEvent(event,args,event_complete_fn,only_active_modes))
            return

        delay = 0
        self.notify_list = []
        self.event_complete_fn = event_complete_fn
        self.args = args
        # if(event.startswith('evt_')):
        #     self.event = event[4:]
        self.event = event

        self.logger.info("Skel: preparing to notify modes of event %s." % event)

        if(only_active_modes):
            handlers = [h() for h in self.event_handlers[self.event] if h() is not None and h() in self.modes]
        else:
            handlers = [h() for h in self.event_handlers[self.event] if h() is not None]

        for h in handlers:
            self.logger.debug("Skel: event '%s' queuing handler found in mode [%s]" % (event, h))
            self.notify_list.append(h)

        # note this sort is in reverse priority order because we pop
        # off the back!
        self.notify_list.sort(lambda x, y: x.priority - y.priority)

        self.notifyNextMode()

    def quickNotifyModes(self, event, args=None, event_complete_fn=None, only_active_modes=True):
        """ this method will notify all AdvencedMode derived modes of the given event.  Modes
            will be notified in priority order and notifications happen within this run_loop cycle -- that is,
            the next mode will be notified immediately after the previous mode has executed its event
            handler method. Modes should not respond to notifications by returning a
            number of seconds required to complete the handling of this event, because it will be ignored.

            Setting the only_active_modes=False will notify _all_ known modes, not just active
            modes.  This will be of _very_ limited utility, however is useful for events such as
            evt_player_added.
        """

        if(self.event is not None):
            #We are still processing an event
            self.logger.info("NOTE: we are notifying modes about a 'quick' event [%s] while a system event [%s] is still being processed!!" % (event, self.event))

        quick_notify_list = []

        self.logger.info("Skel: preparing to notify modes of 'quick' event %s." % event)

        if(only_active_modes):
            handlers = [h() for h in self.event_handlers[event] if h() is not None and h() in self.modes]
        else:
            handlers = [h() for h in self.event_handlers[event] if h() is not None]

        for h in handlers:
            self.logger.debug("Skel: quick event '%s' handler found in mode [%s]" % (event, h))
            quick_notify_list.append(h)

        # note this sort is in reverse priority order because we pop
        # off the back!
        quick_notify_list.sort(lambda x, y: x.priority - y.priority)


        for h in quick_notify_list:
            self.logger.debug("Skel: quick event '%s' being handled in mode [%s]" % (event, h))
            d = h.handle_game_event(event,params=args)
            if(d is not None) and (d!=0):
                self.logger.error("modes '%s' has a quick event handler for event [%s] that seems to be requesting additional time.  This is not possible!" % (event, h))


    # called when you want to fully reset the game
    def reset(self):
        self.logger.info("Skel: RESET()")

        # reset mid-game can leave Lamps, coils or flippers on.  Turn them OFF
        # as modes might use delay() to disable them, but those won't run now
        self.disableAllLamps()
        self.disableAllCoils()

        self.enable_flippers(False)
        self.enable_alphanumeric_flippers(False)

        self.dmdHelper.reset()
        if(hasattr(self,'bonus_mode')):
            self.bonus_mode.reset()

        # clear the notification list
        self.notify_list = []
        self.event_complete_fn = None
        self.sg_event_queue = []
        self.switchmonitor.cancel_delayed(name='notifyNextMode')
        self.event = None

        super(SkeletonGame,self).reset()

        self.ball_search_tries = 0

        self.game_start_pending = False

        # reload settings
        self.load_settings_and_stats()

        # try to set the game up to be in a clean state from the outset:
        if(self.trough.num_balls() < self.num_balls_total):
            self.logger.info("Skel: RESET: trough isn't full [%d of %d] -- requesting search" % (self.trough.num_balls(), self.num_balls_total))
            if(self.use_ballsearch_mode):
                self.ball_search.perform_search(5, silent=True)
            else:
                self.do_ball_search(silent=True)

        self.modes.add(self.sound)
        # handle modes that need to be alerted of the game reset!
        for m in self.known_modes[AdvancedMode.System]:
            self.modes.add(m())

        self.modes.add(self.trough)

        # Only once the ball is fed to the shooter lane is it possible for the ball
        # drain to actually end a ball
        self.trough.drain_callback = None
        self.trough.launch_callback = None
        self.trough.launched_callback = self.__install_drain_logic

        # Link ball_save to trough
        self.trough.ball_save_callback = self.ball_save.launch_callback
        self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
        self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save
        # trough fixes

        self.modes.add(self.ball_save)

        if(self.use_stock_scoredisplay is not False):
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


        self.modes.add(self.dmdHelper)
        self.modes.add(self.switchmonitor)

    def start_attract_mode(self):
        self.modes.add(self.attract_mode) # plays the attract mode and kicks off the game


    def enable_alphanumeric_flippers(self, enable):
        """ overrides the defaults in game.py so that the flipper-relay is checked from the
            machine.yaml.  Looking for either a coil named 'flipperEnable' or a coil tagged: 'flipper_enable'

            If not present, the default value of '79' can be used for WPCAlphanumeric, but is not used for safety.
        """

        # 79 corresponds to the circuit on the power/driver board.  It will be 79 for all WPCAlphanumeric machines.
        self.logger.debug("AN Flipper enable in SkelGame.py called")

        flipperEnableCoil = None
        if('flipperEnable' in self.coils):
            flipperEnableCoil = self.coils.flipperEnable
        else:
            feList = self.coils.items_tagged('flipper_enable')
            if(len(feList)>0):
                flipperEnableCoil = feList[0]

        if(flipperEnableCoil is not None):
            if enable:
                flipperEnableCoil.pulse(0)
            else:
                flipperEnableCoil.disable()
        else:
            self.logger.warning("No flipperEnable entry in PRCoils section of machine yaml")


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

        game_volume = self.load_volume()
        self.logger.info("VOLUME SET TO: %d / %d" % (game_volume, self.sound.get_max_volume()))

        if(self.load_settings('game_default_settings.yaml','game_user_settings.yaml')):
            # settings changed as a result of reconciling with the default template! re-save
            self.user_settings['Sound']['Initial volume'] = game_volume
            self.logger.warning('settings changed.  Re-Saving!')
            self.save_settings()

        # for every coil in the list, if there's a setting that matches this label, take the value as the new default
        for c in self.coils:
            label = c.label
            if(label is not None and label in self.user_settings['Machine (Coils)']):
                c.default_pulse_time = self.user_settings['Machine (Coils)'][label]
                self.log("Settings loaded: setting coil '%s' to strength: %d" % (label, c.default_pulse_time))

        self.balls_per_game = self.user_settings['Machine (Standard)']['Balls Per Game']
        # self.auto_plunge_strength = self.user_settings['Machine (Coils)']['Auto Plunger']

        self.user_settings['Sound']['Initial volume'] = game_volume

        ## high score stuff:
        self.highscore_categories = []

        cat = highscore.HighScoreCategory()
        cat.game_data_key = 'ClassicHighScores'
        cat.titles = ['Grand Champion', 'High Score 1', 'High Score 2', 'High Score 3', 'High Score 4']
        self.highscore_categories.append(cat)

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
        return super(SkeletonGame, self).load_settings(os.path.join('config/' + file_default),os.path.join('config/' + file_game))

    def load_assets(self):
        """ function to clean up code/make things easier to read;
            this handles reading/loading of all assets (sounds, dmd images,
            dmd fonts, lightshows) from the file system
        """
        self.asset_mgr = assetmanager.AssetManager(game=self)
        self.animations = self.asset_mgr.animations
        self.fontstyles = self.asset_mgr.fontstyles
        self.fonts = self.asset_mgr.fonts

    def load_volume(self):
        try:
            v_file_path = os.path.join('config/game_user_volume.txt')
            vol_file = open(v_file_path,'r')
            vol = int(vol_file.readline())
            vol_file.close()
            self.logger.info("Read volume file value: %d" % vol)
        except Exception, e:
            self.logger.warning("Loading volume failed: %s" % e)
            vol = 5
        self.sound.set_volume_idx(vol)
        return vol

    def save_volume(self):
        try:
            v_file_path = os.path.join('config/game_user_volume.txt')
            vol_file = open(v_file_path,'w')
            vol_file.write(str(self.sound.get_volume_idx()))
            vol_file.close()
        except Exception, e:
            self.logger.warning("Saving volume failed: %s" % e)

    def ball_starting(self):
        """ this is auto-called when the ball is actually starting
            (so happens 3 or more times a game) """

        self.logger.info("Skel: BALL STARTING")

        for m in self.known_modes[AdvancedMode.Ball]:
            self.modes.add(m())

        self.notifyModes('evt_ball_starting', args=None, event_complete_fn=self.actually_start_ball)

    def shoot_again(self):
        """ this intentionally does NOT call the super class method because
            we want to block 'ball_starting' from being called immediately """
        self.logger.info("Skel: SHOOT AGAIN")
        self.notifyModes('evt_shoot_again', args=None, event_complete_fn=self.ball_starting, only_active_modes=False)

    def actually_start_ball(self):
        super(SkeletonGame, self).ball_starting()

        # eject a ball into the shooter lane
        self.trough.launch_balls(1)

        self.enable_flippers(True)
        self.enable_alphanumeric_flippers(True)

        if(self.use_ballsearch_mode):
            self.ball_search.enable()

    def __ball_drained_callback(self):
        """ this is the "drain logic" that is called by the trough if a
            ball drains --either from a multiball ball ending or from
            the trough becoming full """
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

            # Remove ball drained logic until the ball is fed into the shooter lane again
            self.trough.drain_callback = None
            self.trough.launch_callback = None
            self.trough.launched_callback = self.__install_drain_logic

            if(self.use_ballsearch_mode):
                self.ball_search.disable()

            if(self.game_tilted):
                self.tilted_ball_end()
            else:
                self.notifyModes('evt_ball_ending', args=(shoot_again,last_ball), event_complete_fn=self.end_ball)
        elif self.trough.num_balls_in_play == 1:
            """ TODO: Ensure we are only seeing this event during multiball """

            # ensure this isn't a situation of a fast-drain when more balls are pending launch
            if(self.trough.num_balls_to_launch >= 1):
                self.logger.warning("one ball in play, but more balls are pending launch (supressing evt_single_ball_play)")
            elif(self.game_tilted):
                self.logger.info("one ball in play, but game is tilted (supressing evt_single_ball_play)")
            else:
                self.notifyModes('evt_single_ball_play', args=None, event_complete_fn=None)
        else:
            self.notifyModes('evt_mb_drain', args=None, event_complete_fn=None)

    def your_search_is_over(self):
        """ all balls have been accounted for --if you were blocking a game start, stop that. """
        if(self.game_start_pending):
            if(self.use_ballsearch_mode):
                self.ball_search.full_stop()
            self.game_start_pending = False
            self.notifyModes('evt_balls_found', args=None, event_complete_fn=None)
            # self.game_started()

    def volume_down(self):
        """ decrease volume and store the new setting """
        volume = self.sound.volume_down()
        self.quickNotifyModes('evt_volume_down', args=volume, event_complete_fn=None)
        self.user_settings['Sound']['Initial volume'] = int(volume)
        self.save_volume()
        # self.save_settings()

    def volume_up(self):
        """ increase volume and store the new setting """
        volume = self.sound.volume_up()
        self.quickNotifyModes('evt_volume_up', args=volume, event_complete_fn=None)
        self.user_settings['Sound']['Initial volume'] = int(volume)
        self.save_volume()
        # self.save_settings()

    def request_additional_player(self):
        """ attempt to add an additional player, but honor the max_players setting """
        if len(self.players) < self.max_players:
            p = self.add_player()
        else:
            self.logger.info("Cannot add more than %d players." % self.max_players)

    def add_player(self):
        """ add another player (even if there are too many); fires evt_player_added to notify modes that care """
        player = super(SkeletonGame, self).add_player()
        self.quickNotifyModes('evt_player_added', args=(player), event_complete_fn=None, only_active_modes=False)
        return player

    def slam_tilted(self):
        self.b_slam_tilted = True
        self.game_tilted = True
        self.notifyModes('evt_tilt', args=True, event_complete_fn=None)

    def slam_tilt_complete(self):
        self.b_slam_tilted = False
        self.game_tilted = False
        self.end_ball()
        self.end_game()
        self.reset()

    def tilt_warning(self, times_warned):
        """ called by the 'TiltMonitor' mode to indicate a tilt warning
        """
        self.notifyModes('evt_tilt_warning', args=times_warned, event_complete_fn=None)

    def tilted(self):
        """ called by the 'Tilted' mode to indicate the machine has been tilted;
            because evt_ball_ending isn't fired, bonus mode will not be tallied
        """
        self.b_slam_tilted = False
        self.game_tilted = True

        if(self.trough.drain_callback == None):
            self.logger.debug("machine tilted before drain logic installed; install it now!")
            self.trough.num_balls_to_launch = 0
            self.trough.drain_callback = self.__ball_drained_callback
            # TODO: check if the trough is full in a few seconds


        self.notifyModes('evt_tilt', args=False, event_complete_fn=None)

    def tilted_ball_end(self):
        """ called by the 'Tilted' mode to indicate the machine has been
            tilted and all balls are back in the trough -- in essence, this
            signals a evt_tilt_ball_ending, which is a variant of evt_ball_ending;
            because evt_ball_ending isn't fired, bonus mode will not be tallied
        """
        self.game_tilted = False
        self.tilt_mode.tilt_reset()
        self.modes.remove(self.tilted_mode)
        if(not self.b_slam_tilted):
            self.notifyModes('evt_tilt_ball_ending', args=None, event_complete_fn=self.end_ball)
        else:
            self.notifyModes('evt_tilt_ball_ending', args=None, event_complete_fn=self.slam_tilt_complete)


    def end_ball(self):
        """ overides game.py version to prevent ball/game time
            increasing (we count it here, to get more accurate data)
            note that super is intentionally not called.

            this method should only be called following appropriate
            event notification --read: don't call this from your game code
            unless you really know what you are doing
        """
        self.ball_ended()
        if self.current_player().extra_balls > 0:
            self.current_player().extra_balls -= 1
            self.shoot_again()
            return
        if self.current_player_index + 1 == len(self.players):
            self.ball += 1
            self.current_player_index = 0
        else:
            self.current_player_index += 1
        if self.ball > self.balls_per_game:
            self.end_game()
        else:
            self.start_ball() # Consider: Do we want to call this here, or should it be called by the game? (for bonus sequence)

    def ball_ended(self):
        """ Subclassed by implementor to react to the ball being completely over
            automatically invoked by end_ball(). At this point the ball is over """
        self.logger.info("Skel: BALL ENDED")

        # turn off the flippers
        self.enable_flippers(False)
        self.enable_alphanumeric_flippers(False)

        if(self.use_ballsearch_mode):
            self.ball_search.disable() # possibly redundant if ball ends normally, but not redundant when slam tilted

        super(SkeletonGame, self).ball_ended()
        for m in self.known_modes[AdvancedMode.Ball]:
            self.modes.remove(m())

    def reset_search(self):
        if(self.game_start_pending):
            # self.clear_status()
            self.game_start_pending = False
            if(self.trough.num_balls() >= self.num_balls_total):
                # we could start now...
                # but don't!
                # self.game_started()
                pass
            else: # insufficient balls to start
                # don't try again, just shut down the status indicator

                # # wait 3s before trying again
                # if(self.use_ballsearch_mode):
                #     self.ball_search.perform_search(3,  completion_handler=self.reset_search)
                #     # self.ball_search.delay(name='ballsearch_start_delay',
                #     #    event_type=None,
                #     #    delay=3,
                #     #    handler=self.game_started)
                # else:
                #     self.do_ball_search(silent=False)
                #     self.ball_search.delay(name='ballsearch_start_delay', event_type=None, delay=3.0, handler=self.reset_search)
                pass
        else:
            # game started on it's own.  Continue living
            pass

    def game_started(self):
        """ this happens after start_game but before start_ball/ball_starting"""
        self.logger.info("Skel:Game START Requested...(check trough first)")

        # check trough and potentially do a ball search first
        if(self.game_start_pending and (self.trough.num_balls() < self.num_balls_total)):
            self.logger.info("Skel: Game START : PLEASE WAIT!! -- TROUGH STATE is still BLOCKING GAME START!")
            # self.set_status("Balls STILL Missing: PLEASE WAIT!!", 3.0)
            self.notifyModes('evt_balls_missing', args=None, event_complete_fn=None)
            return

        if(self.trough.num_balls() < self.num_balls_total):
            self.game_start_pending=True
            self.logger.info("Skel: game_started: trough isn't full [%d of %d] -- requesting search" % (self.trough.num_balls(), self.num_balls_total))
            if(self.use_ballsearch_mode):
                self.ball_search.perform_search(3,  completion_handler=self.reset_search)
                self.logger.debug("Skel: game_started: Standard ball search initiated")
            else:
                self.logger.debug("Skel: game_started: Programmer custom ball search initiated")
                self.do_ball_search(silent=False)
                self.ball_search.delay(name='ballsearch_start_delay', event_type=None, delay=3.0, handler=self.reset_search)
            return
        else: # we have the right number of balls
            self.game_start_pending=False
            if(self.use_ballsearch_mode):
                self.ball_search.cancel_delayed(name='ballsearch_start_delay')

        self.logger.info("Skel:Game START Proceeding")

        # remove attract mode
        self.modes.remove(self.attract_mode)

        super(SkeletonGame, self).game_started()

        for m in self.known_modes[AdvancedMode.Game]:
            self.modes.add(m())

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
        self.logger.info("Skel: 'GAME ENDED")

        # ball time is handled in ball drained callback

        # Also handle game stats.
        for i in range(0,len(self.players)):
            game_time = self.get_game_time(i)
            self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string( self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
            self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
            self.game_data['Audits']['Games Played'] += 1

            self.logger.info("Skel: 'player %d score %d" % (i, self.players[i].score))

        self.save_game_data('game_user_data.yaml')

        # show any animations you want in ball_ending
        self.notifyModes('evt_game_ending', args=None, event_complete_fn=self.game_ended)

    def game_ended(self):
        super(SkeletonGame, self).game_ended()
        self.disableAllLamps()

        # remove Game-duration modes
        for m in self.known_modes[AdvancedMode.Game]:
            self.modes.remove(m())
        pass

        seq_manager = highscore.HD_EntrySequenceManager(game=self, priority=2, multiline=self.use_multiline_score_entry)
        seq_manager.finished_handler = self.high_score_entry_completed
        seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
        seq_manager.ready_handler = self.__pre_high_score_entry
        self.modes.add(seq_manager)

    def __pre_high_score_entry(self, seq_manager, category):
        self.notifyModes('evt_initial_entry', args=category, event_complete_fn=seq_manager.prompt)

    def high_score_entry_completed(self, mode):
        self.save_game_data('game_user_data.yaml')
        self.modes.remove(mode)
        self.notifyModes('evt_game_ended', args=None, event_complete_fn=self.reset)

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
        """ dump all existing modes that are running
            stop music, stop lampshows, disable flippers
            then add the service mode.
        """
        self.modes.modes = [m for m in self.modes.modes if isinstance(m,AdvancedMode) and m.mode_type==AdvancedMode.System]
        for m in self.modes:
            self.modes.remove(m)

        self.lampctrl.stop_show()
        self.rgbshow_player.stop_all()

        self.disableAllLamps()
        self.sound.stop_music()

        # disable flippers
        self.enable_flippers(False)
        self.enable_alphanumeric_flippers(False)

        self.modes.add(self.service_mode)

    def service_mode_ended(self):
        self.save_settings()
        self.load_settings_and_stats()
        self.reset()

    def disableAllCoils(self):
        """ turn off all coils
            needed after a reset while the game is in progress, we don't want
            to leave coils energized that might have been disabled by now cancelled
            delays
        # NOTE: If this behavior is undesirable in your machine, define your own reset method
            and re-engergize any coils you need to OR define your own disableAllCoils that
            leaves some on
        """
        for coil in self.coils:
            coil.disable()

    def disableAllLamps(self):
        # turn off all the lamps
        for lamp in self.lamps:
            lamp.disable()

        # turn off all the LEDs, too
        for lamp in self.leds:
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

    def getPlayerState(self, key, default = None):
        if (self.ball != 0):
            self.p = self.current_player()
            return self.p.getState(key, default)

    def bonus(self, name, quantity=1, value=None):
        """ value is not required if the bonus has been predefined """
        if (self.ball != 0):
            self.p = self.current_player()
            self.p.awardBonus(name,quantity, value)

    def run_loop(self, min_seconds_per_cycle=None):
        #sdl2_DisplayManager.inst().show_window(True)
        super(SkeletonGame, self).run_loop(min_seconds_per_cycle)

    def do_ball_search(self, silent=False):
        self.ball_search_tries += 1
        if(not silent):
            # self.set_status("Balls Missing: PLEASE WAIT!!", 3.0)
            self.notifyModes('evt_balls_missing', args=None, event_complete_fn=None)

class SGEvent(object):
    """An object to hold an SGEvent; useful if multiple events come in at a time"""
    def __init__(self, event_name, evt_args, on_complete_fn, only_active_modes):
        super(SGEvent, self).__init__()
        self.name = event_name
        self.args = evt_args
        self.on_complete_fn = on_complete_fn
        self.only_active_modes = only_active_modes

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

    def awardBonus(self, name, quantity=1, point_value=None):
        """ adds an entry for `quantity` more bonuses named `name`
            assuming the bonus has been defined, the point_value per each
            is considered.  If the bonus has not previously defined, this
            also defines the value (which should be awarded at end_of_ball)
        """
        self.bonuses.award(name,quantity, point_value)

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

    def getState(self, key, default = None):
        return self.state_tracking.get(key,default)


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
    def __init__(self):
        self.bonus_held = False
        self.earned_list = []

    @classmethod
    def define_bonus(cls, name, point_value, max_per_ball=float('inf'), max_per_game=float('inf')):
        """ defines a point value for a specific named bonus """
        master = find_in_list(name, cls.master_list)
        if(master is not None):
            logging.getLogger('Bonus').warning("trying to redefine existing bonus named ['%s']" % name)
        else:
            logging.getLogger('Bonus').info("defining bonus ['%s']" % name)
            master = {  'name':name,
                        'points': point_value,
                        'max_ball': max_per_ball,
                        'max_game': max_per_game,
                        'order':len(cls.master_list)}
            cls.master_list.append(master)
            logging.getLogger('Bonus').info("master list ['%s']" % cls.master_list)

    def award(self, name, quantity=1, point_value=None):
        """ adds an entry for `quantity` more bonuses named `name`
            assuming the bonus has been defined, the point_value per each
            is considered.  If the bonus has not previously defined, this
            also defines the value (which should be awarded at end_of_ball)
        """
        master = find_in_list(name, self.master_list)
        if(master is None):
            logging.getLogger('Bonus').warning("trying to award bonus ['%s'] which is not defined in master list" % name)
            master = {  'name':name,
                        'points': 1000 if point_value is None else point_value,
                        'max_ball':float('inf'),
                        'max_game':float('inf'),
                        'order':len(self.master_list)}
            self.master_list.append(master)
        prev_award = find_in_list(name, self.earned_list)
        if(prev_award is None):
            prev_award = {'name':name, 'count':0, 'points':master['points']}
            self.earned_list.append(prev_award)

        if(prev_award['count'] < master['max_ball'] and prev_award['count'] < master['max_game']):
            prev_award['count'] = prev_award['count'] + quantity
        else:
            logging.getLogger('Bonus').info("Bonus ['%s'] at max!" % name)

        print("==================")
        print("%s" % self.earned_list)
        print("%s" % self.master_list)
        print("==================")

    @classmethod
    def parse_from_file(cls, bonus_def_file):
        # read a yaml fie and load all the bonuses
        try:
            values = yaml.load(open(bonus_def_file, 'r'))
        except yaml.scanner.ScannerError, e:
            raise
        except Exception, e:
            values = dict()

        if "BonusDefs" in values:
            bdefs = values["BonusDefs"]
            for bonus_record_dict in bdefs:
                n = bonus_record_dict.keys()[0]
                bonus_record = value_for_key(bonus_record_dict,n)
                p = value_for_key(bonus_record,'points')
                mpb = value_for_key(bonus_record,'max_per_ball', float('inf'))
                mpg = value_for_key(bonus_record,'max_per_game', float('inf'))
                cls.define_bonus(n, p, mpb, mpg)
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
