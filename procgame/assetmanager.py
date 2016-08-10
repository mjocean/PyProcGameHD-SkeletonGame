from procgame import dmd 
from procgame.dmd.sdl2_displaymanager import sdl2_DisplayManager
import sdl2
"""
"""
import os
import sys
import yaml
import logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
from procgame.yaml_helper import value_for_key

class DictWithDefault(dict):
    # def set_default_miss_key(self, default_miss_key):
    #     self.miss_key = default_miss_key
    def __init__(self, default_miss_key):
        dict.__init__(self)
        self.miss_key = default_miss_key

    def __missing__(self, key):
        logging.error("***ASSET ERROR: An asset with key '%s' has not been loaded.  Using default '%s' instead" % (key, self.miss_key))
        if(not self.miss_key in self):
            raise KeyError("***ASSET ERROR: An asset with key '%s' has not been loaded.  And default '%s' could not be found to be used instead!" % (key, self.miss_key))
        return self[self.miss_key]

class AssetManager(object):
    """ The AssetManager class reads the asset_list.yaml file, loading from it Animations, Fonts, Lampshows, etc.
         the values data structure is loaded from :file:`./config/asset_list.yaml` when this submodule is loaded;
         if not found there, the asset_loader will try :file:`./asset_list.yaml` before giving up.
    """

    values = None
    game = None

    loaded_map = {}
    animations = DictWithDefault(default_miss_key='missing')
    lengths = DictWithDefault(default_miss_key='missing')
    fonts = DictWithDefault(default_miss_key='default')
    sounds = {}
    fontstyles = {}
    numLoaded = 0
    dmd_path =""
    # screen = None
    # pygF = None
    total = ""
    
    def value_for_key_path(self, keypath, default=None):
        return value_for_key(self.values,keypath, default)

    def loadConfig(self, curr_file_path, filename=None):
        if(filename is not None):
            asset_config_path = curr_file_path + "/config/" + filename
        else:
            asset_config_path = curr_file_path + "/config/asset_list.yaml"

        path = asset_config_path
        if not os.path.exists(asset_config_path): # try another location...
            self.logger.warning('No asset configuration file found at %s' % path)

            if(filename):
                asset_config_path = curr_file_path + "/" + filename
            else:
                asset_config_path = curr_file_path + "/asset_list.yaml"
            path = asset_config_path

        if not os.path.exists(asset_config_path):
            self.logger.warning('No asset configuration file found at %s' % path)

            raise ValueError, "No asset configuration file found at '" + path + "'" 

        self.logger.info('asset configuration found at %s' % path)
        try:
            self.values = yaml.load(open(path, 'r'))
        except yaml.scanner.ScannerError, e:
            self.logger.error('Error loading asset config file from %s; your configuration file has a syntax error in it!\nDetails: %s', path, e)
        except Exception, e:
            self.logger.error('Error loading asset config file from %s: %s', path, e)


    def __init__(self, game, yaml_values=None, yaml_file=None):
        super(AssetManager, self).__init__()
        self.logger = logging.getLogger('game.assets')
        self.game = game
        self.dmd_path = game.dmd_path
        # self.screen=game.desktop.screen
        # pygame.font.init()
        # p = pygame.font.match_font('Arial')
        # if(p==None):
        #   raise ValueError, "Specific font could not be found on your system.  Please install '" + fontname + "'."
        ### josh prog par
        # self.pygF = pygame.font.Font(p,32)
        self.screen_height = sdl2_DisplayManager.inst().window_h
        self.screen_width = sdl2_DisplayManager.inst().window_w

        if(yaml_values is not None):
            self.values = yaml_values
        else:
            self.loadConfig(game.curr_file_path,yaml_file)

        splash_file = self.value_for_key_path('UserInterface.splash_screen', None)
        self.rect_color = self.value_for_key_path('UserInterface.progress_bar.border', (120,120,120,255))
        self.inner_rect_color = self.value_for_key_path('UserInterface.progress_bar.fill',(255,84,84,255))
        self.bar_x = self.value_for_key_path('UserInterface.progress_bar.x_center', 0.5)
        self.bar_y = self.value_for_key_path('UserInterface.progress_bar.y_center', 0.25)

        bar_w = self.value_for_key_path('UserInterface.progress_bar.width', 0.8)
        bar_h = self.value_for_key_path('UserInterface.progress_bar.height', 0.15)

        text_y = self.value_for_key_path('UserInterface.text.y_center', 0.15)
        # self.text_font = self.value_for_key_path('UserInterface.text.font', 0.15)
        # self.text_size = self.value_for_key_path('UserInterface.text.size', 0.15)
        self.text_color = self.value_for_key_path('UserInterface.text.color', (255,255,0,255))

        self.prog_bar_width = int(bar_w * self.screen_width)
        self.prog_bar_height = int(bar_h * self.screen_height)

        self.prog_bar_x = int((self.screen_width * self.bar_x) - (self.prog_bar_width/2))
        self.prog_bar_y = int((self.screen_height * self.bar_y) - (self.prog_bar_height/2))

        self.text_y = int(text_y * self.screen_height)

        if(splash_file is not None):
            s = sdl2_DisplayManager.inst().load_surface(game.dmd_path + splash_file)
            self.splash_image = sdl2_DisplayManager.inst().texture_from_surface(s)
            del s
        else:
            self.splash_image = None

        self.load()

    def updateProgressBar(self, displayType,fname):
        if(self.splash_image is not None):
            sdl2_DisplayManager.inst().screen_blit(self.splash_image, expand_to_fill=True)
        else:
            sdl2_DisplayManager.inst().clear((0,0,0,0))


        sdl2_DisplayManager.inst().draw_rect(self.rect_color, (self.prog_bar_x,self.prog_bar_y,self.prog_bar_width,self.prog_bar_height), False)
        percent = int (float(self.numLoaded + 1)/float(self.total) * self.prog_bar_width)

        sdl2_DisplayManager.inst().draw_rect(self.inner_rect_color, (self.prog_bar_x + 2,self.prog_bar_y + 2,percent,self.prog_bar_height-4), True) 

        s = "Loading %s: [%06d] of [%06d]:" % (displayType, self.numLoaded+1,self.total)
        tx = sdl2_DisplayManager.inst().font_render_text(s, font_alias=None, size=None, width=300, color=self.text_color, bg_color=None)
        sdl2_DisplayManager.inst().screen_blit(tx, x=60, y=self.text_y, expand_to_fill=False)

        tx = sdl2_DisplayManager.inst().font_render_text(fname, font_alias=None, size=None, width=300, color=self.text_color, bg_color=None)
        sdl2_DisplayManager.inst().screen_blit(tx, x=80, y=self.text_y+35, expand_to_fill=False)


    #   self.screen.blit(surf,(self.prog_bar_x,self.prog_bar_y + (1.1 * self.prog_bar_height)) )
        sdl2_DisplayManager.inst().flip()

        for event in sdl2.ext.get_events():
            #print("Key: %s" % event.key.keysym.sym)
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    self.game.end_run_loop()
                    sys.exit()
   
        # pygame.display.flip()

    def clearScreen(self):
        self.screen.fill((255,0,0))
        pygame.display.flip()


    def loadIntoCache(self,key,frametime=2,file=None,repeatAnim=False,holdLastFrame=False,  opaque = False, composite_op = None, x_loc =0, y_loc=0, streaming_load=False):
        if(file==None):
            file=key + '.vga.dmd.zip'
        
        self.updateProgressBar("Animations", file)

        tmp = None
        if(self.loaded_map.has_key(file) and not streaming_load):
            tmp = self.animations[self.loaded_map[file]]
            #print("quick loaded '%s'" % key)
        else:
            if(not streaming_load):
                tmp = dmd.Animation().load(self.dmd_path + file , composite_op=composite_op)
            self.loaded_map[file] = key

        if(tmp is not None):
            self.lengths[key] = tmp.frames[-1]
            if(len(tmp.frames)==1):
                holdLastFrame = True
                self.logger.error("Single frame animtation '%s'; setting holdLastFrame to True" % file)

        if(streaming_load):
            self.animations[key] = dmd.MovieLayer(opaque, hold=holdLastFrame, repeat=repeatAnim, frame_time=frametime, movie_file_path=self.dmd_path + file)
        else:
            self.animations[key] = dmd.AnimatedLayer(frames=tmp.frames, frame_time=frametime, repeat=repeatAnim, hold=holdLastFrame) 

        self.animations[key].set_target_position(x_loc, y_loc)
        # if composite_op != None:
        #   self.animations[key].composite_op = composite_op
        self.numLoaded += 1

    def load(self):
        anims = self.value_for_key_path(keypath='Animations', default={}) or list()
        fonts = self.value_for_key_path(keypath='Fonts', default={}) or list()
        hfonts = value_for_key(fonts,'HDFonts',{}) or list()
        rfonts = value_for_key(fonts,'DMDFonts',{}) or list()
        fontstyles = value_for_key(fonts,'FontStyles',{}) or list()
        lamps = self.value_for_key_path(keypath='LampShows', default={}) or list() 
        sounds = self.value_for_key_path(keypath='Audio', default={}) or list()
        music = value_for_key(sounds,'Music',{}) or list()
        effects = value_for_key(sounds,'Effects',{}) or list() 
        voice = value_for_key(sounds,'Voice',{}) or list()
        
        # self.total = str(len(anims)+len(hfonts)+len(rfonts)+len(music)+len(effects)+len(voice))
        self.total = (len(lamps) + len(fontstyles) + len(anims)+len(hfonts)+len(rfonts)+len(music)+len(effects)+len(voice))

        try:
            current = ""            
            for l in lamps:
                k  = value_for_key(l,'key')
                fname = value_for_key(l,'file')
                self.updateProgressBar("Lampshows", fname)
                # self.lampshows = self.game.sound.register_music(k,self.game.music_path+fname, volume=volume)            
                f = self.game.lampshow_path + fname
                current = 'Lampshow: [%s]: %s, %s ' % (k, f, fname)
                self.game.lampctrl.register_show(k, f)

                # Validate the lampshow --as best as possible
                self.game.lampctrl.show.load(f, False, None)
                for tr in self.game.lampctrl.show.lampshow.tracks:
                    if tr.driver == None: # Check drivers.
                        tr.resolve_driver_with_game(self.game)
                    if tr.driver == None:
                        raise ValueError, "Name '%s' specified in lampshow does not match a driver in the machine yaml." % tr.name

                self.numLoaded += 1            
            for f in hfonts:
                k  = value_for_key(f,'key')
                sname = value_for_key(f,'systemName',k)
                size  = value_for_key(f,'size')
                file_path = value_for_key(f, 'file', None)
                self.updateProgressBar("HD Fonts", sname)
                current = 'HD font: [%s]: %s, %d ' % (k, sname, size)

                if(file_path is not None):
                    file_path = self.game.hdfont_path + file_path
                    if(not os.path.isfile(file_path)):
                        raise ValueError, "Could not load font as specified in yaml\n %s\n File [%s] does not exist." % (current, file_path)


                self.fonts[k] = dmd.hdfont_named(sname,size, font_file_path=file_path)
                self.numLoaded += 1

            for f in rfonts:
                k  = value_for_key(f,'key')
                fname = value_for_key(f,'file')
                self.updateProgressBar("DMD Fonts", fname)
                current = 'Font: [%s]: %s ' % (k, fname)
                self.fonts[k] = dmd.font_named(fname)
                self.numLoaded += 1

            for f in fontstyles:
                ic = value_for_key(f, 'interior_color')
                lc = value_for_key(f, 'line_color')
                lw = value_for_key(f, 'line_width')
                k = value_for_key(f, 'key')
                font_style = dmd.HDFontStyle( interior_color=ic, 
                                        line_width=lw, 
                                        line_color=lc )
                self.fontstyles[k] = font_style

            for anim in anims:
                k  = value_for_key(anim,'key')
                ft = value_for_key(anim,'frame_time',2)
                f  = value_for_key(anim,'file')
                r  = value_for_key(anim,'repeatAnim',False)
                h  = value_for_key(anim,'holdLastFrame',False)
                o  = value_for_key(anim,'opaque',False)
                c  = value_for_key(anim,'composite_op')
                x  = value_for_key(anim, 'x_loc', 0)
                y  = value_for_key(anim, 'y_loc', 0)
                streaming_load  = value_for_key(anim, 'streamingMovie', False)
                current = 'Animation: [%s]: %s' % (k, f)
                self.loadIntoCache(k,ft,f,r,h,o,c,x,y,streaming_load)

        except:
            self.logger.error("===ASSET MANAGER - ASSET FAILURE===")
            self.logger.error(current)
            self.logger.error("======")
            raise

        for s in music:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            streaming_load = value_for_key(s,'streaming_load',True)
            self.updateProgressBar("Audio: Music", fname)
            self.game.sound.register_music(k,self.game.music_path+fname, volume=volume) #, streaming_load=streaming_load)
            self.numLoaded += 1

        for s in effects:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio SFX", fname)
            self.game.sound.register_sound(k,self.game.sfx_path+fname, volume=volume)
            self.numLoaded += 1

        for s in voice:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio Voices", fname)
            self.game.sound.register_sound(k,self.game.voice_path+fname, volume=volume) #, is_voice=True)
            self.numLoaded += 1



        # self.clearScreen()    


