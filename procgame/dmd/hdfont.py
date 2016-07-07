import os
import animation, dmd
from dmd import Frame
from procgame import config
from procgame import util
from pygame.font import match_font
from sdl2_displaymanager import sdl2_DisplayManager
# import pygame

# Anchor values are used by Font.draw_in_rect():
AnchorN = 1
AnchorW = 2
AnchorE = 4
AnchorS = 8
AnchorNE = AnchorN | AnchorE
AnchorNW = AnchorN | AnchorW
AnchorSE = AnchorS | AnchorE
AnchorSW = AnchorS | AnchorW
AnchorCenter = 0

class HDFontStyle(object):
    def __init__(self, interior_color=(155,155,255), line_width=1, line_color=(132,32,132), fill_color=None):
        super(HDFontStyle,self).__init__()
        self.line_color=line_color
        self.line_width=line_width
        self.interior_color=interior_color
        self.fill_color=fill_color


class HDFont(object):
    """Object wrapper for a PyGame font.
    
    Fonts can be loaded manually, using :meth:`load`, or with the :func:`font_named` utility function
    which supports searching a font path."""
    
    char_widths = None
    """Array of dot widths for each character, 0-indexed from <space>.  
    This array is populated by :meth:`load`.  You may alter this array
    in order to update the font and then :meth:`save` it."""
    
    tracking = 0
    """Number of dots to adjust the horizontal position between characters, in addition to the last character's width."""
    
    composite_op = 'copy'
    """Composite operation used by :meth:`draw` when calling :meth:`~pinproc.DMDBuffer.copy_rect`."""
    
    pygFont = None


    def __init__(self, fontname, size, bold = False, font_file_path = None):
        super(HDFont, self).__init__()
        # init pyg

        # pygame.font.init()
        # p = pygame.font.match_font(fontname,bold)
        font_path = font_file_path
        if(font_path is None):
            font_path = match_font(fontname)
        try:
            p = sdl2_DisplayManager.inst().font_add(font_path=font_path, font_alias=fontname, size=None, color=None, bgcolor=None)
        except Exception, e:
            raise ValueError, "Specific font '%s' could not be found on your system or in path '%s' Please install/verify." % (fontname, font_file_path)

        if(p==None):
            raise ValueError, "Specific font '%s' could not be found on your system or in path '%s' Please install/verify." % (fontname, font_file_path)

        self.pygFont = p # pygame.font.Font(p,size)

        self.name = fontname
        self.font_size=size
        self.char_widths = []
        for i in range(96):
            self.char_widths += [size]
            #self.char_widths += [ self.pygFont.size(str(chr(i+32)))[0] ]
        self.char_size = size #self.pygFont.get_height()
        (self.font_width, self.font_height) = sdl2_DisplayManager.inst().font_get_size("Z", self.name, self.font_size)


    def textHollow(self, message, col_line, col_interior, line_width, col_bg):
        if(line_width>0):
            base = self.pygFont.render(message, False, col_line, col_bg)
        else:
            base = self.pygFont.render(message, False, col_interior, col_bg)
        size = (base.get_width() + line_width*2, base.get_height() + line_width*2)
        
        img = pygame.Surface(size, 16)

        img.fill(col_bg)
        base.set_colorkey(0)

        if(line_width>0):
            # builds out diagnals
            img.blit(base, (0, 0))
            img.blit(base, (line_width*2, 0))
            img.blit(base, (0, line_width*2))
            img.blit(base, (line_width*2, line_width*2))

            # builds out top sides
            img.blit(base, (0, line_width))
            img.blit(base, (line_width*2, line_width))
            img.blit(base, (line_width, 0))
            img.blit(base, (line_width, line_width*2))
        base.set_colorkey(0)
        base.set_palette_at(1, col_interior)
        img.blit(base, (line_width, line_width))
        img.set_colorkey(None)
        return img.convert()


    def drawHD(self, frame, text, x, y, line_color, line_width, interior_color, fill_color, font_size=None):
        """Uses this font's characters to draw the given string at the given position."""
        #t = self.pygFont.render(text,False,(255,0,255),(0,0,0))
        # print("drawHD(%s) - line color=%s | line width=%d" % (text,line_color, line_width ))
        if(line_color is None or line_width == 0):
            return self.draw(frame, text, x, y, interior_color, fill_color)

        # if(interior_color is None):
        #     interior_color=(255,255,255)

        # surf = self.pygFont.render(text,False,color,(0,0,0))
        # (w,h) = surf.get_size()

        if(text is None or text==""):
            return x

        if(font_size is None):
            font_size = self.font_size

        surf = sdl2_DisplayManager.inst().font_render_bordered_text(text, font_alias=self.name, size=font_size, width=None, color=interior_color, bg_color=fill_color, border_color=line_color, border_width=line_width)
        (w,h) = surf.size

        tmp = Frame(w,h, from_surface=surf)

        # tmp.composite_op = "blacksrc"

        # w = min(w, frame.width)
        # h = min(h, frame.height)        
        Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=tmp, src_x=0, src_y=0, width=w, height=h, op=self.composite_op)
        #Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.bitmap, src_x=char_x, src_y=char_y, width=width, height=self.char_size, op=self.composite_op)
            
        return x+w


    def draw(self, frame, text, x, y, color = None, bg_color = None, font_size=None):
        """Uses this font's characters to draw the given string at the given position."""
        #t = self.pygFont.render(text,False,(255,0,255),(0,0,0))
        if(color is None):
            color=(255,255,255)

        # surf = self.pygFont.render(text,False,color,(0,0,0))
        # (w,h) = surf.get_size()

        if(text is None or text==""):
            return x

        if(font_size is None):
            font_size = self.font_size
            
        surf = sdl2_DisplayManager.inst().font_render_text(text, font_alias=self.name, size=font_size, width=None, color=color, bg_color=bg_color)
        (w,h) = surf.size

        tmp = Frame(w,h, from_surface=surf)

        tmp.composite_op = "blacksrc"

        # w = min(w, frame.width)
        # h = min(h, frame.height)        
        Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=tmp, src_x=0, src_y=0, width=w, height=h, op=self.composite_op)
        #Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.bitmap, src_x=char_x, src_y=char_y, width=width, height=self.char_size, op=self.composite_op)
            
        return x+w
    
    def size(self, text):
        """Returns a tuple of the width and height of this text as rendered with this font."""
        #raise ValueError, "Size is not supported in HDText (yet)"
        return sdl2_DisplayManager.inst().font_get_size( text, self.name, self.font_size)
    
    def draw_in_rect(self, frame, text, rect=(0,0,128,32), anchor=AnchorCenter, font_size=None):
        """Draw *text* on *frame* within the given *rect*, aligned in accordance with *anchor*.
        
        *rect* is a tuple of length 4: (origin_x, origin_y, height, width). 0,0 is in the upper left (NW) corner.
        
        *anchor* is one of:
        :attr:`~procgame.dmd.AnchorN`,
        :attr:`~procgame.dmd.AnchorE`,
        :attr:`~procgame.dmd.AnchorS`,
        :attr:`~procgame.dmd.AnchorW`,
        :attr:`~procgame.dmd.AnchorNE`,
        :attr:`~procgame.dmd.AnchorNW`,
        :attr:`~procgame.dmd.AnchorSE`,
        :attr:`~procgame.dmd.AnchorSW`, or
        :attr:`~procgame.dmd.AnchorCenter` (the default).
        """
        origin_x, origin_y, width, height = rect

        if(font_size is None):
            font_size = self.font_size

        surf = sdl2_DisplayManager.inst().font_render_text(text, font_alias=self.name, size=font_size, width=None, color=None, bg_color=None)

        text_width, text_height = surf.size
        tmp = Frame(text_width,text_height, from_surface=surf)

        tmp.composite_op = "blacksrc"
        x = 0
        y = 0
        
        # print "Size: %d x %d" % (text_height)
        
        if anchor & AnchorN:
            y = origin_y
        elif anchor & AnchorS:
            y = origin_y + (height - text_height)
        else:
            y = origin_y + (height/2.0 - text_height/2.0)
        
        if anchor & AnchorW:
            x = origin_x
        elif anchor & AnchorE:
            x = origin_x + (width - text_width)
        else:
            x = origin_x + (width/2.0 - text_width/2.0)

        # w = min(width, frame.width)
        # h = min(height, frame.height)        
        w = text_width #min(width, frame.width)
        h = text_height#min(height, frame.height)        
        
        # self.draw(frame=frame, text=text, x=x, y=y)
        Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=tmp, src_x=0, src_y=0, width=w, height=h, op=tmp.composite_op)


hdfont_path = []
"""Array of paths that will be searched by :meth:`~procgame.dmd.font_named` to locate fonts.

When this module is initialized the pyprocgame global configuration (:attr:`procgame.config.values`)
``font_path`` key path is used to initialize this array."""

def init_hdfont_path():
    global hdfont_path
    try:
        value = config.value_for_key_path('hdfont_path')
        if issubclass(type(value), list):
            hdfont_path.extend(map(os.path.expanduser, value))
        elif issubclass(type(value), str):
            hdfont_path.append(os.path.expanduser(value))
        elif value == None:
            print('WARNING no font_path set in %s!' % (config.path))
        else:
            print('ERROR loading font_path from %s; type is %s but should be list or str.' % (config.path, type(value)))
            sys.exit(1)
    except ValueError, e:
        #print e
        pass

init_hdfont_path()


__hdfont_cache = {}
def hdfont_named(name, size, bold=False, font_file_path=None):
    """Searches the :attr:`font_path` for a font file of the given name and returns an instance of :class:`Font` if it exists."""
    cname = name + str(size)
    if cname in __hdfont_cache:
        return __hdfont_cache[cname]

    import dmd # have to do this to get dmd.Font to work below... odd.
    font = HDFont(name,size, bold, font_file_path=font_file_path)
    __hdfont_cache[cname] = font
    return font


def show_commandline_help():
    print("HELP!:")
    exit(1)

def main():
    from os import sys

    if len(sys.argv) <= 1:
        show_commandline_help()   

    import font
    from font import Font
    import layers
    from layers import HDTextLayer, TextLayer
    import time 
    import sdl2
    t0 = time.clock()
    import ctypes
    from ctypes import byref, cast, POINTER, c_int, c_float, sizeof, c_uint32, c_double, c_voidp, c_void_p
    from sdl2 import endian
 
    exp_font_name = sys.argv[1]

    font_size = 48

    if len(sys.argv) > 2:
        font_size = int(sys.argv[2])

    sdl2_DisplayManager.Init(10,10,1)
    sdl2_DisplayManager.inst().fonts_init("Courier", "HHSam")
    
    font_path = match_font(exp_font_name) #"coalition") 
    sdl2_DisplayManager.inst().font_add(font_path=font_path, font_alias="export_font", size=font_size)#, color=None, bgcolor=None)

    char_size = 0
    lChars = [ chr(i+ord(' ')) for i in xrange(0,95)]
    for char_offset,c in zip(xrange(0,95),lChars):
        # surf = f.textHollow(c, line_color, interior_color, line_width, fill_color)
        (font_width,font_height) = sdl2_DisplayManager.inst().font_get_size(c,'export_font', font_size)
        char_size = max(char_size, font_width, font_height)

    width = height = char_size * 10
    font_sizes = ''

    # hack stuff to re-attach the correctly sized window
    sdl2_DisplayManager.inst().window = sdl2.ext.Window("Font Preview", size=(width, height))  
    sdl2_DisplayManager.inst().texture_renderer = sdl2.ext.Renderer(sdl2_DisplayManager.inst().window)  
    sdl2_DisplayManager.inst().fill = sdl2_DisplayManager.inst().texture_renderer.fill
    sdl2_DisplayManager.inst().clear = sdl2_DisplayManager.inst().texture_renderer.clear
    sdl2_DisplayManager.inst().factory = sdl2.ext.SpriteFactory(renderer=sdl2_DisplayManager.inst().texture_renderer)  

    sdl2_DisplayManager.inst().show_window()

    frame = Frame(width, height)

    #BGR?
    interior_color = (255,255,255)
    line_width = 0
    #fill_color = (255,0,0)
    line_color = (1,1,1)

    for char_offset,c in zip(xrange(0,95),lChars):
        # surf = f.textHollow(c, line_color, interior_color, line_width, fill_color)
        
        surf = sdl2_DisplayManager.inst().font_render_bordered_text(c, font_alias='export_font', size=font_size, border_width=line_width, border_color=line_color, color=interior_color)
        (w,h) = surf.size
        (font_width,font_height) = sdl2_DisplayManager.inst().font_get_size(c,'export_font', font_size)
        
        #font_sizes += format(font_width,'x')
        font_sizes  += str(font_width)
        font_sizes += ","
        F = Frame(width=w, height=h, from_surface=surf)
            
        char_x = char_size * (char_offset % 10)
        char_y = char_size * (char_offset / 10)

        Frame.copy_rect(dst=frame, dst_x=char_x, dst_y=char_y, src=F, src_x=0, src_y=0, width=w, height=h, op='copy')
        #x += width + self.tracking

        
    sdl2_DisplayManager.inst().screen_blit(source_tx=frame.pySurface, expand_to_fill=True)#, area=(10,10,400,200))
    
    texture_renderer = sdl2_DisplayManager.inst().texture_renderer
    bk = sdl2.SDL_GetRenderTarget(texture_renderer.renderer)
    
    t =  sdl2.render.SDL_CreateTexture(texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
                                                                  sdl2.render.SDL_TEXTUREACCESS_STREAMING,
                                                                  width, height)
    #create a new texture and blit the frame to it, then grab bits from that
    texture_renderer.clear((0,0,0,0))
    sdl2.SDL_SetRenderTarget(texture_renderer.renderer, t)
    
    

    #sdl2_DisplayManager.inst().blit(source_tx=frame.pySurface, dest_tx = t, dest = (0,0,512,512))
    texture_renderer.copy(frame.pySurface, (0,0,width,height),(0,0,width,height))
    

    pitch = c_int()
    bytes = c_void_p()
    rect=sdl2.SDL_Rect(0,0,width,height)
    
    sdl2.SDL_LockTexture(t, rect, ctypes.byref(bytes), ctypes.byref(pitch))
        
    if endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN:
        rmask = 0x000000FF
        gmask = 0x0000FF00
        bmask = 0x00FF0000
        amask = 0xFF000000
    else:
        rmask = 0xFF000000
        gmask = 0x00FF0000
        bmask = 0x0000FF00
        amask = 0x000000FF
        
    print rmask
            
    imgsurface = sdl2.surface.SDL_CreateRGBSurfaceFrom(bytes, width, height,
                                                      32, pitch, rmask,
                                                      gmask, bmask, amask)
    if not imgsurface:
        raise sdl2.ext.SDLError()
    
    sdl2.SDL_RenderReadPixels(texture_renderer.renderer, rect, 0, bytes, pitch)
    sdl2.SDL_SaveBMP(imgsurface, 'image.png')
    
    
    #4) Restore renderer's texture target
    sdl2.SDL_SetRenderTarget(texture_renderer.renderer, bk)
    
    #ss = sdl2.ext.SoftwareSprite(surf, True)

    #ss = sdl2.ext.SoftwareSprite(imgsurface, True)
    #sdl2.SDL_SaveBMP(ss.contents, "file.bmp")
    #
    #
    print font_sizes

    sdl2_DisplayManager.inst().flip()
    sdl2.SDL_Delay(2)


    # evilFont = Font()
    # evilFont.char_size = char_size
    # evilFont.bitmap = frame
    # evilFont.char_widths = [30]*96

    # dFrame = Frame(500,500)

    # t0 = time.clock()
    # # print "Drawing via bitmap stamping % 10.3fms" % (t0)
    # tl = TextLayer(224/2, 140, evilFont, "center", opaque=True, width=500, height=50)
    # tl.set_text("Hello World!")

    # now = time.clock()
    # print "TextLayer and set_text  % 3.10fms" % (now - t0)
    # #screen.blit(tl.next_frame().pySurface,(0,0))
    # screen.blit(dFrame.pySurface,(0,0))
    # pygame.display.flip()
    # #screen.fill((0,0,0))


    # t0 = time.clock()
    # # print "Drawing via bitmap stamping % 10.3fms" % (t0)
    # x = 0
    # y = 0
    # w = evilFont.draw(dFrame, "Hello, World!", x, y) - x
    # h = 50
    # src_rect = pygame.Rect(int(0),int(0),int(w),int(h))
    # dst_rect = pygame.Rect(int(x),int(y),int(w),int(h))

    # center = Frame(w,h)
    # edge = Frame(w,h)
    # center.fill_rect(0,0,w,h,(255,0,0))
    # edge.fill_rect(0,0,w,h,(255,128,255))
    
    # dFrame.pySurface.set_colorkey((255,0,255))
    # edge.pySurface.blit(dFrame.pySurface, dst_rect, src_rect, special_flags = 0)
    # dFrame.pySurface.set_colorkey(None)

    # edge.pySurface.set_colorkey((0,255,0))
    # center.pySurface.blit(edge.pySurface, dst_rect, src_rect, special_flags = 0)
    # #src.copy_to_rect(dst, int(dst_x), int(dst_y), int(src_x), int(src_y), int(width), int(height), op)
    
    # #src.pySurface.set_colorkey(None)

    # #tl = HDTextLayer(224/2, 140, f, "center", opaque=True, width=500, height=50,line_color=(132,32,132), line_width=1, interior_color=(155,155,255),fill_color=None)

    # # tl = TextLayer(224/2, 7, evilFont, "center", opaque=True, width=500, height=50)
    # # tl.set_text("Hello World!")

    # # frame.pySurface.fill((0,0,128))

    # now = time.clock()
    # print "bitmap draw +  colorkey % 3.10fms" % (now - t0)
    # screen.fill((0,0,0))
    # #screen.blit(tl.next_frame().pySurface,(0,0))
    # screen.blit(center.pySurface,(0,0))
    # pygame.display.flip()

    # f.draw(dFrame, "Hello, World!", 0,200)

    # t0 = time.clock()
    # # print "% 10.3f - Starting new surface" % (t0)

    # tl = HDTextLayer(224/2, 140, f, "center", opaque=True, width=500, height=50,line_color=(132,32,132), line_width=1, interior_color=(155,155,255),fill_color=None)
    # tl.set_text("Hello World!")

    # # f.draw(dFrame, "Hello, World!", 0,200)

    #screen.blit(dFrame.pySurface,(0,0))

    # now = time.clock()
    # print "HDTextLayer +set_text() % 3.10fms" % (now - t0)

    # screen.blit(tl.next_frame().pySurface,(0,0))

    # #screen.blit(dFrame.pySurface,(0,0))

    # pygame.display.flip()


    # dFrame.clear()

    # ###----------------------------------
    # t0 = time.clock()

    ###----------------------------------

    # now = time.clock()
    # print "font draw % 3.10fms" % (now - t0)

    # screen.blit(dFrame.pySurface,(0,0))
    # pygame.display.flip()

    # ###----------------------------------

    # ###----------------------------------
    # t0 = time.clock()

    ###----------------------------------

    # now = time.clock()
    # print "HD draw() % 3.10fms" % (now - t0)

    # screen.blit(dFrame.pySurface,(0,0))
    # pygame.display.flip()

    # ###----------------------------------

    # ###----------------------------------
    # t0 = time.clock()

    # f.drawHD(dFrame, "Hello, world!", 224/2, 140, line_color=(132,32,132), line_width=1, interior_color=(155,155,255),fill_color=None)

    # now = time.clock()
    # print "HD drawHD % 3.10fms" % (now - t0)

    # screen.blit(dFrame.pySurface,(0,0))
    # pygame.display.flip()

    ###----------------------------------

    # now = time.clock()
    # print "% 10.6f -ms new surface Done" % (now - t0)



    # screen.blit(frame.pySurface,(0,0))
    # pygame.display.flip()

    # import time
    # time.sleep(10)
    # pygame.quit()

if __name__ == '__main__':
    main()
