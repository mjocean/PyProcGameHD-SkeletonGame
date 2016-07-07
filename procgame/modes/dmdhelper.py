import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from ..game import Mode
from .. import dmd
from ..dmd import TransitionLayer
from ..dmd import Transition
from ..dmd import HDTextLayer
from ..dmd import HDFont
from procgame.yaml_helper import value_for_key

class DMDHelper(Mode):
    """A mode that displays a message to the player on the DMD"""
    msgfont = None
    
    def __init__(self, game):
        super(DMDHelper, self).__init__(game=game, priority=12)
        self.timer_name = 'message_display_ended'
        self.msgfont = self.game.fonts['med']
        pass

    def msg_over(self):
        self.layer = None
    
    def genMsgFrame(self, msg, background_layer=None, font_style=None, font_key=None, opaque=False, flashing=False):
        if(font_style is None):
            font_style = dmd.HDFontStyle()
        elif(isinstance(font_style,basestring)):
            font_style = self.game.fontstyles[font_style]
        if(font_key is None):
            font = self.msgfont
        else:
            font = self.game.fonts[font_key]

        if(isinstance(msg, list)):
            num_lines = len(msg)
            t_layers = []
            i = 1
            for line in msg:
                if (line != ""):
                    tL = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height*i/(num_lines+1), font, "center", vert_justify="center", opaque=False, width=self.game.dmd.width, height=100,line_color=font_style.line_color, line_width=font_style.line_width, interior_color=font_style.interior_color,fill_color=font_style.fill_color).set_text(line, blink_frames=flashing)
                    t_layers.append(tL)
                i = i + 1
            t = dmd.GroupedLayer(self.game.dmd.width, self.game.dmd.height, t_layers)
        else:
            t = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, font, "center",  vert_justify="center",opaque=False, width=self.game.dmd.width, height=100,line_color=font_style.line_color, line_width=font_style.line_width, interior_color=font_style.interior_color,fill_color=font_style.fill_color).set_text(msg, blink_frames=flashing)

        if(background_layer is None):
            t.opaque = opaque
            return t
        else:
            t.opaque = opaque
            t.composite_op = "blacksrc"
            # t = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height/4, self.msgfont, "center", opaque=False).set_text(msg)    
            # t = TransitionLayer(layerA=None, layerB=txt, transitionType=Transition.TYPE_CROSSFADE, transitionParameter=None)

            if(isinstance(background_layer, list)):
                lAnimations = [self.game.animations[animation_key] for animation_key in background_layer]
                for each_anim in lAnimations:
                    each_anim.reset()
                lAnimations.append(t)
                # lAnimations[0].opaque=True
                gl = dmd.GroupedLayer(self.game.dmd.width, self.game.dmd.height, lAnimations)
            else:
                # self.game.animations[background_layer].opaque=True
                self.game.animations[background_layer].reset()
                gl = dmd.GroupedLayer(self.game.dmd.width, self.game.dmd.height, [self.game.animations[background_layer],t])
            gl.opaque = opaque
            return gl

    def showMessage(self, msg, background_layer=None, font_style=None, opaque=False, duration=2.0, font_key=None, flashing=False):
        self.layer = self.genMsgFrame(msg, background_layer=background_layer, font_style=font_style, opaque=opaque, font_key=font_key, flashing=flashing)
        self.message = msg
                
        #cancel any old outstanding timers 
        self.cancel_delayed(name=self.timer_name)

        #create a new timer
        self.delay(name=self.timer_name,
                   event_type=None,
                   delay=duration,
                   handler=self.msg_over)


    def generateTextLayerFromYaml(self, yaml_struct):
        """ parses a text descriptor format yaml and generates a text layer to be filled with text via set_text() 
              For now, the score_display.yaml example(s) should suffice; better documentation forthcoming
        """
        enabled = value_for_key(yaml_struct, 'enabled', True)
        if(not enabled):
            return None

        # get font
        fname = value_for_key(yaml_struct, 'font')
        if(fname is None):
            raise ValueError, "yaml refers to a font '%s' that does not exist.  Please check the assetList to ensure this font is present [%s]" % (fname, yaml_struct)

        f = self.game.fonts[fname]
        if(fname not in self.game.fonts):
            raise ValueError, "yaml refers to a font '%s' that does not exist.  Please check the assetList to ensure this font is present" % fname

        # get font style
        font_style = value_for_key(yaml_struct, 'font_style')
        if(isinstance(font_style,dict)):
            # dive deeper into this struct, making a new font_style on the fly for the user
            ic = value_for_key(font_style, 'interior_color')
            lc = value_for_key(font_style, 'line_color')
            lw = value_for_key(font_style, 'line_width')
            k = value_for_key(font_style, 'key')
            font_style = dmd.HDFontStyle( interior_color=ic, 
                                    line_width=lw, 
                                    line_color=lc )
            #self.fontstyles[k] = font_style

        elif(isinstance(font_style,basestring)):
            font_style=self.game.fontstyles[font_style]
        else:
            # no font style specified or value is none
            font_style = None

        # get positional data
        location = value_for_key(yaml_struct, 'location')
        if(location is None):
            # no location data -- log an error and use the center of the display
            raise ValueError, "No location information found in Yaml block."
        else:
            x = value_for_key(location, 'x', 0.5)
            y = value_for_key(location, 'y', 0.5)
            vj = value_for_key(location, 'v_justify', "center")
            hj = value_for_key(location, 'h_justify', "center")

            if(isinstance(x,int)):
                # offset values -- use the values as given unless negative!
                if(x < 0):
                    x = self.game.dmd.width - x
                pass
            elif(isinstance(x,float)):
                # percentage values - set to appropriate percentage of display width
                x = self.game.dmd.width * x

            if(isinstance(y,int)):
                # offset values -- use the values as given unless negative!
                if(y < 0):
                    y = self.game.dmd.height - y
                pass
            elif(isinstance(y,float)):
                # percentage values - set to appropriate percentage of display height
                y = self.game.dmd.height * y

        # create the layer -- it matters if we have an HD font or not...
        if(isinstance(f,HDFont)):
            tL = dmd.HDTextLayer(x=x, y=y, font=f, justify=hj, vert_justify=vj, opaque=False, width=None, height=None)
            tL.style = font_style            
        else:
            tL = dmd.TextLayer(x=x, y=y, font=f, justify=hj, opaque=False, width=None, height=None, fill_color=None) 
        
        tL.enabled = value_for_key(yaml_struct,"visible",True)
        return tL


    def genLayerFromYAML(self, yamlStruct):
        duration = None
        lampshow = None
        sound = None
        lyrTmp = None

        if('Combo' in yamlStruct):
            v = yamlStruct['Combo']

            fsV = value_for_key(v, 'FontStyle')
            if(fsV is not None):
                font_style=self.game.fontstyles[fsV]
            else:
                font_style=None
            lyrTmp = self.genMsgFrame(value_for_key(v,'Text'), value_for_key(v,'Animation'), font_key=value_for_key(v,'Font'), font_style=font_style)
            duration = value_for_key(v,'duration')
        elif ('Animation' in yamlStruct):
            v = yamlStruct['Animation']
            lyrTmp = self.game.animations[value_for_key(v,'Name')]
            lyrTmp.reset()
            duration = lyrTmp.duration()

        if(v is not None):
            lampshow = value_for_key(v, 'lampshow')
            sound = value_for_key(v, 'sound')

        return (lyrTmp, duration, lampshow, sound)


