import sys
import procgame
import pinproc
from threading import Thread
import random
import string
import time
import locale
import math
import copy
import ctypes
from .. import config
import os
from time import sleep
try:
    import serial
except Exception, e:
    print "pySerial not found; RGBDMD support will be unavailable"

from procgame.events import EventManager

try:
    from ..dmd import sdl2_displaymanager  
    from ..dmd.sdl2_displaymanager import *
    import sdl2.ext
    import pygame
except ImportError:
    print "PySDL2 is required, but not found."
    raise


class Desktop():
    """The :class:`Desktop` class helps manage interaction with the desktop, providing both a windowed
    representation of the DMD, as well as translating keyboard input into pyprocgame events."""
    
    exit_event_type = 99
    """Event type sent when Ctrl-C is received."""
    
    key_map = {}

    dots_w = 128
    dots_h = 32
    screen_scale = 2 # this is the factor to pygame scale the display.  192x96 (x6) = 1152x576


    def __init__(self):
        print 'Desktop init begun.'
        self.ctrl = 0
        self.i = 0
        self.key_events = []

        self.dots_w = config.value_for_key_path(keypath='dmd_dots_w', default=128)
        self.dots_h = config.value_for_key_path(keypath='dmd_dots_h', default=32)
        self.screen_position_x = config.value_for_key_path(keypath = 'screen_position_x', default=0)
        self.screen_position_y = config.value_for_key_path(keypath='screen_position_y', default=0)
        self.screen_scale = config.value_for_key_path(keypath='desktop_dmd_scale', default=2)
        self.dot_filter = config.value_for_key_path(keypath='dmd_dot_filter', default=True)
        self.fullscreen = config.value_for_key_path(keypath='dmd_fullscreen', default=False)
        self.window_border = config.value_for_key_path(keypath='dmd_window_border', default=True)
        self.dmd_screen_size = ((self.dots_w)*self.screen_scale, (self.dots_h)*self.screen_scale)
        self.dmd_soften = config.value_for_key_path(keypath='dmd_soften', default="0")
        self.use_rgb_dmd_device = config.value_for_key_path(keypath='rgb_dmd.enabled', default=False)
        if(self.use_rgb_dmd_device):
            # turn off dots and scaling, since they are incompatible (at this time) --SDL2 bug.
            self.screen_scale = 1
            self.dot_filter = False
            self.serial_port_number = config.value_for_key_path(keypath='rgb_dmd.com_port', default=None)
            if(self.serial_port_number is None):
                raise ValueError, "RGBDMD: config.yaml specified rgb_dmd enabled, but no com_port value (e.g., com3) given!"

        self.setup_window()

        if(self.use_rgb_dmd_device):
            if(serial is None):
                raise ValueError, "RGBDMD: config.yaml specified rgb_dmd enabled, but requird pySerial library not installed/found."
            self.serialPort = serial.Serial(port=self.serial_port_number, baudrate=2500000)  
            self.magic_cookie = bytearray([0xBA,0x11,0x00,0x03,  0x04,  0x00,  0x00,0x00])

            self.serialPort.write(self.magic_cookie);

            self.draw = self.draw_to_rgb_dmd            
            return

        if(self.dot_filter==True):
            dmd_grid_path = config.value_for_key_path(keypath='dmd_grid_path', default='./')
            # self.dot_filter = False
            # self.draw = self.draw_no_dot_effect

            ############## Make the Dot filter ############################
            dot_sprite = sdl2_DisplayManager.inst().load_texture(os.path.join(dmd_grid_path,'dmdgrid32x32.png'))

            # 1. Make the destination texture (huge)
            self.dot_tex = sdl2.render.SDL_CreateTexture(sdl2_DisplayManager.inst().texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
                                                                          sdl2.render.SDL_TEXTUREACCESS_TARGET,
                                                                          self.dots_w*10,self.dots_h*10)
            sdl2.SDL_SetTextureBlendMode(self.dot_tex,sdl2.SDL_BLENDMODE_BLEND)

            # 2. backup the old renderer destination
            bk = sdl2.SDL_GetRenderTarget(sdl2_DisplayManager.inst().texture_renderer.renderer)
            sdl2.SDL_SetRenderTarget(sdl2_DisplayManager.inst().texture_renderer.renderer, self.dot_tex)
            # the following is needed on OSX, but breaks nothing being present for both
            sdl2_DisplayManager.inst().texture_renderer.clear((0,0,0))

            # 3. start the stamping process
            acr = int(math.ceil(self.dots_w/float(32)))
            down = int(math.ceil(self.dots_h/float(32)))

            for step_w in range(0,acr):
                for step_h in range(0,down):
                    sdl2_DisplayManager.inst().texture_renderer.copy(dot_sprite, dstrect= (step_w*320,step_h*320,320,320))

            del dot_sprite

            # 4. restore the target for the renderer
            sdl2.SDL_SetRenderTarget(sdl2_DisplayManager.inst().texture_renderer.renderer, bk) # revert back
        else:
            self.draw = self.draw_no_dot_effect


    
    def add_key_map(self, key, switch_number):
        """Maps the given *key* to *switch_number*, where *key* is one of the key constants in :mod:`pygame.locals`."""
        self.key_map[key] = switch_number
    
    def clear_key_map(self):
        """Empties the key map."""
        self.key_map = {}

    def get_keyboard_events(self):
        """Asks :mod:`pySDL2` for recent keyboard events and translates them into an array
        of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
        # print event.key.keysym.sym <-- number
        # print sdl2.SDL_GetKeyName(event.key.keysym.sym) <-- name

        for event in sdl2.ext.get_events():
            EventManager.default().post(name=self.event_name_for_pygame_event_type(event.type), object=self, info=event)
            key_event = {}
            #print("Key: %s" % event.key.keysym.sym)
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_LCTRL or event.key.keysym.sym == sdl2.SDLK_RCTRL:
                    self.ctrl = 1
                if event.key.keysym.sym == sdl2.SDLK_c:
                    if self.ctrl == 1:
                        key_event['type'] = self.exit_event_type
                        key_event['value'] = 'quit'
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    key_event['type'] = self.exit_event_type
                    key_event['value'] = 'quit'
                elif event.key.keysym.sym in self.key_map:
                    key_event['type'] = pinproc.EventTypeSwitchClosedDebounced
                    key_event['value'] = self.key_map[event.key.keysym.sym]
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym == sdl2.SDLK_LCTRL or event.key.keysym.sym == sdl2.SDLK_RCTRL:
                    self.ctrl = 0
                elif event.key.keysym.sym in self.key_map:
                    key_event['type'] = pinproc.EventTypeSwitchOpenDebounced
                    key_event['value'] = self.key_map[event.key.keysym.sym]
            if len(key_event):
                self.key_events.append(key_event)
        e = self.key_events
        self.key_events = []
        return e
    
    
    event_listeners = {}
    
    def event_name_for_pygame_event_type(self, event_type):
        return 'pygame(%s)' % (event_type)
    
    screen = None
    """:class:`pygame.Surface` object representing the screen's surface."""

    # you'll need to change your displayController to width=192, height=96 and the same for all layers created

    def setup_window(self):
        #os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.screen_position_x,self.screen_position_y)
        self.window_w = self.dots_w * self.screen_scale
        self.window_h = self.dots_h * self.screen_scale

        flags = 0
        if(self.fullscreen):
            flags = flags | sdl2.SDL_WINDOW_FULLSCREEN
        if(self.window_border is False):
            flags = flags | sdl2.SDL_WINDOW_BORDERLESS

        sdl2_DisplayManager.Init(self.dots_w, self.dots_h, self.screen_scale,  "PyProcGameHD.  [CTRL-C to exit]", self.screen_position_x,self.screen_position_y, flags, self.dmd_soften)
        sdl2_DisplayManager.inst().fonts_init(None,"Courier")

        # pygame.mouse.set_visible(False)

        # todo: these...
        # if(self.fullscreen==True):
        #     opts = pygame.HWPALETTE|pygame.FULLSCREEN|pygame.DOUBLEBUF
        # elif(self.window_border == False):
        #     opts =  pygame.NOFRAME  
        # else:
        #     opts = 0
        
        print("****************")
        # print(pygame.display.Info())
        pygame.init()
        print "WINDOW SET"
        print("****************")


    def draw(self, frame):
        """Draw the given :class:`~procgame.dmd.Frame` in the window."""
        sdl2_DisplayManager.inst().clear((0,0,0,255))

        if(not self.fullscreen==True):
            sdl2_DisplayManager.inst().screen_blit(source_tx=frame.pySurface, expand_to_fill=True)
        else:
            sdl2.SDL_RenderCopy(sdl2_DisplayManager.inst().texture_renderer.renderer, frame.pySurface.texture, None, sdl2.rect.SDL_Rect(0,0,self.window_w,self.window_h))

        # sdl2_DisplayManager.inst().screen_blit(source_tx=self.dot_tex, expand_to_fill=True)
        sdl2.SDL_RenderCopy(sdl2_DisplayManager.inst().texture_renderer.renderer, self.dot_tex, None, sdl2.rect.SDL_Rect(0,0,self.window_w,self.window_h))

        # sdl2.SDL_RenderCopy(texture_renderer.renderer, dot_tex, None, sdl2.rect.SDL_Rect(0,0,window_w,window_h))

        sdl2_DisplayManager.inst().flip()

    def draw_no_dot_effect(self, frame):
        """Draw the given :class:`~procgame.dmd.Frame` in the window."""
        sdl2_DisplayManager.inst().clear((0,0,0,255))
        if(not self.fullscreen==True):
            sdl2_DisplayManager.inst().screen_blit(source_tx=frame.pySurface, expand_to_fill=True)
        else:
            sdl2.SDL_RenderCopy(sdl2_DisplayManager.inst().texture_renderer.renderer, frame.pySurface.texture, None, sdl2.rect.SDL_Rect(self.screen_position_x,self.screen_position_y,self.screen_position_x+self.window_w,self.screen_position_y+self.window_h))
        sdl2_DisplayManager.inst().flip()


    def draw_to_rgb_dmd(self, frame):
        sdl2_DisplayManager.inst().clear((0,0,0,255))
        sdl2_DisplayManager.inst().screen_blit(source_tx=frame.pySurface, expand_to_fill=True)
        sdl2_DisplayManager.inst().flip()

        bucket = sdl2_DisplayManager.inst().make_bits_from_texture(frame.pySurface, 128, 32)
        
        self.serialPort.write(self.magic_cookie);
        s = bytearray([])
        i = 0

        while(i < 128*32*4):
            # print("pixel %i: %s, %s, %s, %s" % (i/4, bucket[i], bucket[i+1], bucket[i+2], bucket[i+3]))
            
            s.append(bucket[i])
            s.append(bucket[i+1])
            s.append(bucket[i+2])
            # s.append("%c%c%c" % (bucket[i], bucket[i+1], bucket[i+2]))
            # self.serialPort.write("%c%c%c" % (bucket[i], bucket[i+1], bucket[i+2]))

            i+=4
        # print (s)
        self.serialPort.write(s)            

        del bucket
        # print(type(b))

        # del tx
        # do python send


    def __str__(self):
        return '<Desktop pySDL2>'


