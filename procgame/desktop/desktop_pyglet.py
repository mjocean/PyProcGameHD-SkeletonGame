import procgame.config
import procgame.dmd
import pinproc
import pyglet
import pyglet.image
import pyglet.window
from pyglet import gl
import colorsys

# Bitmap data for luminance-alpha mask image.
# See image_to_string below for code to generate this:
MASK_DATA = """\x00\xec\x00\xc8\x00\x7f\x00\x5a\x00\x5a\x00\x7f\x00\xc8\x00\xed\x00\xc8\x00\x5a\x00\x36\x00\x11\x00\x11\x00\x36\x00\x5a\x00\xc8\x00\x7f\x00\x36\xff\x00\xff\x00\xff\x00\xff\x00\x00\x36\x00\x7e\x00\x5a\x00\x10\xff\x00\xff\x00\xff\x00\xff\x00\x00\x11\x00\x5a\x00\x5a\x00\x11\xff\x00\xff\x00\xff\x00\xff\x00\x00\x11\x00\x5a\x00\x7e\x00\x36\xff\x00\xff\x00\xff\x00\xff\x00\x00\x35\x00\x7f\x00\xc8\x00\x5a\x00\x36\x00\x11\x00\x11\x00\x35\x00\x5a\x00\xc8\x00\xed\x00\xc8\x00\x7e\x00\x5a\x00\x5a\x00\x7f\x00\xc8\x00\xed"""
MASK_SIZE = 8

DMD_SIZE = (128, 32)
DMD_SCALE = int(procgame.config.value_for_key_path('desktop_dmd_scale', str(MASK_SIZE)))

class Desktop(object):
    """The :class:`Desktop` class helps manage interaction with the desktop, providing both a windowed
    representation of the DMD, as well as translating keyboard input into pyprocgame events."""

    exit_event_type = 99
    """Event type sent when Ctrl-C is received."""

    key_map = {}

    window = None

    def __init__(self):
        self.key_events = []
        self.setup_window()
        self.add_key_map(pyglet.window.key.LSHIFT, 3)
        self.add_key_map(pyglet.window.key.RSHIFT, 1)
        self.frame_drawer = FrameDrawer()



    def add_key_map(self, key, switch_number):
        """Maps the given *key* to *switch_number*, where *key* is one of the key constants in :mod:`pygame.locals`."""
        self.key_map[key] = switch_number

    def clear_key_map(self):
        """Empties the key map."""
        self.key_map = {}

    def get_keyboard_events(self):
        """Asks :mod:`pygame` for recent keyboard events and translates them into an array
        of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
        if self.window.has_exit:
            self.append_exit_event()
        e = self.key_events
        self.key_events = []
        return e

    def append_exit_event(self):
        self.key_events.append({'type':self.exit_event_type, 'value':'quit'})

    def setup_window(self):
        self.window = pyglet.window.Window(width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)

        @self.window.event
        def on_close():
            self.append_exit_event()

        @self.window.event
        def on_key_press(symbol, modifiers):
            if (symbol == pyglet.window.key.C and modifiers & pyglet.window.key.MOD_CTRL) or (symbol == pyglet.window.key.ESCAPE):
                self.append_exit_event()
            elif symbol in self.key_map:
                self.key_events.append({'type':pinproc.EventTypeSwitchClosedDebounced, 'value':self.key_map[symbol]})

        @self.window.event
        def on_key_release(symbol, modifiers):
            if symbol in self.key_map:
                self.key_events.append({'type':pinproc.EventTypeSwitchOpenDebounced, 'value':self.key_map[symbol]})

    def draw(self, frame):
        """Draw the given :class:`~procgame.dmd.Frame` in the window."""
        self.window.dispatch_events()
        self.window.clear()
        self.frame_drawer.draw(frame)
        self.window.flip()

    def __str__(self):
        return '<Desktop pyglet>'







class FrameDrawer(object):
    """Manages drawing a DMD frame using pyglet."""
    def __init__(self):
        super(FrameDrawer, self).__init__()
        self.mask = pyglet.image.ImageData(MASK_SIZE, MASK_SIZE, 'LA', MASK_DATA, pitch=16)
        self.mask_texture = pyglet.image.TileableTexture.create_for_image(self.mask)
        
        self.eight_to_RGB_map = self.buildMap()

    def draw(self, frame):
        # The gneneral plan here is:
        #  1. Get the dots in the range of 0-255.
        #  2. Create a texture with the dots data.
        #  3. Draw the texture, scaled up with nearest-neighbor.
        #  4. Draw a mask over the dots to give them a slightly more realistic look.

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glLoadIdentity()

        # Draw the dots in this color:
        #gl.glColor3f(1.0, 0.5, 0.25)

        gl.glScalef(1, -1, 1)
        gl.glTranslatef(0, -DMD_SIZE[1]*DMD_SCALE, 0)

        #data = frame.get_data_mult()
        
        #this new jk_get_data will read the dots using the dmd function
        #and convert them via the map to rGB.
        data = self.jk_get_data(frame)

        image = pyglet.image.ImageData(DMD_SIZE[0], DMD_SIZE[1], 'RGB', data, pitch=DMD_SIZE[0] * 3)  

        gl.glTexParameteri(image.get_texture().target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        image.blit(0, 0, width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)

        del image

        gl.glScalef(DMD_SCALE/float(MASK_SIZE), DMD_SCALE/float(MASK_SIZE), 1.0)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.mask_texture.blit_tiled(x=0, y=0, z=0, width=DMD_SIZE[0]*MASK_SIZE, height=DMD_SIZE[1]*MASK_SIZE)

    def jk_get_data(self,frame):
        data=''
        for y in range(0,32):
            for x in range(0,128):
                dot = frame.get_dot(x,y)
                r,g,b = self.eight_to_RGB_map[dot]
                
                data = data + chr(r) + chr(g) + chr(b)
        return data

    def buildMap_2(self):

        my_map=[(0,0,0)] * 256
        
        for shad in range(0,16):
            red_on = 1 # defines the shade
            grn_on = 1 # for the default
            blu_on = 0 # dmd coloring
            dot = shad

            scaled_shade = int((shad/15.0) * 255)

            color = (red_on * scaled_shade,grn_on*int(scaled_shade/2),blu_on*scaled_shade)
            my_map[dot] = color
        
        idx=16
        for r in range(0,6):
            for g in range(0,8):
                for b in range(0,5):
                    color = (int(255/5 * r) ,int(255/7 * g) , int(255/4 * b))
                    if idx <= 255:
                        my_map[idx]= color
                    idx +=1
        my_map[255]=(255,255,255)

        return my_map


    def buildMap(self):
        HLS_map = [0] * 256 

        # build the first 16 shades, these are the default
        # "non-colored" shades (e.g., the defaults).  I make
        # them orange, because I like an orange DMD.
        for shad in range(0,16):
                red_on = 1 # defines the shade
                grn_on = 1 # for the default
                blu_on = 0 # dmd coloring
                dot = shad

                scaled_shade = int((shad/15.0) * 255)

                color = (red_on * scaled_shade,grn_on*int(scaled_shade/2),blu_on*scaled_shade)
                HLS_map[dot] = color

        # fill the remainder of the first 128 with 0's
        # this is because the left-most bit (128's) 
        # indicates 1='color' or 0='non-color'
        for i in range(16,128):
                HLS_map[i] = (0,0,0)

        # this is my selection of hues and respective saturations
        # each hue is paired with a saturation.
        hues = [0,   0, 12,  22,  31,  42,  46,  68,  85, 110, 145, 155, 165, 192, 221, 245]
        sats = [0, 180, 80, 150, 150,  50, 150, 150, 150, 150, 150,  50, 150, 150, 150,  50]

        # for each of the 16 hue/sat pairs, add 8 colors of that pair with
        # increasing lightness. 
        idx = 128
        for deg in range(0,16):
                for lum in range (0,8):
                        (r,g,b) = colorsys.hls_to_rgb(hues[deg]/255.0, (lum+1)/9.0,sats[deg]/255.0)
                        color = (int(r*255),int(g*255),int(b*255))
                        HLS_map[idx] = color
                        idx = idx + 1
        return HLS_map

def image_to_string(filename):
    """Generate a string representation of the image at the given path, for embedding in code."""
    image = pyglet.image.load(filename)
    data = image.get_data('LA', 16)
    s = ''
    for x in data:
        s += "\\x%02x" % (ord(x))
    return s
