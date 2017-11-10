### A new playback engine for playing RGB based
### lampshows.
#######
import re
import logging
import sys
from procgame.game import Mode
from procgame.game.advancedmode import AdvancedMode

class RgbShowPlayer(AdvancedMode):  
    def __init__(self, game, priority=3):
        super(RgbShowPlayer, self).__init__(game, priority, mode_type=AdvancedMode.System)
        self.logger = logging.getLogger("RgbShowPlayer")
        self.shows = {}
        self.active_shows = []
        self.prior_lamp_states = {}

    def load(self, key, filename):
        # load the show
        self.shows[key] = RgbShow(self.game, key, filename)

    def stop(self, key, cleanup=False):
        if(key not in self.active_shows):
            self.logger.info("suppressing request to stop inactive show: %s" % key)
            return

        if(cleanup):
            self.shows[key].restart()
        
        self.shows[key].stop()
        self.cancel_delayed(name=key)
        self.active_shows.remove(key)

    def stop_all(self):
        for key in self.active_shows:
            self.shows[key].stop()
            self.cancel_delayed(name=key)
        
        self.active_shows = []

    def restart(self, key):
        if(key not in self.active_shows):
            self.logger.info("suppressing request to restart inactive show: %s" % key)
            return

        self.shows[key].restart()

    def play_show(self, key, repeat=None, callback=None, save_state=True):
        """ plays an RgbShow -- if non-repeating, the callback function will be called on completion
            use repeat to override the behavior described in the show file 
        """
        if(key not in self.shows):
            self.logger.info("suppressing request to play unknown show: %s" % key)
            return

        if(key in self.active_shows):
            self.logger.info("suppressing request to play already active show: %s" % key)
            return

        # TODO: determine which lamps are already in use and disable them...
        self.logger.info("Show '%s' is starting." % key)

        if(save_state):
            self.save_state(key)
            self.shows[key].set_callback(self.restore_state, key)
        self.active_shows.append(key)
        if(repeat is not None):
            self.shows[key].repeat = repeat
        self.shows[key].restart()
        # self.shows[key].debug_show()
        self.__update_show(key)

    def save_state(self, key):
        """ saves the current state of the devices used in the show 'key'
            so they can be restored at the conclusion of playback.  If the
            device already has a saved state, we assume it's already in use
            by another show (and the state was stored at that time), so when 
            playback of this new show finishes that state should be restored.
        """
        if(key not in self.shows):
            self.logger.info("suppressing request to save_state for unknown show: %s" % key)
            return
        device_list = self.shows[key].get_device_list()
        for device in device_list:
            if(device.name not in self.prior_lamp_states):
                if(not callable(device.state)):
                    state = device.state
                else:
                    state = device.state()
                if state['outputDriveTime'] == 0: # only store indef schedules
                    sched = state['timeslots']
                else:
                    sched = 0x0
                r = {'device':device, 'schedule':sched}
                if(hasattr(device,'color')):
                    r['color']=device.color
                # self.logger.info("saving state for device '%s' (%x)" %  (device.name,sched))

                self.prior_lamp_states[device.name] = r

    def restore_state(self, key):
        """ this method is used when a show (identified by key) has finished,
            so that lamps can be restored to their state prior to the playback
            of this show. 
        """
        if(key not in self.shows):
            self.logger.info("suppressing request to restore_state for unknown show: %s" % key)
            return
        device_list = self.shows[key].get_device_list()

        for device in device_list:
            # make sure device isn't in use in another show! 
            if(self.is_device_in_use(device.name, exclude=key)):
                self.logger.info("Not restoring state for device '%s' because it's still in use elsewhere" % device.name)
                pass
            elif(device.name in self.prior_lamp_states):
                # self.logger.info("restoring state for device '%s'" %  device.name)
                r = self.prior_lamp_states[device.name]
                if('color' in r):
                    device.set_color(r['color'])
                device.schedule(r['schedule'])
                if(key not in self.active_shows):
                    del self.prior_lamp_states[device.name]
                
    def is_device_in_use(self, name, exclude=None):
        show_list = self.active_shows[:] 
        if exclude is not None and exclude in show_list:
            show_list.remove(exclude)
        for s in show_list:
            if(self.shows[s].is_device_in_use(name)):
                return True
        return False

    def __update_show(self, key):
        if(key not in self.shows):
            raise ValueError, "request to update unknown show: %s" % key
            return

        if(key not in self.active_shows):
            raise ValueError, "request to update inactive show: %s" % key
            return

        if(self.shows[key].update()):
            # if it returns true, the show is still live
            self.delay(name=key,
                event_type=None,
                delay=(self.shows[key].time)/1000.0, # delay is in seconds...
                handler=self.__update_show,
                param=key)
        else: 
            self.logger.info("Show '%s' is done." % key)
            self.active_shows.remove(key)
            if(len(self.active_shows)==0):
                self.logger.info("all shows done, calling update lamps")
                self.game.update_lamps()
            # show is done
            pass

    def reset(self):
        # TODO: ???
        pass

class RgbShow(object):
    def __init__(self, game, key, filename):
        self.logger = logging.getLogger("rgbShow")
        self.logger.info("loading RgbShow '%s'" % filename)

        self.game = game
        self.color_map = {}
        self.tracks = []
        self.length = 0
        self.hold = False
        self.repeat = False
        self.time = 33
        self.callback_fired = False
        self.callback = None
        self.callback_param = None
        self.now = 0
        self.key = key
        self.shows_over = False

        f = open(filename, 'r')
        for line in f.readlines():
            if (line.lstrip().startswith('#') or line.lstrip().rstrip()==""):
                # comment or blank line, ignore
                pass
            elif(line.lstrip().startswith('!')):
                # header data
                t = line.lstrip()[1:].lstrip()
                k = t[0:1]
                # print("t=%s;k=%s" % (t, k))
                if(t.find('~>')>=0):
                    # FADE TO
                    v = t[t.find("~>")+2:].lstrip().rstrip()
                    v=int(v,16)
                    c = [v >> 16, (v & 0x00ff00) >> 8 , v & 0x0000ff]
                    self.color_map[k] = {'color': c, 'fade': True}
                elif(t.find('=>')>=0):
                    # IMMEDIATE COLOR CHANGE 
                    v = t[t.find("=>")+2:].lstrip().rstrip()
                    if(v=='None'):
                        self.color_map[k] = None
                    else:
                        v=int(v,16)
                        c = [v >> 16, (v & 0x00ff00) >> 8 , v & 0x0000ff]
                        self.color_map[k] = {'color': c, 'fade': False}
                elif(t.find('=')>0):
                    # RGB Show Parameter
                    k = t[:t.find("=")-1].lstrip().rstrip()
                    v = t[t.find("=")+1:].lstrip().rstrip()
                    if(k=="time"):
                        self.time = int(v)
                        pass
                    elif(k=="repeat"):
                        tmp = v.lower()
                        self.repeat = (tmp =='true' or tmp == '1')
                        pass
                    elif(k=="hold"):
                        tmp = v.lower()
                        self.hold = (tmp =='true' or tmp == '1')
                        pass
                    else:
                        raise ValueError, "Could not parse RgbShow header line: '%s'" % line
                else:
                    # bad line!
                    raise ValueError, "Could not parse RgbShow header line: '%s'" % line
                pass
            else:
                # track data
                t = RgbTrack(line, self.color_map, self)
                self.tracks.append(t)
                self.length = t.length

        f.close()        

    def debug_show(self):
        self.logger.info("Show Parameters:")
        self.logger.info("  hold: %s" % self.hold)
        self.logger.info("  repeat: %s" % self.repeat)
        self.logger.info("  time: %s" % self.time)
        self.logger.info("Show Color Map:")
        for k,v in self.color_map.iteritems():
            self.logger.info("%s:%s" % (k, v))
        self.logger.info("Show Tracks:")
        for t in self.tracks:
            self.logger.info("%s: <%s>" % (t.name,str(t)))

    def stop(self):
        self.shows_over = True

    def restart(self):
        self.now = 0
        self.shows_over = False
        for t in self.tracks:
            # t.fn([0,0,0], 0)  # set this lamp's color to black
            # t.device.enable() # turn on the device (schedule-wise)
            pass

    def update(self):
        # self.logger.debug("Show '%s' received update(%d/%d)" % (self.key, self.now, self.length))

        if(self.now < self.length):
            for track in self.tracks:
                track.update(self.now)
            self.now += 1
            return True
        else:
            # if(self.now >= self.length):
            # show is done playing through once, but is it *done*
            if(self.callback is not None and not self.callback_fired):
                self.logger.info("show '%s' is done; calling callback" % self.key)
                self.callback(self.callback_param)
                self.callback_fired = True

            if(self.repeat):
                self.now = 0
                self.callback_fired = False
                return True

            if(self.hold): 
                # reset back to the last frame
                self.now = self.length-1
                return True

            return False

    def is_device_in_use(self, name):
        for t in self.tracks:
            if(t.name == name and t.enabled):
                return True
        return False

    def get_device_list(self):
        """ returns a list of gameitems that are in use by this show """
        devices = []
        for t in self.tracks:
            # if(t.enabled):
            devices.append(t.device)
        return devices

    def set_callback(self, callback_fn, callback_param):
        self.callback = callback_fn;
        self.callback_fired = False
        self.callback_param = callback_param

class RgbTrack(object):
    def __str__(self):
        return "".join([str(t)+":"+str(v)+";" for t,v in enumerate(self.data)])

    def update(self, now):
        # self.logger.debug("Track '%s' received update(%d) [length of the track is (%d)]" % (self.name, now, self.length))

        if(self.enabled):
            if(now >= len(self.data)):
                raise ValueError, "Track '%s' received index '%d' beyond the length of the track (%d)" % (self.name, now, self.length)
            cmd = self.data[now]
            if(cmd is not None):
                cmd.process_command()
                self.device.enable()

    def __init__(self, line, color_map, show):
        self.logger = logging.getLogger("rgbTrack")
        self.data = []
        self.device = None
        self.fn = None
        self.enabled = True # a track may be disabled if it's device is in use by another playing show

        #print line
        line_re = re.compile('\s*(?P<type>\S+\:)?\s*(?P<name>\S+)\s*\| (?P<data>.*)$')

        m = line_re.match(line)
        if m is None:
            raise ValueError("Regexp didn't match on track line: " + line)

        device_type = m.group('type')
        self.name = m.group('name')

        # build function map
        if(device_type is None):
            # auto-detect
            if(self.name in show.game.leds):
                device_type = "led"
                self.device = show.game.leds[self.name]
            elif(self.name in show.game.lamps):
                device_type = "lamp"
                self.device = show.game.lamps[self.name]
            elif(hasattr(show.game, 'wsRGBs') and self.name in show.game.wsRGBs):
                device_type = "rgb"
                self.device = show.game.wsRGBs[self.name]
            else:
                raise ValueError, "RGB Track created for unknown device named '%s'" % self.name

        if(device_type == "lamp"):
            fn = show.game.lamps[self.name].set_color
        elif(device_type == "led"):
            fn = show.game.leds[self.name].color_with_fade
        elif(device_type == "rgb"):
            fn = show.game.wsRGBs[self.name].set_color
        else:
            raise ValueError, "RGB Track created for unknown device named '%s'" % self.name
        self.fn = fn
        self.device_type = device_type

        data = m.group('data')
      
        self.data = [None]* len(data)

        last_color = None
        last_run_starts = 0
        last_run_length = 0

        for i in range(0,len(data),1):
            this_color = data[i]
    
            if(this_color!=last_color):
                # end prev run, start new run
                if(last_color is not None):
                    # save old run
                    cdata = color_map[last_color]
                    if(cdata is None):
                        c = None
                    elif(cdata['fade']):
                        c = RgbCommand(self.name, fn, cdata['color'], last_run_length*show.time)
                    else:
                        c = RgbCommand(self.name, fn, cdata['color'], 0)
                    self.data[last_run_starts] = c
                # start new run
                last_run_length = 0
                last_run_starts = i
            if(i==len(data)-1): # last slot
                if(last_run_length==0) or (last_color==this_color): # just started a new run; so store this run
                    cdata = color_map[this_color]
                    if(cdata is None):
                        c = None
                    elif(cdata['fade']):
                        c = RgbCommand(self.name, fn, cdata['color'], last_run_length*show.time)
                    else:
                        c = RgbCommand(self.name, fn, cdata['color'], 0)
                    self.data[last_run_starts] = c                    
            else:
                # continuing run
                last_run_length += 1
            last_color = this_color
        self.length = len(data)

class RgbCommand(object):
    def __init__(self, name, fn, new_color, transition_time):
        self.new_color = new_color
        self.time = transition_time
        self.name = name
        self.fn = fn

    def __str__(self):
        return "[name=%s color='%s';time='%s']" % (self.name, self.new_color, self.time)

    def process_command(self):
        # print(" doing  %s" % str(self))
        self.fn(self.new_color, self.time)