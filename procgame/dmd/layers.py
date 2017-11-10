from dmd import *
from procgame import config
from random import randrange
import hdfont
import logging
try:
    import cv2
    import cv2 as cv
    from movie import capPropId, getColorProp
    OpenCV_avail = True
    from movie import Movie
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.error("OpenCV is not available on your system.  The MovieLayer (mp4) support is unavailable")
    OpenCV_avail = False
    
class FrameLayer(Layer):
    """Displays a single frame."""
    
    blink_frames = None # Number of frame times to turn frame on/off
    blink_frames_counter = 0
    frame_old = None
    
    def __init__(self, opaque=False, frame=None):
        super(FrameLayer, self).__init__(opaque)
        self.frame = frame
    def next_frame(self):
        if self.blink_frames > 0:
            if self.blink_frames_counter == 0:
                self.blink_frames_counter = self.blink_frames
                if self.frame == None:
                    self.frame = self.frame_old
                else:
                    self.frame_old = self.frame
                    self.frame = None
            else:
                self.blink_frames_counter -= 1
        return self.frame

    def stop_blinking(self):
        self.blink_frames = 0
        self.blink_frames_counter = 0
        if(self.frame is None):
            self.frame = self.frame_old


class ScaledLayer(Layer):
    """ a layer that scales it's contents to a specific size 
        most useful if a scaled layer contains a grouped layer
    """
    def __init__(self, width, height, content_layer):
        super(ScaledLayer, self).__init__(content_layer.opaque)
        self.width = width
        self.height = height
        self.content_layer = content_layer
        self.nframe = None

    def next_frame(self):
        if(self.nframe is not None):
            del self.nframe

        t = self.content_layer.next_frame()

        if(t is None):
            return None
        else:
            self.nframe = t.copy()
            self.nframe.scale(0.5, new_w=self.width, new_h=self.height)
        return self.nframe

class SolidLayer(Layer):
    def __init__(self, width, height, color, opaque=True):
        super(SolidLayer, self).__init__(opaque)
        self.frame = Frame(width,height)
        self.frame.fill_rect(0,0,width,height,color)#.append(255))
    def next_frame(self):
        return self.frame


class AnimatedLayer(Layer):
    """Collection of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen."""
    
    hold = True
    """``True`` if the last frame of the animation should be held on-screen indefinitely."""
    
    repeat = False
    """``True`` if the animation should be repeated indefinitely."""
    
    frame_time = 1
    """Number of frame times each frame should be shown on screen before advancing to the next frame.  The default is 1."""
    
    frame_pointer = 0
    """Index of the next frame to display.  Incremented by :meth:`next_frame`."""
    
    def __init__(self, opaque=False, hold=True, repeat=False, frame_time=1, frames=None):
        super(AnimatedLayer, self).__init__(opaque)
        self.hold = hold
        self.repeat = repeat
        self.fps = config.value_for_key_path('dmd_framerate', None) 
        if frames == None:
            self.frames = list()
        else:
            self.frames = frames
        
        self.frame_time = frame_time # Number of frames each frame should be displayed for before moving to the next.
        self.frame_time_counter = self.frame_time
        
        self.frame_listeners = []
        self.frame_sequence=[]
        
        self.reset()

    def play_sequence(self, sequence, repeat=None, seq_when_done=None, hold_last=None):
        self.frame_sequence = sequence
        self.frame_listeners = []

        if(repeat is not None):
            self.repeat = repeat
        if(hold_last is not None):
            self.hold = hold_last
        if(seq_when_done is not None):
            self.add_frame_listener(-1,self.play_sequence,seq_when_done)
        self.reset()


    def duration(self):
        """Returns the duration of the animation, as played once through."""
        if(self.frame_sequence is not None and len(self.frame_sequence) > 0):
            return (len(self.frame_sequence) * self.frame_time) / self.fps
        return (len(self.frames) * self.frame_time) / self.fps 
    
    def reset(self):
        """Resets the animation back to the first frame."""
        self.frame_pointer = 0
        self.frame_sequence_pointer = 0
    
    def add_frame_listener(self, frame_index, listener, arg=None):
        """Registers a method (``listener``) to be called when a specific 
        frame number (``frame_index``) in the animation has been reached.
        Negative numbers, like Python list indexes, indicate a number of
        frames from the last frame.  That is, a ``frame_index`` of -1 will
        trigger on the last frame of the animation.
        """
        self.frame_listeners.append((frame_index, listener, arg))
    
    def notify_frame_listeners(self):
        for frame_listener in self.frame_listeners:
            (index, listener, arg) = frame_listener
            if(self.frame_sequence is not None):
                if(self.frame_sequence_pointer == (len(self.frame_sequence) + index)):
                    #print("Calling listener for %d" % self.frame_sequence[self.frame_sequence_pointer])
                    if(arg is None):
                        listener()
                    else:
                        listener(arg)
            elif index >= 0 and self.frame_pointer == index:
                listener(arg)
            elif self.frame_pointer == (len(self.frames) + index):
                listener(arg)

    
    def next_frame(self):
        """Returns the frame to be shown, or None if there is no frame."""
        #we have to see if we are using a frame seqence or not
        
        #hmm, what are theyse next lines  really doing . . . 
        if self.frame_sequence:
            if self.frame_sequence_pointer >= len(self.frame_sequence):
                return None
        
        elif self.frame_pointer >= len(self.frames):
            return None
        
        # Important: Notify the frame listeners before frame_pointer has been advanced.
        # Only notify the listeners if this is the first time this frame has been shown
        # (such as if frame_time is > 1).
        if self.frame_time_counter == self.frame_time:
            self.notify_frame_listeners()

        self.frame_time_counter -= 1
        
        if self.frame_sequence:
            #print 'This is using a frame sequence'
            frame = self.frames[self.frame_sequence[self.frame_sequence_pointer]]

            
            if len(self.frame_sequence) > 1 and self.frame_time_counter == 0:
                if (self.frame_sequence_pointer == len(self.frame_sequence)-1):  #last frame
                    if self.repeat:
                        #self.frame_pointer = self.frame_listeners[0]
                        self.frame_sequence_pointer=0
                    elif not self.hold:
                        self.frame_sequence_pointer += 1
                else:
                    self.frame_sequence_pointer += 1
            
        else:
            frame = self.frames[self.frame_pointer]
            
            if len(self.frames) > 1 and self.frame_time_counter == 0:
                if (self.frame_pointer == len(self.frames)-1):
                    if self.repeat:
                        self.frame_pointer = 0
                    elif not self.hold:
                        self.frame_pointer += 1
                else:
                    self.frame_pointer += 1
    
        if self.frame_time_counter == 0:
            self.frame_time_counter = self.frame_time
        
        return frame




class MovieLayer(Layer):
    """This will pull the next frame from an mp4 (or other supported video format
    and converts it to a frame/surface)
 Optionally holds the last frame on-screen."""
    
    hold = True
    """``True`` if the last frame of the animation should be held on-screen indefinitely."""
    
    repeat = False
    """``True`` if the animation should be repeated indefinitely."""
    
    frame_time = 1
    """Number of frame times each frame should be shown on screen before advancing to the next frame.  The default is 1."""
    
    frame_pointer = 0
    """Index of the next frame to display.  Incremented by :meth:`next_frame`."""
    
    vc = None
    """ this is the video controller that is handling the interface to the video
    it handles the next frame stuff"""

    composite_op = None
    """ set via transparency_op argument,  value of blacksrc, magentasrc, etc. will cause those pixels to be translated
        to transparent.  Performance may drop as a result of using this argument
    """
    
    duration = None

    def __init__(self, opaque=False, hold=True, repeat=False, frame_time=1, movie=None, movie_file_path=None, transparency_op=None):
        if(cv2 is None):
            raise ValueError, "MP4 is unavailable as OpenCV is not installed"
        # self.logger = logging.getLogger('movie_layer')

        super(MovieLayer, self).__init__(opaque)
        self.hold = hold
        self.repeat = repeat
        
        if(movie is None and movie_file_path is None):
            raise ValueError, "MovieLayer requires either a movie_file_path argument -or- an instantiated movie object"
        elif(movie_file_path is not None):
            movie = Movie(movie_file_path)

        self.movie = movie

        if self.movie.vc == None:
            raise ValueError, "OpenCV failed to handle this movie"
            pass  #something bad has happened, need to decide how to handle

        # print("movie loaded: frame count = %d." % self.movie.frame_count)
        
        self.frame_time = frame_time # Number of frames each frame should be displayed for before moving to the next.
        self.frame_time_counter = self.frame_time
        
        self.frame_listeners = []
        self.frame_pointer = 0

        self.composite_op = transparency_op
        
        self.frame = Frame(self.movie.width, self.movie.height)
        self.fps = config.value_for_key_path('dmd_framerate', None) 
        self.reset()
    
    def duration(self):
        """Returns the duration of the animation, as played once through."""
        if(self.movie.vc is not None):
            return (self.movie.frame_count * self.frame_time) / self.fps
        return 0

    def reset(self):
        """Resets the animation back to the first frame."""
        self.frame_pointer = 0
        # and reset the video capture position to 0
        self.movie.vc.set(capPropId("POS_FRAMES"),0)
    
    def add_frame_listener(self, frame_index, listener):
        """Registers a method (``listener``) to be called when a specific 
        frame number (``frame_index``) in the animation has been reached.
        Negative numbers, like Python list indexes, indicate a number of
        frames from the last frame.  That is, a ``frame_index`` of -1 will
        trigger on the last frame of the animation.
        """
        self.frame_listeners.append((frame_index, listener))
    
    def notify_frame_listeners(self):
        for frame_listener in self.frame_listeners:
            (index, listener) = frame_listener
            if index >= 0 and self.frame_pointer == index:
                listener()
            elif self.frame_pointer == (len(self.frames) + index):
                listener()
                
    
    def next_frame(self):
        """Returns the frame to be shown, or None if there is no frame."""
        #lets check if we are at end of video and if not, grab next frame
        #and convert to a surface and shove into frame
        
        # Important: Notify the frame listeners before frame_pointer has been advanced.
        # Only notify the listeners if this is the first time this frame has been shown
        # (such as if frame_time is > 1).
        if self.frame_time_counter == self.frame_time:
            self.notify_frame_listeners()
        
        self.frame_time_counter -= 1
        
        rval = None
        #now we grab the next frame
        if (self.frame_pointer >= self.movie.frame_count) and self.frame_time_counter == 0:
            if self.repeat:
                self.frame_pointer = 0
                self.movie.vc.set(capPropId("POS_FRAMES"),0)
            elif self.hold:
                self.frame_time_counter = self.frame_time
                return self.frame
            else:
                self.frame_time_counter = 0
                return None
        
        video_frame = None
        if self.frame_time_counter == 0:
            rval, video_frame = self.movie.vc.read()
            self.frame_pointer += 1
            self.frame_time_counter = self.frame_time

            if rval is True and video_frame is not None:
                # self.logger.info("pulling frame %d / %d" % (self.frame_pointer, self.movie.frame_count))
                video_frame = cv2.cvtColor(video_frame,getColorProp())
                the_frame = video_frame #tODO: OpenCV3 fix cv.fromarray(video_frame)
                # surface = pygame.image.frombuffer(the_frame.tostring(), (self.movie.width, self.movie.height), 'RGB')
                surf = sdl2_DisplayManager.inst().make_texture_from_imagebits(bits=the_frame.tostring(), width=self.movie.width, height=self.movie.height, mode='RGB', composite_op = self.composite_op)

                self.frame.pySurface = surf
            else:
                # self.logger.info("ERROR OCCURED [%s] [%s]" % (rval, video_frame))
                # end movie prematurely
                self.movie.frame_count = self.frame_pointer - 1



        return self.frame




class FrameQueueLayer(Layer):
    """Queue of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen.
    Destroys the frame list as it displays frames.  In that respect this class implements the old behavior
    of :class:`AnimatedLayer`.
    """
    def __init__(self, opaque=False, hold=True, repeat=False, frame_time=1, frames=None):
        super(FrameQueueLayer, self).__init__(opaque)
        self.hold = hold
        self.repeat = repeat
        if frames == None:
            self.frames = list()
        else:
            self.frames = frames
        self.frame_time = frame_time # Number of frames each frame should be displayed for before moving to the next.
        self.frame_time_counter = self.frame_time
    
    def next_frame(self):
        """Returns the frame to be shown, or None if there is no frame."""
        if len(self.frames) == 0:
            return None
        frame = self.frames[0] # Get the first frame in this layer's list.
        self.frame_time_counter -= 1
        if (self.hold == False or len(self.frames) > 1) and (self.frame_time_counter == 0):
            if self.repeat:
                f = self.frames[0]
                del self.frames[0]
                self.frames += [f]
            else:
                del self.frames[0] # Pop off the frame if there are others
        if self.frame_time_counter == 0:
            self.frame_time_counter = self.frame_time
        return frame



class TextLayer(Layer):
    """Layer that displays text."""
    
    fill_color = None
    text = None
    """Dot value to fill the frame with.  Requres that ``width`` and ``height`` be set.  If ``None`` only the font characters will be drawn."""
    
    def __init__(self, x, y, font, justify="left", opaque=False, width=None, height=None, fill_color=None):
        super(TextLayer, self).__init__(opaque)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.font = font
        self.started_at = None
        self.seconds = None # Number of seconds to show the text for
        self.frame = None # Frame that text is rendered into.
        self.frame_old = None
        self.justify = justify
        self.blink_frames = None # Number of frame times to turn frame on/off
        self.blink_frames_counter = 0

    def set_text(self, text, seconds=None, blink_frames=None):
        """Displays the given message for the given number of seconds."""
        if(self.text is not None and self.text == text): 
            return self

        self.text = text
        self.started_at = None
        self.seconds = seconds
        self.blink_frames = blink_frames
        self.blink_frames_counter = self.blink_frames
        if text == None:
            self.frame = None
        else:
            (w, h) = self.font.size(text)
            x, y = 0, 0
            if self.justify == 'left':
                (x, y) = (0,0)
            elif self.justify == 'right':
                (x, y) = (-w,0)
            elif self.justify == 'center':
                (x, y) = (-w/2,0)


            if self.fill_color != None and self.width != None and self.height != None:
                #width and height must not be none
                #self.set_target_position(0, 0)
                #self.frame = Frame(width=self.width, height=self.height)
                #self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
                #self.font.draw(self.frame, text, self.x + x, self.y + y)
                #
                self.set_target_position(self.x, self.y)
                self.frame = Frame(self.width, self.height)
                self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color) # but taking this away shouldn't break it should it??
                self.font.draw(self.frame, text, 0, 0)
                (self.target_x_offset, self.target_y_offset) = (x,y)
                
            else:
                self.set_target_position(self.x, self.y)
                (w, h) = self.font.size(text)
                (w,h) = (max(w,1),max(h,1))
                self.frame = Frame(w, h)
                self.frame.fill_rect(0, 0, w, h, (0,0,0,0)) # but taking this away shouldn't break it should it??
                self.font.draw(self.frame, text, 0, 0)
                (self.target_x_offset, self.target_y_offset) = (x,y)
            # self.frame = Frame(self.width, self.height)
            # if self.fill_color != None:
            #     self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
            # if self.justify == 'left':
            #     anchor = hdfont.AnchorW
            # elif self.justify == 'right':
            #     anchor = hdfont.AnchorE
            # elif self.justify == 'center':
            #     anchor = hdfont.AnchorCenter

            # self.font.draw_in_rect(self.frame, text, (self.x,self.y,self.width,self.height), anchor=anchor)

        return self

    # def set_text(self, text, seconds=None, blink_frames=None):
    #     """Displays the given message for the given number of seconds."""
    #     if(self.text is not None and self.text == text): 
    #         return self

    #     self.text = text
    #     self.started_at = None
    #     self.seconds = seconds
    #     self.blink_frames = blink_frames
    #     self.blink_frames_counter = self.blink_frames
    #     if text == None:
    #         self.frame = None
    #     else:
    #         (w, h) = self.font.size(text)
    #         x, y = 0, 0
    #         if self.justify == 'left':
    #             (x, y) = (0,0)
    #         elif self.justify == 'right':
    #             (x, y) = (-w,0)
    #         elif self.justify == 'center':
    #             (x, y) = (-w/2,0)

    #         if self.fill_color != None:
    #             self.set_target_position(0, 0)
    #             self.frame = Frame(width=self.width, height=self.height)
    #             self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
    #             self.font.draw(self.frame, text, self.x + x, self.y + y)
    #         else:
    #             self.set_target_position(self.x, self.y)
    #             (w, h) = self.font.size(text)
    #             self.frame = Frame(w, h)
    #             self.font.draw(self.frame, text, 0, 0)
    #             (self.target_x_offset, self.target_y_offset) = (x,y)

    #     return self

    def next_frame(self):
        if self.started_at == None:
            self.started_at = time.time()
        if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
            self.frame = None
        elif self.blink_frames > 0:
            if self.blink_frames_counter == 0:
                self.blink_frames_counter = self.blink_frames
                if self.frame == None:
                    self.frame = self.frame_old
                else:
                    self.frame_old = self.frame
                    self.frame = None
            else:
                self.blink_frames_counter -= 1
        return self.frame

    def is_visible(self):
        return self.frame != None


class AnimatedTextLayer(TextLayer):
    
    def __init__(self, x, y, font, justify="left", opaque=False, width=192, height=96, fill_color=None, frame_time = 1):
        super(AnimatedTextLayer, self).__init__( x, y, font, justify, opaque, width, height, fill_color)
        
        self.frame_time = frame_time # Number of frames each frame should be displayed for before moving to the next.
        self.frame_time_counter = self.frame_time

    def next_frame(self):
        if self.started_at == None:
            self.started_at = time.time()
        if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
            self.frame = None
        # elif self.blink_frames > 0:
        #     if self.blink_frames_counter == 0:
        #         self.blink_frames_counter = self.blink_frames
        #         if self.frame == None:
        #             self.frame = self.frame_old
        #         else:
        #             self.frame_old = self.frame
        #             self.frame = None
        #     else:
        #         self.blink_frames_counter -= 1
        if(self.frame_time_counter == 0):
            self.set_text(self.text, seconds=self.seconds)
            self.frame_time_counter = self.frame_time
        else:
            self.frame_time_counter = self.frame_time_counter - 1
        return self.frame

    def set_text(self, text, seconds=None, blink_frames=None):
        """Displays the given message for the given number of seconds."""
        if(text is None): 
            return self

        self.text = text
        self.started_at = None
        self.seconds = seconds
        self.blink_frames = blink_frames
        self.blink_frames_counter = self.blink_frames
        if text == None:
            self.frame = None
        else:
            (w, h) = self.font.size(text)
            x, y = 0, 0
            if self.justify == 'left':
                (x, y) = (0,0)
            elif self.justify == 'right':
                (x, y) = (-w,0)
            elif self.justify == 'center':
                (x, y) = (-w/2,0)

            if self.fill_color != None:
                self.set_target_position(0, 0)
                self.frame = Frame(width=self.width, height=self.height)
                self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
                self.font.draw(self.frame, text, self.x + x, self.y + y)
            else:
                self.set_target_position(self.x, self.y)
                (w, h) = self.font.size(text)
                (w,h) = (max(w,1),max(h,1))
                self.frame = Frame(w, h)
                self.frame.fill_rect(0, 0, w, h, (0,0,0,0)) # but taking this away shouldn't break it should it??
                self.font.draw(self.frame, text, 0, 0)
                (self.target_x_offset, self.target_y_offset) = (x,y)
        return self


class ScriptedLayer(Layer):
    """Displays a set of layers based on a simple script.
    
    **Script Format**
    
    The script is an list of dictionaries.  Each dictionary contains two keys: ``seconds`` and
    ``layer``.  ``seconds`` is the number of seconds that ``layer`` will be displayed before 
    advancing to the next script element.
    
    If ``layer`` is ``None``, no frame will be returned by this layer for the duration of that script
    element.
    
    Example script::
    
      [{'seconds':3.0, 'layer':self.game_over_layer}, {'seconds':3.0, 'layer':None}]
    
    """
    def __init__(self, width, height, script, hold=False, opaque=False):
        super(ScriptedLayer, self).__init__(opaque)
        self.buffer = Frame(width, height)
        self.script = script
        self.hold = hold
        self.script_index = 0
        self.frame_start_time = None
        self.force_direction = None
        self.on_complete = None
        self.is_new_script_item = True
        self.last_layer = None
        self.on_next = None
        self.callback = []
    
    def next_frame(self):
        # This assumes looping.  TODO: Add code to not loop!
        holding=False 
        if self.frame_start_time == None:
            self.frame_start_time = time.time()
        
        #print "index and script length  "+ str(self.script_index) + "   " +  str(len(self.script))
        script_item = self.script[self.script_index]
        
        time_on_frame = time.time() - self.frame_start_time
        
        # If we are being forced to the next frame, or if the current script item has expired:
        if self.force_direction != None or time_on_frame > script_item['seconds']:
            
            self.last_layer = script_item['layer']
            
            # Update the script index:
            if self.force_direction == False:
                if self.script_index == 0:
                    self.script_index = len(self.script)-1 
                else:
                    self.script_index -= 1
            else:
                if self.script_index == len(self.script):
                    if not self.hold:
                        self.reset()
                    else:
                        holding = True
                        self.script_index -= 1
                else:
                    self.script_index += 1
            
            # Only force one item.
            self.force_direction = None
            
            # If we are at the end of the script, reset to the beginning:
            if self.script_index == len(self.script):
                if not self.hold:
                    self.reset()
                else:
                    holding = True
                    self.script_index -= 1
                if self.on_complete != None:
                    self.on_complete()
            else:
                if self.on_next != None:
                    self.on_next()
                    
            # Assign the new script item:
            if not holding:
                script_item = self.script[self.script_index]
                self.frame_start_time = time.time()
                
                layer = script_item['layer']
                if layer:
                    layer.reset()
                self.is_new_script_item = True
            
                if('callback' in script_item and script_item['callback'] is not None):
                    script_item['callback']()

        # Composite the current script item's layer:
        layer = script_item['layer']
        
        transition = None
        if layer and layer.transition:
            if self.is_new_script_item:
                layer.transition.start()
        
        self.is_new_script_item = False
        
        if layer:
            self.buffer.clear()
            
            # If the layer is opaque we can composite the last layer onto our buffer
            # first.  This will allow us to do transitions between script 'frames'.
            if self.last_layer and (self.opaque and layer.transition):
                self.last_layer.composite_next(self.buffer)
            
            layer.composite_next(self.buffer)
            return self.buffer
        else:
            # If this script item has None set for its layer, return None (transparent):
            return None

    def force_next(self, forward=True):
        """Advances to the next script element in the given direction."""
        self.force_direction = forward
    
    def duration(self):
        """Returns the complete duration of the script."""
        seconds = 0
        for script_item in self.script:
            seconds += script_item['seconds']
        return seconds

    def reset(self):
        #print 'RESET SCRIPTED LAYER      RESET SCRIPTED LAYER ' + str(self.script_index)
        self.script_index = 0
        #print self.script_index
        self.frame_start_time = None
        #now reset the layers
        for layer_item in self.script:
           # print layer_item['layer']
           if layer_item['layer'] != None:
               layer_item['layer'].reset()

    def regenerate(self):
        """ calls regenerate on layers that support it """
        for layer_item in self.script:
           if layer_item['layer'] != None and hasattr(layer_item['layer'],'regenerate'):
               layer_item['layer'].regenerate()

class ScriptlessLayer(ScriptedLayer):
    """ displays a set of layers but builds the script internally via helper methods

        Example:    sl = ScriptLessLayer(width, height)

        add items to the script with:
                    .append(layer,seconds)

        E.g.,
                    sl.append(first_layer, 2.0)
                    sl.append(second_layer, 4.0)
                    sl.append(third_layer, 2.0)
    """

    def __init__(self, width, height, opaque=False):
        script = list()
        super(ScriptlessLayer, self).__init__(width, height, script, opaque)

    def append(self, layer, seconds = None, callback = None):
        """ adds the given layer to the current script, to be displayed for seconds 
            if 'None' is specified for seconds, then the duration of the animation 
            will be used (which, if this isn't an animatedLayer, WILL be a problem.
        """
        if(seconds is None):
            seconds = layer.duration()
        if(callback is None):
        	self.script.append({'layer':layer, 'seconds':seconds})
        else:
            self.script.append({'layer':layer, 'seconds':seconds, 'callback':callback})

class ScoresLayer(ScriptlessLayer):
    def __init__(self, game, fields, fnt, font_style, background, duration):
        super(ScoresLayer, self).__init__(game.dmd.width, game.dmd.height)
        self.fields = fields
        self.fnt = fnt
        self.font_style = font_style
        self.game = game
        self.duration = duration
        self.background = background

    def regenerate(self):
        self.game.logger.info("re-generating scores layer!!!!!!!!!!!!!!!!!!!!")
        self.script = []
        entry_ct = len(self.game.get_highscore_data())
        for rec in self.game.get_highscore_data():
            if self.fields is not None:
                records = [rec[f] for f in self.fields]
            else:
                records = [rec['category'], rec['player'], rec['score']]
            self.game.logger.info("re-generating scores: %s " % str(records))
            lT = self.game.dmdHelper.genMsgFrame(records, self.background, font_key=self.fnt, font_style=self.font_style)

            self.append(lT, self.duration)

        duration = entry_ct*self.duration
        return duration

    def reset(self):
        super(ScoresLayer,self).reset()

class GroupedLayer(Layer):
    """:class:`.Layer` subclass that composites several sublayers (members of its :attr:`layers` list attribute) together."""
    
    layers = None
    """List of layers to be composited together whenever this layer's :meth:`~Layer.next_frame` is called.
    
    Layers are composited first to last using each layer's
    :meth:`~procgame.dmd.Layer.composite_next` method.  Compositing is ended after a layer that returns
    non-``None`` from :meth:`~Layer.composite_next` is :attr:`~Layer.opaque`."""
    
    def __init__(self, width=None, height=None, layers=None, fill_color=None, opaque=False):
        """ size is auto-detected from layers if omitted """
        if(width is None or height is None):
            if(layers is None):
                raise ValueError, "Cannot create an unsized grouped layer with no contents!"
            if(width is None):
                width = max([l.get_width() for l in layers])
            if(height is None):
                height = max([l.get_height() for l in layers])

        super(GroupedLayer, self).__init__(opaque)
        self.buffer = Frame(width, height)
        self.fill_color = fill_color
        if layers == None:
            self.layers = list()
        else:
            self.layers = layers

    @property
    def width(self):
        return self.buffer.width

    @property
    def height(self):
        return self.buffer.height

    def reset(self):
        for layer in self.layers:
            if(layer is not None):
                layer.reset()

    def next_frame(self):       
        layers = []
        for layer in self.layers[::-1]:
            if(layer is not None):
                layers.append(layer)
                if layer.opaque:
                    break # if we have an opaque layer we don't render any lower layers
        # the following would let groups engage in their old behavior of filling black
        # if not blacksrc'd but truly this is 'wrong' so programmers are recommended
        # to change their implementations, instead.

        if(self.fill_color is None):
            self.buffer.clear()
        else:
            self.buffer.clear(self.fill_color)
           
        composited_count = 0
        for layer in layers[::-1]:
            frame = None
            if layer.enabled:
                frame = layer.composite_next(self.buffer)
            if frame != None:
                composited_count += 1
        if composited_count == 0:
            return None
        return self.buffer

class RandomizedLayer(GroupedLayer):
    """ Layer that contains other layers and shows one at random when requested """
    def __init__(self, layers):
        if(layers is None):
            raise ValueError, "Cannot initialize a RandomizedLayer with no content layers!"

        super(RandomizedLayer, self).__init__(layers[0].width, layers[0].height, layers, layers[0].opaque)
        self.layer = None

    def reset(self):
        for layer in self.layers:
            if(layer is not None):
                layer.reset()
        self.randomize()

    def randomize(self):
        self.layer = None
        idx = randrange(0,len(self.layers))
        self.layer = self.layers[idx]
        self.opaque = self.layers[idx].opaque
        self.fill_color = self.layers[idx].opaque

    def next_frame(self):       
        if(self.layer is None):
            return None
        return self.layer.next_frame()

class PanningLayer_pysurf(Layer):
    """Pans a frame about on a (width)x(height) buffer, possibly bouncing when it reaches the boundaries.
        translate is a pair (x,y) which indicates the amount to move the frame per update; 
        a positive y-value moves down, because the origin is top-left. 
    """
    def __init__(self, width, height, frame, origin, translate, bounce=True, numFramesDrawnBetweenMovementUpdate=3):
        super(PanningLayer, self).__init__()

        self.width = width
        self.height = height
        self.src_frame = frame

        self.buffer = Frame(self.width, self.height)
        Frame.copy_rect(dst=self.buffer, dst_x=0, dst_y=0, src=self.src_frame, src_x=0, src_y=0, width=self.src_frame.width, height=self.src_frame.height)

        self.origin = origin
        self.original_origin = origin
        self.translate = translate 
        self.bounce = bounce
        self.holdFrames = numFramesDrawnBetweenMovementUpdate
        self.tick = 0
        # Make sure the translate value doesn't cause us to do any strange movements:
        if width == frame.width:
            self.translate = (0, self.translate[1])
        if height == frame.height:
            self.translate = (self.translate[0], 0)

    def reset(self):
        self.origin = self.original_origin
        # self.buffer.clear()
        Frame.copy_rect(dst=self.buffer, dst_x=0, dst_y=0, src=self.src_frame, src_x=0, src_y=0, width=self.src_frame.width, height=self.src_frame.height)

    def next_frame(self):
        self.tick += 1
        if (self.tick % self.holdFrames) != 0:
            return self.buffer
        # Frame.copy_rect(dst=self.buffer, dst_x=0, dst_y=0, src=self.src_frame, src_x=self.origin[0], src_y=self.origin[1], width=self.buffer.width, height=self.buffer.height)

        if self.bounce:
            if self.translate[0] > 0 and (self.origin[0] + self.src_frame.width + self.translate[0] > self.width):
                self.translate = (self.translate[0] * -1, self.translate[1])
                # print("hit right side")
            elif self.translate[0] < 0 and (self.origin[0] + self.translate[0] < 0):
                self.translate = (self.translate[0] * -1, self.translate[1])
                # print("hit left side")
            if self.translate[1] > 0 and (self.origin[1] + self.src_frame.height + self.translate[1] > self.height):
                self.translate = (self.translate[0], self.translate[1] * -1)
                # print("hit bottom")
            elif  self.translate[1] < 0 and (self.origin[1] + self.translate[1] < 0):                 
                self.translate = (self.translate[0], self.translate[1] * -1)
                # print("hit top")
        self.origin = (self.origin[0] + self.translate[0], self.origin[1] + self.translate[1])

        self.buffer.pySurface.scroll(self.translate[0],self.translate[1])

        return self.buffer


class PanningLayer(Layer):
    """Pans a frame about on a 128x32 buffer, bouncing when it reaches the boundaries."""
    def __init__(self, width, height, frame, origin, translate, bounce=True, numFramesDrawnBetweenMovementUpdate=3, fill_color=None):

        if(isinstance(frame, Frame)):
            self.content_layer = FrameLayer(frame=frame)
        else:
            self.content_layer = frame
        

        super(PanningLayer, self).__init__()

        self.width = width
        self.height = height
        self.buffer = Frame(width, height)
        #self.frame = frame
        # self.buffer = self.frame.copy()
        self.origin = origin
        self.original_origin = origin
        self.translate = translate #(-translate[0],-translate[1])
        self.bounce = bounce
        self.holdFrames = numFramesDrawnBetweenMovementUpdate
        self.tick = 0
        self.fill_color=fill_color
        # Make sure the translate value doesn't cause us to do any strange movements:
        # if width == frame.width:
        #     self.translate = (0, self.translate[1])
        # if height == frame.height:
        #     self.translate = (self.translate[0], 0)

    def reset(self):
        self.origin = self.original_origin
        #self.buffer = self.frame.copy()
        self.content_layer.reset()

    def next_frame(self):
        self.tick += 1
        frame = self.content_layer.next_frame()
        if(frame is None):
            return None

        if (self.tick % self.holdFrames) == 0:
            if self.bounce:
                if self.translate[0] < 0 and (-self.origin[0] + frame.width + self.translate[0] > self.width):
                    self.translate = (self.translate[0] * -1, self.translate[1])
                    # print("hit right side")
                elif self.translate[0] > 0 and (-self.origin[0] + self.translate[0] < 0):
                    self.translate = (self.translate[0] * -1, self.translate[1])
                    # print("hit left side")
                if self.translate[1] < 0 and (-self.origin[1] + frame.height + self.translate[1] > self.height):
                    self.translate = (self.translate[0], self.translate[1] * -1)
                    # print("hit top")
                elif  self.translate[1] > 0 and (-self.origin[1] + self.translate[1] < 0):                 
                    self.translate = (self.translate[0], self.translate[1] * -1)
                    # print("hit bottom")

            self.origin = (self.origin[0] + self.translate[0], self.origin[1] + self.translate[1])

        if(self.fill_color is None):
            self.buffer.clear()
        else:
            self.buffer.clear(self.fill_color)

        Frame.copy_rect(dst=self.buffer, dst_x=-self.origin[0], dst_y=-self.origin[1], src=frame, src_x=0, src_y=0, width=frame.width, height=frame.height)

        return self.buffer

class RotationLayer(Layer):
    def __init__(self, x, y, rotation_per_update, content_layer, opaque=False, fill_color=None):
        self.x = x
        self.y = y
        self.rotation = 0
        self.rotation_per_update = rotation_per_update
        self.content_layer = content_layer
        self.width = content_layer.width
        self.height = content_layer.height
        self.opaque=opaque
        self.fill_color = fill_color

    def next_frame(self):
        self.tmp = self.content_layer.next_frame()
        (w,h) = self.tmp.pySurface.size
        dest = (0,0,w,h) 
        self.rotation = self.rotation + self.rotation_per_update
        self.buffer = Frame(w,h)
        sdl2_DisplayManager.inst().roto_blit(self.tmp.pySurface, self.buffer.pySurface, dest, angle=self.rotation)
        self.buffer.target_x_offset = self.x
        self.buffer.target_y_offset = self.y
        return self.buffer

class ZoomingLayer(Layer):
    """ A layer that zooms another layer.  

        TODO: Detect text style layers and change the relative x/y position of the next_frame to honor the
                justification parameters of the underlying text layer.
        """
    orig_x = 0
    orig_y = 0
    orig_w = 0
    orig_h = 0

    def __init__(self, layer_to_zoom, hold=False, frames_per_zoom = 1, scale_start = 1.0, scale_stop = 2.0, total_zooms=30):
        """Will call 'next_frame' on the @param layer_to_zoom, and will zoom 
        that layer from @param scale_start through @param scale_stop, showing the frame at each scaled size
        for @param frames_per_zoom many frames.  The total number of zoomed frames to be displayed is 
        @param total_zooms.  If @param hold is True, then next_frame will continue to be called and displayed
        at the final zoom scale.  If @param is False then the Layer will retun None after returning the last zoomed
        frame for the appropriate number of frames_per zoom.
        """
        self.source_layer = layer_to_zoom 
        self.scale_stop = scale_stop
        self.scale_start = scale_start
        self.scale_current = scale_start
        self.frames_per_zoom = frames_per_zoom
        self.frames_to_show = frames_per_zoom
        self.total_zooms = total_zooms
        self.total_zoomed = 0
        self.nframe = None
        self.hold = hold
        self.scale_per_step = float(scale_stop - scale_start)/total_zooms
        
    def next_frame(self):       
        if(self.total_zoomed > self.total_zooms and self.hold is False):
            return None

        if(self.nframe is not None):
            del self.nframe
        self.nframe = self.source_layer.next_frame().copy()
        
        if(self.nframe is None):
            return None

        # 1. Zoom this frame
        self.nframe.scale(self.scale_current)

        # TODO determine if layer_to_zoom is a text layer and adjust x/y to honor justification
        
        # 2. if we aren't done zooming, decrease the zoom counter and compute next zoom
        if(self.total_zoomed < self.total_zooms):
            self.frames_to_show -= 1
            if(self.frames_to_show == 0):
                # 3. if the zoom counter is zero, reset and change zoom amount by step
                self.frames_to_show = self.frames_per_zoom
                # compute next zoom
                self.scale_current = self.scale_current + self.scale_per_step
                
                self.total_zoomed += 1

        return self.nframe

class HDTextLayer(TextLayer):
    """Layer that displays text."""
    
    fill_color = None
    line_color = None
    interior_color = None
    line_width = 0
    text = None
    style = None

    # def __init__(self, x, y, font, justify="left", opaque=False, width=192, height=96, fill_color=None):

    def __init__(self, x, y, font, justify="left", vert_justify=None, opaque=False, width=192, height=96, line_color=None, line_width=0, interior_color=(255,255,255), fill_color=None, fontstyle=None):
        super(HDTextLayer, self).__init__(x,y,font,justify,opaque,width,height,fill_color)
        # self.x = x
        # self.y = y
        # self.width = width
        # self.height = height
        if fontstyle != None:
            
            self.line_color=fontstyle.line_color
            self.line_width=fontstyle.line_width
            self.interior_color=fontstyle.interior_color
            self.fill_color=fontstyle.fill_color
            self.style = fontstyle
        else:
            self.interior_color = interior_color
            self.line_color = line_color
            self.fill_color = fill_color
            self.line_width = line_width
        
        self.Vjustify = vert_justify
        # self.font = font
        # self.started_at = None
        # self.seconds = None # Number of seconds to show the text for
        # self.frame = None # Frame that text is rendered into.
        # self.frame_old = None
        # self.justify = justify
        # self.blink_frames = None # Number of frame times to turn frame on/off
        # self.blink_frames_counter = 0


    def set_text(self, text, seconds=None, blink_frames=None, style=None, force_update=False):
        """Displays the given message for the given number of seconds."""
        if((self.text is not None and self.text == text) and not force_update): 
            return self
        #print("set_text: '%s'" % text)

        self.text = text
        self.started_at = None
        self.seconds = seconds
        self.blink_frames = blink_frames
        self.blink_frames_counter = self.blink_frames

        if(style is not None):
            fill_color = style.fill_color 
            line_color = style.line_color 
            interior_color = style.interior_color 
            line_width = style.line_width 
        elif(self.style is not None):
            fill_color = self.style.fill_color 
            line_color = self.style.line_color 
            interior_color = self.style.interior_color 
            line_width = self.style.line_width 
        else:
            fill_color = self.fill_color 
            line_color = self.line_color 
            interior_color = self.interior_color 
            line_width = self.line_width 

        if(fill_color is None):
            fill_color = self.fill_color

        if(fill_color == (0,0,0) and self.composite_op == 'blacksrc'):
            fill_color = None

        # crazy composite_op sensing fixes
        # if(interior_color == (0,0,0) and self.composite_op == 'blacksrc'):
        #     interior_color = None
        # if(interior_color == (0,255,0) and self.composite_op == 'greensrc'):
        #     interior_color = None
        # if(interior_color == (255,0,255) and self.composite_op == 'magentasrc'):
        #     interior_color = None


        if text == None or text=="":
            self.frame = None
        else:
            (w, h) = self.font.size(text)
            x, y = 0, 0
            if self.justify == 'left':
                (x, y) = (0,0)
            elif self.justify == 'right':
                (x, y) = (-w,0)
            elif self.justify == 'center':
                (x, y) = (-w/2,0)

            (wOfText, hOfText) = self.font.size(text)
            (wOfText , hOfText) = (wOfText+(2*line_width), hOfText+(2*line_width))
            self.text_width = wOfText
            self.text_height = hOfText
            x, y = 0, 0
            rectx, recty = 0, 0
            x_offset, y_offset = 0,0

            if self.justify == 'left':
                x_offset = 0
            elif self.justify == 'right':
                x_offset = -1
            elif self.justify == 'center':
                x_offset = -0.5

            if self.Vjustify == 'bottom':
                y_offset = -1
            elif self.Vjustify == 'center':
                y_offset = -0.5
            # the use of fill_color is intentional...
            if fill_color != None:
                (x,y) = (self.width*x_offset, self.height*y_offset)
                self.set_target_position(x, y)

                self.frame = Frame(width=self.width, height=self.height)
                self.frame.fill_rect(0, 0, self.width, self.height, fill_color)

                (x, y) = ((wOfText-self.width)*x_offset, (hOfText-self.height)*y_offset)
                
                self.font.drawHD(self.frame, text, x, y, line_color, line_width, interior_color, None)
                # self.font.draw(self.frame, text, x, y, interior_color)

                (self.target_x_offset, self.target_y_offset) = (self.x,self.y)
            else:
                (x, y) = (wOfText*x_offset, hOfText*y_offset)
                self.set_target_position(self.x, self.y)
                self.frame = Frame(wOfText, hOfText)
                # I think this fixes it??
                self.frame.fill_rect(0, 0, wOfText, hOfText, (0,0,0,0)) # but taking this away shouldn't break it should it??

                self.font.drawHD(self.frame, text, 0, 0, line_color, line_width, interior_color, fill_color)
                # self.font.draw(self.frame, text, 0,0, interior_color)
                (self.target_x_offset, self.target_y_offset) = (x,y)

        return self


    def set_textTL(self, text, seconds=None, blink_frames=None, style=None):
        """Displays the given message for the given number of seconds."""
        if(self.text is not None and self.text == text): 
            return self
        #print("set_text: '%s'" % text)

        self.text = text
        self.started_at = None
        self.seconds = seconds
        self.blink_frames = blink_frames
        self.blink_frames_counter = self.blink_frames

        if(style is not None):
            fill_color = style.fill_color 
            line_color = style.line_color 
            interior_color = style.interior_color 
            line_width = style.line_width 
        elif(self.style is not None):
            fill_color = self.style.fill_color 
            line_color = self.style.line_color 
            interior_color = self.style.interior_color 
            line_width = self.style.line_width 
        else:
            fill_color = self.fill_color 
            line_color = self.line_color 
            interior_color = self.interior_color 
            line_width = self.line_width 

        if(fill_color is None):
            fill_color = self.fill_color

        if(fill_color == (0,0,0) and self.composite_op == 'blacksrc'):
            fill_color = None

        # crazy composite_op sensing fixes
        # if(interior_color == (0,0,0) and self.composite_op == 'blacksrc'):
        #     interior_color = None
        # if(interior_color == (0,255,0) and self.composite_op == 'greensrc'):
        #     interior_color = None
        # if(interior_color == (255,0,255) and self.composite_op == 'magentasrc'):
        #     interior_color = None


        if text == None or text=="":
            self.frame = None
            return self
        
        # make a box of width.height at x/y
        self.frame = Frame(self.width, self.height)
        if(fill_color is None):
            rect_fill = (0,0,0,0)
        else:
            rect_fill = fill_color

        self.frame.fill_rect(0, 0, self.width, self.height, rect_fill) 

        x_txt_off, y_txt_off = 0, 0
        (w_txt, h_txt) = self.font.size(text)
        (w_txt , h_txt) = (w_txt+(2*line_width), h_txt+(2*line_width))

        self.text_width = w_txt
        self.text_height = h_txt

        if self.justify == 'right':
            x_txt_off = self.width - w_txt
        elif self.justify == 'center':
            x_txt_off = (self.width - w_txt)/2
        else: #  if self.justify == 'left':
            x_txt_off = 0

        if self.Vjustify == 'bottom':
            y_txt_off = self.height - h_txt
        elif self.Vjustify == 'center':
            y_txt_off = (self.height - h_txt)/2
        else: # self.Vjustify == 'top':
            y_txt_off = 0

        self.font.drawHD(self.frame, text, x_txt_off, y_txt_off, line_color, line_width, interior_color, None)

        self.set_target_position(self.x, self.y)

        return self


class AnimatedHDTextLayer(Layer):
    """Layer that displays text."""

    texTextBorder = None
    texTextInterior = None
    strLastMessage = None

    fill_anim = None
    line_anim = None

    frmAssembledResult = None
    frmBufferedResults = None

    def __init__(self, x, y, font, justify="center", vert_justify="top",
                    line_width=2, line_color=None, line_anim=None, 
                    fill_color=None, fill_anim=None, bg_color=None,
                    width=224, height=112):

        super(AnimatedHDTextLayer, self).__init__()
        self.width = width
        self.height = height
        self.justify = justify

        self.x = x
        self.y = y

        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
        self.bg_color = bg_color

        self.font = font

        self.fill_anim = fill_anim
        self.line_anim = line_anim

        self.strLastMessage = None

        self.Vjustify = vert_justify

        if(fill_anim is not None) and (line_anim is not None):
            # both are animated.
            self.fill_color = (255,255,255,255)
            self.line_color = (255,255,255,255)

        elif(fill_anim is not None):
            # only fill is animated
            self.fill_color = (255,255,255,255)

        elif(line_anim is not None):
            # only line is animated
            self.line_color = (255,255,255,255)
        else:
            raise ValueError, "Don't use AnimatedHDTextLayer if nothing is animated!"

        self.frmAssembledResult = Frame(width, height)
        self.frmBufferedResults = list()

    def next_frame(self):
        if(self.strLastMessage is None):
            return None

        if self.started_at == None:
            self.started_at = time.time()

        if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
            return None

        if self.blink_frames > 0:
            if self.blink_frames_counter == 0:
                self.blink_frames_counter = self.blink_frames
                self.blink_on = not self.blink_on
            else:
                self.blink_frames_counter -= 1

            if(not self.blink_on):
                return None
            # print("blink frames: %d" % self.blink_frames_counter)

        if(self.fill_anim is not None):
            nf = self.fill_anim.next_frame()
            if(nf is None):
                interior = self.texTextInterior
            else:
                fill = nf.pySurface
                interior = sdl2_DisplayManager.inst().mask(self.texTextInterior, fill)
        else:
            interior = self.texTextInterior

        (w, h) = interior.size

        if(self.line_width > 0):
            if(self.line_anim is not None):
                nf = self.line_anim.next_frame()
                if(nf is None):
                    edge = self.texTextBorder
                else:
                    line = nf.pySurface
                    edge = sdl2_DisplayManager.inst().mask(self.texTextBorder, line)
            else:
                edge = self.texTextBorder

            sdl2_DisplayManager.inst().blit(source_tx = edge, dest_tx=interior, dest=(0,0,w,h))                
            (w, h) = edge.size

            del edge

        self.frmAssembledResult.clear(self.bg_color)

        # positioning logic:
        x, y = 0, 0
        
        if self.justify == 'left':
            (x, y) = (0,0)
        elif self.justify == 'right':
            (x, y) = (-w,0)
        elif self.justify == 'center':
            (x, y) = (-w/2,0)

        (wOfText , hOfText) = (w,h)
        self.text_width = wOfText
        self.text_height = hOfText
        x, y = 0, 0
        rectx, recty = 0, 0
        x_offset, y_offset = 0,0

        if self.justify == 'left':
            x_offset = 0
        elif self.justify == 'right':
            x_offset = -1
        elif self.justify == 'center':
            x_offset = -0.5

        if self.Vjustify == 'bottom':
            y_offset = -1
        elif self.Vjustify == 'center':
            y_offset = -0.5

        if self.bg_color is not None:
            (x,y) = (int(self.width*x_offset), int(self.height*y_offset))
            self.set_target_position(x, y)

            # self.frame = Frame(width=self.width, height=self.height)
            # self.frame.fill_rect(0, 0, self.width, self.height, fill_color)

            (x, y) = (int((wOfText-self.width)*x_offset), int((hOfText-self.height)*y_offset))
            
            # self.font.drawHD(self.frame, text, x, y, line_color, line_width, interior_color, fill_color)
            sdl2_DisplayManager.inst().blit(source_tx=interior, dest_tx=self.frmAssembledResult.pySurface, dest=(x,y,w,h))


            (self.target_x_offset, self.target_y_offset) = (self.x,self.y)
        else:
            (x, y) = (int(wOfText*x_offset), int(hOfText*y_offset))
            self.set_target_position(self.x, self.y)
            # self.frame = Frame(wOfText, hOfText)
            # I think this fixes it??
            # self.frame.fill_rect(0, 0, wOfText, hOfText, (0,0,0,0)) # but taking this away shouldn't break it should it??

            # self.font.drawHD(self.frame, text, 0, 0, line_color, line_width, interior_color, fill_color)
            sdl2_DisplayManager.inst().blit(source_tx=interior, dest_tx=self.frmAssembledResult.pySurface, dest=(0,0,w,h))

            (self.target_x_offset, self.target_y_offset) = (x,y)

        # x, y = 0, 0
        
        # if self.justify == 'left':
        #     (x, y) = (0,0)
        # elif self.justify == 'right':
        #     (x, y) = (-w,0)
        # elif self.justify == 'center':
        #     (x, y) = (-w/2,0)

        # if self.Vjustify == 'bottom':
        #     y = -h
        # elif self.Vjustify == 'center':
        #     y = -h/2
        # else:
        #     y = 0

        # sdl2_DisplayManager.inst().blit(source_tx=interior, dest_tx=self.frmAssembledResult.pySurface, dest=(x,y,w,h))

        # Frame.copy_rect(dst=self.frmAssembledResult, dst_x=x, dst_y=y, src=self.frame, src_x=0, src_y=0, width=self.buffer.width, height=self.buffer.height)

        # x, y = 0, 0
        # x_offset, y_offset = 0,0

        # if self.justify == 'left':
        #     x_offset = 0
        # elif self.justify == 'right':
        #     x_offset = -1
        # elif self.justify == 'center':
        #     x_offset = -0.5

        return self.frmAssembledResult

    def set_text(self, text, seconds=None, blink_frames=None):
        if(text != self.strLastMessage):
            self.started_at = None
            self.seconds = seconds
            self.blink_frames = blink_frames
            self.blink_frames_counter = self.blink_frames
            self.blink_on = True

            (self.texTextBorder, self.texTextInterior) = sdl2_DisplayManager.inst().font_render_bordered_text_dual(text, 
                    font_alias=self.font.name, size=self.font.font_size, 
                    width=None, color=self.fill_color, bg_color=(0,0,0,255), 
                    border_color=self.line_color, border_width=self.line_width) 
            # print("set_text sizes:")
            # print(self.texTextBorder.size)
            # print(self.texTextInterior.size)
            # print("---")
            self.strLastMessage = text


def main():


    #import layers
    #from layers import HDTextLayer, TextLayer
    import time 
    import dmd
    import sdl2
    from procgame.dmd import font, AnimFont, layers
    import procgame
    #from font import *

    sdl2_DisplayManager.Init(450,225,2)

    f = AnimFont("ExportedFont.dmd")
    self.layer = dmd.AnimatedTextLayer(self.game.dmd.width/2, self.game.dmd.height/2, f, "center", 2)
    self.layer.set_text("Hello!!")


    
    for i in range(0,30):


        sdl2.SDL_Delay(33)

if __name__ == '__main__':
    main()

