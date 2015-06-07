from dmd import *
from layers import *


class DisplayController(object):
    """Manages the process of obtaining DMD frames from active modes and compositing them together for
    display on the DMD.
    
    **Using DisplayController**
    
    1. Add a :class:`DisplayController` instance to your :class:`~procgame.game.GameController` subclass::
    
        class Game(game.GameController):
          def __init__(self, machine_type):
            super(Game, self).__init__(machine_type)
            self.dmd = dmd.DisplayController(self, width=128, height=32,
                                             message_font=font_tiny7)
    
    2. In your subclass's :meth:`~procgame.game.GameController.dmd_event` call :meth:`DisplayController.update`::
    
        def dmd_event(self):
            self.dmd.update()
    
    """
    
    frame_handlers = []
    """If set, frames obtained by :meth:`.update` will be sent to the functions
    in this list with the frame as the only parameter.
    
    This list is initialized to contain only ``self.game.proc.dmd_draw``."""
    
    def __init__(self, game, width=192, height=96, message_font=None):
        self.game = game
        self.message_layer = None
        self.width = width
        self.height = height
        self.frame = Frame(self.width, self.height)
        if message_font != None:
            self.message_layer = TextLayer(width/2, height-2*7, message_font, "center")
        # Do two updates to get the pump primed:
        for x in range(2):
            self.update()
        # if(game.use_virtual_dmd_only is False):     # MJO: added to stop DMD events when no physical DMD is present 
        #     print("using physical DMD, b/c use_virtual_dmd_only is " + str(game.use_virtual_dmd_only))
        #     print("change via config.yaml --> use_virtual_dmd_only: True")
        #     self.frame_handlers.append(self.game.proc.dmd_draw)
        # else:
            print("Using a virtual DMD ONLY - no physical DMD output will be sent")
            
    def set_message(self, message, seconds):
        if self.message_layer == None:
            raise ValueError, "Message_font must be specified in constructor to enable message layer."
        self.message_layer.set_text(message, seconds)

    def update(self):
        """Iterates over :attr:`procgame.game.GameController.modes` from lowest to highest
        and composites a DMD image for this
        point in time by checking for a ``layer`` attribute on each :class:`~procgame.game.Mode`.
        If the mode has a layer attribute, that layer's :meth:`~procgame.dmd.Layer.composite_next` method is called
        to apply that layer's next frame to the frame in progress.
        
        The resulting frame is sent to the :attr:`frame_handlers` and then returned from this method."""
        
        #lets increment a counter on how many dmd updates we have done
        self.game.dmd_updates+=1
        layers = []
        for mode in self.game.modes.modes:
            if hasattr(mode, 'layer') and mode.layer != None and mode.layer.enabled:
                layers.append(mode.layer)
                if mode.layer.opaque:
                    break # if we have an opaque layer we don't render any lower layers
        
        #frame = Frame(self.width, self.height)
        self.frame.clear((0,0,0,255))
        for layer in layers[::-1]: # We reverse the list here so that the top layer gets the last say.
            if layer.enabled:
                layer.composite_next(self.frame)
        
        if self.message_layer != None:
            self.message_layer.composite_next(self.frame)
            
        if self.frame != None:
            for handler in self.frame_handlers:
                handler(self.frame)
                
        return self.frame
