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

from procgame.events import EventManager

try:
    import pygame
    import pygame.locals
except ImportError:
    print "Error importing pygame; ignoring."
    pygame = None


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
        if 'pygame' in globals():
            self.dots_w = config.value_for_key_path(keypath='dmd_dots_w', default=128)
            self.dots_h = config.value_for_key_path(keypath='dmd_dots_h', default=32)
            self.screen_position_x = config.value_for_key_path(keypath = 'screen_position_x', default=0)
            self.screen_position_y = config.value_for_key_path(keypath='screen_position_y', default=0)
            self.screen_scale = config.value_for_key_path(keypath='desktop_dmd_scale', default=2)
            self.dot_filter = config.value_for_key_path(keypath='dmd_dot_filter', default=True)
            self.fullscreen = config.value_for_key_path(keypath='dmd_fullscreen', default=False)
            self.window_border = config.value_for_key_path(keypath='dmd_window_border', default=True)
            self.dmd_screen_size = ((self.dots_w)*self.screen_scale, (self.dots_h)*self.screen_scale)
            self.setup_window()

            
            if(self.dot_filter==True):
                dmd_grid_path = config.value_for_key_path(keypath='dmd_grid_path', default='./')
                self.grid_image = pygame.surface.Surface((self.dots_w*10,self.dots_h*10),pygame.SRCALPHA)
                r = pygame.Rect(0,0,self.dots_w*10,self.dots_h*10)
                self.grid_image.fill((0,0,0,0),r)


                grid_32x32segment = pygame.image.load(dmd_grid_path + 'dmdgrid32x32.png')
                acr = int(math.ceil(self.dots_w/float(32)))
                down = int(math.ceil(self.dots_h/float(32)))


                for step_w in range(0,acr):
                    for step_h in range(0,down):
                        self.grid_image.blit(grid_32x32segment,(step_w*320,step_h*320))
                #self.grid_image = pygame.image.load('./dmdgrid.png')
                #self.grid_image = pygame.image.load('./dmdgrid256x128.png')
                
                # why am I converting this to alpha..?!
                self.grid_image = pygame.transform.smoothscale(self.grid_image, self.dmd_screen_size).convert_alpha()
            else:
                self.draw = self.draw_no_dot_effect
            

        else:
            print 'Desktop init skipping setup_window(); pygame does not appear to be loaded.'
    
    def add_key_map(self, key, switch_number):
        """Maps the given *key* to *switch_number*, where *key* is one of the key constants in :mod:`pygame.locals`."""
        self.key_map[key] = switch_number
    
    def clear_key_map(self):
        """Empties the key map."""
        self.key_map = {}

    def get_keyboard_events(self):
        """Asks :mod:`pygame` for recent keyboard events and translates them into an array
        of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
        #self.key_events = []
        for event in pygame.event.get():
            EventManager.default().post(name=self.event_name_for_pygame_event_type(event.type), object=self, info=event)
            key_event = {}
            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_RCTRL or event.key == pygame.locals.K_LCTRL:
                    self.ctrl = 1
                if event.key == pygame.locals.K_c:
                    if self.ctrl == 1:
                        key_event['type'] = self.exit_event_type
                        key_event['value'] = 'quit'
                elif (event.key == pygame.locals.K_ESCAPE):
                    key_event['type'] = self.exit_event_type
                    key_event['value'] = 'quit'
                elif event.key in self.key_map:
                    key_event['type'] = pinproc.EventTypeSwitchClosedDebounced
                    key_event['value'] = self.key_map[event.key]
            elif event.type == pygame.locals.KEYUP:
                if event.key == pygame.locals.K_RCTRL or event.key == pygame.locals.K_LCTRL:
                    self.ctrl = 0
                elif event.key in self.key_map:
                    key_event['type'] = pinproc.EventTypeSwitchOpenDebounced
                    key_event['value'] = self.key_map[event.key]
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
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.screen_position_x,self.screen_position_y)
        pygame.init()
        pygame.mouse.set_visible(False)
        #self.screen = pygame.display.set_mode((128*self.screen_multiplier, 32*self.screen_multiplier))
        # self.screen = pygame.display.set_mode((self.dots_w*self.screen_scale, self.dots_h*self.screen_scale),pygame.OPENGL|pygame.FULLSCREEN|pygame.DOUBLEBUF)
        # self.screen = pygame.display.set_mode((self.dots_w*self.screen_scale, self.dots_h*self.screen_scale),pygame.HWPALETTE|pygame.FULLSCREEN|pygame.DOUBLEBUF)
        if(self.fullscreen==True):
            opts = pygame.HWPALETTE|pygame.FULLSCREEN|pygame.DOUBLEBUF
        elif(self.window_border == False):
            opts =  pygame.NOFRAME  
        else:
            opts = 0

        self.screen = pygame.display.set_mode(self.dmd_screen_size,opts)
        
        print("****************")
        print(pygame.display.Info())
        print("****************")

        pygame.display.set_caption('Press CTRL-C to exit')
        self.scratch_surface = pygame.surface.Surface((self.dots_w, self.dots_h)).convert()
        print("****************")
        print(self.scratch_surface.get_flags())
        print("****************")

    def draw(self, frame):
        """Draw the given :class:`~procgame.dmd.Frame` in the window."""

        #self.scratch_surface.blit(frame.pySurface,(0,0))

        # scale the created image using pygame's (hardware scaler)
        # swap the uncommented line with the commented one for "rounded" 
        # effect, overall darker dots, and some performance penalty

        #scaled = pygame.transform.scale(self.screen,frame.pySurface, self.dmd_screen_size)
        #self.screen.blit(scaled,(self.w_margin+self.window_offset_x,self.h_margin+self.window_offset_y))
        #pygame.transform.smoothscale(self.scratch_surface, self.screen.get_size(), self.screen)

        pygame.transform.scale(frame.pySurface, self.dmd_screen_size, self.screen)

        # Blit the grid on top to give it a more authentic DMD look.        
        self.screen.blit(self.grid_image,(0,0))

        #pygame.display.update()
        pygame.display.flip()

    def draw_no_dot_effect(self, frame):
        """Draw the given :class:`~procgame.dmd.Frame` in the window."""

        pygame.transform.scale(frame.pySurface, self.dmd_screen_size, self.screen)
        pygame.display.flip()   
        
    def __str__(self):
        return '<Desktop pygame>'

