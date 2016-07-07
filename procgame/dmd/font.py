import os
from animation import Animation
from dmd import Frame
from procgame import config
from procgame import util
import csv

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

class Font(object):
    """Variable-width bitmap font.
    
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
    
    def __init__(self, filename=None, char_widths=None):
        super(Font, self).__init__()
        self.__anim = Animation()
        self.char_size = None
        self.bitmap = None
        if filename != None:
            self.load(filename, char_widths)
        
    def load(self, filename, char_widths = None):
        """Loads the font from a ``.dmd`` file (see :meth:`Animation.load`).
        Fonts are stored in .dmd files with frame 0 containing the bitmap data
        and frame 1 containing the character widths.  96 characters (32..127,
        ASCII printables) are stored in a 10x10 grid, starting with space (``' '``) 
        in the upper left at 0, 0.  The character widths are stored in the second frame
        within the 'raw' bitmap data in bytes 0-95.
        """
        (font_info_file, ext) = os.path.splitext(filename)
        (file_base_name, file_extension) = os.path.splitext(filename)
        #if ext == '.bmp':
        #    self.load_png_font(filename)
        self.__anim.load(filename, composite_op = 'blacksrc')
        if self.__anim.width != self.__anim.height:
            raise ValueError, "Width != height!"
        if ext == '.dmd':
            if len(self.__anim.frames) == 1:
                # We allow 1 frame for handmade fonts.
                # This is so that they can be loaded as a basic bitmap, have their char widths modified, and then be saved.
                print "Font animation file %s has 1 frame; adding one" % (filename)
                self.__anim.frames += [Frame(self.__anim.width, self.__anim.height)]
            elif len(self.__anim.frames) != 2:
                raise ValueError, "Expected 2 frames: %d" % (len(self.__anim.frames))
        self.char_size = self.__anim.width / 10
        self.bitmap = self.__anim.frames[0]

        self.char_widths = []
        if ext=='.dmd':
            
            if(char_widths==None):
                for i in range(96):
                    #print 'getting widths for character number: ' + str(i)
                    #print  'x ' + str(i%self.__anim.width)
                    self.char_widths += [self.__anim.frames[1].get_font_dot(i%self.__anim.width, i/self.__anim.width)]
                    #self.char_widths += [self.char_size] #JEK hack
            else:
                # print("font widths provided")
                self.char_widths = char_widths
                # for i in range(96):
                #   self.__anim.frames[1].set_font_dot(i%self.__anim.width, i/self.__anim.width, self.char_widths[i])
        
        elif ext =='.bmp' or ext == '.png' or ext =='.jpg':
                    #now read in the widths
            (path,file) = os.path.split(filename)
            csv_file = font_info_file + ".csv"
            with open(csv_file, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in reader:                    
                    for s in row:
                        self.char_widths +=[int(s)]
        else:
            raise ValueError, "Font failed to load [%s] Expected font of type .dmd, .png, .bmp, or .jpg" % filename
        return self
    
    def save(self, filename):
        """Save the font to the given path."""
        out = Animation()
        out.width = self.__anim.width
        out.height = self.__anim.height
        out.frames = [self.bitmap, Frame(out.width, out.height)]
        for i in range(96):
            out.frames[1].set_font_dot(i%self.__anim.width, i/self.__anim.width, self.char_widths[i])
        out.save_old(filename)
        
    def draw(self, frame, text, x, y):
        """Uses this font's characters to draw the given string at the given position."""
        for ch in text:
            char_offset = ord(ch) - ord(' ')
            if char_offset < 0 or char_offset >= 96:
                continue
            char_x = self.char_size * (char_offset % 10)
            char_y = self.char_size * (char_offset / 10)
            width = self.char_widths[char_offset]
            Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.bitmap, src_x=char_x, src_y=char_y, width=width, height=self.char_size, op=self.composite_op)
            x += width + self.tracking
        return x
    
    def size(self, text):
        """Returns a tuple of the width and height of this text as rendered with this font."""
        x = 0
        for ch in text:
            char_offset = ord(ch) - ord(' ')
            if char_offset < 0 or char_offset >= 96:
                continue
            width = self.char_widths[char_offset]
            x += width + self.tracking
        return (x, self.char_size)
    
    def draw_in_rect(self, frame, text, rect=(0,0,128,32), anchor=AnchorCenter):
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
        text_width, text_height = self.size(text)
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
        
        self.draw(frame=frame, text=text, x=x, y=y)

###################################
# Animated Fonts
class AnimFont(Font):
    """An animated Font with multiple frames per letter.
    
    Fonts can be loaded manually, using :meth:`load`, or with the :func:`font_named` utility function
    which supports searching a font path."""
        
    frames = None
    current = 0

    def __init__(self, filename=None):
        super(AnimFont, self).__init__()
        self.frames = list()
        self.current = 0
        self.__anim = Animation()
        if filename != None:
            self.load(filename)
        
    def load(self, filename): 
        """Loads the font from a ``.dmd`` file (see :meth:`Animation.load`).
        Fonts are stored in .dmd files with frame 0 containing the bitmap data
        and frame 1 containing the character widths.  96 characters (32..127,
        ASCII printables) are stored in a 10x10 grid, starting with space (``' '``) 
        in the upper left at 0, 0.  The character widths are stored in the second frame
        (index 1) within the 'raw' bitmap data in bytes 0-95; additional frames make
        up the rest of the animation.
        """
        (font_info_file, ext) = os.path.splitext(filename)

        if(ext == '.dmd'):
            composite_op = 'blacksrc'
        else:
            composite_op = None
        self.__anim.load(filename, composite_op=composite_op)

        if len(self.__anim.frames) < 1:
            raise ValueError, "Expected a minimum 2 frames: %d" % (len(self.__anim.frames))
        
        self.frames = list(self.__anim.frames)

        font_info_file = font_info_file + ".csv"
        self.char_data = self.parseCBFGinfo(font_info_file)
        self.char_height = self.char_data['Cell Height']
        self.char_width = self.char_data['Cell Width']
        self.char_size = self.char_width
        self.char_widths = list()
        # if(char_widths==None):
        for i in range(96):
            ch = chr(int(i+ord(' ')))
            self.char_widths += [self.char_data['positions'][ch]['Base Width'] + self.char_data['positions'][ch]['Width Offset']]
        #         self.char_widths += [14] #[self.__anim.frames[1].get_font_dot(i%self.__anim.width, i/self.__anim.width)]
        #         # self.char_widths += [self.__anim.frames[1].get_font_dot(i%self.__anim.width, i/self.__anim.width)]
        #         # print("Width: %d" % self.char_widths[-1])
        # else:
        #     self.char_widths = char_widths

        # for i in range(2,len(self.__anim.frames)):
        #     self.frames.append(self.__anim.frames[i])

        return self

    def parseCBFGinfo(self, filename):
        font_data = {}
        width_file = open(filename)

        for line in width_file:
            parse = line.split(',')
            line_data = parse[0]
            if line_data == "Font Name":
                line_value = parse[1][:-1]
                font_data[line_data] = line_value                
            else:
                line_value = int(parse[1][:-1])

                if line_data.startswith('Char'):
                    char_info = line_data.split(' ')
                    char = chr(int(char_info[1]))
                    if('positions' not in font_data):
                        font_data['positions'] = {}
                    if(char in font_data['positions']):
                        place = font_data['positions'][char]
                    else:
                        place = {}
                        font_data['positions'][char] = place

                    place[char_info[2] + ' ' + char_info[3]] = line_value
                else:
                    font_data[line_data] = line_value
    
        return font_data

    def size(self, text):
        """Returns a tuple of the width and height of this text as rendered with this font."""
        x = 0
        for ch in text:
            char_offset = ord(ch) - ord(' ')
            if char_offset < 0 or char_offset >= 96:
                continue
            width = self.char_widths[char_offset]
            x += width + self.tracking
        return (x, self.char_size)

    def save(self, filename):
        """Save the font to the given path."""
        out = Animation()
        out.width = self.__anim.width
        out.height = self.__anim.height
        out.frames = [self.bitmap, Frame(out.width, out.height)]
        for i in range(96):
            out.frames[1].set_font_dot(i%self.__anim.width, i/self.__anim.width, self.char_widths[i])
        out.save_old(filename)

    # def draw(self, frame, text, x, y):
    #     Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.frames[self.current], src_x=0, src_y=0, width=224, height=112, op=self.composite_op)

    def draw(self, frame, text, x, y):
        """Uses this font's characters to draw the given string at the given position."""
        #print("drawing word with animation # %d" % self.current)
        for ch in text:
            char_offset = ord(ch) - ord(' ')
            if char_offset < 0 or char_offset >= 96:
                continue
            char_x = self.char_width * (char_offset % 10) + self.char_data['positions'][ch]['X Offset']
            char_y = self.char_height * (char_offset / 10) + self.char_data['positions'][ch]['Y Offset']
            width = self.char_widths[char_offset]
            #print("Blitting an %c at [%d,%d] width=%d" % (ch,char_x,char_y,width))
            Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.frames[self.current], src_x=char_x, src_y=char_y, width=width, height=self.char_height, op=self.composite_op)
            x += width + self.tracking
        self.current = (self.current + 1) % len(self.frames)
        return x
    

#
# convert ./flames_000.png -resize 512x50\! ftmp.png ; composite -tile ./ftmp.png -size 512x512  xc:none  flame_font_000.png ; rm ftmp.png
# 
####################################

font_path = []
"""Array of paths that will be searched by :meth:`~procgame.dmd.font_named` to locate fonts.

When this module is initialized the pyprocgame global configuration (:attr:`procgame.config.values`)
``font_path`` key path is used to initialize this array."""

def init_font_path():
    global font_path
    try:
        value = config.value_for_key_path('font_path')
        if issubclass(type(value), list):
            font_path.extend(map(os.path.expanduser, value))
        elif issubclass(type(value), str):
            font_path.append(os.path.expanduser(value))
        elif value == None:
            print('WARNING no font_path set in %s!' % (config.path))
        else:
            print('ERROR loading font_path from %s; type is %s but should be list or str.' % (config.path, type(value)))
            sys.exit(1)
    except ValueError, e:
        #print e
        pass

init_font_path()


__font_cache = {}
def font_named(name):
    """Searches the :attr:`font_path` for a font file of the given name and returns an instance of :class:`Font` if it exists."""
    if name in __font_cache:
        return __font_cache[name]
    path = util.find_file_in_path(name, font_path)
    if path:
        import dmd # have to do this to get dmd.Font to work below... odd.
        font = Font(path)
        __font_cache[name] = font
        return font
    else:
        if(font_path is None):
            raise ValueError, 'Failed to load font "%s"; font_path was not set in your config.yaml (or config.yaml contains errors)' % (name)    
        raise ValueError, 'Font named "%s" was not found in the following font_path=%s. Add the file or add additional folders to the font path in config.yaml' % (name, font_path)

