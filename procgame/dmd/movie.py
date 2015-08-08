import os
import struct
import yaml
import sqlite3
import bz2
import StringIO
import time
import Image
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
    import cv2.cv as cv
except Exception, e:
    logging.error("OpenCV is not available on your system.  The Movie (mp4) support is unavailable")

class Movie(object):
    """An ordered collection of :class:`~procgame.dmd.Frame` objects."""
    
    width = None
    """Width of each of the animation frames in dots."""
    height = None
    """Height of each of the animation frames in dots."""
    frames = None
    """Ordered collection of :class:`~procgame.dmd.Frame` objects."""
    vc=None
    
    
    
    def __init__(self):
        """Initializes the animation."""
        super(Movie, self).__init__()
        if(cv2 is None):
            raise ValueError, "MP4 is unavailable as OpenCV is not installed"
        
    def __del__(self):
        if self.vc != None:
            self.vc.release()

    def load(self, filename):
        """This is really jsut setting up the access to the file
        and then giving hte video capture object to the moive layer"""

        self.vc = cv2.VideoCapture(filename)
        self.width = int(self.vc.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        self.frame_count  = int(self.vc.get(cv.CV_CAP_PROP_FRAME_COUNT))
        if self.width==0 or self.height==0:
            raise ValueError, "Movie failed to load filename: '%s'" % filename
        #print 'ARE WE SET TO RGB?'
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)
        #self.vc.set(cv.CV_CAP_PROP_CONVERT_RGB, True)
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)

        return self

