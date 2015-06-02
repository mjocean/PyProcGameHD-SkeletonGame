import procgame.game
import pygame
from pygame.locals import *
from pygame.font import *
from procgame.game import AdvancedMode
from procgame.dmd import HDFontStyle, GroupedLayer, HDTextLayer


class BonusMode(AdvancedMode):
  """
  This mode idles until the ball_ending event, at which point it shows
  the bonus tally sequence.
  """

  def __init__(self, game):
    """ 
    The __init__ function is called automatically whenever an instance 
    of this object is created --e.g., whenever the code:
        something = new BonusMode() 
    is executed, this __init__ function is called
    """

    # a call to 'super' call's the parent object's __init__ method
    # in this case, it calls the procgame.game.Mode's init()
    super(BonusMode, self).__init__(game=game, priority=1, mode_type=AdvancedMode.Ball)

    pass

  """
  the mode_started method is called whenever this mode is added
  to the mode queue; this might happen multiple times per game,
  depending on how the Game itself adds/removes it
  """
  def mode_started(self):
    pass

  """
  the mode_started method is called whenever this mode is removed
  from the mode queue; this might happen multiple times per game,
  depending on how the Game itself adds/removes it
  """
  def mode_stopped(self): 
    pass

  """ 
  update_lamps is a very important method -- you use it to set the lamps
  to reflect the current state of the internal mode progress variables.
  This function is called after a lampshow is played so that the state
  variables are correct after the lampshow is done.  It's also used other
  times
  """
  def update_lamps(self):
    pass

  def getBonusFrame(self, bonusName, bonusCount):
    lyrTop = HDTextLayer(self.game.dmd.width/2, self.game.dmd.height*1/3, self.game.fonts['med'], justify="center", vert_justify=None, opaque=False, width=self.game.dmd.width, height=40, line_color=None, line_width=0, interior_color=(255, 255, 255), fill_color=None)
    lyrBottom = HDTextLayer(self.game.dmd.width/2, self.game.dmd.height*2/3, self.game.fonts['med'], justify="center", vert_justify=None, opaque=False, width=self.game.dmd.width, height=40, line_color=None, line_width=0, interior_color=(255, 255, 255), fill_color=None)
    fs = HDFontStyle()
    fs.line_color=(232,32,32)
    fs.line_width=1
    fs.interior_color=(32,32,32)    
    lyrTop.set_text(bonusName,style=fs)
    lyrBottom.set_text(str(bonusCount),style=fs)
    gl = GroupedLayer(self.game.dmd.width, self.game.dmd.height, layers=[lyrBottom, lyrTop])
    gl.opaque=True
    return gl

  def next_bonus_display(self):
    self.cancel_delayed(name='next_bonus_display')
    if(len(self.bonus_list)>0):
      this_bonus = self.bonus_list.pop()
      self.layer = self.getBonusFrame(this_bonus['name'], this_bonus['count'])
      self.delay(name='next_bonus_display', delay=2, handler=self.next_bonus_display)
    else:
      self.layer = None
      self.force_event_next()


  def evt_ball_ending(self, (shoot_again, last_ball)):
    self.game.log("Bonus Mode awakened!!")
    if(shoot_again==True):
      return 0

    self.game.sound.play('ball_drain')
    fs = HDFontStyle()
    fs.line_color=(232,32,32)
    fs.line_width=2
    self.bonus_list = self.game.current_player().getBonusList()

    self.game.displayText('End of Ball',opaque=True)
    self.delay(delay=2, handler=self.next_bonus_display)
    return 2 + 2*len(self.bonus_list)

  def evt_tilt_ball_ending(self):
    self.game.log("Bonus Mode awakened (TILT)!")

    self.game.sound.play('ball_drain')
    fs = HDFontStyle()
    fs.line_color=(232,32,32)
    fs.line_width=2

    self.game.displayText('End of Ball',opaque=True)
    return 2