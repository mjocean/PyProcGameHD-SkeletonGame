from procgame.dmd import Frame, font_named

class MarkupFrameGenerator:
    """Renders a :class:`~procgame.dmd.Frame` for given text-based markup.
        This is updated from the standard PyProcGame version in several ways.

        The markup format presently uses three markup tokens: 
        ``#`` (for headlines) and ``[`` and ``]`` for plain text.  The markup tokens
        indicate justification.  Lines with no markup or a leading ``#`` or ``[``
        will be left-justified.  Lines with a trailing ``#`` or ``]`` will be right-
        justified.  Lines with both will be centered.

        lines that begin and end with a curly-brace ``{`` and ``}`` are expected to refer
        to a known animation asset in the ``asset_list.yaml``;  this line will be replaced
        with the contents of the first frame of that animation.

        The width and min_height are specified with instantiation.
           
        Font and FontStyle for the Bold and Plain fonts can be set using the 
        :meth:`set_font_plain()` and :meth:`set_font_bold` methods.
        """
    
    font_plain = None
    """Font used for plain, non-bold characters."""
    font_bold = None
    """Font used for bold characters."""

    font_plain_style = None
    font_bold_style = None
    game = None

    def __init__(self, game, font_plain, font_bold, width=128, min_height=32):
        self.width = width
        self.min_height = min_height
        self.frame = None
        self.game = game
        self.font_plain = font_plain
        self.font_bold = font_bold

    def set_plain_font(self, font, interior_color=None, border_width=None, border_color=None):
        self.font_plain = font
        if(interior_color is not None and border_width is not None and border_color is not None):
            if(self.font_plain_style is None):
                self.font_plain_style = {}
            self.font_plain_style['interior_color'] = interior_color
            self.font_plain_style['border_color'] = border_color
            self.font_plain_style['border_width'] = border_width
        else:
            self.font_plain_style = None

    def set_bold_font(self,font, interior_color = None, border_width = None, border_color = None):
        self.font_bold = font
        if(interior_color is not None and border_width is not None and border_color is not None):
            if(self.font_bold_style is None):
                self.font_bold_style = {}
            self.font_bold_style['interior_color'] = interior_color
            self.font_bold_style['border_color'] = border_color
            self.font_bold_style['border_width'] = border_width
        else:
            self.font_bold_style = None

    def frame_for_markup(self, markup, y_offset=0):
        """Returns a Frame with the given markup rendered within it.
        The frame width is fixed, but the height will be adjusted
        to fit the contents while respecting min_height.
        
        The Y offset can be configured supplying *y_offset*.
        """
        lines = markup.split('\n')
        for draw in [False, True]:
            y = y_offset
            for line in lines:
                if line.startswith("{") and line.endswith('}'): # frame!!
                    y = self.__draw_frame(y=y, anim=line[1:-1], draw=draw)
                elif line.startswith('#') and line.endswith('#'): # centered headline!
                    y = self.__draw_text(y=y, text=line[1:-1], font=self.font_bold, justify='center', draw=draw)
                elif line.startswith('#'): # left-justified headline
                    y = self.__draw_text(y=y, text=line[1:], font=self.font_bold, justify='left', draw=draw)
                elif line.endswith('#'): # right-justified headline
                    y = self.__draw_text(y=y, text=line[:-1], font=self.font_bold, justify='right', draw=draw)
                elif line.startswith('[') and line.endswith(']'): # centered text
                    y = self.__draw_text(y=y, text=line[1:-1], font=self.font_plain, justify='center', draw=draw)
                elif line.endswith(']'): # right-justified text
                    y = self.__draw_text(y=y, text=line[:-1], font=self.font_plain, justify='right', draw=draw)
                elif line.startswith('['): # left-justified text
                    y = self.__draw_text(y=y, text=line[1:], font=self.font_plain, justify='left', draw=draw)
                else: # left-justified but nothing to clip off
                    y = self.__draw_text(y=y, text=line, font=self.font_plain, justify='left', draw=draw)
            if not draw: # this was a test run to get the height
                self.frame = Frame(width=self.width, height=max(self.min_height, y))
        return self.frame

    def __draw_text(self, y, text, font, justify, draw):
        if max(font.char_widths) * len(text) > self.width:
            # Need to do word-wrapping!
            line = ''
            w = 0
            for ch in text:
                line += ch
                w += font.size(ch)[0]
                if w > self.width:
                    # Too much! We need to back-track for the last space, if possible..
                    idx = line.rfind(' ')
                    if idx == -1:
                        # No space; we'll have to break before this char and continue.
                        y = self.__draw_line(y=y, text=line[:-1], font=font, justify=justify, draw=draw)
                        line = ch
                    else:
                        # We have found a space!
                        y = self.__draw_line(y=y, text=line[:idx], font=font, justify=justify, draw=draw)
                        line = line[idx+1:]
                    # Recalculate w.
                    w = font.size(line)[0]
            if len(line) > 0: # leftover text we need to draw
                y = self.__draw_line(y=y, text=line, font=font, justify=justify, draw=draw)
            return y
        else:
            return self.__draw_line(y=y, text=text, font=font, justify=justify, draw=draw)
    def __draw_line(self, y, text, font, justify, draw):
        """Draw a line without concern for word-wrapping."""
        if draw:
            x = 0 # TODO: x should be set based on 'justify'.
            if justify != 'left':
                w = font.size(text)[0]
                if justify == 'center':
                    x = (self.frame.width - w)/2
                else:
                    x = (self.frame.width - w)
            if(font is self.font_plain and self.font_plain_style is not None):
                col = self.font_plain_style['interior_color']
                bordercol = self.font_plain_style['border_color']
                borderwidth = self.font_plain_style['border_width']

                font.drawHD(self.frame, text, x, y, bordercol, borderwidth, col, None)

            elif(font is self.font_bold and self.font_bold_style is not None):
                col = self.font_bold_style['interior_color']
                bordercol = self.font_bold_style['border_color']
                borderwidth = self.font_bold_style['border_width']

                font.drawHD(self.frame, text, x, y, bordercol, borderwidth, col, None)
            else:
                font.draw(frame=self.frame, text=text, x=x, y=y)
        try:
            y += font.font_height
        except Exception, e:
            #print("*******UH OH... failover*******")
            y += font.char_size
        return y

    def __draw_frame(self, y, anim, draw):
        if(self.game is None):
            return y
        if(anim not in self.game.animations):
            return y

        src = self.game.animations[anim].frames[0]
        if draw:
            Frame.copy_rect(dst=self.frame, dst_x=0, dst_y=y, src=src, src_x=0, src_y=0, width=self.frame.width, height=src.height)
        y+=src.height
        return y
