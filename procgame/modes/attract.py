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
                    for rec in self.game.get_highscore_data():
                        if fields is not None:
                            records = [rec[f] for f in fields]
                        else:
                            records = [rec['category'], rec['player'], rec['score']]
                        lyrTmp = self.game.generateLayer(records, value_for_key(v,'Background'), font_key=value_for_key(v,'Font'))

                        if(lampshow is not None):
                            self.shows.append(lampshow)
                            sl.append(lyrTmp, duration, callback=self.next_show)
                            lampshow = None
                        else:
                            sl.append(lyrTmp, duration)

                else:
                    (lyrTmp,duration, lampshow) = self.game.genLayerFromYAML(l)

                    if(lampshow is not None):
                        self.shows.append(lampshow)
                        sl.append(lyrTmp, duration, callback=self.next_show)
                    else:
                        sl.append(lyrTmp, duration)

        sl.opaque=True
        self.layer = sl

    def reset(self):
        self.game.sound.fadeout_music()
        self.show = 0
        if(self.layer is not None):
            self.layer.reset()
        pass

    def next_show(self):
        self.game.log("Attract: Playing NEXT show: %s" % self.shows[self.show])
        self.game.lampctrl.play_show(self.shows[self.show],  repeat=True)
        self.show += 1 
        self.show = self.show % len(self.shows)
        
    def mode_started(self):
        # self.game.sound.play_music('main_theme')
        self.reset()
        pass

    def mode_stopped(self):
        self.game.lampctrl.stop_show()
        self.game.disableAllLamps()
        pass 

        

