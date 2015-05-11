#from procgame import *
# import dmd
from procgame import config
from layers import *
import transitions
import sys

DMD_WIDTH = config.value_for_key_path('dmd_dots_w', 480)
DMD_HEIGHT = config.value_for_key_path('dmd_dots_h', 240) 
LENGTH_IN_FRAMES = config.value_for_key_path('dmd_framerate', 30) 

class moveLayer(Layer):
    def __init__(self,layer=None, start_x=0,start_y=0, target_x=0,target_y=0, lengthInFrames=LENGTH_IN_FRAMES, callback=None, param=None, loop=False, composite_op = 'blacksrc' ):
        super(moveLayer,self).__init__(False)

        self.step_number=0
        self.object_layer = layer
        self.callback = callback
        self.param = param
        self.start_x = start_x
        self.start_y = start_y
        self.lengthInFrames = lengthInFrames
        self.move_target_x = target_x
        self.move_target_y = target_y
        self.finished = False
        self.composite_op = composite_op
        self.loop = loop
    
    
    def next_frame(self):
        if not self.finished:
            #print self.object_layer.frames[0].width, self.object_layer.frames[0].height
            self.step_number+=1
            if self.step_number < self.lengthInFrames:
                new_x = int((self.move_target_x - self.start_x )* self.step_number/self.lengthInFrames) + self.start_x
                new_y = int((self.move_target_y - self.start_y )* self.step_number/self.lengthInFrames) + self.start_y
                self.set_target_position(new_x,new_y)
            elif self.step_number == self.lengthInFrames:
                self.set_target_position(self.move_target_x, self.move_target_y)
                self.finished = True
                if self.loop:
                    self.finished = False
                    self.step_number = 1
                if self.callback != None:
                    if self.param != None:
                        self.callback(self.param)
                    else:
                        self.callback()
        return self.object_layer.next_frame()
        
    def reset(self):
        self.step_number = 0
        self.finished = False
        

class TransitionLayer(Layer):

    # Constants
    TYPE_EXPAND = "ExpandTransition"   #fails
    TYPE_PUSH = "PushTransition"     #works
    TYPE_SLIDEOVER = "SlideOverTransition" #works
    TYPE_WIPE = "WipeTransition"   #does not blow up, but not right
    TYPE_CROSSFADE = "CrossFadeTransition" #blows up
    TYPE_FADE = "FadeTransition"   #blows up
    #TYPE_ZOOM = "ZoomTransition"  #blows up
    TYPE_OBSCURED = "ObscuredWipeTransition"

    PARAM_HORIZONTAL = "horizontal"
    PARAM_VERTICAL = "vertical"
    PARAM_NORTH = "north"
    PARAM_SOUTH = "south"
    PARAM_WEST = "west"
    PARAM_EAST = "east"
    PARAM_IN = "in"
    PARAM_OUT = "out"

    LENGTH_IN_FRAMES = 30

    def __init__(self, layerA=None, layerB=None, transitionType=TYPE_PUSH, transitionParameter=None, lengthInFrames=LENGTH_IN_FRAMES,callback = None, width=DMD_WIDTH, height=DMD_HEIGHT):
        super(TransitionLayer, self).__init__(False)

        if layerA == None: layerA = FrameLayer(False,Frame(width,height))
        self.layerA = layerA
        if layerB == None: layerB = FrameLayer(False,Frame(width,height))
        self.layerB = layerB
        self.callback = callback
        self.finished_flag = False
        

        self.layer_A_wrapped = GroupedLayer(width,height, [self.layerA])
        self.layer_B_wrapped = GroupedLayer(width,height, [self.layerB])
        
        self.layer_A_wrapped.composite_op = self.layerA.composite_op
        self.layer_B_wrapped.composite_op = self.layerB.composite_op

        # if transitionType == self.TYPE_DOUBLEEXPAND:
        #     transition_class = self.get_class('transition.' + transitionType)
        # else:
        transition_class = self.get_class("procgame.dmd.transitions." + transitionType)
        
        if transitionType == self.TYPE_CROSSFADE:
            self.transitionMgr = transition_class(width,height)
        elif transitionType == self.TYPE_FADE:
            self.transitionMgr = transition_class(frame_count = lengthInFrames, direction=transitionParameter)
        else:
            if transitionParameter:
                self.transitionMgr = transition_class(transitionParameter)
            else:
                self.transitionMgr = transition_class()
                        
        self.transitionMgr.progress_per_frame = 1.0 / lengthInFrames
        self.transitionMgr.completed_handler = self.finished
        self.transitionMgr.start()
        self.next_frame()


    def get_class(self, class_path):
        paths = class_path.split('.')
        modulename = '.'.join(paths[:-1])
        classname = paths[-1]
        return getattr(sys.modules[modulename], classname)


    #def next_frame(self):
    #    self.transitionMgr.next_frame()
    #    return None

    def next_frame(self):
        if self.finished_flag:
            return self.layer_B_wrapped.next_frame()
            #even returns None if B returns None (is an Animation w/o hold frame)

        f = self.transitionMgr.next_frame(self.layer_A_wrapped.next_frame(),self.layer_B_wrapped.next_frame())        
        return f

    def finished(self):

        self.finished_flag = True
        self.transitionMgr.pause()

        self.layer = self.layerB

        if self.callback:
            self.callback()
        # MJO: Commented this out, since transitions can live inside of
        # scripts, and therefore need to be reset
        # self.transitionMgr = None

    def reset(self):
        """Resets the animation back to the first frame."""
        self.finished_flag = False
        if(self.transitionMgr is not None):
            # this if will never fail.  I might as well assert this.
            self.transitionMgr.start()


class UpdateLayer(Layer):

    def __init__(self, callbackFunction = None):
        super(UpdateLayer, self).__init__(False)
        self.callbackFunction = callbackFunction

    def next_frame(self):
        if self.callbackFunction:
            self.callbackFunction()
        return None
    
class Transition(object):

    # Constants
    TYPE_EXPAND = "ExpandTransition"
    TYPE_PUSH = "PushTransition"
    TYPE_SLIDEOVER = "SlideOverTransition"
    TYPE_WIPE = "WipeTransition"
    TYPE_CROSSFADE = "CrossFadeTransition"
    TYPE_OBSCURED = "ObscuredWipeTransition"
    TYPE_FADE = "FadeTransition"
    # TYPE_DOUBLEEXPAND ="DoubleExpandTransition"

    PARAM_HORIZONTAL = "horizontal"
    PARAM_VERTICAL = "vertical"
    PARAM_NORTH = "north"
    PARAM_SOUTH = "south"
    PARAM_WEST = "west"
    PARAM_EAST = "east"

    def __init__(self, layerA=None, layerB=None, transitionType=TYPE_PUSH, transitionParameter=None, lengthInFrames=LENGTH_IN_FRAMES,callback = None):

        if layerA == None: layerA = FrameLayer(False,Frame(DMD_WIDTH,DMD_HEIGHT))
        self.layerA = layerA
        if layerB == None: layerB = FrameLayer(False,Frame(DMD_WIDTH,DMD_HEIGHT))
        self.layerB = layerB
        self.callback = callback
        self.finished_flag = False
        

        transition_class = self.get_class("procgame.transitions." + transitionType)
        
        if transitionType == self.TYPE_CROSSFADE:
            self.transition = transition_class(DMD_WIDTH,DMD_HEIGHT)
        elif transitionType == self.TYPE_OBSCURED:
            #frames = dmd.Animation().load('dmd/gift/mailbox.dmd').frames
            #myframe = dmd.FrameLayer(opaque=False, frame = frames[0])
            #self.transition = transition_class(frames[0], 'blacksrc',transitionParameter)
            pass
        else:
            if transitionParameter:
                self.transition = transition_class(transitionParameter)
            else:
                self.transition = transition_class()
                        
        self.transition.progress_per_frame = 1.0 / lengthInFrames
        self.transition.completed_handler = self.finished
        self.transition.start()

        self.update()

    # def __init__(self, layerA=None, layerB=None, transitionType=TYPE_PUSH, transitionParameter=None, lengthInFrames=LENGTH_IN_FRAMES,callback = None):
    #     if layerA == None: layerA = FrameLayer(False,Frame(DMD_WIDTH,DMD_HEIGHT))
    #     self.layerA = layerA
    #     if layerB == None: layerB = FrameLayer(False,Frame(DMD_WIDTH,DMD_HEIGHT))
    #     self.layerB = layerB
    #     self.callback = callback
    #     self.finished_flag = False
        
    #     # if transitionType == self.TYPE_DOUBLEEXPAND:
    #     #     transition_class = self.get_class('transition.' + transitionType)
    #     # else:
    #     transition_class = self.get_class("procgame.dmd.transitions." + transitionType)
        
    #     if transitionType == self.TYPE_CROSSFADE:
    #         self.transition = transition_class(DMD_WIDTH,DMD_HEIGHT)
    #     elif transitionType == self.TYPE_OBSCURED:
    #         #frames = dmd.Animation().load('dmd/gift/mailbox.dmd').frames
    #         #myframe = dmd.FrameLayer(opaque=False, frame = frames[0])
    #         #self.transition = transition_class(frames[0], 'blacksrc',transitionParameter)
    #         pass
    #     else:
    #         if transitionParameter:
    #             self.transition = transition_class(transitionParameter)
    #         else:
    #             self.transition = transition_class()
                        
    #     self.transition.progress_per_frame = 1.0 / lengthInFrames
    #     self.transition.completed_handler = self.finished
    #     self.transition.start()
    #     self.next_frame()

    def get_class(self, class_path):
        paths = class_path.split('.')
        modulename = '.'.join(paths[:-1])
        classname = paths[-1]
        return getattr(sys.modules[modulename], classname)

    def next_frame(self):
        #Wrapping the layers in group layers, to maintain the positioning of text layers
        #print "TESTING NOW IN UPDATE IN jk_transitions"
        if self.finished_flag:
            self.layer = self.layerB
            return
        layer_A_wrapped = GroupedLayer(DMD_WIDTH,DMD_HEIGHT, [self.layerA])
        layer_A_wrapped.composite_op = self.layerA.composite_op
        layer_B_wrapped = GroupedLayer(DMD_WIDTH,DMD_HEIGHT, [self.layerB])
        layer_B_wrapped.composite_op = self.layerB.composite_op

        self.layer = FrameLayer(False,self.transition.next_frame(layer_A_wrapped.next_frame(),layer_B_wrapped.next_frame())),
        
        self.layer.composite_op = self.layerB.composite_op


    def finished(self):
        # The transition keeps calling the completed_handler, which we probably don't want, so we clear the reference
        #self.transition.completed_handler = None
        self.finished_flag = True
        #print "INSIDE TRANSITION FINISHED"
        self.transition.pause()

        self.mode.layer = self.layerB

        if self.callback:
            self.callback()
        self.mode.transition = None
        self.transition = None
            
class DoubleExpandTransition(transitions.LayerTransitionBase):
    def __init__(self , direction='center'):
        super(DoubleExpandTransition, self).__init__()
        self.direction = direction
        self.progress_per_frame = 1.0/11.0
        
    def transition_frame(self, from_frame, to_frame):
        frame = from_frame.copy()
        dst_x, dst_y = 0, 0
        prog = self.progress
        if self.in_out == 'out':
            prog = 1.0 - prog

        if self.direction=='center':
            dst_y = frame.height/2-prog*(frame.height/2)
            dst_x = frame.width/2-prog*(frame.width/2)
        else:
            dst_y = frame.height/2-prog*(frame.height/2)
            dst_x = frame.width/2-prog*(frame.width/2)

        width=prog*frame.width
        height = prog*frame.height

        Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=dst_x, src_y=dst_y, width=width, height=height, op='copy')
        return frame