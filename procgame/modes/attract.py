import procgame.game
from ..game import Mode
from .. import dmd
from ..dmd import TransitionLayer, Transition
from ..dmd import HDFont, HDFontStyle
import yaml
from procgame.yaml_helper import value_for_key

class Attract(Mode):
    """A mode that runs whenever the attract show is in progress."""
    def __init__(self, game, yaml_file='config/attract.yaml'):
        super(Attract, self).__init__(game=game, priority=9)


        self.shows = []
        self.show = 0
        self.sounds = []
        self.sound = 0

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
                if ('HighScores' in l):
                    v = l['HighScores']
                    fields = value_for_key(v,'Order')
                    duration =  value_for_key(v,'duration', 2.0)
                    lampshow = value_for_key(v, 'lampshow')
                    sound = value_for_key(v, 'sound')
                    for rec in self.game.get_highscore_data():
                        if fields is not None:
                            records = [rec[f] for f in fields]
                        else:
                            records = [rec['category'], rec['player'], rec['score']]
                        lyrTmp = self.game.generateLayer(records, value_for_key(v,'Background'), font_key=value_for_key(v,'Font'), font_style=value_for_key(v,'FontStyle'))

                        if(lampshow is not None):
                            self.shows.append(lampshow)
                            sl.append(lyrTmp, duration, callback=self.next_show)
                            lampshow = None
                        else:
                            sl.append(lyrTmp, duration)

                else:
                    (lyrTmp, duration, lampshow, sound) = self.game.genLayerFromYAML(l)

                    cb = None
                    if(lampshow is not None and sound is not None):
                        self.shows.append(lampshow)
                        self.sounds.append(sound)
                        cb = self.next_both
                    elif(lampshow is not None):
                        self.shows.append(lampshow)
                        cb = self.next_show
                    elif(sound is not None):
                        self.sounds.append(sound)
                        cb = self.next_sound

                    sl.append(lyrTmp, duration, callback=cb)

        sl.opaque=True
        self.layer = sl

    def reset(self):
        self.game.sound.fadeout_music()
        self.show = 0
        if(self.layer is not None):
            self.layer.reset()
        pass

    def sw_flipperLwL_active_for_250ms(self, sw):
        self.layer.force_next(False)
        return False

    def sw_flipperLwR_active_for_250ms(self, sw):
        self.layer.force_next(True)
        return False

    def next_both(self):
        self.next_show()
        self.next_sound()

    def next_show(self):
        self.game.log("Attract: Playing next lampshow: %s" % self.shows[self.show])
        self.game.lampctrl.play_show(self.shows[self.show],  repeat=True)
        self.show += 1 
        self.show = self.show % len(self.shows)

    def next_sound(self):
        self.game.log("Attract: Playing next sound: %s" % self.sounds[self.sound])
        self.game.sound.play(self.sounds[self.sound])
        self.sound += 1 
        self.sound = self.sound % len(self.sounds)
        
    def mode_started(self):
        # self.game.sound.play_music('main_theme')
        self.reset()
        pass

    def mode_stopped(self):
        self.game.lampctrl.stop_show()
        self.game.disableAllLamps()
        pass 

        

