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
from pygame import movie
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
        #print 'ARE WE SET TO RGB?'
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)
        #self.vc.set(cv.CV_CAP_PROP_CONVERT_RGB, True)
        #print self.vc.get(cv.CV_CAP_PROP_CONVERT_RGB)

        return self



    def populate_from_mp4_file(self,file):
        vc = cv2.VideoCapture(file)
        self.width = int(vc.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.height = int(vc.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        frame_count  = int(vc.get(cv.CV_CAP_PROP_FRAME_COUNT))
        #vc.set(cv.CV_CAP_PROP_CONVERT_RGB, True)
        
        #print "width:" + str(self.width) + "   Height: " + str(self.height) + "frame count: " + str(frame_count)

        for i in range(frame_count):
            rval, video_frame = vc.read()
            the_frame = cv.fromarray(video_frame)
            surface = pygame.image.frombuffer(the_frame.tostring(), (self.width, self.height), 'RGB')
            new_frame = Frame(self.width, self.height)
            new_frame.set_surface(surface)
            self.frames.append(new_frame)

        vc.release()
