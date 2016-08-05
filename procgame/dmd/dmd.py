import pinproc
import time
import os
from sdl2_displaymanager import sdl2_DisplayManager
import sdl2.ext  #can this be removed MO does not have this
from procgame.dmd import VgaDMD
# import pygame
# import pygame.locals

class Frame(object):
    """DMD frame/bitmap.
    
    """
    
    width = 0
    """Width of the frame in dots."""
    height = 0
    """Height of the frame in dots."""
    
    pySurface = None
    """ the pygame surface that backs the frame """

    def __init__(self, width, height, from_surface=None):
        """Initializes the frame to the given `width` and `height`."""
        # super(Frame, self).__init__(width, height)
        width = int(width)
        height = int(height)
        self.width = width
        self.height = height
        if(from_surface is None):
            self.pySurface = sdl2_DisplayManager.inst().new_texture(width, height) #pygame.surface.Surface((width, height))
            #self.clear() -- don't need this, the new_texture function does this for us.
        else: 
            self.pySurface = from_surface

        self.x_offset = 4 #bytes_per_pixel 
        self.y_offset = self.width*4 # every y_offset Bytes is the next line
        self.font_dots = []

    def copy_rect(dst, dst_x, dst_y, src, src_x, src_y, width, height, op="copy", blendmode=None, alpha=None):
        """Static method which performs some type checking before calling :meth:`pinproc.DMDBuffer.copy_to_rect`."""

        # print "copy_rect(dst_x=%d, dst_y=%d, src_x=%d, src_y=%d, width=%d, height=%d)" % (dst_x, dst_y, src_x, src_y, width, height)
        
        # src_rect = pygame.Rect(int(src_x),int(src_y),int(width),int(height))
        # dst_rect = pygame.Rect(int(dst_x),int(dst_y),int(width),int(height))

        src_rect = (int(src_x),int(src_y),int(width),int(height))
        # if(width > src.width):
        #     width = src.width
        # if(height > src.height):
        #     height = src.height
        dest_rect = (int(dst_x),int(dst_y),int(width),int(height))

        # """ 1.8.0: BLEND_ADD, BLEND_SUB, BLEND_MULT, BLEND_MIN, BLEND_MAX 
        #  in 1.8.1: BLEND_RGBA_ADD, BLEND_RGBA_SUB, BLEND_RGBA_MULT, BLEND_RGBA_MIN, 
        #             BLEND_RGBA_MAX BLEND_RGB_ADD, BLEND_RGB_SUB, BLEND_RGB_MULT, 
        #             BLEND_RGB_MIN, BLEND_RGB_MAX 
        # """
        # if (op=="copy"):
        #     special_flags = 0
        # elif(op=="add"):
        #     special_flags = pygame.BLEND_ADD
        # elif(op == "sub"):
        #     special_flags = pygame.BLEND_SUB
        # elif(op == "mult"):
        #     special_flags = pygame.BLEND_MULT
        # elif(op == "min"):
        #     special_flags = pygame.BLEND_MIN
        # elif(op == "max"):
        #     special_flags = pygame.BLEND_MAX
        # elif(op=="rgb_add"):
        #     special_flags = pygame.BLEND_RGB_ADD
        # elif(op == "rgb_sub"):
        #     special_flags = pygame.BLEND_RGB_SUB
        # elif(op == "rgb_mult"):
        #     special_flags = pygame.BLEND_RGB_MULT
        # elif(op == "blacksrc"):
        #     special_flags = 0;
        #     src.pySurface.set_colorkey((0,0,0))
        # elif(op == "magentasrc"):
        #     special_flags = 0;
        #     src.pySurface.set_colorkey((255,0,255))
        # elif(op == "greensrc"):
        #     special_flags = 0;
        #     src.pySurface.set_colorkey((0,255,0))
        # elif(op == "alpha"):
        #     special_flags = 0
        #     # TODO: THIS...
        # elif(op == "alphaboth"):
        #     special_flags = 0
        #     # TODO: THIS...
        # else:
        #     raise ValueError, "Operation type not recognized."


        #HD_copy_texture(src.pySurface, dst.pySurface, src_rect, dst_rect)
        sdl2_DisplayManager.inst().blit(source_tx=src.pySurface, dest_tx=dst.pySurface, dest=dest_rect, area=src_rect, special_flags = 0, blendmode=blendmode, alpha=alpha)


        # dst.pySurface.blit(src.pySurface, dst_rect, src_rect, special_flags = special_flags)
        #src.copy_to_rect(dst, int(dst_x), int(dst_y), int(src_x), int(src_y), int(width), int(height), op)
        # src.pySurface.set_colorkey(None)

    copy_rect = staticmethod(copy_rect)
    
    # def color_replacement(self, old_color, new_color):
    #   dst = self.pySurface.copy()
    #   dst.fill(new_color)
    #   self.pySurface.set_colorkey(old_color)
    #   dst.blit(self.pySurface, self.pySurface.get_rect())
    #   #src.copy_to_rect(dst, int(dst_x), int(dst_y), int(src_x), int(src_y), int(width), int(height), op)
    #   self.pySurface = None
    #   self.pySurface = dst

    def subframe(self, x, y, width, height):
        """Generates a new frame based on a sub rectangle of this frame."""
        subframe = Frame(width, height)
        Frame.copy_rect(subframe, 0, 0, self, x, y, width, height, 'copy')
        return subframe
    
    def copy(self):
        """Returns a copy of itself."""
        # frame = Frame(self.width, self.height, from_surface=self.pySurface.copy())
        #frame.pySurface.blit(self.pySurface, (0,0,self.width,self.height), (0,0,self.width,self.height), special_flags = 0)
        
        frame = Frame(self.width, self.height)
        sdl2_DisplayManager.inst().blit(source_tx=self.pySurface, dest_tx=frame.pySurface, dest=(0,0,self.width,self.height), area=(0,0,self.width,self.height), special_flags = 0)

        #frame.set_data(self.get_data())
        return frame
    
    def tint(self, r,g,b):
        """ returns a copy of a Frame, tinted with the set R, G, B amounts.  Useful for cheap effects """
        frame = Frame(self.width, self.height)
        dframe = self.copy()
        frame.fill_rect(0,0,self.width,self.height,(r,g,b))
        # sdl2_DisplayManager.inst().blit(source_tx=self.pySurface, dest_tx=frame.pySurface, dest=(0,0,self.width,self.height), area=(0,0,self.width,self.height), special_flags = 0,blendmode='MOD')
        sdl2_DisplayManager.inst().blit(source_tx=frame.pySurface, dest_tx=dframe.pySurface, dest=(0,0,self.width,self.height), area=(0,0,self.width,self.height), special_flags = 0,blendmode='MOD')

        #frame.set_data(self.get_data())
        return dframe


    def scale(self, percentage, new_w=None, new_h=None):
        # resizes a frame...
        # raise ValueError, "Scale not yet programmed..."

        if(new_w is None):
            new_w = int(percentage * self.width)
            new_h = int(percentage * self.height)

        dstrect = (0, 0, int(new_w), int(new_h))
        self.width = new_w
        self.height = new_h

        F = Frame(new_w, new_h)

        sdl2_DisplayManager.inst().roto_blit(self.pySurface, F.pySurface, dstrect, None)

        del self.pySurface 

        self.pySurface = F.pySurface

        # #print(new_w, new_h)
        # self.width = new_w
        # self.height = new_h
        # newSurf = pygame.surface.Surface((new_w,new_h))
        # pygame.transform.scale(self.pySurface,(new_w,new_h), newSurf)
        # del self.pySurface
        # self.pySurface = newSurf
        # self.font_dots = []

    def rotozoom(self,rotation=0, scale=1, origin=None):
        """ Returns a rotated and possibly scaled version of the original frame """
        # resizes a frame...
        (sw, sh) = (self.width*scale, self.height*scale)
        dstrect = (0, 0, int(sw), int(sh))

        F = Frame(self.width, self.height)

        sdl2_DisplayManager.inst().roto_blit(self.pySurface, F.pySurface, dstrect, None, angle=rotation, origin=origin)

        return F
        # del self.pySurface
        # self.pySurface = F.pySurface

        # raise ValueError, "RotoZoom not yet programmed..."
        # self.pySurface = pygame.transform.rotozoom(self.pySurface,rotation, scale)
        # #self.pySurface = pygame.transform.rotate(self.pySurface,rotation)
        # self.width = self.pySurface.get_width()
        # self.height = self.pySurface.get_height()



    def smoothscale(self, percentage):
        self.scale(percentage)

    def ascii(self):
        """Returns an ASCII representation of itself."""
        # output = ''
        # table = [' ', '.', '.', '.', ',', ',', ',', '-', '-', '=', '=', '=', '*', '*', '#', '#',]
        # for y in range(self.height):
        #   for x in range(self.width):
        #       dot = self.get_dot(x, y)
        #       output += table[dot & 0xf]
        #   output += "\n"
        # return output
        raise ValueError, "Unsupported method Ascii"
    
    def create_with_text(lines, palette = {' ':0, '*':15}):
        """Create a frame based on text.
        
        This class method can be used to generate small sprites within the game's source code::
        
            frame = Frame.create_with_text(lines=[ \\
                '*+++*', \\
                ' *+* ', \\
                '  *  '], palette={' ':0, '+':7, '*':15})
        """
        height = len(lines)
        if height > 0:
            width = len(lines[0])
        else:
            width = 0
        frame = Frame(width, height)
        for y in range(height):
            for x in range(width):
                char = lines[y][x]
                frame.set_dot(x, y, palette[char])
        return frame
    create_with_text = staticmethod(create_with_text)

    def create_frames_from_grid( self, num_cols, num_rows ):
        frames = []
        width = self.width / num_cols
        height = self.height / num_rows
    
        # Use nested loops to step through each column of each row, creating a new frame at each iteration and copying in the appropriate data.
        for row_index in range(0,num_rows):
            for col_index in range(0,num_cols):
                new_frame = Frame(width, height)
                Frame.copy_rect(dst=new_frame, dst_x=0, dst_y=0, src=self, src_x=width*col_index, src_y=height*row_index, width=width, height=height, op='copy')
                frames += [new_frame]
        return frames

    def set_font_dot(self, x, y, color):
        #print("set_font_dot(" + str(x) + "," + str(y) + ")")
        if(len(self.font_dots)<=(x+(y*self.width))):
            self.font_dots.append(color)
            assert(self.font_dots[x+(y*self.width)]==color)
        else:
            self.font_dots[x+(y*self.width)]=color

    def get_font_dot(self, x, y):
        if (len(self.font_dots) == 0):
            string = self.get_surface_string()
            return ord(string[x+(y*self.width)])
        else:
            return ord(self.font_dots[x+(y*self.width)])

    def fill_rect(self, x,y,w,h,c):
        if(len(c)==3):
            c = (c[0],c[1],c[2],255)
        old = sdl2_DisplayManager.inst().switch_target(self.pySurface)
        sdl2_DisplayManager.inst().fill((int(x),int(y),int(w),int(h)), c)

        sdl2_DisplayManager.inst().switch_target(old)
        
        # r = pygame.Rect(int(x),int(y),int(w),int(h))
        # self.pySurface.fill(c,r)

    def set_alpha(self,value=255):
        print "SETTING ALPHA VALUE TO : " + str(value)
        #self.pySurface.convert_alpha()  
        #self.pySurface.set_alpha(value)
        sdl2.SDL_SetTextureAlphaMod(self.pySurface.texture,value)

    def clear(self, color=(0,0,0,0)):
        sdl2_DisplayManager.inst().texture_clear(self.pySurface, color)
        #self.pySurface.fill((0,0,0))

    def set_surface(self, surf):
        raise ValueError, "Don't use set_surface..."
        # try:
        #     self.pySurface = surf.convert()
        # except Exception as e:
        #     self.pySurface = surf
        

    def build_surface_from_8bit_dmd_string(self, str_data, composite_op=None):
        
        self.eight_to_RGB_map = VgaDMD.get_palette_ch()
        self.font_dots = str_data
        x = 0
        y = 0
        d = ""
        for dot in str_data:
            # get the Byte from the frame data
            dot = ord(dot) 
            # convert it to the correct RGB pallette color
            (r,g,b) = self.eight_to_RGB_map[dot]

            d +=r + g + b
            # # write out the color into the target buffer array
            # index = y*self.y_offset + x*self.x_offset

            # #self.pySurface[index:(index+bytes_per_pixel)] = (b,g,r,0)
            # buffer_interface[index:(index+4)] = (b,g,r,0)

            # #move to the next dot
            # x += 1
            # if x == self.width:
            #   x = 0
            #   y += 1 
        #self.pySurface = pygame.image.fromstring(d,(self.width,self.height),'RGB').convert()

        # surf = HD_load_file(path)
        self.pySurface = sdl2_DisplayManager.inst().make_texture_from_imagebits(bits=d, width=self.width, height=self.height, mode='RGB', composite_op=composite_op)
        

    def get_surface_string(self):
        # convert every pixel to 8 bit mapping
        raise ValueError, "get_surface_string yet programmed..."

        return pygame.image.tostring(self.pySurface,'RGB')
    #   #self.pySurface.get_buffer()

    # def set_data(self, frame_string):
    #   ar = pygame.PixelArray(self.pySurface)
    #   ar = frame_string
    #   del ar
        #self.pySurface = pygame.image.fromstring(frame_string,(self.width,self.height),'P')
        
        # x = 0
        # y = 0
        # for dot in frame_string:
        #   # get the Byte from the frame data
        #   dot = ord(dot) 
        #   # convert it to the correct RGB pallette color
        #   (r,g,b) = self.eight_to_RGB_map[dot]

        #   # write out the color into the target buffer array
        #   index = y*self.y_offset + x*self.x_offset

        #   #self.pySurface[index:(index+bytes_per_pixel)] = (b,g,r,0)
        #   self.pySurface[index:(index+4)] = (b,g,r,0)

        #   #move to the next dot
        #   x += 1
        #   if x == self.width:
        #       x = 0
        #       y += 1 


class Layer(object):
    """
    The ``Layer`` class is the basis for the pyprocgame display architecture.
    Subclasses override :meth:`next_frame` to provide a frame for the current moment in time.
    Handles compositing of provided frames and applying transitions within a :class:`DisplayController` context.
    """
    
    opaque = False
    """Determines whether layers below this one will be rendered.  
    If `True`, the :class:`DisplayController` will not render any layers after this one 
    (such as from modes with lower priorities -- see :class:`DisplayController` for more information).
    """
    
    target_x = 0
    """Base `x` component of the coordinates at which this layer will be composited upon a target buffer."""
    target_y = 0
    """Base `y` component of the coordinates at which this layer will be composited upon a target buffer."""
    target_x_offset = 0
    """Translation component used in addition to :attr:`target_x` as this layer's final compositing position."""
    target_y_offset = 0
    """Translation component used in addition to :attr:`target_y` as this layer's final compositing position."""
    enabled = True
    """If `False`, :class:`DisplayController` will ignore this layer."""
    composite_op = 'copy'
    """DEPRICATED: Composite operation used by :meth:`composite_next` when calling :meth:`~pinproc.DMDBuffer.copy_rect`."""
    transition = None
    """Transition which :meth:`composite_next` applies to the result of :meth:`next_frame` prior to compositing upon the output."""
    blendmode = None
    """The blendmode operation to apply - default is 'BLEND', options are ADD, BLEND, MOD and NONE """
    alpha = None
    """The alpha transparency of this entire layer (0 to 255) as invisible to visible - None means fully visible."""

    def __init__(self, opaque=False):
        """Initialize a new Layer object."""
        super(Layer, self).__init__()
        self.opaque = opaque
        self.set_target_position(0, 0)
        self.blendmode = None
        self.alpha = None

    def get_width(self):
        if(hasattr(self,'width')):
            return self.width
        elif(not hasattr(self, 'frames') or self.frames is None):
            return self.frame.width
        else:
            return max([f.width for f in self.frames])

    def get_height(self):
        if(hasattr(self,'height')):
            return self.height
        elif(not hasattr(self, 'frames') or self.frames is None):
            return self.frame.height
        else:
            return max([f.height for f in self.frames])


    def scale(self, amount):
        if(not hasattr(self, 'frames') or self.frames is None):
            self.frame.scale(amount)
        else:
            for f in self.frames: f.scale(amount)
            
    def rotozoom(self,rotation=0, scale=1):
        if(self.frames is None):
            self.frame.rotozoom(rotation, scale)
        else:
            for f in self.frames: f.rotozoom(rotation,scale)

    def reset(self):
        # To be overridden
        pass

    def set_target_position(self, x, y):
        """Setter for :attr:`target_x` and :attr:`target_y`."""
        self.target_x = x
        self.target_y = y
    def next_frame(self):
        """Returns an instance of a Frame object to be shown, or None if there is no frame.
        The default implementation returns ``None``; subclasses should implement this method."""
        return None
    def composite_next(self, target):
        """Composites the next frame of this layer onto the given target buffer.
        Called by :meth:`DisplayController.update`.
        Generally subclasses should not override this method; implementing :meth:`next_frame` is recommended instead.
        """
        src = self.next_frame()
        if src != None:
            if self.transition != None:
                src = self.transition.next_frame(from_frame=target, to_frame=src)
            Frame.copy_rect(dst=target, dst_x=self.target_x+self.target_x_offset, dst_y=self.target_y+self.target_y_offset, src=src, src_x=0, src_y=0, width=src.width, height=src.height, op=self.composite_op, blendmode=self.blendmode, alpha=self.alpha)
        return src


def main():
    # RESOURCES = sdl2.ext.Resources(__file__, "resources")
    # Uint32 * pixels = new Uint32[640 * 480];
    # SDL_UpdateTexture(texture, NULL, pixels, 640 * sizeof(Uint32));
    sdl2_DisplayManager.Init(450,225,2)

    sw_sprite = sdl2_DisplayManager.inst().load_surface("assets/dmd/smile.png")
    # sprite = HD_load_file("hello.bmp")
    # sprite2 = HD_load_file("transparent_test.png")
    # dot_sprite = HD_load_file("dmdgrid32x32_v1.png")

    sprite = sdl2_DisplayManager.inst().texture_from_surface(sw_sprite)

    f = Frame(20,20,from_surface=sprite)
    f.x_offset=400
    
    sdl2_DisplayManager.inst().screen_blit(source_tx=f.pySurface)
    sdl2_DisplayManager.inst().flip()
    import sdl2
    sdl2.SDL_Delay(1000)
    pass

if __name__ == "__main__":
    main()
