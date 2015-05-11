# from dmd import *
# from layers import *
# from procgame.dmd import Frame
import colorsys

# try:
#   import Image
# except ImportError:
#   Image = None

class VgaDMD(object):
    # def convertImage(src):
    #   pal_image= Image.new("P", (1,1))

    #   tuplePal = VgaDMD.get_palette()
    #   flatPal = [element for tupl in tuplePal for element in tupl]
    #   pal_image.putpalette(flatPal)
    #   src_rgb = src.convert("RGB").quantize(palette=pal_image)
    #   src_p = src_rgb.convert("P")

    #   (w,h) = src.size
    #   frame = Frame(w, h)
    #   for x in range(w):
    #       for y in range(h):
    #           color = src_p.getpixel((x,y))
    #           # if(color > 0 and color < 8):
    #           #   # 0 is transparent; 1 to 7 are "reseved"
    #           #   # nothing should be assigning colors in this range...
    #           #   color = 0
    #           frame.set_dot(x=x, y=y, value=color)
    #   return frame

    # convertImage = staticmethod(convertImage)


    # def convertImage_oldWay(src):
    #   frame = Frame(w, h)

    #   # Construct a lookup table from 0-255 to 0-15:
    #   #eight_to_four_map = self.buildMap()

    #   print(range(w))
    #   print(range(h))
    #   src_rgb = src.convert('RGB')
    #   print src_rgb.size[0]
    #   print src_rgb.size[1]
        
    #   for x in range(w):
    #       for y in range(h):
    #           #print "starting [" + str(x) + "," + str(y) + "]..."

    #           r,g,b =  src_rgb.getpixel((x,y))

    #           rb = (r/255.0)
    #           gb = (g/255.0)
    #           bb = (b/255.0)

    #           (hue,lum,sat) = colorsys.rgb_to_hls(rb,gb,bb)
    #           hue=(hue*255.0)
    #           #l=l*255
    #           sat=(sat*255.0)
    #           #print "[" + str(x) + "," + str(y) + "], RGB:(" + str(r) + "," + str(g) + "," + str(b) + "):" + str(rb) + "," + str(gb) + "," + str(bb) + " as HSL: H:" + str(hue) + ", S:" + str(sat)
                
    #           closest = 255
    #           c = 0
    #           for i in range(0,16):                       
    #               # compute distance function, hues/sats
    #               # should tweak these for closert color matches
    #               # fine for now..?
    #               tmp = abs(hues[i] - hue) + abs(sats[i] - sat)
    #               if(tmp < closest):
    #                   closest = tmp
    #                   c = i

    #           color = 128 + (c * 8) + int(lum * 7)

    #           #print  "==>" + str(color)

    #           frame.set_dot(x=x, y=y, value=color)
    #           #print "[" + str(x) + "," + str(y) + "], done."
    #   return frame
    # convertImage_oldWay = staticmethod(convertImage_oldWay)

    def get_palette_ch():
        return [('\x00', '\x00', '\x00'), ('\x11', '\x11', '\x11'), ('"', '"', '"'), ('3', '3', '3'), ('D', 'D', 'D'), ('U', 'U', 'U'), ('f', 'f', 'f'), ('w', 'w', 'w'), ('\x88', '\x88', '\x88'), ('\x99', '\x99', '\x99'), ('\xaa', '\xaa', '\xaa'), ('\xbb', '\xbb', '\xbb'), ('\xcc', '\xcc', '\xcc'), ('\xdd', '\xdd', '\xdd'), ('\xee', '\xee', '\xee'), ('\xff', '\xff', '\xff'), ('\xff', '\xff', '0'), ('\xff', '0', '0'), ('\x81', '8', '8'), ('\xa1', 'F', 'F'), ('\xb8', ']', ']'), ('\xc6', '}', '}'), ('\xd4', '\x9e', '\x9e'), ('\xe2', '\xbe', '\xbe'), ('R', '\n', '\n'), ('|', '\x0f', '\x0f'), ('\xa5', '\x14', '\x14'), ('\xce', '\x19', '\x19'), ('\xe5', '0', '0'), ('\xeb', 'Y', 'Y'), ('\xf0', '\x82', '\x82'), ('\xf5', '\xac', '\xac'), ('@', ')', '\x1c'), ('`', '>', '*'), ('\x81', 'S', '8'), ('\xa1', 'h', 'F'), ('\xb8', '\x7f', ']'), ('\xc6', '\x99', '}'), ('\xd4', '\xb2', '\x9e'), ('\xe2', '\xcc', '\xbe'), ('R', '%', '\n'), ('|', '8', '\x0f'), ('\xa5', 'J', '\x14'), ('\xce', ']', '\x19'), ('\xe5', 't', '0'), ('\xeb', '\x90', 'Y'), ('\xf0', '\xab', '\x82'), ('\xf5', '\xc7', '\xac'), ('@', '7', '\x1c'), ('`', 'S', '*'), ('\x81', 'o', '8'), ('\xa1', '\x8a', 'F'), ('\xb8', '\xa2', ']'), ('\xc6', '\xb4', '}'), ('\xd4', '\xc7', '\x9e'), ('\xe2', '\xd9', '\xbe'), ('R', '@', '\n'), ('|', 'a', '\x0f'), ('\xa5', '\x81', '\x14'), ('\xce', '\xa1', '\x19'), ('\xe5', '\xb9', '0'), ('\xeb', '\xc7', 'Y'), ('\xf0', '\xd5', '\x82'), ('\xf5', '\xe3', '\xac'), (';', '@', '\x1c'), ('Y', '`', '*'), ('w', '\x81', '8'), ('\x95', '\xa1', 'F'), ('\xac', '\xb8', ']'), ('\xbd', '\xc6', '}'), ('\xcd', '\xd4', '\x9e'), ('\xde', '\xe2', '\xbe'), ('I', 'R', '\n'), ('m', '|', '\x0f'), ('\x92', '\xa5', '\x14'), ('\xb7', '\xce', '\x19'), ('\xce', '\xe5', '0'), ('\xd8', '\xeb', 'Y'), ('\xe1', '\xf0', '\x82'), ('\xeb', '\xf5', '\xac'), ('.', '@', '\x1c'), ('E', '`', '*'), ('\\', '\x81', '8'), ('s', '\xa1', 'F'), ('\x8a', '\xb8', ']'), ('\xa1', '\xc6', '}'), ('\xb9', '\xd4', '\x9e'), ('\xd0', '\xe2', '\xbe'), ('-', 'R', '\n'), ('D', '|', '\x0f'), ('[', '\xa5', '\x14'), ('r', '\xce', '\x19'), ('\x8a', '\xe5', '0'), ('\xa1', '\xeb', 'Y'), ('\xb8', '\xf0', '\x82'), ('\xd0', '\xf5', '\xac'), (' ', '@', '\x1c'), ('0', '`', '*'), ('@', '\x81', '8'), ('Q', '\xa1', 'F'), ('h', '\xb8', ']'), ('\x86', '\xc6', '}'), ('\xa4', '\xd4', '\x9e'), ('\xc2', '\xe2', '\xbe'), ('\x12', 'R', '\n'), ('\x1b', '|', '\x0f'), ('%', '\xa5', '\x14'), ('.', '\xce', '\x19'), ('E', '\xe5', '0'), ('j', '\xeb', 'Y'), ('\x8f', '\xf0', '\x82'), ('\xb4', '\xf5', '\xac'), ('\x1c', '@', '%'), ('*', '`', '8'), ('8', '\x81', 'K'), ('F', '\xa1', ']'), (']', '\xb8', 'u'), ('}', '\xc6', '\x90'), ('\x9e', '\xd4', '\xac'), ('\xbe', '\xe2', '\xc7'), ('\n', 'R', '\x1c'), ('\x0f', '|', '+'), ('\x14', '\xa5', '9'), ('\x19', '\xce', 'H'), ('0', '\xe5', '_'), ('Y', '\xeb', '\x7f'), ('\x82', '\xf0', '\x9f'), ('\xac', '\xf5', '\xbf'), ('\x1c', '@', '3'), ('*', '`', 'L'), ('8', '\x81', 'f'), ('F', '\xa1', '\x80'), (']', '\xb8', '\x97'), ('}', '\xc6', '\xac'), ('\x9e', '\xd4', '\xc0'), ('\xbe', '\xe2', '\xd5'), ('\n', 'R', '8'), ('\x0f', '|', 'T'), ('\x14', '\xa5', 'p'), ('\x19', '\xce', '\x8c'), ('0', '\xe5', '\xa3'), ('Y', '\xeb', '\xb5'), ('\x82', '\xf0', '\xc8'), ('\xac', '\xf5', '\xda'), ('\x1c', '@', '@'), ('*', '`', '`'), ('8', '\x80', '\x81'), ('F', '\xa0', '\xa1'), (']', '\xb7', '\xb8'), ('}', '\xc5', '\xc6'), ('\x9e', '\xd4', '\xd4'), ('\xbe', '\xe2', '\xe2'), ('\n', 'Q', 'R'), ('\x0f', 'z', '|'), ('\x14', '\xa3', '\xa5'), ('\x19', '\xcc', '\xce'), ('0', '\xe3', '\xe5'), ('Y', '\xe9', '\xeb'), ('\x82', '\xee', '\xf0'), ('\xac', '\xf4', '\xf5'), ('\x1c', '2', '@'), ('*', 'K', '`'), ('8', 'd', '\x81'), ('F', '~', '\xa1'), (']', '\x95', '\xb8'), ('}', '\xaa', '\xc6'), ('\x9e', '\xbf', '\xd4'), ('\xbe', '\xd4', '\xe2'), ('\n', '6', 'R'), ('\x0f', 'Q', '|'), ('\x14', 'l', '\xa5'), ('\x19', '\x88', '\xce'), ('0', '\x9f', '\xe5'), ('Y', '\xb2', '\xeb'), ('\x82', '\xc5', '\xf0'), ('\xac', '\xd8', '\xf5'), ('\x1c', '$', '@'), ('*', '7', '`'), ('8', 'I', '\x81'), ('F', '[', '\xa1'), (']', 's', '\xb8'), ('}', '\x8f', '\xc6'), ('\x9e', '\xab', '\xd4'), ('\xbe', '\xc7', '\xe2'), ('\n', '\x1b', 'R'), ('\x0f', '(', '|'), ('\x14', '6', '\xa5'), ('\x19', 'C', '\xce'), ('0', 'Z', '\xe5'), ('Y', '{', '\xeb'), ('\x82', '\x9c', '\xf0'), ('\xac', '\xbd', '\xf5'), ('!', '\x1c', '@'), ('1', '*', '`'), ('B', '8', '\x81'), ('S', 'F', '\xa1'), ('j', ']', '\xb8'), ('\x88', '}', '\xc6'), ('\xa5', '\x9e', '\xd4'), ('\xc3', '\xbe', '\xe2'), ('\x14', '\n', 'R'), ('\x1e', '\x0f', '|'), ('(', '\x14', '\xa5'), ('2', '\x19', '\xce'), ('I', '0', '\xe5'), ('n', 'Y', '\xeb'), ('\x92', '\x82', '\xf0'), ('\xb6', '\xac', '\xf5'), ('/', '\x1c', '@'), ('F', '*', '`'), ('^', '8', '\x81'), ('u', 'F', '\xa1'), ('\x8c', ']', '\xb8'), ('\xa3', '}', '\xc6'), ('\xba', '\x9e', '\xd4'), ('\xd1', '\xbe', '\xe2'), ('/', '\n', 'R'), ('G', '\x0f', '|'), ('_', '\x14', '\xa5'), ('w', '\x19', '\xce'), ('\x8e', '0', '\xe5'), ('\xa4', 'Y', '\xeb'), ('\xbb', '\x82', '\xf0'), ('\xd1', '\xac', '\xf5'), ('<', '\x1c', '@'), ('[', '*', '`'), ('y', '8', '\x81'), ('\x97', 'F', '\xa1'), ('\xae', ']', '\xb8'), ('\xbe', '}', '\xc6'), ('\xce', '\x9e', '\xd4'), ('\xde', '\xbe', '\xe2'), ('K', '\n', 'R'), ('p', '\x0f', '|'), ('\x96', '\x14', '\xa5'), ('\xbb', '\x19', '\xce'), ('\xd2', '0', '\xe5'), ('\xdb', 'Y', '\xeb'), ('\xe4', '\x82', '\xf0'), ('\xed', '\xac', '\xf5'), ('@', '\x1c', '6'), ('`', '*', 'R'), ('\x81', '8', 'm'), ('\xa1', 'F', '\x88'), ('\xb8', ']', '\x9f'), ('\xc6', '}', '\xb2'), ('\xd4', '\x9e', '\xc5'), ('\xe2', '\xbe', '\xd8'), ('R', '\n', '?'), ('|', '\x0f', '^'), ('\xa5', '\x14', '~'), ('\xce', '\x19', '\x9d'), ('\xe5', '0', '\xb4'), ('\xeb', 'Y', '\xc3'), ('\xf0', '\x82', '\xd2'), ('\xf5', '\xac', '\xe1')]
    get_palette_ch = staticmethod(get_palette_ch)

    def get_palette():
        return [(0, 0, 0), (17, 17, 17), (34, 34, 34), (51, 51, 51), (68, 68, 68), (85, 85, 85), (102, 102, 102), (119, 119, 119), (136, 136, 136), (153, 153, 153), (170, 170, 170), (187, 187, 187), (204, 204, 204), (221, 221, 221), (238, 238, 238), (255, 255, 255), (255,255,0), (255,0,0), (129, 56, 56), (161, 70, 70), (184, 93, 93), (198, 125, 125), (212, 158, 158), (226, 190, 190), (82, 10, 10), (124, 15, 15), (165, 20, 20), (206, 25, 25), (229, 48, 48), (235, 89, 89), (240, 130, 130), (245, 172, 172), (64, 41, 28), (96, 62, 42), (129, 83, 56), (161, 104, 70), (184, 127, 93), (198, 153, 125), (212, 178, 158), (226, 204, 190), (82, 37, 10), (124, 56, 15), (165, 74, 20), (206, 93, 25), (229, 116, 48), (235, 144, 89), (240, 171, 130), (245, 199, 172), (64, 55, 28), (96, 83, 42), (129, 111, 56), (161, 138, 70), (184, 162, 93), (198, 180, 125), (212, 199, 158), (226, 217, 190), (82, 64, 10), (124, 97, 15), (165, 129, 20), (206, 161, 25), (229, 185, 48), (235, 199, 89), (240, 213, 130), (245, 227, 172), (59, 64, 28), (89, 96, 42), (119, 129, 56), (149, 161, 70), (172, 184, 93), (189, 198, 125), (205, 212, 158), (222, 226, 190), (73, 82, 10), (109, 124, 15), (146, 165, 20), (183, 206, 25), (206, 229, 48), (216, 235, 89), (225, 240, 130), (235, 245, 172), (46, 64, 28), (69, 96, 42), (92, 129, 56), (115, 161, 70), (138, 184, 93), (161, 198, 125), (185, 212, 158), (208, 226, 190), (45, 82, 10), (68, 124, 15), (91, 165, 20), (114, 206, 25), (138, 229, 48), (161, 235, 89), (184, 240, 130), (208, 245, 172), (32, 64, 28), (48, 96, 42), (64, 129, 56), (81, 161, 70), (104, 184, 93), (134, 198, 125), (164, 212, 158), (194, 226, 190), (18, 82, 10), (27, 124, 15), (37, 165, 20), (46, 206, 25), (69, 229, 48), (106, 235, 89), (143, 240, 130), (180, 245, 172), (28, 64, 37), (42, 96, 56), (56, 129, 75), (70, 161, 93), (93, 184, 117), (125, 198, 144), (158, 212, 172), (190, 226, 199), (10, 82, 28), (15, 124, 43), (20, 165, 57), (25, 206, 72), (48, 229, 95), (89, 235, 127), (130, 240, 159), (172, 245, 191), (28, 64, 51), (42, 96, 76), (56, 129, 102), (70, 161, 128), (93, 184, 151), (125, 198, 172), (158, 212, 192), (190, 226, 213), (10, 82, 56), (15, 124, 84), (20, 165, 112), (25, 206, 140), (48, 229, 163), (89, 235, 181), (130, 240, 200), (172, 245, 218), (28, 64, 64), (42, 96, 96), (56, 128, 129), (70, 160, 161), (93, 183, 184), (125, 197, 198), (158, 212, 212), (190, 226, 226), (10, 81, 82), (15, 122, 124), (20, 163, 165), (25, 204, 206), (48, 227, 229), (89, 233, 235), (130, 238, 240), (172, 244, 245), (28, 50, 64), (42, 75, 96), (56, 100, 129), (70, 126, 161), (93, 149, 184), (125, 170, 198), (158, 191, 212), (190, 212, 226), (10, 54, 82), (15, 81, 124), (20, 108, 165), (25, 136, 206), (48, 159, 229), (89, 178, 235), (130, 197, 240), (172, 216, 245), (28, 36, 64), (42, 55, 96), (56, 73, 129), (70, 91, 161), (93, 115, 184), (125, 143, 198), (158, 171, 212), (190, 199, 226), (10, 27, 82), (15, 40, 124), (20, 54, 165), (25, 67, 206), (48, 90, 229), (89, 123, 235), (130, 156, 240), (172, 189, 245), (33, 28, 64), (49, 42, 96), (66, 56, 129), (83, 70, 161), (106, 93, 184), (136, 125, 198), (165, 158, 212), (195, 190, 226), (20, 10, 82), (30, 15, 124), (40, 20, 165), (50, 25, 206), (73, 48, 229), (110, 89, 235), (146, 130, 240), (182, 172, 245), (47, 28, 64), (70, 42, 96), (94, 56, 129), (117, 70, 161), (140, 93, 184), (163, 125, 198), (186, 158, 212), (209, 190, 226), (47, 10, 82), (71, 15, 124), (95, 20, 165), (119, 25, 206), (142, 48, 229), (164, 89, 235), (187, 130, 240), (209, 172, 245), (60, 28, 64), (91, 42, 96), (121, 56, 129), (151, 70, 161), (174, 93, 184), (190, 125, 198), (206, 158, 212), (222, 190, 226), (75, 10, 82), (112, 15, 124), (150, 20, 165), (187, 25, 206), (210, 48, 229), (219, 89, 235), (228, 130, 240), (237, 172, 245), (64, 28, 54), (96, 42, 82), (129, 56, 109), (161, 70, 136), (184, 93, 159), (198, 125, 178), (212, 158, 197), (226, 190, 216), (82, 10, 63), (124, 15, 94), (165, 20, 126), (206, 25, 157), (229, 48, 180), (235, 89, 195), (240, 130, 210), (245, 172, 225)]

    get_palette = staticmethod(get_palette)

    def compute_palette():
        HLS_map = [0] * 256 

        # build the first 16 shades, these are the default
        # for d in range(0,8):
        #   HLS_map[d] = (0,0,0)

        for shad in range(0,16):
            red_on = 1 # defines the shade
            grn_on = 1 # for the default
            blu_on = 1 # dmd coloring
            dot = shad

            scaled_shade = int((shad/15.0) * 255)

            color = (red_on * scaled_shade,grn_on*scaled_shade,blu_on*scaled_shade)
            HLS_map[dot] = color

        #HLS_map[8] = (1,1,1)

        # fill the remainder of the first 128 with 0's
        # this is because the left-most bit (128's) 
        # indicates 1='color' or 0='non-color'
        idx = 16
        for deg in range(0,15):
            for sat in range(1,3):
                for lum in range (0,8):
                    hue = deg * 16
                    (r,g,b) = colorsys.hls_to_rgb(hue/255.0, (lum+2)/11.0,sat*100/255.0)
                    color = (int(r*255),int(g*255),int(b*255))
                    HLS_map[idx] = color
                    idx = idx + 1

        return HLS_map
    compute_palette = staticmethod(compute_palette)

    def compute_palette_ch():
        HLS_map = [0] * 256 

        # build the first 16 shades, these are the default
        # for d in range(0,8):
        #   HLS_map[d] = (0,0,0)

        for shad in range(0,16):
            red_on = 1 # defines the shade
            grn_on = 1 # for the default
            blu_on = 1 # dmd coloring
            dot = shad

            scaled_shade = int((shad/15.0) * 255)

            color = (chr(red_on * scaled_shade),chr(grn_on*scaled_shade),chr(blu_on*scaled_shade))
            HLS_map[dot] = color

        #HLS_map[8] = (1,1,1)

        # fill the remainder of the first 128 with 0's
        # this is because the left-most bit (128's) 
        # indicates 1='color' or 0='non-color'
        idx = 16
        for deg in range(0,15):
            for sat in range(1,3):
                for lum in range (0,8):
                    hue = deg * 16
                    (r,g,b) = colorsys.hls_to_rgb(hue/255.0, (lum+2)/11.0,sat*100/255.0)
                    color = (chr(int(r*255)),chr(int(g*255)),chr(int(b*255)))
                    HLS_map[idx] = color
                    idx = idx + 1

        return HLS_map
    compute_palette_ch = staticmethod(compute_palette_ch)


    def buildMapClassic():
        HLS_map = [0] * 256 

        # build the first 16 shades, these are the default
        # "non-colored" shades (e.g., the defaults).  I make
        # them orange, because I like an orange DMD.
        for shad in range(0,16):
            red_on = 1 # defines the shade
            grn_on = 1 # for the default
            blu_on = 1 # dmd coloring
            #blu_on = 0 # dmd coloring
            dot = shad

            scaled_shade = int((shad/15.0) * 255)

            #color = (red_on * scaled_shade,grn_on*int(scaled_shade/2),blu_on*scaled_shade)
            color = (red_on * scaled_shade,grn_on*int(scaled_shade),blu_on*scaled_shade)
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
    buildMapClassic = staticmethod(buildMapClassic)

def main():
    print(VgaDMD.compute_palette_ch())

if __name__ == '__main__':
    main()