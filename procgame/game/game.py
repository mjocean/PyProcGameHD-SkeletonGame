import os
import sys
import pinproc
import Queue
import yaml
import time
import copy
import logging
from procgame import config
from gameitems import *
from procgame import util
from mode import *
from pdb import PDBConfig, LED
from procgame import LEDs

def config_named(name):
    if not os.path.isfile(name): # If we cannot find this file easily, try searching the config_path:
        config_paths = config.value_for_key_path('config_path', ['.'])
        if issubclass(type(config_paths), str):
            config_paths = [config_paths]
        found_path = util.find_file_in_path(name, config_paths)
        if found_path:
            name = found_path
        else:
            return None
    return yaml.load(open(name, 'r'))


class GameController(object):
    """Core object representing the game itself.
    Usually a game developer will create a new game by subclassing this class.
    Consider subclassing :class:`BasicGame` instead, as it makes use of several helpful modes
    and controllers.
    """

    machine_type = None
    """Machine type used to configure :attr:`proc` in this class's initializer."""
    proc = None
    """A :class:`pinproc.PinPROC` instance, created in the initializer with machine type :attr:`machine_type`."""
    modes = None
    """An instance of :class:`ModeQueue`, which manages the presently active modes."""

    coils = AttrCollection("drivers")
    """An :class:`AttrCollection` of :class:`Driver` objects.  Populated by :meth:`load_config`."""
    lamps = AttrCollection("lamps")
    """An :class:`AttrCollection` of :class:`Driver` objects.  Populated by :meth:`load_config`."""
    switches = AttrCollection("switches")
    """An :class:`AttrCollection` of :class:`Switch` objects.  Populated by :meth:`load_config`."""
    leds = AttrCollection("leds")
    """An :class:`AttrCollection` of :class:`LED` objects.  Populated by :meth:`load_config`."""

    ball = 0
    """The number of the current ball.  A value of 1 represents the first ball; 0 indicates game over."""
    players = []
    """Collection of :class:`Player` objects."""
    old_players = []
    """Copy of :attr:`players` made when :meth:`reset` is called."""
    current_player_index = 0
    """Index in :attr:`players` of the current player."""
    t0 = None
    """Start :class:`time.time` of the game program.  I.e., the time of power-up."""
    config = None
    """YAML game configuration loaded by :meth:`load_config`."""
    balls_per_game = 3
    """Number of balls per game."""
    game_data = {}
    """Contains high score and audit information.  That is, transient information specific to one game installation."""
    user_settings = {}
    """Contains local game configuration, such as the volume."""

    logger = None
    """:class:`Logger` object instance; instantiated in :meth:`__init__` with the logger name "game"."""

    # MJO: Virtual DMD w/o h/w DMD
    frames_per_second = 30

    """Setting this to true in the config.yaml enables a virtual DMD without physical DMD events going to the PROC"""

    LEDs = None
    def __init__(self, machine_type):
        super(GameController, self).__init__()
        self.logger = logging.getLogger('game')
        self.machine_type = pinproc.normalize_machine_type(machine_type)
        self.proc = self.create_pinproc()
        self.proc.reset(1)
        self.modes = ModeQueue(self)
        self.t0 = time.time()
        self.LEDs = LEDs.LEDcontroller(self)
        self.dmd_updates = 0
        self.use_proc_dmd = config.value_for_key_path(keypath='proc_dmd', default=False)

    def create_pinproc(self):
        """Instantiates and returns the class to use as the P-ROC device.
        This method is called by :class:`GameController`'s init method to populate :attr:`proc`.

        Checks :mod:`~procgame.config` for the key path ``pinproc_class``.
        If that key path exists the string is used as the fully qualified class name
        to instantiate.  The class is then instantiated with one initializer argument,
        :attr:`machine_type`.

        If that key path does not exist then this method returns an instance of :class:`pinproc.PinPROC`.
        """
        self.frames_per_second = config.value_for_key_path('dmd_framerate', 30)
        klass_name = config.value_for_key_path('pinproc_class', 'pinproc.PinPROC')
        klass = util.get_class(klass_name)
        return klass(self.machine_type)

    def create_player(self, name):
        """Instantiates and returns a new instance of the :class:`Player` class with the
        name *name*.
        This method is called by :meth:`add_player`.
        This can be used to supply a custom subclass of :class:`Player`.
        """
        return Player(name)

    def __enter__(self):
        pass

    def __exit__(self):
        del self.proc

    def reset(self):
        """Reset the game state as a slam tilt might."""
        self.ball = 0
        self.old_players = []
        self.old_players = self.players[:]
        self.players = []
        self.current_player_index = 0
        self.modes.modes = []

    def current_player(self):
        """Returns the current :class:`Player` as described by :attr:`current_player_index`."""
        if len(self.players) > self.current_player_index:
            return self.players[self.current_player_index]
        else:
            return None

    def add_player(self):
        """Adds a new player to :attr:`players` and assigns it an appropriate name."""
        player = self.create_player('Player %d' % (len(self.players) + 1))
        self.players += [player]
        return player

    def get_ball_time(self):
            return self.ball_end_time - self.ball_start_time

    def get_game_time(self, player):
            return self.players[player].game_time

    def save_ball_start_time(self):
        self.ball_start_time = time.time()

    def start_ball(self):
        """Called by the implementor to notify the game that (usually the first) ball should be started."""
        self.ball_starting()

    def ball_starting(self):
        """Called by the game framework when a new ball is starting."""
        self.save_ball_start_time()

    def shoot_again(self):
        """Called by the game framework when a new ball is starting which was the result of a stored extra ball (Player.extra_balls).
           The default implementation calls ball_starting(), which is not called by the framework in this case."""
        self.ball_starting()

    def ball_ended(self):
        """Called by the game framework when the current ball has ended."""
        pass

    def end_ball(self):
        """Called by the implementor to notify the game that the current ball has ended."""

        self.ball_end_time = time.time()
        # Calculate ball time and save it because the start time
        # gets overwritten when the next ball starts.
        self.ball_time = self.get_ball_time()
        self.current_player().game_time += self.ball_time

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

    def game_started(self):
        """Called by the GameController when a new game is starting."""
        self.ball = 1
        self.players = []
        self.current_player_index = 0

    def start_game(self):
        """Called by the implementor to notify the game that the game has started."""
        self.game_started()

    def game_ended(self):
        """Called by the GameController when the current game has ended."""
        pass

    def end_game(self):
        """Called by the implementor to mark notify the game that the game has ended."""
        self.ball = 0
        self.game_ended()

    def is_game_over(self):
        """Returns `True` if the game is in game over.  A game is in game over if :attr:`ball` is 0."""
        return self.ball == 0

    def dmd_event(self):
        """Called by the GameController when a DMD event has been received."""
        pass

    def tick(self):
        """Called by the GameController once per run loop."""
        pass

    def load_config(self, filename):
        """Reads the YAML machine configuration file into memory.
        Configures the switches, lamps, and coils members.
        Enables notifyHost for the open and closed debounced states on each configured switch.
        """
        self.logger.info('Loading machine configuration from "%s"...', filename)
        self.config = config_named(filename)
        if not self.config:
            raise ValueError, 'load_config(filename="%s") could not be found. Did you set config_path?' % (filename)
        self.process_config()

    def load_config_stream(self, stream):
        """Reads the YAML machine configuration in stream form (string or opened file) into memory.
        Configures the switches, lamps, and coils members.
        Enables notifyHost for the open and closed debounced states on each configured switch.
        """
        self.config = yaml.load(stream)
        if not self.config:
            raise ValueError, 'load_config_stream() could not load configuration.  Malformed YAML?'
        self.process_config()

    def process_config(self):
        """Called by :meth:`load_config` and :meth:`load_config_stream` to process the values in :attr:`config`."""
        pairs = [('PRCoils', self.coils, Driver),
                 ('PRLamps', self.lamps, Driver),
                 ('PRSwitches', self.switches, Switch),
                 ('PRLEDs', self.leds, LED) ]

        new_virtual_drivers = []
        polarity = self.machine_type == pinproc.MachineTypeSternWhitestar or self.machine_type == pinproc.MachineTypeSternSAM or self.machine_type == pinproc.MachineTypePDB

        # Because PDBs can be configured in many different ways, we need to traverse
        # the YAML settings to see how many PDBs are being used.  Then we can configure
        # the P-ROC appropriately to use those PDBs.  Only then can we relate the YAML
        # coil/lamp #'s to P-ROC numbers for the collections.
        if self.machine_type == pinproc.MachineTypePDB:
            pdb_config = PDBConfig(self.proc, self.config)

        for section, collection, klass in pairs:
            if section in self.config:
                sect_dict = self.config[section] or {}
                for name in sect_dict:

                    item_dict = sect_dict[name]

                    # Find the P-ROC number for each item in the YAML sections.  For PDB's
                    # the number is based on the PDB configuration determined above.  For
                    # other machine types, pinproc's decode() method can provide the number.
                    if self.machine_type == pinproc.MachineTypePDB:
                        number = pdb_config.get_proc_number(section, str(item_dict['number']))
                        if number == -1:
                            self.logger.error('%s Item: %s cannot be controlled by the P-ROC.  Ignoring...', section, name)
                            continue
                    else:
                        number = pinproc.decode(self.machine_type, str(item_dict['number']))

                    item = None
                    if ('bus' in item_dict and item_dict['bus'] == 'AuxPort') or number >= pinproc.DriverCount:
                        item = VirtualDriver(self, name, number, polarity)
                        new_virtual_drivers += [number]
                    else:
                        yaml_number = str(item_dict['number'])
                        if klass==LED:
                            number = yaml_number

                        item = klass(self, name, number)
                        item.yaml_number = yaml_number
                        if 'label' in item_dict:
                            item.label = item_dict['label']
                        if 'type' in item_dict:
                            item.type = item_dict['type']

                        if 'tags' in item_dict:
                            tags = item_dict['tags']
                            if type(tags) == str:
                                item.tags = tags.split(',')
                            elif type(tags) == list:
                                item.tags = tags
                            else:
                                self.logger.warning('Configuration item named "%s" has unexpected tags type %s. Should be list or comma-delimited string.' % (name, type(tags)))

                        if klass==Switch:
                            if (('debounce' in item_dict and item_dict['debounce'] == False) or number >= pinproc.SwitchNeverDebounceFirst):
                                item.debounce = False
                        if klass==Driver:
                            if ('pulseTime' in item_dict):
                                item.default_pulse_time = item_dict['pulseTime']
                            if ('polarity' in item_dict):
                                item.reconfigure(item_dict['polarity'])
                        if klass==LED:
                            if ('polarity' in item_dict):
                                item.invert = not item_dict['polarity']

                    collection.add(name, item)

        # In the P-ROC, VirtualDrivers will conflict with regular drivers on the same group.
        # So if any VirtualDrivers were added, the regular drivers in that group must be changed
        # to VirtualDrivers as well.
        for virtual_driver in new_virtual_drivers:
            base_group_number = virtual_driver/8
            for collection in [self.coils, self.lamps]:
                items_to_remove = []
                for item in collection:
                    if item.number/8 == base_group_number:
                        items_to_remove += [{name:item.name,number:item.number}]
                for item in items_to_remove:
                    self.logger.info( "Removing %s from %s" , item[name],str(collection))
                    collection.remove(item[name], item[number])
                    self.logger.info("Adding %s to VirtualDrivers",item[name])
                    collection.add(item[name], VirtualDriver(self, item[name], item[number], polarity))

        if 'PRBallSave' in self.config:
            sect_dict = self.config['PRBallSave']
            self.ballsearch_coils = sect_dict['pulseCoils']
            self.ballsearch_stopSwitches = sect_dict['stopSwitches']
            self.ballsearch_resetSwitches = sect_dict['resetSwitches']


        # We want to receive events for all of the defined switches:
        self.logger.info("Programming switch rules...")
        for switch in self.switches:
            if switch.debounce:
                self.proc.switch_update_rule(switch.number, 'closed_debounced', {'notifyHost':True, 'reloadActive':False}, [], False)
                self.proc.switch_update_rule(switch.number, 'open_debounced', {'notifyHost':True, 'reloadActive':False}, [], False)
            else:
                self.proc.switch_update_rule(switch.number, 'closed_nondebounced', {'notifyHost':True, 'reloadActive':False}, [], False)
                self.proc.switch_update_rule(switch.number, 'open_nondebounced', {'notifyHost':True, 'reloadActive':False}, [], False)

        # Configure the initial switch states:
        states = self.proc.switch_get_states()
        for sw in self.switches:
            sw.set_state(states[sw.number] == 1)

        sect_dict = self.config['PRGame']
        self.num_balls_total = sect_dict['numBalls']

        self.logger.info("LEDS...")
        for led in self.leds:
            self.logger.info(" LED name=%s; number=%s" % (led.name,led.yaml_number))


    def load_settings(self, template_filename, user_filename):
        """Loads the YAML game settings configuration file.  The game settings
        describe operator configuration options, such as balls per game and
        replay levels.
        The *template_filename* provides default values for the game;
        *user_filename* contains the values set by the user.

        See also: :meth:`save_settings`
        """
        settings_changed = False

        self.user_settings = {}
        self.settings = yaml.load(open(template_filename, 'r'))
        if os.path.exists(user_filename):
            self.user_settings = yaml.load(open(user_filename, 'r'))

        # this pass ensures the user settings include everything in the
        # game settings by assigning defaults for anything missing
        for section in self.settings:
            for item in self.settings[section]:
                if not section in self.user_settings:
                    self.user_settings[section] = {}
                    settings_changed = True
                if not item in self.user_settings[section]:
                    settings_changed = True
                    self.logger.error("Missing setting in user settings file; will be replaced with default:\n%s:{%s}\n-------" % (section,item))
                    if 'default' in self.settings[section][item]:
                        self.user_settings[section][item] = self.settings[section][item]['default']
                    else:
                        self.user_settings[section][item] = self.settings[section][item]['options'][0]
                else:
                    if 'increments' not in self.settings[section][item]:
                        if(self.user_settings[section][item] not in self.settings[section][item]['options']):
                            settings_changed = True
                            self.logger.error("Invalid value found in user settings file; will be replaced with default:\n%s:{%s}\n-------" % (section,item))
                            if 'default' in self.settings[section][item]:
                                self.user_settings[section][item] = self.settings[section][item]['default']
                            else:
                                self.user_settings[section][item] = self.settings[section][item]['options'][0]


        # this pass logs settings that occur in the user settings
        # but not in game settings and removes them
        invalid_sections = []
        for section in self.user_settings:
            if(section not in self.settings):
                settings_changed = True
                self.logger.error("Deprecated section found in user settings file; will be removed:\n%s\n-------" % section)
                invalid_sections.append(section)
            else:
                invalid_items = []
                for item in self.user_settings[section]:
                    if item not in self.settings[section]:
                        settings_changed = True
                        self.logger.error("Deprecated setting found in user settings file; will be removed:\n%s:{%s}\n-------" % (section, item))
                        invalid_items.append(item)
                for item in invalid_items:
                    self.user_settings[section].pop(item)
        for section in invalid_sections:
            self.user_settings.pop(section)

        return settings_changed


    def save_settings(self, filename):
        """Writes the game settings to *filename*.  See :meth:`load_settings`."""
        if os.path.exists(filename):
            if os.path.exists(filename+'.bak'):
                os.remove(filename+'.bak')
            os.rename(filename, filename+'.bak')

        if os.path.exists(filename):
            os.remove(filename)

        stream = open(filename, 'w')
        yaml.dump(self.user_settings, stream)
        file.close(stream)

        if os.path.getsize(filename) == 0:
            self.logger.error( " ****** CORRUPT GAME USER SETTINGS FILE REPLACING WITH CLEAN DATA  --- restoring last copy ****************")
            #remove bad file
            os.remove(filename)
            os.rename(filename+'.bak', filename)
        else:
            self.logger.info("Settings saved to " + str(filename))


    def load_game_data(self, template_filename, user_filename):
        """Loads the YAML game data configuration file.  This file contains
        transient information such as audits, high scores and other statistics.
        The *template_filename* provides default values for the game;
        *user_filename* contains the values set by the user.

        See also: :meth:`save_game_data`
        """
        self.game_data = {}
        template_file = open(template_filename,'r')
        template = yaml.load(template_file)
        file.close(template_file)

        if os.path.exists(user_filename):
            if os.path.getsize(user_filename) == 0:
                self.logger.error(  " ****************   CORRUPT DATA FILE REPLACING WITH CLEAN DATA  --- ****************")
                os.remove(user_filename)
                os.rename(user_filename+'.bak', user_filename)

            user_filename_file = open(user_filename, 'r')
            self.game_data = yaml.load(user_filename_file)
            file.close(user_filename_file)

        if template:
            for key, value in template.iteritems():
                if key not in self.game_data:
                    self.game_data[key] = copy.deepcopy(value)

    def save_game_data(self, filename):
        """Writes the game data to *filename*.  See :meth:`load_game_data`."""
        if os.path.exists(filename):
            if os.path.exists(filename+'.bak'):
                os.remove(filename+'.bak')
            os.rename(filename, filename+'.bak')

        stream = open(filename, 'w')
        yaml.dump(self.game_data, stream)
        file.close(stream)
        #now check for successful write, if not restore backup file
        if os.path.getsize(filename) == 0:
            self.logger.info(  " ****************   CORRUPT DATA FILE REPLACING WITH CLEAN DATA  --- restoring last copy ****************")
            #remove bad file
            os.remove(filename)
            os.rename(filename+'.bak', filename)

    def enable_flippers(self, enable):
        #return True

        """Enables or disables the flippers AND bumpers."""
        for flipper in self.config['PRFlippers']:
            self.logger.info("Programming flipper %s", flipper)
            main_coil = self.coils[flipper+'Main']
            if self.coils.has_key(flipper+'Hold'):
                style = 'wpc'
                self.logger.info("%sabling WPC style flipper" % ("En" if enable else "Dis"))
                hold_coil = self.coils[flipper+'Hold']
            else:
                self.logger.info("%sabling Stern style flipper" % ("En" if enable else "Dis"))
                style = 'stern'
            switch_num = self.switches[flipper].number

            drivers = []
            if enable:
                if style == 'wpc':
                    drivers += [pinproc.driver_state_pulse(main_coil.state(), main_coil.default_pulse_time)]
                    drivers += [pinproc.driver_state_pulse(hold_coil.state(), 0)]
                else:
                    drivers += [pinproc.driver_state_patter(main_coil.state(), 2, 18, main_coil.default_pulse_time, True)]
            self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False, 'reloadActive':False}, drivers, len(drivers) > 0)

            drivers = []
            if enable:
                drivers += [pinproc.driver_state_disable(main_coil.state())]
                if style == 'wpc':
                    drivers += [pinproc.driver_state_disable(hold_coil.state())]

            self.proc.switch_update_rule(switch_num, 'open_nondebounced', {'notifyHost':False, 'reloadActive':False}, drivers, len(drivers) > 0)

            if not enable:
                main_coil.disable()
                if style == 'wpc':
                    hold_coil.disable()

        # Enable the flipper relay on wpcAlphanumeric machines
        if self.machine_type == pinproc.MachineTypeWPCAlphanumeric:
            self.enable_alphanumeric_flippers(enable)

        self.enable_bumpers(enable)

    def enable_alphanumeric_flippers(self, enable):
        # 79 corresponds to the circuit on the power/driver board.  It will be 79 for all WPCAlphanumeric machines.
        self.log("AN Flipper enable in game.py called")
        flipperRelayPRNumber = 79
        if enable:
            self.coils[79].pulse(0)
        else:
            self.coils[79].disable()

    def enable_bumpers(self, enable):
        # Scott Danesi modified to allow pulsed patter for these PRBumpers.
        # You must include teh tag 'pulsed' in your machine.yaml file for the coil, example below
        #   slingR:
        #       number: A6-B1-4
        #       pulseTime: 5
        #       label: 'Sling - Right'
        #       tags: pulsed

        for bumper in self.config['PRBumpers']:
            switch_num = self.switches[bumper].number
            coil = self.coils[bumper]

            drivers = []
            if enable:
                if "pulsed" in coil.tags:
                    drivers += [pinproc.driver_state_pulsed_patter(coil.state(), 2, 2, coil.default_pulse_time, True)]
                else:
                    drivers += [pinproc.driver_state_pulse(coil.state(), coil.default_pulse_time)]

            self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':True, 'reloadActive':True}, drivers, False)

    def install_switch_rule_coil_disable(self, switch_num, switch_state, coil_name, notify_host, enable, reload_active = False, drive_coil_now_if_valid=False):
        coil = self.coils[coil_name];
        drivers = []
        if enable:
            drivers += [pinproc.driver_state_disable(coil.state())]
        self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host, 'reloadActive':reload_active}, drivers, drive_coil_now_if_valid)

    def install_switch_rule_coil_pulse(self, switch_num, switch_state, coil_name, pulse_duration, notify_host, enable, reload_active = False, drive_coil_now_if_valid=False):
        coil = self.coils[coil_name];
        drivers = []
        if enable:
            drivers += [pinproc.driver_state_pulse(coil.state(),pulse_duration)]
        self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host, 'reloadActive':reload_active}, drivers, drive_coil_now_if_valid)

    def install_switch_rule_coil_schedule(self, switch_num, switch_state, coil_name, schedule, schedule_seconds, now, notify_host, enable, reload_active = False, drive_coil_now_if_valid=False):

        coil = self.coils[coil_name];
        drivers = []
        if enable:
            drivers += [pinproc.driver_state_schedule(coil.state(),schedule,schedule_seconds,now)]
        self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host, 'reloadActive':reload_active}, drivers, drive_coil_now_if_valid)

    def install_switch_rule_coil_patter(self, switch_num, switch_state, coil_name, milliseconds_on, milliseconds_off, original_on_time, notify_host, enable, reload_active = False, drive_coil_now_if_valid=False):
        coil = self.coils[coil_name];
        drivers = []
        if enable:
            drivers += [pinproc.driver_state_patter(coil.state(),milliseconds_on,milliseconds_off,original_on_time, True)]
        self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host, 'reloadActive':reload_active}, drivers, drive_coil_now_if_valid)

    def process_event(self, event):
        event_type = event['type']
        event_value = event['value']
        if event_type == 99: # CTRL-C to quit
            print "CTRL-C detected, quiting..."
            self.end_run_loop()
        elif event_type == pinproc.EventTypeDMDFrameDisplayed: # DMD events
            # print "% 10.3f Frame event.  Value=%x" % (time.time()-self.t0, event_value)
            self.dmd_event()
        elif event_type == pinproc.EventTypeBurstSwitchOpen or \
             event_type == pinproc.EventTypeBurstSwitchClosed:
            self.burst_event(event)
        elif event_type == pinproc.EventTypeSwitchClosedDebounced or \
             event_type == pinproc.EventTypeSwitchOpenDebounced or \
             event_type == pinproc.EventTypeSwitchClosedNondebounced or \
             event_type == pinproc.EventTypeSwitchOpenNondebounced:
            self.switch_event(event)
        else:
            self.other_event(event)

    def other_event(self, event):
        self.logger.warning("Unknown event type received.  Type:%d, Value:%s." % (event['type'], event['value']))

    def switch_event(self, event):
        event_type = event['type']
        event_value = event['value']
        try:
            sw = self.switches[event_value]
            if 'time' in event:
                sw.hw_timestamp = event['time']
        except KeyError:
            self.logger.warning("Received switch event but couldn't find switch %s." % event_value)
            return

        if sw.debounce:
            recvd_state = event_type == pinproc.EventTypeSwitchClosedDebounced
        else:
            recvd_state = event_type == pinproc.EventTypeSwitchClosedNondebounced

        if sw.state != recvd_state:
            sw.set_state(recvd_state)
            self.logger.info("%s:\t%s\t(%s)", sw.name, sw.state_str(),event_type)
            self.modes.handle_event(event)
            sw.reset_timer()
        else:
            #self.logger.warning("DUPLICATE STATE RECEIVED, IGNORING: %s:\t%s", sw.name, sw.state_str())
            pass

    def burst_event(self, event):
        pass

    def update_lamps(self):
        for mode in reversed(self.modes.modes):
            mode.update_lamps()

    def end_run_loop(self):
        """Called by the programmer when he wants the run_loop to end"""
        self.done = True

    def log(self, line):
        """Deprecated; use :attr:`logger` to log messages."""
        self.logger.info(line)

    def get_events(self):
        """Called by :meth:`run_loop` once per cycle to get the events to process during
        this cycle of the run loop.
        """
        events = []
        events.extend(self.proc.get_events())
        if not self.use_proc_dmd:
            events.extend(self.get_virtualDMDevents()) # MJO: changed to support fake DMD w/o h/w DMD
        return events

    def tick_virtual_drivers(self):
        for coil in self.coils:
            coil.tick()
        for lamp in self.lamps:
            lamp.tick()
        for led in self.leds:
            led.tick()


    def LED_event(self):
        if self.LEDs:
            self.LEDs.update()


    # MJO: added to support virtual DMD only (i.e., without hardware)
    last_dmd_event = 0.0
    frames_per_second = 30
    rem_frames = 0.0
    def get_virtualDMDevents(self):
        """ Get all switch and DMD events since the last time this was called. """
        events = []
        now = time.time()

        frame_interval = float(1/float(self.frames_per_second))
        seconds_since_last_dmd_event = now - self.last_dmd_event

        f_frames_past = float(seconds_since_last_dmd_event / float(frame_interval))

        f_full_frames = f_frames_past  + float(self.rem_frames)
        i_full_frames = int(f_full_frames)

        i_full_frames = min(i_full_frames, 16)
        missed_dmd_events = i_full_frames

        if missed_dmd_events > 0:
            self.rem_frames = f_full_frames-i_full_frames
            if(missed_dmd_events>1):
                pass
                # print ("-----")
                # print("DMDMDMDMDMD FRAMES PAST (by time): " + str(f_frames_past))
                # print("DMDMDMDMDMD rem FRAMES: " + str(self.rem_frames))
                # print("DMDMDMDMDMD missed FRAMES: " + str(i_full_frames))
                # print("DMDMDMDMDMD CARRY FRAMES: " + str(self.rem_frames))
            self.last_dmd_event = now
            events.extend([{'type':pinproc.EventTypeDMDFrameDisplayed, 'value':0}] * missed_dmd_events)

        return events

    def run_loop(self, min_seconds_per_cycle=None):
        """Called by the programmer to read and process switch events until interrupted."""
        loops = 0
        self.done = False
        self.last_dmd_event = time.time()
        self.run_started = self.last_dmd_event
        self.dmd_updates = 0
        self.dmd_event()
        try:
            while self.done == False:

                if min_seconds_per_cycle:
                    t0 = time.time()

                loops += 1
                for event in self.get_events():
                    self.process_event(event)
                self.tick()
                self.tick_virtual_drivers()
                self.modes.tick()
                self.LED_event()
                if self.proc:
                    self.proc.watchdog_tickle()
                    self.proc.flush()
                if self.modes.changed:
                    self.modes.logger.info("Modes changed in last run loop cycle, now:")
                    self.modes.log_queue()
                    self.modes.changed = False

                if min_seconds_per_cycle:
                    dt = time.time() - t0
                    if min_seconds_per_cycle > dt:
                        time.sleep(min_seconds_per_cycle - dt)
        finally:
            if loops != 0:
                dt = time.time()-self.t0
                dd = time.time() - self.run_started
                self.logger.info("\nTotal Time: %0.3f Seconds",dt)
                self.logger.info("Loops: " + str(loops))
                if(dd > 0):
                    self.logger.info("Overall loop rate: %0.3fHz", (loops/dd))
                    self.logger.info("Frame rate: %0.3fFPS", (self.dmd_updates/dd))
                if(self.dmd_updates>0):
                    self.logger.info("DMD Updates: %s", str(self.dmd_updates))
                    self.logger.info("loops between dmd updates: %0.3f", (loops/self.dmd_updates))

                #unload OSC server
                try:
                    self.osc.OSC_shutdown()
                except:
                    pass

