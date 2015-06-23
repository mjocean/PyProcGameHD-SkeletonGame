import sys
import os
import procgame.dmd
import procgame.game
import time
import re
import string
import Image
import struct

import logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def image_from_dmd_file(path, composite_op = None):
    f = open(path, 'rb')
    f.seek(0, os.SEEK_END) # Go to the end of the file to get its length
    file_length = f.tell()
    ## MJO: Don't just skip the header!  Check it.
    
    f.seek(0) # Skip over the 4 byte DMD header.
    dmd_version = struct.unpack("I", f.read(4))[0]
    dmd_style = 0 # old
    if(dmd_version == 0x00646D64):
        # print("old dmd style")
        pass
    elif(dmd_version == 0x00DEFACE):
        # print("full color dmd style")
        dmd_style = 1

    frame_count = struct.unpack("I", f.read(4))[0]
    width = struct.unpack("I", f.read(4))[0]
    height = struct.unpack("I", f.read(4))[0]
    print("Processing DMD file: width=%d  height=%d  number of frames=%d" % (width,height,frame_count))
    print("  --VGA (new-style) DMD data?: %s" % (dmd_style==1))

    if(dmd_style==0):
        if file_length != 16 + width * height * frame_count:
            logging.getLogger('game.dmdcache').warning(f)
            logging.getLogger('game.dmdcache').warning("expected size = {%d} got {%d}", (16 + width * height * frame_count), (file_length))
            raise ValueError, "File size inconsistent with original DMD format header information.  Old or incompatible file format?"
    elif(dmd_style==1):
        if file_length != 16 + width * height * frame_count * 3:
            logging.getLogger('game.dmdcache').warning(f)
            raise ValueError, "File size inconsistent with true-color DMD format header information. Old or incompatible file format?"

    results = list()
    for frame_index in range(frame_count):
        if(dmd_style==0):
            str_frame = f.read(width * height)
            rgb_frame = make_24bit_from_8bit_dmd_string(str_frame)
            str_frame = rgb_frame
            print("len(rgb_frame)=%d" % len(rgb_frame))
        elif(dmd_style==1):
            # print("LOADING FRAME...")
            size = width * height * 3
            str_frame = f.read(size)

        im = Image.fromstring('RGB', (width, height), str_frame)
        
        results.append(im)
    return results

def make_24bit_from_8bit_dmd_string(str_data):
    eight_to_RGB_map = procgame.dmd.VgaDMD.get_palette_ch()
    x = 0
    y = 0
    d = ""
    for dot in str_data:
        # get the Byte from the frame data
        dot = ord(dot) 
        # convert it to the correct RGB pallette color
        (r,g,b) = eight_to_RGB_map[dot]
        d += r + g + b
    return d

def dmd_to_image(src_filename, dst_filename, dots_w=128, dots_h=32):

    g = procgame.game.BasicGame(None)
    g.dmd = procgame.dmd.DisplayController(g, width=dots_w, height=dots_h)

    images  = image_from_dmd_file(src_filename)

    # print("file has resolution (%d x %d)" % (anim.width, anim.height))
    
    if(len(images)>1):        
        dst_basename = os.path.splitext(dst_filename)[0]
        dst_ext = os.path.splitext(dst_filename)[-1]
        for index,frame in enumerate(images):
            dst_file = dst_basename + "_" + str("%03d" % index) + dst_ext
            print("writing %s" % dst_file)
            frame.save(dst_file)
            #pygame.image.save(frame.pySurface,dst_file)    
    else:
        images[0].save(dst_filename)
        #pygame.image.save(frame.pySurface,dst_filename)

def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """[options] <input.dmd> <outputimage> [width height]"""

def tool_run(options, args):
	if len(args) < 2:
		return False
	if len(args) == 4:
		w = args[2]
		h = args[3]
		dmd_to_image(src_filename=args[0], dst_filename=args[1], dots_w = w, dots_h =h)
	else:
		dmd_to_image(src_filename=args[0], dst_filename=args[1])
	return True
