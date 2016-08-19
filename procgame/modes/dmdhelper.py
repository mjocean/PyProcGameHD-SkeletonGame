import logging

from ..game import Mode
from .. import dmd
from ..dmd import TransitionLayer
from ..dmd import Transition
from ..dmd import HDTextLayer
from ..dmd import HDFont
from ..dmd import RandomizedLayer
from ..dmd import AnimatedLayer
from procgame.yaml_helper import value_for_key

class DMDHelper(Mode):
    """A mode that displays a message to the player on the DMD"""
    msgfont = None
    
    def __init__(self, game):
        super(DMDHelper, self).__init__(game=game, priority=12)
        self.logger = logging.getLogger('dmdhelper')
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
        elif(type(font_key) is str):
            font = self.game.fonts[font_key]
        else:
            font = font_key

        if(isinstance(msg, list)):
            num_lines = len(msg)
            t_layers = []
            i = 1
            for line in msg:
                if (line != ""):
                    line = str(line)
                    tL = dmd.HDTextLayer(self.game.dmd.width/2, self.game.dmd.height*i/(num_lines+1), font, "center", vert_justify="center", opaque=False, width=self.game.dmd.width, height=100,line_color=font_style.line_color, line_width=font_style.line_width, interior_color=font_style.interior_color,fill_color=font_style.fill_color).set_text(line, blink_frames=flashing)
                    t_layers.append(tL)
                i = i + 1
            t = dmd.GroupedLayer(self.game.dmd.width, self.game.dmd.height, t_layers)
        else:
            if(msg is not None):
                msg = str(msg)
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

    def __parse_relative_num(self, yaml_struct, key, relative_to, default, relative_match=None):
        """ parses the key from the given yaml_struct and computes
            its value relative to the value passed for relative_to

            if a positive int is specified, the value is taken as-is
            if a negative int is specified, the value is taken as offset from the relative value
            if a float is specified the value is taken as a percentage of the relative value
            if a string value matching the key is specified, the relative value is returned
                (equiv to specifying 1.0 as 100%)
        """
        if(relative_match is None):
            relative_match = key

        tmp = value_for_key(yaml_struct, key, default)
        if(isinstance(tmp,int)):
            # offset values -- use the values as given unless negative!
            if(tmp < 0):
                tmp = relative_to + tmp
            pass
        elif(isinstance(tmp,float)):
            # percentage values - set to appropriate percentage of 'relative_to' value
            tmp = relative_to * tmp
        elif(isinstance(tmp, basestring) and (tmp==relative_match)):
            tmp = relative_to
        return tmp

    def __parse_position_data(self, yaml_struct, for_text=False):
        """ returns a tuple of x/y values for placement or x/y/horiz_justify/vert_justify
            if for_text is True; expects data to be found in yaml_struct.
            Fallback values are different for_text (centered) vs. other types of
            content (top left -- 0,0)
        """
        
        if(for_text):
            fallback = 0.5
        else:
            fallback = int(0)

        x = self.__parse_relative_num(yaml_struct, key='x', relative_to=self.game.dmd.width, default=fallback, relative_match="width")
        y = self.__parse_relative_num(yaml_struct, key='y', relative_to=self.game.dmd.height, default=fallback, relative_match="height")

        if(for_text):
            vj = value_for_key(yaml_struct, 'v_justify', "center")
            hj = value_for_key(yaml_struct, 'h_justify', "center")
            return (x,y,hj,vj)
        return (x,y)

    def __parse_font_data(self, yaml_struct, required=True):
        """ returns a Font and FontStyle as loaded from a yaml based descriptor of
            Font and FontStyle information. """
        # get font
        fname = value_for_key(yaml_struct, 'font', value_for_key(yaml_struct, 'Font'))
        if(fname is None):
            if(required):
                raise ValueError, "Cannot find required Font tag in yaml segment [%s]" % (yaml_struct)
            else:
                f = None 
        else:
            if(fname not in self.game.fonts):
                self.logger.error("yaml refers to a font '%s' that does not exist.  Please check the assetList to ensure this font is present" % fname)

            # the assetManager will take care of providing a default font even if the above doesn't work
            f = self.game.fonts[fname]

        # get font style
        font_style = value_for_key(yaml_struct, 'font_style', value_for_key(yaml_struct, 'FontStyle'))
        if(isinstance(font_style,dict)):
            # dive deeper into this struct, making a new font_style on the fly for the user
            ic = value_for_key(font_style, 'interior_color')
            lc = value_for_key(font_style, 'line_color')
            lw = value_for_key(font_style, 'line_width')
            # k = value_for_key(font_style, 'key')
            font_style = dmd.HDFontStyle( interior_color=ic, 
                                    line_width=lw, 
                                    line_color=lc )
            #self.fontstyles[k] = font_style

        elif(isinstance(font_style,basestring)):
            font_style=self.game.fontstyles[font_style]
        else:
            # no font style specified or value is none
            font_style = None

        return f, font_style

    def generateTextLayerFromYaml(self, yaml_struct):
        """ parses a text descriptor format yaml and generates a text layer to be filled with text via set_text() 
              For now, the score_display.yaml example(s) should suffice; better documentation forthcoming
        """
        enabled = value_for_key(yaml_struct, 'enabled', True)
        if(not enabled):
            return None

        (f, font_style) = self.__parse_font_data(yaml_struct)
        (x,y,hj,vj) = self.__parse_position_data(yaml_struct, for_text=True)
        opaque = value_for_key(yaml_struct, 'opaque', False)

        # create the layer -- it matters if we have an HD font or not...
        if(isinstance(f,HDFont)):
            tL = dmd.HDTextLayer(x=x, y=y, font=f, justify=hj, vert_justify=vj, opaque=opaque, width=None, height=None)
            tL.style = font_style            
        else:
            tL = dmd.TextLayer(x=x, y=y, font=f, justify=hj, opaque=opaque, width=None, height=None, fill_color=None) 
              
        tL.enabled = value_for_key(yaml_struct,"visible",True)

        return tL


    def genLayerFromYAML(self, yamlStruct):
        """ a helper that parses the 'attract sequence' format -- an augmented version
            of the yaml serialized layer format, however also includes coordination 
            of lampshows and sound playback """

        duration = None
        lampshow = None
        sound = None
        lyrTmp = None
        v = None
        try:
            if ('HighScores' in yamlStruct):
                v = yamlStruct['HighScores']

                fields = value_for_key(v,'Order')
                duration =  value_for_key(v,'duration', 2.0)
                lampshow = value_for_key(v, 'lampshow')
                sound = value_for_key(v, 'sound')
                (fnt, font_style) = self.__parse_font_data(v, required=False)

                background = value_for_key(v,'Background', value_for_key(v,'Animation'))

                lyrTmp = dmd.ScriptlessLayer(self.game.dmd.width,self.game.dmd.height)
                entry_ct = len(self.game.get_highscore_data())
                for rec in self.game.get_highscore_data():
                    if fields is not None:
                        records = [rec[f] for f in fields]
                    else:
                        records = [rec['category'], rec['player'], rec['score']]
                    lT = self.genMsgFrame(records, background, font_key=fnt, font_style=font_style)

                    lyrTmp.append(lT, duration)

                duration = entry_ct*duration

            elif('LastScores' in yamlStruct):
                v = yamlStruct['LastScores']

                duration =  value_for_key(v,'duration', 2.0)
                lampshow = value_for_key(v, 'lampshow')
                sound = value_for_key(v, 'sound')

                (fnt, font_style) = self.__parse_font_data(v, required=False)

                last_score_count = len(self.game.old_players)

                if(last_score_count==0):
                    return None

                background = value_for_key(v,'Background', value_for_key(v,'Animation'))

                lyrTmp = dmd.ScriptlessLayer(self.game.dmd.width,self.game.dmd.height)
                lyrTmp.append(self.genMsgFrame(["Last Game","Final Scores"], background, font_key=fnt, font_style=font_style), duration)

                for player in self.game.old_players:
                    lT = self.genMsgFrame([player.name, self.game.score_display.format_score(player.score)], background,  font_key=fnt, font_style=font_style)
                    lyrTmp.append(lT, duration)

                duration = (last_score_count+1)*duration

            elif('RandomText' in yamlStruct):
                v = yamlStruct['RandomText']
                (fnt, font_style) = self.__parse_font_data(v, required=False)
                randomText = value_for_key(v,'TextOptions', exception_on_miss=True)
                headerText = value_for_key(v,'Header', None)
                duration = value_for_key(v,'duration')

                rndmLayers = []
                for line in randomText:
                    selectedRandomText = line['Text']
                    if(type(selectedRandomText) is list):
                        completeText = selectedRandomText
                    else:
                        completeText = [selectedRandomText]

                    if (headerText is not None):
                        completeText[:0] = [headerText] # prepend the header text entry at the start of the list

                    rndmLayers.append(self.genMsgFrame(completeText, value_for_key(v,'Animation'), font_key=fnt, font_style=font_style))

                if(len(rndmLayers) > 0):
                    lyrTmp = RandomizedLayer(layers=rndmLayers)            
            else:
                lyrTmp = self.generateLayerFromYaml(yamlStruct) # not sure what this is, let the other method parse it
                v = yamlStruct[yamlStruct.keys()[0]]    # but we reach in and grab it to pull duration, lampshow and sound.
                duration = value_for_key(v,'duration',None)

            if(v is not None):
                lampshow = value_for_key(v, 'lampshow')
                sound = value_for_key(v, 'sound')

        except Exception, e:
            current_tag = None
            if(yamlStruct is not None and len(yamlStruct.keys())>0):
                current_tag = yamlStruct.keys()[0]
            self.logger.critical("YAML processing failure occured within tag '%s' of yaml section: \n'%s'" % (current_tag,yamlStruct))
            raise e

        return (lyrTmp, duration, lampshow, sound)

    def generateLayerFromYaml(self, yaml_struct):
        """ a helper to generate Display Layers given properly formatted YAML """
        new_layer = None

        if(yaml_struct is None or (isinstance(yaml_struct,basestring) and yaml_struct=='None')):
            return None

        try:
            if('display' in yaml_struct ):
                yaml_struct = yaml_struct['display']
                return self.generateLayerFromYaml(yaml_struct)

            elif('Combo' in yaml_struct):
                v = yaml_struct['Combo']

                (fnt, font_style) = self.__parse_font_data(v, required=False)
                msg = value_for_key(v,'Text')
                if(msg is None):
                    self.logger.warning("Processing YAML, Combo section contains no 'Text' tag.  Consider using Animation instead.")

                new_layer = self.genMsgFrame(msg, value_for_key(v,'Animation'), font_key=fnt, font_style=font_style)
                
            elif ('Animation' in yaml_struct):
                v = yaml_struct['Animation']
                
                new_layer = self.game.animations[value_for_key(v,'Name', value_for_key(v,'Animation'), exception_on_miss=True)]
                new_layer.reset()
                
                if(value_for_key(v,'duration') is None): # no value found, set it so it will be later.
                    v['duration'] = new_layer.duration()

            elif('sequence_layer' in yaml_struct):                
                v = yaml_struct['sequence_layer']
                
                new_layer = dmd.ScriptlessLayer(self.game.dmd.width,self.game.dmd.height)
                repeat = value_for_key(v, 'repeat', True)

                for c in v['contents']:
                    if not 'item' in c:
                        raise ValueError, "malformed YAML file; sequence must contain a list of 'item's"
                    c = c['item']
                    l = self.generateLayerFromYaml(c)
                    if(hasattr(l,'duration') and callable(l.duration)):
                        def_duration = l.duration()
                    else:
                        def_duration = 2.0
                    d = value_for_key(c,'duration',def_duration)
                    new_layer.append(l,d)
                #sl.set_target_position(x, y)
                new_layer.hold = not repeat
            
            elif('panning_layer' in yaml_struct):
                v = yaml_struct['panning_layer']

                w = self.__parse_relative_num(v, 'width', self.game.dmd.width, None)
                h = self.__parse_relative_num(v, 'height', self.game.dmd.height, None)

                origin_x = value_for_key(v,'origin_x',0)
                origin_y = value_for_key(v,'origin_y',0)
                scroll_x = value_for_key(v,'scroll_x', exception_on_miss=True)
                scroll_y = value_for_key(v,'scroll_y', exception_on_miss=True)
                frames_per_movement = value_for_key(v,'frames_per_movement', 1)
                bounce = value_for_key(v,'bounce',False)

                c = self.generateLayerFromYaml(value_for_key(v,'contents', exception_on_miss=True))

                new_layer = dmd.PanningLayer(width=w, height=h, frame=c, origin=(origin_x, origin_y), translate=(scroll_x, scroll_y), numFramesDrawnBetweenMovementUpdate=frames_per_movement, bounce=bounce)

            elif('group_layer' in yaml_struct):
                v = yaml_struct['group_layer']

                (x,y) = self.__parse_position_data(v)

                w = self.__parse_relative_num(v, 'width', self.game.dmd.width, None)
                h = self.__parse_relative_num(v, 'height', self.game.dmd.height, None)

                contents = value_for_key(v,'contents', exception_on_miss=True)
                opaque = value_for_key(v, 'opaque', None)
                fill_color = value_for_key(v, 'fill_color', None)

                lyrs = []

                duration = 0
                for c in contents:
                    l = self.generateLayerFromYaml(c)
                    lyrs.append(l)
                    if(hasattr(l,'duration') and callable(l.duration)):
                        def_duration = l.duration()
                    else:
                        def_duration = 0.0
                    d = value_for_key(c,'duration',def_duration)
                    duration=max(d,duration)

                new_layer = dmd.GroupedLayer(w, h, lyrs, fill_color=fill_color)
                if(opaque):
                    new_layer.opaque = opaque
                new_layer.set_target_position(x, y)

            elif('animation_layer' in yaml_struct):
                v = yaml_struct['animation_layer']

                (x,y) = self.__parse_position_data(v)

                source_layer = self.game.animations[value_for_key(v,'name',value_for_key(v,'Name'), exception_on_miss=True)]

                opaque = value_for_key(v, 'opaque', source_layer.opaque)
                repeat = value_for_key(v, 'repeat', source_layer.repeat)
                hold_last_frame = value_for_key(v, 'hold_last_frame', source_layer.hold)

                frame_list = value_for_key(v, 'frame_list', {})
                
                if(len(frame_list)==0):
                    new_layer = source_layer
                else:
                    new_layer = AnimatedLayer(frame_time=source_layer.frame_time, frames=[source_layer.frames[idx] for idx in frame_list])

                new_layer.opaque=opaque
                new_layer.repeat = repeat
                new_layer.hold = (hold_last_frame or len(frame_list)==1)

                new_layer.reset()
                new_layer.set_target_position(x, y)

            elif ('text_layer' in yaml_struct):
                v = yaml_struct['text_layer']

                new_layer = self.generateTextLayerFromYaml(v)
                txt = value_for_key(v,'Text', exception_on_miss=True) 

                w = self.__parse_relative_num(v, 'width', self.game.dmd.width, default=None)
                h = self.__parse_relative_num(v, 'height', self.game.dmd.height, default=None)

                blink_frames = value_for_key(v,'blink_frames', None) 

                new_layer.set_text(txt, blink_frames=blink_frames)

                if(w is None):
                    new_layer.width = new_layer.text_width
                if(h is None):
                    new_layer.height = new_layer.text_height

                # fill_color = value_for_key(v,'fill_color',(0,0,0))

            elif ('markup_layer' in yaml_struct):
                v = yaml_struct['markup_layer']

                w = self.__parse_relative_num(v, 'width', self.game.dmd.width, None)
                (bold_font, bold_style) = self.__parse_font_data(value_for_key(v, 'Bold', exception_on_miss=True))
                (plain_font, plain_style) = self.__parse_font_data(value_for_key(v, 'Normal', exception_on_miss=True))
                txt = value_for_key(v, "Message", exception_on_miss=True)
                if(isinstance(txt,list)):
                    txt = "\n".join(txt)

                gen = dmd.MarkupFrameGenerator(game=self.game, font_plain=plain_font, font_bold=bold_font, width=w)
                gen.set_bold_font(bold_font, interior_color=bold_style.interior_color, border_width=bold_style.line_width, border_color=bold_style.line_color)
                gen.set_plain_font(plain_font, interior_color=plain_style.interior_color, border_width=plain_style.line_width, border_color=plain_style.line_color)

                frm = gen.frame_for_markup(txt)
                new_layer = dmd.FrameLayer(frame=frm)

            else:
                unknown_tag = None
                if(yaml_struct is not None and len(yaml_struct.keys())>0):
                    unknown_tag = yaml_struct.keys()[0]
                raise ValueError, "Unknown tag '%s' in yaml section.  Check spelling/caps/etc." % (unknown_tag)

        except Exception, e:
            current_tag = None
            if(yaml_struct is not None and len(yaml_struct.keys())>0):
                current_tag = yaml_struct.keys()[0]
            self.logger.critical("YAML processing failure occured within tag '%s' of yaml section: \n'%s'" % (current_tag,yaml_struct))
            raise e


        return new_layer
