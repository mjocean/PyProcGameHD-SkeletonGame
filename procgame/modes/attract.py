import procgame.game
from ..game import Mode
from .. import dmd
from ..dmd import TransitionLayer, Transition, RandomizedLayer
from ..dmd import HDFont, HDFontStyle
import yaml
from procgame.yaml_helper import value_for_key

class Attract(Mode):
    """A mode that runs whenever the attract show is in progress."""
    def __init__(self, game, yaml_file='config/attract.yaml'):
        super(Attract, self).__init__(game=game, priority=9)


        self.shows = []
        self.show = 0
        self.sound_keys = []
        self.sound_num = 0

        sl = dmd.ScriptlessLayer(self.game.dmd.width,self.game.dmd.height)

        try:
            values = yaml.load(open(yaml_file, 'r'))
        except yaml.scanner.ScannerError, e:
            self.game.log('Attract mode: Error loading yaml file from %s; the file has a syntax error in it!\nDetails: %s' % (yaml_file, e))
            raise
        except Exception, e:
            self.game.log('Attract mode: Error loading yaml file from %s: %s' % (yaml_file, e))
            raise

        if "Sequence" in values:
            s = values["Sequence"]
            t = 0
            for l in s:
                layer_data = self.game.genLayerFromYAML(l)
                if(layer_data is None):
                    continue

                (lyrTmp, duration, lampshow, sound) = layer_data

                cb = None
                if(lampshow is not None and sound is not None):
                    self.shows.append(lampshow)
                    self.sound_keys.append(sound)
                    cb = self.next_both
                elif(lampshow is not None):
                    self.shows.append(lampshow)
                    self.sound_keys.append(None)
                    cb = self.next_show
                elif(sound is not None):
                    self.shows.append(None)
                    self.sound_keys.append(sound)
                    cb = self.next_sound
                else:
                    self.shows.append(None)
                    self.sound_keys.append(None)
                    cb = self.stop_sounds

                sl.append(lyrTmp, duration, callback=cb)

        sl.opaque=True
        self.layer = sl

    def reset(self):
        self.game.sound.fadeout_music()
        self.show = 0
        if(self.layer is not None):
            self.layer.reset()
        pass

    def sw_flipperLwL_active_for_50ms(self, sw):
        self.layer.force_next(False)
        return False

    def sw_flipperLwR_active_for_50ms(self, sw):
        self.layer.force_next(True)
        return False

    def next_both(self):
        self.next_show()
        self.next_sound()

    def next_show(self):
        """ play the lampshow that corresponds to this specific step in the sequence """
        self.stop_sounds()

        lampshow_key = self.shows[self.layer.script_index]

        self.game.log("Attract: Playing next lampshow: %s" % lampshow_key)
        self.game.lampctrl.play_show(lampshow_key,  repeat=True)

    def next_sound(self):
        """ play the sound that corresponds to this specific step in the sequence """
        sound_key = self.sound_keys[self.layer.script_index]

        self.stop_sounds()

        self.game.log("Attract: Playing next sound: %s" % sound_key)

        if(sound_key in self.game.sound.music):
            if(self.game.user_settings['Machine (Standard)']['Attract Mode Music']=='On'):
                self.game.sound.play_music(sound_key)
        else:
            if(self.game.user_settings['Machine (Standard)']['Attract Mode Sounds']=='On'):
                self.game.sound.play(sound_key)

    def stop_sounds(self):
        """ this is invoked if the next item in the sequence has no sound listed and
            no lampshow listed.  The old lampshow will continue *but* we need to
            stop the last song, if still playing """

        # self.game.log("Attract: stopping audio")
        self.game.sound.fadeout_music() # stop old music if music is already playing
        # would be wise to stop previous sound, too
        # self.game.sound.stop(last_sound_key) # what _is_ the last sound key..?

    def mode_started(self):
        self.reset()
        pass

    def mode_stopped(self):
        self.game.lampctrl.stop_show()
        self.game.disableAllLamps()
        self.game.sound.fadeout_music()
        pass
