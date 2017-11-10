import os
import struct
import yaml
import sqlite3
import bz2
import StringIO
import time
from PIL import Image
from procgame.dmd import Frame
from procgame.dmd import VgaDMD
from procgame import config
import logging
import re
import colorsys
import pygame
import zipfile

try:
    import cv2
    from pkg_resources import parse_version
    OPCV3 = parse_version(cv2.__version__) >= parse_version('3')
except Exception, e:
    logging.error("OpenCV is not available on your system.  The Movie (mp4) support is unavailable")

# returns OpenCV VideoCapture property id given, e.g., "FPS"
def capPropId(prop):
  return getattr(cv2 if OPCV3 else cv2.cv,
    ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)

def getColorProp():
  return cv2.cv.CV_BGR2RGB if not OPCV3 else cv2.COLOR_BGR2RGB

class Movie(object):
    """An ordered collection of :class:`~procgame.dmd.Frame` objects."""
    
    width = None
    """Width of each of the animation frames in dots."""
    height = None
    """Height of each of the animation frames in dots."""
    frames = None
    """Ordered collection of :class:`~procgame.dmd.Frame` objects."""
    vc=None
    
    
    
    def __init__(self, filename):
        """Initializes the animation."""
        super(Movie, self).__init__()

        if(cv2 is None):
            raise ValueError, "MP4 is unavailable as OpenCV is not installed"
        
        self.vc = cv2.VideoCapture(filename)
        self.width = int(self.vc.get(capPropId("FRAME_WIDTH")))
        self.height = int(self.vc.get(capPropId("FRAME_HEIGHT")))
        self.frame_count  = int(self.vc.get(capPropId("FRAME_COUNT")))
        if self.width==0 or self.height==0:
            raise ValueError, "Movie failed to load filename: '%s'" % filename

        #print 'ARE WE SET TO RGB?'
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)
        #self.vc.set(cv.CV_CAP_PROP_CONVERT_RGB, True)
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)

    def __del__(self):
        if self.vc != None:
            self.vc.release()
        

