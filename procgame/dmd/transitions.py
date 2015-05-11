from dmd import *
import sdl2.ext
from sdl2.ext import *

class LayerTransitionBase(object):
    """Transition base class."""

    progress = 0.0
    """Transition progress from 0.0 (100% from frame, 0% to frame) to 1.0 (0% from frame, 100% to frame).
    Updated by :meth:`next_frame`."""
    
    progress_per_frame = 1.0/30.0
    """Progress increment for each frame.  Defaults to 1/30, or 30fps."""
    
    progress_mult = 0 # not moving, -1 for B to A, 1 for A to B .... not documented as play/pause manipulates.
    
    completed_handler = None
    """Function to be called once the transition has completed."""
    
    in_out = 'in'
    """If ``'in'`` the transition is moving from `from` to `to`; if ``'out'`` the transition is moving
    from `to` to `from`."""

    def __init__(self):
        super(LayerTransitionBase, self).__init__()
    
    def start(self):
        """Start the transition."""
        self.reset()
        self.progress_mult = 1
    def pause(self):
        """Pauses the transition at the current position."""
        self.progress_mult = 0
    def reset(self):
        """Reset the transition to the beginning."""
        self.progress_mult = 0
        self.progress = 0
    def next_frame(self, from_frame, to_frame):
        """Applies the transition and increments the progress if the transition is running.  Returns the resulting frame."""
        #print 'TRANSITION NEXT FRAME PROGRESS IS' +str(self.progress)
        self.progress = max(0.0, min(1.0, self.progress + self.progress_mult * self.progress_per_frame))
        if self.progress <= 0.0:
            if self.in_out == 'in':
                return from_frame
            else:
                return to_frame
        if self.progress >= 1.0:
            if self.completed_handler != None:
                self.completed_handler()
            if self.in_out == 'in':
                return to_frame
            else:
                return from_frame
        return self.transition_frame(from_frame=from_frame, to_frame=to_frame)
    def transition_frame(self, from_frame, to_frame):
        """Applies the transition at the current progress value.
           Subclasses should override this method to provide more interesting transition effects.
           Base implementation simply returns the from_frame."""
        return from_frame

class ExpandTransition(LayerTransitionBase):
    def __init__(self, direction='vertical'):
        super(ExpandTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/11.0
    def transition_frame(self, from_frame, to_frame):
        frame = from_frame.copy()
        dst_x, dst_y = 0, 0
        prog = self.progress
        if self.in_out == 'out':
            prog = 1.0 - prog
        dst_x, dst_y = {
         'vertical': (0, frame.height/2-prog*(frame.height/2)),
         'horizontal':  (frame.width/2-prog*(frame.width/2), 0),
        }[self.direction]

        if (self.direction == 'vertical'):
            width = frame.width
            height = prog*frame.height
        else:
            width = prog*frame.width
            height = frame.height

        Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=dst_x, src_y=dst_y, width=width, height=height, op='copy')
        return frame

class SlideOverTransition(LayerTransitionBase):
    def __init__(self, direction='north'):
        super(SlideOverTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/15.0
    def transition_frame(self, from_frame, to_frame):
        frame = from_frame.copy()
        dst_x, dst_y = 0, 0
        prog = self.progress
        if self.in_out == 'in':
            prog = 1.0 - prog
        dst_x, dst_y = {
         'north': (0,  prog*frame.height),
         'south': (0, -prog*frame.height),
         'east':  (-prog*frame.width, 0),
         'west':  ( prog*frame.width, 0),
        }[self.direction]
        Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
        return frame

class PushTransition(LayerTransitionBase):
    def __init__(self, direction='north'):
        super(PushTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/15.0
    def transition_frame(self, from_frame, to_frame):
        frame = Frame(width=from_frame.width, height=from_frame.height)
        dst_x, dst_y = 0, 0
        prog = self.progress
        prog1 = self.progress
        if self.in_out == 'in':
            prog = 1.0 - prog
        else:
            prog1 = 1.0 - prog1
        dst_x, dst_y, dst_x1, dst_y1 = {
         'north': (0,  prog*frame.height,  0, -prog1*frame.height),
         'south': (0, -prog*frame.height,  0,  prog1*frame.height),
         'east':  (-prog*frame.width, 0,    prog1*frame.width, 0),
         'west':  ( prog*frame.width, 0,   -prog1*frame.width, 0),
        }[self.direction]
        Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
        Frame.copy_rect(dst=frame, dst_x=dst_x1, dst_y=dst_y1, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
        return frame


class WipeTransition(LayerTransitionBase):
    def __init__(self, direction='north'):
        super(WipeTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/30.0
    def transition_frame(self, from_frame, to_frame):
        frame = Frame(width=from_frame.width, height=from_frame.height)
        prog0 = self.progress
        prog1 = self.progress
        if self.in_out == 'out':
            prog0 = 1.0 - prog0
        else:
            prog1 = 1.0 - prog1
            
        src_x, src_y = {
         'north': (0,  prog1*frame.height),
         'south': (0,  prog0*frame.height),
         'east':  (prog0*frame.width, 0),
         'west':  (prog1*frame.width, 0),
        }[self.direction]
        
        width, height = {
         'north': (frame.width,  prog1*frame.height+1),
         'south': (frame.width,  prog0*frame.height+1),
         'east':  (prog0*frame.width+1, frame.height),
         'west':  (prog1*frame.width+1, frame.height),
        }[self.direction]

        
        if self.direction in ['east', 'south']:
            from_frame, to_frame = to_frame, from_frame
            #print "reverse to and from seeing going east or south" + str(self.direction)
        
        src_x = int(round(src_x))
        src_y = int(round(src_y))
        Frame.copy_rect(dst=frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=width, height=height, op='copy')
        
        #print  src_x,  src_y, to_frame.height, to_frame.width, from_frame.height, from_frame.width, prog0, prog1, self.progress
        
        Frame.copy_rect(dst=frame, dst_x=src_x, dst_y=src_y, src=to_frame, src_x=src_x, src_y=src_y, width=from_frame.width-src_x, height=from_frame.height-src_y, op='copy')
        return frame




class AccordianTransition(LayerTransitionBase):
    def __init__(self, direction='north'):
        super(WipeTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/15.0
    def transition_frame(self, from_frame, to_frame):
        frame = Frame(width=from_frame.width, height=from_frame.height)
        prog0 = self.progress
        prog1 = self.progress
        if self.in_out == 'out':
            prog0 = 1.0 - prog0
        else:
            prog1 = 1.0 - prog1
        src_x, src_y = {
         'north': (0,  prog1*frame.height),
         'south': (0,  prog0*frame.height),
         'east':  (prog0*frame.width, 0),
         'west':  (prog1*frame.width, 0),
        }[self.direction]
        if self.direction in ['east', 'south']:
            from_frame, to_frame = to_frame, from_frame
        src_x = int(round(src_x))
        src_y = int(round(src_y))
        Frame.copy_rect(dst=frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
        Frame.copy_rect(dst=frame, dst_x=src_x, dst_y=src_y, src=to_frame, src_x=src_x, src_y=src_y, width=from_frame.width-src_x, height=from_frame.height-src_y, op='copy')
        return frame

class ObscuredWipeTransition(LayerTransitionBase):
    def __init__(self, obscuring_frame, composite_op, direction='north'):
        super(ObscuredWipeTransition, self).__init__()
        self.composite_op = composite_op
        self.direction = direction
        self.progress_per_frame = 1.0/15.0
        self.obs_frame = obscuring_frame
    
    def transition_frame(self, from_frame, to_frame):
        frame = Frame(width=from_frame.width, height=from_frame.height)
        prog0 = self.progress
        prog1 = self.progress
        if self.in_out == 'out':
            prog0 = 1.0 - prog0
        else:
            prog1 = 1.0 - prog1
        # TODO: Improve the src_x/y so that it moves at the same speed as ovr_x/y, with the midpoint.
        src_x, src_y, ovr_x, ovr_y = {
         'north': (0,  prog1*frame.height,   0,  frame.height-prog0*(self.obs_frame.height+2*frame.height)),
         'south': (0,  prog0*frame.height,   0,  frame.height-prog1*(self.obs_frame.height+2*frame.height)),
         'east':  (prog0*frame.width, 0,     frame.width-prog1*(self.obs_frame.width+2*frame.width), 0),
         'west':  (prog1*frame.width, 0,     frame.width-prog0*(self.obs_frame.width+2*frame.width), 0),
        }[self.direction]
        if self.direction in ['east', 'south']:
            from_frame, to_frame = to_frame, from_frame
        src_x = int(round(src_x))
        src_y = int(round(src_y))
        Frame.copy_rect(dst=frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
        Frame.copy_rect(dst=frame, dst_x=src_x, dst_y=src_y, src=to_frame, src_x=src_x, src_y=src_y, width=from_frame.width-src_x, height=from_frame.height-src_y, op='copy')
        Frame.copy_rect(dst=frame, dst_x=ovr_x, dst_y=ovr_y, src=self.obs_frame, src_x=0, src_y=0, width=self.obs_frame.width, height=self.obs_frame.height, op=self.composite_op)
        return frame


class CrossFadeTransition(LayerTransitionBase):
    """Performs a cross-fade between two layers.  As one fades out the other one fades in."""
    def __init__(self, width=128, height=32, frame_count=45):
        LayerTransitionBase.__init__(self)
        self.width, self.height = width, height
        self.progress_per_frame = 1.0/frame_count

    def transition_frame(self, from_frame, to_frame):
        alpha_value = (self.progress * 255)
        
        from_frame = from_frame.copy()
        to_frame = to_frame.copy()
        sdl2.SDL_SetTextureAlphaMod(from_frame.pySurface.texture, int(255-alpha_value))
        
        #sdl2.SDL_SetTextureAlphaMod(to_frame.pySurface.texture, int(alpha_value))
        
        Frame.copy_rect(dst=to_frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=self.width, height=self.height) #, op='add')
        
        return to_frame

class FadeTransition(LayerTransitionBase):
    """Performs a fade in or out."""
    def __init__(self, frame_count=45, direction='in'):
        self.direction = direction
        LayerTransitionBase.__init__(self)
        #self.width, self.height = width, height
        self.progress_per_frame = 1.0/frame_count


    def transition_frame(self, from_frame, to_frame=None):
        # Calculate the frame index:
        if self.direction == 'in':
            alpha_value = (self.progress * 255)
            frame = to_frame.copy()
        else:
            alpha_value = 255-(self.progress * 255)
            frame = from_frame.copy()

        sdl2.SDL_SetTextureAlphaMod(frame.pySurface.texture, int(alpha_value))

        
        return frame
