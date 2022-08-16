from procgame import dmd
from procgame.dmd.sdl2_displaymanager import sdl2_DisplayManager
import sdl2
import pinproc
"""
"""
import os
import sys
import yaml
import logging
import timeit
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
    loaded_assets_files = []
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

        self.dots_w = sdl2_DisplayManager.inst().dots_w
        self.dots_h = sdl2_DisplayManager.inst().dots_h

        if(yaml_values is not None):
            self.values = yaml_values
        else:
            self.loadConfig(game.curr_file_path,yaml_file)

        splash_file = self.value_for_key_path('UserInterface.splash_screen', None)
        self.single_line = self.value_for_key_path('UserInterface.single_line', False)
        default_line_format = "Loading %s: [%06d] of [%06d]: %s" if self.single_line else "Loading %s: [%06d] of [%06d]"
        self.line_format = self.value_for_key_path('UserInterface.line_format', default_line_format)
        self.border_width = self.value_for_key_path('UserInterface.progress_bar.border_width', 1)
        self.border_color = self.verify_alpha(self.value_for_key_path('UserInterface.progress_bar.border', (120,120,120,255)))
        self.background_color = self.verify_alpha(self.value_for_key_path('UserInterface.progress_bar.background', None))
        self.fill_color = self.verify_alpha(self.value_for_key_path('UserInterface.progress_bar.fill',(255,84,84,255)))
        self.bar_x = self.value_for_key_path('UserInterface.progress_bar.x_center', 0.5)
        self.bar_y = self.value_for_key_path('UserInterface.progress_bar.y_center', 0.25)

        bar_w = self.value_for_key_path('UserInterface.progress_bar.width', 0.8)
        bar_h = self.value_for_key_path('UserInterface.progress_bar.height', 0.15)

        text_y = self.value_for_key_path('UserInterface.text.y_center', 0.15)
        # self.text_font = self.value_for_key_path('UserInterface.text.font', 0.15)
        # self.text_size = self.value_for_key_path('UserInterface.text.size', 0.15)
        self.text_color = self.verify_alpha(self.value_for_key_path('UserInterface.text.color', (255,255,0,255)))

        self.prog_bar_width = int(bar_w * self.dots_w)
        self.prog_bar_height = int(bar_h * self.dots_h)

        self.prog_bar_x = int((self.dots_w * self.bar_x) - (self.prog_bar_width/2))
        self.prog_bar_y = int((self.dots_h * self.bar_y) - (self.prog_bar_height/2))

        self.text_x = self.prog_bar_x
        self.text_y = int(text_y * self.dots_h)

        self.frame = dmd.Frame(self.dots_w, self.dots_h)

        if(splash_file is not None):
            s = sdl2_DisplayManager.inst().load_surface(game.dmd_path + splash_file)
            self.splash_image = sdl2_DisplayManager.inst().texture_from_surface(s)
            del s
        else:
            self.splash_image = None

        if self.game.use_proc_dmd:
            self.rfont = dmd.font_named('Font07x5.dmd')

        self.load()

    def verify_alpha(self, color):
        if type(color) == list and len(color) == 3:
            return color + [255]
        else:
            return color

    def updateProgressBar(self, displayType, fname):
        if(self.splash_image is not None):
            sdl2_DisplayManager.inst().roto_blit(self.splash_image, self.frame.pySurface, dest=None, area=None, angle=0, origin=None, flip=0)
        else:
            self.frame.clear()

        bk = sdl2_DisplayManager.inst().switch_target(self.frame.pySurface)

        for r in range(self.border_width):
            sdl2_DisplayManager.inst().draw_rect(self.border_color, (self.prog_bar_x + r, self.prog_bar_y + r, self.prog_bar_width - 2 * r, self.prog_bar_height - 2 * r), False)

        bar_width = int(float(self.numLoaded + 1)/float(self.total) * self.prog_bar_width)

        if self.background_color:
            sdl2_DisplayManager.inst().draw_rect(self.background_color, (self.prog_bar_x + self.border_width + bar_width, self.prog_bar_y + self.border_width, self.prog_bar_width - bar_width - 2 * self.border_width, self.prog_bar_height - 2 * self.border_width), True)

        sdl2_DisplayManager.inst().draw_rect(self.fill_color, (self.prog_bar_x + self.border_width, self.prog_bar_y + self.border_width, bar_width, self.prog_bar_height - 2 * self.border_width), True)

        if (self.single_line):
            s = self.line_format % (displayType, self.numLoaded+1,self.total, fname)
            self.render_text(s, x=self.text_x, y=self.text_y)
        else:
            s = self.line_format % (displayType, self.numLoaded+1,self.total)
            tx_size = self.render_text(s, x=self.text_x, y=self.text_y)
            (unused_tx_w, tx_h) = tx_size
            self.render_text(fname, x=self.text_x, y=int(self.text_y+1.2*tx_h))

        sdl2_DisplayManager.inst().switch_target(bk)
        if self.game.use_proc_dmd:
            self.game.dmd.proc_dmd_draw(self.frame)
        if self.game.desktop:
            self.game.desktop.draw(self.frame) # desktop handles pixel scaling
        else:
            sdl2_DisplayManager.inst().screen_blit(self.frame.texture, expand_to_fill=True)

        for event in sdl2.ext.get_events():
            #print("Key: %s" % event.key.keysym.sym)
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    self.game.end_run_loop()
                    sys.exit()

    def render_text(self, text, x, y):
        if self.rfont:
            w = self.rfont.draw(self.frame, text, x, y)
            return (w, self.rfont.char_size)
        else:
            tx = sdl2_DisplayManager.inst().font_render_text(text, font_alias=None, size=None, width=self.dots_w, color=self.text_color, bg_color=None)
            sdl2_DisplayManager.inst().screen_blit(tx, x, y, expand_to_fill=False)
            size = tx.size
        return size

    def loadIntoCache(self,key,frametime=1,file=None,repeatAnim=False,holdLastFrame=False,  opaque = False, composite_op = None, x_loc =0, y_loc=0, streaming_load=False, streaming_png=False, png_stream_cache=False, custom_sequence=None, scale=None):
        if(file==None):
            file=key + '.vga.dmd.zip'

        self.updateProgressBar("Animations", file)

        tmp = None
        if(self.loaded_map.has_key(file) and not streaming_load):
            tmp = self.animations[self.loaded_map[file]]
            #print("quick loaded '%s'" % key)
        else:
            if(not streaming_load):
                tmp = dmd.Animation().load(self.dmd_path + file , composite_op=composite_op, use_streaming_mode = streaming_png, png_stream_cache=png_stream_cache)
            self.loaded_map[file] = key

        if(tmp is not None):
            self.lengths[key] = tmp.frames[-1]
            if(len(tmp.frames)==1):
                holdLastFrame = True
                # self.logger.info("Single frame animtation '%s'; setting holdLastFrame to True" % file)

        if(streaming_load):
            self.animations[key] = dmd.MovieLayer(opaque, hold=holdLastFrame, repeat=repeatAnim, frame_time=frametime, movie_file_path=self.dmd_path + file, transparency_op=composite_op)
        else:
            self.animations[key] = dmd.AnimatedLayer(frames=tmp.frames, frame_time=frametime, repeat=repeatAnim, hold=holdLastFrame, opaque = opaque)

        if(custom_sequence is not None):
            self.animations[key].play_sequence(sequence=custom_sequence)

        if(scale is not None):
            self.animations[key].set_scale(scale)

        self.animations[key].set_target_position(x_loc, y_loc)
        # if composite_op != None:
        #   self.animations[key].composite_op = composite_op
        self.numLoaded += 1

    def load(self):
        l = logging.getLogger("PIL.PngImagePlugin")
        l.setLevel(logging.WARNING)
        l = logging.getLogger("game.assets")
        l.setLevel(logging.WARNING)
        l = logging.getLogger("game.sound")
        l.setLevel(logging.WARNING)
        l = logging.getLogger("game.dmdcache")
        l.setLevel(logging.WARNING)
        anims = self.value_for_key_path(keypath='Animations', default={}) or list()
        fonts = self.value_for_key_path(keypath='Fonts', default={}) or list()
        hfonts = value_for_key(fonts,'HDFonts',{}) or list()
        rfonts = value_for_key(fonts,'DMDFonts',{}) or list()
        fontstyles = value_for_key(fonts,'FontStyles',{}) or list()
        lamps = self.value_for_key_path(keypath='LampShows', default={}) or list()
        rgbshows = self.value_for_key_path(keypath='RGBShows', default={}) or list()
        sounds = self.value_for_key_path(keypath='Audio', default={}) or list()
        music = value_for_key(sounds,'Music',{}) or list()
        effects = value_for_key(sounds,'Effects',{}) or list()
        voice = value_for_key(sounds,'Voice',{}) or list()

        paths = self.value_for_key_path(keypath='AssetListFiles', default={}) or list()
        #if there was a list of files to load, then load those
        for path in paths:
            self.loaded_assets_files.append(path)
            self.values = yaml.load(open(path, 'r'))
            anims += self.value_for_key_path(keypath='Animations', default={}) or list()
            fonts = self.value_for_key_path(keypath='Fonts') or list()
            hfonts += value_for_key(fonts,'HDFonts',{})
            rfonts += value_for_key(fonts,'DMDFonts',{}) or list()
            fontstyles += value_for_key(fonts,'FontStyles',{}) or list()
            lamps += self.value_for_key_path(keypath='LampShows', default={}) or list()
            rgbshows += self.value_for_key_path(keypath='RGBShows', default={}) or list()
            sounds = self.value_for_key_path(keypath='Audio', default={}) or list()
            music += value_for_key(sounds,'Music',{}) or list()
            effects += value_for_key(sounds,'Effects',{}) or list()
            voice += value_for_key(sounds,'Voice',{}) or list()

        self.total = len(lamps) + len(rgbshows) + len(hfonts) + len(rfonts) + len(anims) + len(music) + len(effects) + len(voice)

        try:
            current = ""
            for l in lamps:
                k  = value_for_key(l,'key')
                fname = value_for_key(l,'file')
                self.updateProgressBar("Lampshows", fname)
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

            for l in rgbshows:
                k  = value_for_key(l,'key')
                fname = value_for_key(l,'file')
                self.updateProgressBar("RGBShows", fname)
                f = self.game.lampshow_path + fname
                current = 'RGBshow: [%s]: %s, %s ' % (k, f, fname)
                self.game.rgbshow_player.load(k, f)
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
                font_style = dmd.HDFontStyle(interior_color=ic, line_width=lw, line_color=lc)
                self.fontstyles[k] = font_style
                # fontstyles load instantly, do not count fontstyles in number of loaded assets

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
                png_stream_cache  = value_for_key(anim, 'streamingPNG_Cached', False)
                streaming_png  = value_for_key(anim, 'streamingPNG', png_stream_cache)
                custom_sequence  = value_for_key(anim, 'sequence', None)
                scaling = value_for_key(anim, 'scale', None)
                current = 'Animation: [%s]: %s' % (k, f)
                # started = timeit.time.time()
                started = timeit.time.time()
                self.loadIntoCache(k,ft,f,r,h,o,c,x,y,streaming_load, streaming_png, png_stream_cache, custom_sequence, scaling)
                time_taken = timeit.time.time() - started
                self.logger.info("loading visual asset took %.3f seconds" % time_taken)
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
            is_voice = value_for_key(s, 'voice', False)
            self.updateProgressBar("Audio SFX", fname)
            self.game.sound.register_sound(k,self.game.sfx_path+fname, volume=volume, is_voice=is_voice)
            self.numLoaded += 1

        for s in voice:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio Voices", fname)
            self.game.sound.register_sound(k,self.game.voice_path+fname, volume=volume, is_voice=True)
            self.numLoaded += 1
