import os
from animation import Animation
from dmd import Frame
from procgame import config
from procgame import util
from font import Font

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
