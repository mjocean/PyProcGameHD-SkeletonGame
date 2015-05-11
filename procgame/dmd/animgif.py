import Image
import procgame.dmd
import colorsys
from dmd import Frame
from sdl2_displaymanager import *
# import pygame

class ImageSequence:
	"""Iterates over all images in a sequence (of PIL Images)."""
	# Source: http://www.pythonware.com/library/pil/handbook/introduction.htm
	def __init__(self, im):
		self.im = im
	def __getitem__(self, ix):
		try:
			if ix:
				self.im.seek(ix)
			return self.im
		except EOFError:
			raise IndexError # end of sequence

def gif_frames(src, composite_op=None):
	"""Returns an array of frames to be added to the animation."""
	frames = []
	
	# We have to do some special stuff for animated GIFs: check for the background index, and if we get it use the last frame's value.
	transparent_idx = -1
	background_idx = -1
	if 'transparency' in src.info:
		transparent_idx = src.info['transparency']
	if 'background' in src.info:
		background_idx = src.info['background']
	last_frame = None
	
	(w, h) = src.size
		
	for src_im in ImageSequence(src):

		image = src_im.convert("RGB")
		(w,h) = image.size

		frame = procgame.dmd.Frame(w, h)

		surf = sdl2_DisplayManager.inst().make_texture_from_imagebits(bits=image.tostring(), width=w, height=h, mode=image.mode, composite_op=composite_op)
		
		# for x in range(w):
		# 	for y in range(h):
		# 		idx = src_im.getpixel((x, y)) # Get the palette index for this pixel
		# 		if idx == background_idx:
		# 			# background index means use the prior frame's dot data
		# 			if last_frame:
		# 				color = last_frame.pySurface.get_at((x,y))
		# 	 			surface.set_at((x,y), (0,0,0))

		# 			else:
		# 				# No prior frame to refer to.
		# 	 			surface.set_at((x,y), (0,0,0))
		# 		elif idx == transparent_idx:
		#  			surface.set_at((x,y), (0,0,0))
		frame = Frame(w,h,surf)

		frames.append(frame)
		# last_frame = frame
		
	return frames
