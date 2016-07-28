import os
try:
    import sdl2.ext
except Exception, e:
    if (os.getenv("PYSDL2_DLL_PATH")  is None):
        from procgame import config
        p = config.value_for_key_path('PYSDL2_DLL_PATH', None)
        if(p is None):
            print("Tried to load SDL2 but failed.  Please set PYSDL2_DLL_PATH in your system environment variables or in your config.yaml")
            import sys
            sys.exit()
        else:
            os.environ["PYSDL2_DLL_PATH"] = p
            try:
                import sdl2.ext
            except Exception, e2:
                print("Tried to load SDL2 but failed. \nThe PYSDL2_DLL_PATH in your config.yaml ['%s'] does contain a valid SDL2 DLL (or SDL2 is not properly installed on your system)" % p)
                print(e2)
                import sys
                sys.exit()

from sdl2.ext.draw import prepare_color
from sdl2.ext.color import convert_to_color
import ctypes
import random 
from sdl2 import endian, hints
import time

from ctypes import byref, cast, POINTER, c_int, c_float, sizeof, c_uint32, c_double

# An SDL2 Display Helper ; Somewhat PyGame like 

# class DisplayObject(sdl2.ext.TextureSprite):

SDL2_DM = None

class FontManagerExtended(sdl2.ext.FontManager):
    """ this clas serves to add a few useful features to the default (py)SDL2 FontManager """

    def get_font_pointer(self, alias, size):
        """ returns the pointer to the TTF_Font object """
        if alias not in self.aliases:
            raise KeyError("Font %s not loaded" % font)
        elif size not in self.fonts[alias]:
            self._change_font_size(alias, size)
        return self.fonts[alias][size]

    def render_border(self, text, alias=None, size=None, width=None, color=None,
               bg_color=None, border_width=1, border_color=None, **kwargs):
        """ Renders text to a surface and returns a pair: (outline, interior)

        This method uses the font designated by the alias or the
        default_font.  A size can be passed even if the font was not
        loaded with this size.  A width can be given for line wrapping.
        If no bg_color or color are given, it will default to the
        FontManager's bg_color and color.
        """
        alias = alias or self.default_font
        size = size or self.size
        if bg_color is None:
            bg_color = self._bgcolor
        elif not isinstance(bg_color, sdl2.pixels.SDL_Color):
            c = sdl2.ext.convert_to_color(bg_color)
            bg_color = sdl2.pixels.SDL_Color(c.r, c.g, c.b, c.a)

        if(border_color is None):
            raise ValueError, "Border color should not be None when calling render_border"
        c = sdl2.ext.convert_to_color(border_color)
        border_color = sdl2.pixels.SDL_Color(c.r, c.g, c.b, c.a)

        if color is None:
            color = self._textcolor
        elif not isinstance(color, sdl2.pixels.SDL_Color):
            c = sdl2.ext.convert_to_color(color)
            color = sdl2.pixels.SDL_Color(c.r, c.g, c.b, c.a)

        font = self.get_font_pointer(alias, size)

        if(font is None):
            raise KeyError("Font %s not loaded" % font)
        text = sdl2.ext.compat.byteify(text, "utf-8")

        # render the outline
        sdl2.sdlttf.TTF_SetFontOutline(font, border_width)           
        # if width:
        #     sf = sdl2.sdlttf.TTF_RenderUTF8_Blended_Wrapped(font, text, border_color,
        #                                                    width)
        # elif bg_color == sdl2.pixels.SDL_Color(0, 0, 0):
        sf = sdl2.sdlttf.TTF_RenderUTF8_Blended(font, text, border_color)
        # else:
        #     sf = sdl2.sdlttf.TTF_RenderUTF8_Shaded(font, text, border_color, bg_color)
        if not sf:
            raise sdl2.ext.SDLError(sdl2.sdlttf.TTF_GetError())

        # now render the middle
        sdl2.sdlttf.TTF_SetFontOutline(font, 0)

        # if width:
        #     sf2 = sdl2.sdlttf.TTF_RenderUTF8_Blended_Wrapped(font, text, color,
        #                                                    width)
        # if bg_color == sdl2.pixels.SDL_Color(0, 0, 0):
        sf2 = sdl2.sdlttf.TTF_RenderUTF8_Blended(font, text, color)
        # sf2 = sdl2.sdlttf.TTF_RenderUTF8_Solid(font, text, color)
        # else:
        #     sf2 = sdl2.sdlttf.TTF_RenderUTF8_Shaded(font, text, color, sdl2.pixels.SDL_Color(0,0,0))
                                              # bg_color)
        if not sf2:
            raise sdl2.ext.SDLError(sdl2.sdlttf.TTF_GetError())

        return (sf.contents, sf2.contents)

    def __del__(self):
        """Close all opened fonts."""
        if(sdl2 is not None and sdl2.sdlttf is not None):
            self.close()

class sdl2_DisplayManager(object):
    def __init__(self, dots_w, dots_h, scale=1, title="PyProcGameHD", screen_position_x=0,screen_position_y=0, flags=None, blur="0"):
        self.dots_w = dots_w
        self.dots_h = dots_h
        self.scale = scale
        self.window_w = dots_w * scale
        self.window_h = dots_h * scale

        sdl2.ext.Window.DEFAULTPOS=(screen_position_x, screen_position_y)
        sdl2.ext.init()
        self.window = sdl2.ext.Window(title, size=(self.window_w, self.window_h), flags=flags)
        sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)


        # self.window2 = sdl2.ext.Window(title, size=(self.window_w/2, self.window_h/2))
        # self.window2.show()
        self.window.show()

        self.texture_renderer = sdl2.ext.Renderer(self.window)
        sdl2.hints.SDL_SetHint(sdl2.hints.SDL_HINT_RENDER_SCALE_QUALITY, blur)

        # setting scale might help if we want to use full-screen but not zoom,
        # unfortunately a bug in sdl2 prevents this at present
        # sc = c_float(0.8)
        # sc_y = c_float(0.8)
        # self.texture_renderer.scale = (sc, sc_y)

        self.fill = self.texture_renderer.fill
        self.clear = self.texture_renderer.clear

        self.factory = sdl2.ext.SpriteFactory(renderer=self.texture_renderer)  
        self.font_manager = None

    def show_window(self, show=True):
        if(show):
            self.window.show()
        else:
            self.window.hide()

    def fonts_init(self, default_font_path, default_font_alias, size=30, color=(0,0,128,255), bgcolor=(0,0,0)):
        from pygame.font import match_font
        font_path = default_font_path or  match_font(default_font_alias)
        if(self.font_manager is None):
            self.font_manager = FontManagerExtended(font_path = font_path, alias=default_font_alias, size = size)
        else:
            raise ValueError, "sdl2_DisplayManager: fonts_init already completed previously.  Don't do it again."

    def font_add(self, font_path, font_alias, size=None, color=None, bgcolor=None, bold=False):
        tmp = self.font_manager.add(font_path = font_path, alias=font_alias, size=size)
        # one day I will figure out why this does not work...
        # if(bold):
        #     sdl2.sdlttf.TTF_SetFontStyle(tmp, sdl2.sdlttf.TTF_STYLE_BOLD)
        # else:
        #     sdl2.sdlttf.TTF_SetFontStyle(tmp, sdl2.sdlttf.TTF_STYLE_NORMAL)            
        return tmp

    def font_render_text(self, msg, font_alias=None, size=None, width=None, color=None, bg_color=None):
        # color = (color[0], color[1], color[2], 255)
        tsurf = self.font_manager.render(msg, alias=font_alias, size=size, width=None, color=color, bg_color=bg_color)
        # print(tsurf.format.contents.BytesPerPixel)
        # csurf = sdl2.surface.SDL_ConvertSurface(tsurf, sdl2.pixels.SDL_PIXELFORMAT_RGBA8888, 0)
        ssurf = sdl2.ext.SoftwareSprite(tsurf, True)
        del tsurf

        textsurf = self.texture_from_surface(ssurf)
        # print(textsurf.texture.format.contents.BytesPerPixel)
        
        del ssurf
        return textsurf

    def font_get_size(self, text, font_alias, font_size):
        sdl_font = self.font_manager.get_font_pointer(font_alias, font_size)
        if(sdl_font is None):
            raise ValueError, "sdl2_DisplayManager: specified font not found."

        text = sdl2.ext.compat.byteify(text, "utf-8")
        w = c_int()
        h = c_int()
        ret = sdl2.sdlttf.TTF_SizeUTF8(sdl_font, text, byref(w), byref(h))
        if ret == -1:
            raise sdl2.ext.SDLError()
        #print "SIZE: %dx%d" % (w.value,h.value)
        return (w.value,h.value)

    def font_render_bordered_text_dual(self, msg, font_alias=None, size=None, width=None, color=None, bg_color=None, border_width=1, border_color=None):
        # returns center then outline
        (bsurf, isurf) = self.font_manager.render_border(msg, alias=font_alias, size=size, width=width, color=color, bg_color=bg_color, border_width=border_width, border_color=border_color)

        tx_surf = self.texture_from_surface(bsurf)  # outline
        tx_isurf = self.texture_from_surface(isurf) # interior

        del bsurf
        del isurf

        return (tx_surf, tx_isurf)

    def mask(self, txA, txB):
        width, height = txA.size
        # print("Making mask of size (%s, %s)" % (width,height))
        t =  self.new_texture(width, height)

        self.blit(txA, t, (0,0,width,height))

        ret = sdl2.SDL_SetTextureBlendMode(txB.texture, sdl2.SDL_BLENDMODE_MOD) # apply mod to 'source'
        if ret == -1:
            raise sdl2.ext.SDLError()

        # SDL_BLENDMODE_MOD a/k/a color modulate
        # dstRGB = srcRGB * dstRGB
        # dstA = dstA
        # alpha of destination is preserved
        # src should be white and black to remove pixels
        # destination RGB is src * dest

        self.blit(txB, t, (0,0,width,height)) # draw B on t

        sdl2.SDL_SetTextureBlendMode(txB.texture, sdl2.SDL_BLENDMODE_BLEND)

        return t

    def combine(self,txA, txB, txC):
        """ blits (txB mod txC) then adds txA
        """

        width, height = txA.size
        # t =  sdl2.render.SDL_CreateTexture(self.texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
        #                                                           sdl2.render.SDL_TEXTUREACCESS_TARGET,
        #                                                           width, height)
        t =  self.new_texture(width, height)

        self.blit(txB, t, (0,0,width,height)) # blits B into t

        ret = sdl2.SDL_SetTextureBlendMode(txC.texture, sdl2.SDL_BLENDMODE_MOD) # apply mod to 'source'
        if ret == -1:
            raise sdl2.ext.SDLError()

        self.blit(txC, t, (0,0,width,height)) # draw C on t

        # sdl2.SDL_SetTextureBlendMode(t.texture, sdl2.SDL_BLENDMODE_MOD)

        # sdl2.SDL_SetTextureBlendMode(t.texture, sdl2.SDL_BLENDMODE_BLEND)

        self.blit(txA, t, (0,0,width,height))

        # del txA
        # del txB

        return t

    def font_render_bordered_text(self, msg, font_alias=None, size=None, width=None, color=None, bg_color=None, border_width=1, border_color=None):
        # returns surfaces (outline, interior)
        (srf_outline, srf_interior) = self.font_manager.render_border(msg, alias=font_alias, size=size, width=width, color=color, bg_color=bg_color, border_width=border_width, border_color=border_color)

        # make target
        rtarget =  sdl2.render.SDL_CreateTexture(self.texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGB888,
                                                                  sdl2.render.SDL_TEXTUREACCESS_TARGET,
                                                                  srf_outline.w, srf_outline.h)
        sdl2.SDL_SetTextureBlendMode(rtarget, sdl2.SDL_BLENDMODE_BLEND)
        txtarget = sdl2.ext.TextureSprite(rtarget)
        self.texture_clear(txtarget, color=(0,0,0,0))

        tx_outline = self.texture_from_surface(srf_outline)  # make outline texture
        tx_interior = self.texture_from_surface(srf_interior) # make interior texture

        # blit the outline, then the interior
        # blit(source_tx, dest_tx, dest_loc)
        if(len(border_color)==4):
            ret = sdl2.SDL_SetTextureAlphaMod(tx_outline.texture, int(border_color[3]))            
            if ret == -1:
                raise sdl2.ext.SDLError()

        if(len(color)==4):
            ret = sdl2.SDL_SetTextureAlphaMod(tx_interior.texture, int(color[3]))            
            if ret == -1:
                raise sdl2.ext.SDLError()


        self.blit(tx_outline, txtarget, (0,0, srf_outline.w, srf_outline.h))
        self.blit(tx_interior, txtarget, (border_width,border_width, srf_interior.w, srf_interior.h))

        sdl2.surface.SDL_FreeSurface(srf_interior)
        sdl2.surface.SDL_FreeSurface(srf_outline)

        del srf_interior
        del srf_outline
        del tx_interior
        del tx_outline

        return txtarget


    # def font_render_bordered_text(self, msg, font_alias=None, size=None, width=None, color=None, bg_color=None, border_width=1, border_color=None):
    #     # returns center then outline
    #     (bsurf, isurf) = self.font_manager.render_border(msg, alias=font_alias, size=size, width=width, color=color, bg_color=bg_color, border_width=border_width, border_color=border_color)

    #     r = sdl2.rect.SDL_Rect(border_width, border_width, bsurf.w, bsurf.h)

    #     sdl2.surface.SDL_BlitSurface(isurf, None, bsurf, r)

    #     # ssurf = sdl2.ext.SoftwareSprite(tsurf, True)
    #     tx_surf = self.texture_from_surface(bsurf)  # outline

    #     # tx_isurf = self.texture_from_surface(isurf) # interior

    #     # self.blit(tx_surf, tx_isurf, (0,0,bsurf.w, bsurf.h))
    #     del bsurf
    #     del isurf

    #     #del tx_isurf

    #     # self.texture_renderer.copy(source_tx, srcrect=area, dstrect=dstrect)

    #     return tx_surf
    
    def Init(dots_w, dots_h, scale=1, title="ppgHD", x=0, y=0, flags=None, blur="0"):
        global SDL2_DM 
        SDL2_DM = sdl2_DisplayManager(dots_w, dots_h, scale, title, x, y, flags, blur)

    Init = staticmethod(Init)

    def inst():
        return SDL2_DM

    inst = staticmethod(inst)

    def flip(self):
        self.texture_renderer.present()

    def blit(self, source_tx, dest_tx, dest, area=None, special_flags = 0, blendmode=None, alpha=None):
        """ a blit function, backed by RenderCopy, that emulates PyGame 1.9.2 style blitting 
        def blit(source_tx, dest_tx, area=None, special_flags = 0) 

        Draws a source_tx Surface onto this Surface. 
        The draw can be positioned with the dest argument. 
        Dest can either be pair of coordinates representing the upper left corner or a rect with the topleft corner of the rectangle will be used as the position for the blit. 
        (The size of the destination rectangle does not effect the blit).
        An optional area rectangle can be passed as well. This represents a smaller portion of the source_tx Surface to draw.    
        """
        # 1) backup the renderer's destination 
        bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, dest_tx.texture)

        # 2) copmpute locations:
        ###(sw, sh) = source_tx.size
        # (dw, dh) = dest_tx.size
        # w_to_draw = min(sw, dw)
        # h_to_draw = min(sh, dh)
        # if(area is not None):
        #     w_to_draw = min(w_to_draw-area[0], area[2])
        #     h_to_draw = min(h_to_draw-area[1], area[3])            
        # dstrect = (dest[0], dest[1], w_to_draw, h_to_draw)
        dstrect = dest ###(dest[0], dest[1], sw, sh)

        if(blendmode is not None):
            if(blendmode == 'ADD'):
                ret = sdl2.SDL_SetTextureBlendMode(source_tx.texture, sdl2.SDL_BLENDMODE_ADD) 
            elif(blendmode == 'MOD'):
                ret = sdl2.SDL_SetTextureBlendMode(source_tx.texture, sdl2.SDL_BLENDMODE_MOD) 
            elif(blendmode == 'BLEND'):
                ret = sdl2.SDL_SetTextureBlendMode(source_tx.texture, sdl2.SDL_BLENDMODE_BLEND) 
            else:
                ret = sdl2.SDL_SetTextureBlendMode(source_tx.texture, sdl2.SDL_BLENDMODE_NONE) 
            if ret == -1:
                raise sdl2.ext.SDLError()

        if(alpha is not None):
            ret = sdl2.SDL_SetTextureAlphaMod(source_tx.texture, int(alpha))            
            if ret == -1:
                raise sdl2.ext.SDLError()
        #3) Draw!
        self.texture_renderer.copy(source_tx, srcrect=area, dstrect=dstrect)

        #4) Restore renderer's texture target
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back

    def roto_blit(self, source_tx, dest_tx, dest, area=None, angle=0, origin = None, flip=0):
        """ a blit function, backed by RenderCopy, that emulates PyGame 1.9.2 style blitting 
        def blit(source_tx, dest_tx, area=None, special_flags = 0) 

        Draws a source_tx Surface onto this Surface. 
        The draw can be positioned with the dest argument. 
        Dest can either be pair of coordinates representing the upper left corner or a rect with the topleft corner of the rectangle will be used as the position for the blit. 
        (The size of the destination rectangle does not effect the blit).
        An optional area rectangle can be passed as well. This represents a smaller portion of the source_tx Surface to draw.    
        """
        # 1) backup the renderer's destination 
        bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, dest_tx.texture)

        # 2) copmpute locations:
        ###(sw, sh) = source_tx.size
        # (dw, dh) = dest_tx.size
        # w_to_draw = min(sw, dw)
        # h_to_draw = min(sh, dh)
        # if(area is not None):
        #     w_to_draw = min(w_to_draw-area[0], area[2])
        #     h_to_draw = min(h_to_draw-area[1], area[3])            
        # dstrect = (dest[0], dest[1], w_to_draw, h_to_draw)
        dstrect = dest ###(dest[0], dest[1], sw, sh)

        #3) Draw!
        self._render_copy_ex(source_tx, srcrect=area, dstrect=dstrect, angle=angle, origin=origin, flip=flip)

        #4) Restore renderer's texture target
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back

    def _render_copy_ex(self, src, srcrect=None, dstrect=None, angle=0, origin=None, flip=0):
        """Copies (blits) the passed source to the target of the Renderer."""
        SDL_Rect = sdl2.rect.SDL_Rect
        
        rdr = self.texture_renderer.renderer

        if isinstance(src, sdl2.ext.TextureSprite):
            texture = src.texture
        elif isinstance(src, sdl2.render.SDL_Texture):
            texture = src
        else:
            raise TypeError("src must be a TextureSprite or SDL_Texture")
        if srcrect is not None:
            x, y, w, h = srcrect
            srcrect = SDL_Rect(x, y, w, h)
        if dstrect is not None:
            x, y, w, h = dstrect
            dstrect = SDL_Rect(x, y, int(w), int(h))

        if(flip==0):
            flip = sdl2.SDL_FLIP_NONE
        elif(flip==1):
            sdl2.SDL_FLIP_HORIZONTAL
        else:
            sdl2.SDL_FLIP_VERTICAL

        angle = c_double(angle)

        if(origin is not None):
            origin = sdl2.rect.SDL_Point(origin[0], origin[1])

        ret = sdl2.render.SDL_RenderCopyEx(rdr, texture, srcrect, dstrect, angle, origin, flip)

        if ret == -1:
            raise sdl2.ext.SDLError()

    def texture_clear(self, texture, color=None):
        """
        Fills a texture with the specified color or None (which does something specific in SDL2)
        texture may be a pySDL2 'TextureSprite' or a pointer to an SDL_Texture 
        """
        # 1) backup the renderer's destination 
        bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)

        if(isinstance(texture,sdl2.ext.TextureSprite)):
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, texture.texture)
        else:
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, texture)

        # 2) clear:
        self.texture_renderer.clear(color)

        #3) Restore renderer's texture target
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back


    def screen_blit(self, source_tx, area=None, x=0, y=0, expand_to_fill=False, flip = 0):
        """ write the source to the screen at it's original size, showing either a sub-area or the whole thing
        """
        bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, None)

        # 2) copmpute locations:
        if expand_to_fill is True:
            dstrect = None
        else:
            (sw, sh) = source_tx.size
            dstrect = (x, y, sw, sh)

        #3) Draw!
        # self.texture_renderer.copy(source_tx, srcrect=area, dstrect=dstrect)
        self._render_copy_ex(source_tx, srcrect=area, dstrect=dstrect, flip=flip)

        #3) Restore renderer's texture target
        sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back

    def copy_rect(self, src_tex, dst_tex=None, srcrect=None, dstrect=None):
        """ Copy a texture from the src texture to the dst texture
            if the dst_tex is None, the default texture of the rendererer (i.e., the window)
            used.  
        """
        if(dst_tex is not None):
            # backup the destination just in case it wasn't the window previously
            bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, dst_tex.texture)
        else:
            print("hdDisplayMgr: copy_rect to nowehere")
        self.texture_renderer.copy(src_tex, srcrect=srcrect, dstrect=dstrect)

        if(dst_tex is not None):
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back

    def switch_target(self, new_target):
        bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
        try:
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, new_target)
        except Exception, e:
            sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, new_target.texture)
        return bk

    def load_surface(self, fname):
        tsurface = sdl2.ext.image.load_image(fname)

        s = sdl2.ext.SoftwareSprite(tsurface, False)
        return s

    def load_texture(self, fname):
        tsurface = sdl2.ext.image.load_image(fname)

        texture = sdl2.render.SDL_CreateTextureFromSurface(self.texture_renderer.renderer,
                                                      tsurface)
        if not texture:
            raise sdl2.ext.SDLError()
        t = sdl2.ext.TextureSprite(texture.contents)

        sdl2.surface.SDL_FreeSurface(tsurface)

        return t



    def make_texture_from_imagebits(self, width, height, bits, mode="RGB", composite_op=None):
        """Creates a Sprite from a Python imaging Image's bits."""
        rmask = gmask = bmask = amask = 0
        
        if mode == "RGB":
            # 3x8-bit, 24bpp
            if endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN:
                rmask = 0x0000FF
                gmask = 0x00FF00
                bmask = 0xFF0000
            else:
                rmask = 0xFF0000
                gmask = 0x00FF00
                bmask = 0x0000FF
            depth = 24
            pitch = width * 3
        elif mode in ("RGBA", "RGBX"):
            # RGBX: 4x8-bit, no alpha
            # RGBA: 4x8-bit, alpha
            if endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN:
                rmask = 0x000000FF
                gmask = 0x0000FF00
                bmask = 0x00FF0000
                if mode == "RGBA":
                    amask = 0xFF000000
            else:
                rmask = 0xFF000000
                gmask = 0x00FF0000
                bmask = 0x0000FF00
                if mode == "RGBA":
                    amask = 0x000000FF
            depth = 32
            pitch = width * 4
        else:
            raise ValueError, "Format not supported"

        imgsurface = sdl2.surface.SDL_CreateRGBSurfaceFrom(bits, width, height,
                                                      depth, pitch, rmask,
                                                      gmask, bmask, amask)
        if not imgsurface:
            raise sdl2.ext.SDLError()

        if(composite_op is not None and composite_op!="None"):
            if(composite_op == "blacksrc"):
                trans_color = (0,0,0)
            elif(composite_op == "greensrc"):
                trans_color = (0,255,0)
            elif(composite_op == "magentasrc"):
                trans_color = (255,0,255)
            else:
                raise ValueError, "Composite_op '%s' not recognized/supported." % composite_op

            #trans_color = prepare_color(trans_color, imgsurface)
            trans_color = convert_to_color(trans_color)
            sf = imgsurface.contents
            fmt = sf.format.contents

            if(mode=="RGBA"):
                trans_color = sdl2.pixels.SDL_MapRGBA(fmt, trans_color.r, trans_color.g, trans_color.b, trans_color.a)
            else:
                trans_color = sdl2.pixels.SDL_MapRGB(fmt, trans_color.r, trans_color.g, trans_color.b)

            ret = sdl2.surface.SDL_SetColorKey( imgsurface, sdl2.SDL_TRUE, trans_color );
            if ret == -1:
                raise sdl2.ext.SDLError()

        imgsurface = imgsurface.contents
        # the pixel buffer must not be freed for the lifetime of the surface
        imgsurface._pxbuf = bits

        tx = self.texture_from_surface(imgsurface)

        del imgsurface
        return tx

    def make_bits_from_texture(self, frame, width, height):
        # 1) backup the renderer's destination 
        # bk = sdl2.SDL_GetRenderTarget(self.texture_renderer.renderer)
        
        # sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, frame.texture)
        # self.texture_renderer.copy(frame.texture, srcrect=(0,0,width,height), dstrect=None)
        # sdl2.render.SDL_RenderPresent(self.texture_renderer.renderer)

        rmask = gmask = bmask = amask = 0

        mode = "RGBA"
        pixel_format = None
        if mode == "RGB":
            # 3x8-bit, 24bpp
            if endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN:
                rmask = 0x0000FF
                gmask = 0x00FF00
                bmask = 0xFF0000
                pixel_format = sdl2.pixels.SDL_PIXELFORMAT_BGR888
            else:
                rmask = 0xFF0000
                gmask = 0x00FF00
                bmask = 0x0000FF
                pixel_format = sdl2.pixels.SDL_PIXELFORMAT_RGB888
            depth = 24
            pitch = width * 3
        elif mode in ("RGBA", "RGBX"):
            # RGBX: 4x8-bit, no alpha
            # RGBA: 4x8-bit, alpha
            if endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN:
                rmask = 0x000000FF
                gmask = 0x0000FF00
                bmask = 0x00FF0000
                if mode == "RGBA":
                    amask = 0xFF000000
                    pixel_format = sdl2.pixels.SDL_PIXELFORMAT_ABGR8888
                else:
                    pixel_format = sdl2.pixels.SDL_PIXELFORMAT_BGRX8888                    
            else:
                rmask = 0xFF000000
                gmask = 0x00FF0000
                bmask = 0x0000FF00
                if mode == "RGBA":
                    amask = 0x000000FF
                    pixel_format = sdl2.pixels.SDL_PIXELFORMAT_RGBA8888
                else:
                    pixel_format = sdl2.pixels.SDL_PIXELFORMAT_RGBX8888                    
            depth = 32
            pitch = width * 4
        else:
            raise ValueError, "Format not supported"

        # ?!?
        # tsurf = self.new_texture(128,32,(255,0,255,128))
        # ssurf = sdl2.ext.SoftwareSprite(tsurf.te, True)
        # del tsurf

        # imgsurface = sdl2.surface.SDL_CreateRGBSurface(0, width, height,
        #                                               depth, rmask,
        #                                               gmask, bmask, amask)
        # if not imgsurface:
        #     raise sdl2.ext.SDLError()

        # bits = (ctypes.c_uint8)*128*32*4
        # for x in range(0, 128*32*4):
        #     bits[x] = 128
        # imgsurface = sdl2.surface.SDL_CreateRGBSurfaceFrom(bits, width, height,
        #                                               depth, pitch, rmask,
        #                                               gmask, bmask, amask)


        #??
        # bucket = (ctypes.c_uint8*(128*32*4))()
        # not better

        ## ALLOC MEMBER
        bucket = ctypes.create_string_buffer(height*pitch*chr(128))
        pxbuf = ctypes.cast(bucket, ctypes.POINTER(ctypes.c_uint8))

        # pxbuf = byref(bucket)
        # pxbuf = ctypes.cast(bucket, ctypes.POINTER(ctypes.c_uint8*128*32*3))

        # pxbuf = ctypes.cast(bucket,
        #                 ctypes.POINTER(ctypes.c_ubyte * 128*32*3)) #.contents        

        # swtarget = sdl2.ext.SoftwareSprite(imgsurface.contents, True)
        # rtarget = swtarget.surface

        # pxbuf = ctypes.cast(imgsurface.contents.pixels, ctypes.POINTER(ctypes.c_uint8))

        # Bucket = ctypes.c_uint8*128*32*3
        # pxbuf = Bucket()


        # pxbuf = ctypes.cast(imgsurface.contents.pixels, ctypes.POINTER(ctypes.c_uint8))
        # pxbuf = ctypes.cast(imgsurface.contents.pixels, ctypes.POINTER(ctypes.c_uint32))


        # pxbuf = ctypes.cast(imgsurface.contents.pixels, ctypes.POINTER(ctypes.c_uint32))
        # pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint32))
        # pxbuf = ctypes.cast(bucket, ctypes.POINTER(ctypes.c_uint8))

        clip_r = sdl2.rect.SDL_Rect(0,0,width,height)

        # print("---------------------%d----------------" % pitch)

        ret = sdl2.render.SDL_RenderReadPixels(
            self.texture_renderer.renderer, 
            clip_r, pixel_format, 
            pxbuf, ctypes.c_int(pitch))
            # imgsurface.contents.pixels, ctypes.c_int(pitch))

        # [POINTER(SDL_Renderer), POINTER(SDL_Rect), Uint32, c_void_p, c_int], c_int)

        # ctypes.c_int(pitch)

        # if ret != 0:
        #    print "ERROR: %s " % ret
        #    raise sdl2.ext.SDLError()

        # i = 0
        # while(i < width*height*3):
        #     print("pixel %i: %s, %s, %s" % (i, bucket[i], bucket[i+1], bucket[i+2]))
        #     i+=3

        #4) Restore renderer's texture target
        # sdl2.SDL_SetRenderTarget(self.texture_renderer.renderer, bk) # revert back

        # go into a software sprite
        # swtarget = sdl2.ext.SoftwareSprite(imgsurface.contents, True)
        # tx = self.texture_from_surface(swtarget)

        # tx = sdl2_DisplayManager.inst().make_texture_from_imagebits(width,height, pxbuf, mode=mode, composite_op=None)
        # tx = sdl2_DisplayManager.inst().make_texture_from_imagebits(width,height, imgsurface.contents.pixels, mode=mode, composite_op=None)

        # sdl2_DisplayManager.inst().clear((0,0,0,255))
        # sdl2_DisplayManager.inst().screen_blit(source_tx=tx, expand_to_fill=True)
        # sdl2_DisplayManager.inst().flip()

        # del tx
        # del pxbuf

        return pxbuf


    def draw_rect(self, color, rect, filled=False):
        if(not filled):
            self.texture_renderer.draw_rect(rects=list(rect), color=color)
        else:
            self.texture_renderer.fill(rects=list(rect), color=color)

    def make_texture_from_image_tedious(self, img):
        """Creates a Sprite from a Python imaging Image."""
        width, height = img.size

        if width < 1:
            raise ValueError("width must be greater than 0")

        # rtarget =  sdl2.render.SDL_CreateTexture(self.texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGB888,
        #                                                           sdl2.render.SDL_TEXTUREACCESS_TARGET,
        #                                                           width, height)
        # sdl2.SDL_SetTextureBlendMode(rtarget, sdl2.SDL_BLENDMODE_BLEND)

        # txtarget = sdl2.ext.TextureSprite(rtarget)

        rmask = gmask = bmask = amask = 0
        imgsurface = sdl2.surface.SDL_CreateRGBSurface(0, width, height, 32,
                                                  rmask, gmask, bmask, amask)
        if not imgsurface:
            raise sdl2.ext.SDLError()
        swtarget = sdl2.ext.SoftwareSprite(imgsurface.contents, True)
        rtarget = swtarget.surface

        pitch = rtarget.pitch
        bpp = rtarget.format.contents.BytesPerPixel
        frac = pitch / bpp
        clip_rect = rtarget.clip_rect
        left, right = clip_rect.x, clip_rect.x + clip_rect.w - 1
        top, bottom = clip_rect.y, clip_rect.y + clip_rect.h - 1

        print((width, height))
        print(pitch)
        print(bpp)
        print(frac)
        print(clip_rect)
        # if bpp == 3:
        #     raise UnsupportedError(line, "24bpp are currently not supported")
        # if bpp == 2:
        #     pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint16))
        # elif bpp == 4:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint32))
        # else:
        #     pxbuf = rtarget.pixels  # byte-wise access.

        #pxbuf = bytes
        # for y in range(0, height):
        #     for x in range(0,width):
        #         pxbuff[int()]

        # casting -- no.
        # b = (ctypes.c_uint32 * int(width * height / int(4)) )(bytes)

        # for i,b in enumerate(bytes):
        #     pxbuf[int(i)] = (b)
        for i,col in enumerate(img.getdata()): #range(0,pitch):
            # col = mpx
            # # col = (ord(bytes[i]),ord(bytes[i+1]),ord(bytes[i+2]),ord(bytes[i+3]))
            #col = (random.randint(0,255),0,0, 128)
            # pxbuf[int(i)] = prepare_color( col , swtarget)
            pxbuf[int(i)] = prepare_color( col , swtarget)
            print("[%05d] copy data %s" % (i,col))

        # Uint32 * pixels = new Uint32[640 * 480];
        ###sdl2.SDL_UpdateTexture(rtarget, None, pxbuf, width * sizeof(ctypes.c_uint32));

        # sw_sprite = self.load_surface("assets/dmd/smile.png")
        # tx = self.texture_from_surface(sw_sprite)
        
        tx = self.texture_from_surface(swtarget)
        #self.copy_rect(tx)
        del swtarget
        return tx

    def make_texture_from_bits(self, bits, width, height):
        if width < 1:
            raise ValueError("width must be greater than 0")

        rmask = gmask = bmask = amask = 0
        imgsurface = sdl2.surface.SDL_CreateRGBSurface(0, width, height, 32,
                                                  rmask, gmask, bmask, amask)
        if not imgsurface:
            raise sdl2.ext.SDLError()
        swtarget = sdl2.ext.SoftwareSprite(imgsurface.contents, True)
        rtarget = swtarget.surface

        sdl2.surface.SDL_FreeSurface(imgsurface)


        pitch = rtarget.pitch
        bpp = rtarget.format.contents.BytesPerPixel
        frac = pitch / bpp
        clip_rect = rtarget.clip_rect
        left, right = clip_rect.x, clip_rect.x + clip_rect.w - 1
        top, bottom = clip_rect.y, clip_rect.y + clip_rect.h - 1

        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint32))

        for idx in range(0,width*height):
            b_data = bits[idx:idx+3]
            # print("data: [%s]" % b_data)
            b_num = [ord(b) for b in b_data]
            col = (b_num[0],b_num[1],b_num[2],255)
            #col = (random.randint(0,255),0,0, 128)
            # pxbuf[int(i)] = prepare_color( col , swtarget)
            # if(col[0]!=0) or (col[1]!=0) or (col[2]!=0):
            #     print("[%05d] copy data %s" % (idx,col))
            pxbuf[int(idx)] = prepare_color( col , swtarget)


        # Uint32 * pixels = new Uint32[640 * 480];
        ###sdl2.SDL_UpdateTexture(rtarget, None, pxbuf, width * sizeof(ctypes.c_uint32));

        # sw_sprite = self.load_surface("assets/dmd/smile.png")
        # tx = self.texture_from_surface(sw_sprite)
        
        tx = self.texture_from_surface(swtarget)
        #self.copy_rect(tx)
        del swtarget
        return tx

    def make_texture_from_bits_fail(self, obj):
        """Creates a Sprite from an arbitrary object."""
        if True: #self.sprite_type == TEXTURE:
            rw = sdl2.rwops.rw_from_object(obj)
            # TODO: support arbitrary objects.
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise sdl2.ext.SDLError()
            s = self.from_surface(imgsurface.contents, True)
        else: #elif self.sprite_type == SOFTWARE:
            rw = sdl2.rwops.rw_from_object(obj)
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise sdl2.ext.SDLError()
            s = SoftwareSprite(imgsurface.contents, True)
        return s   



    def new_texture(self, width, height, color=(0,0,0,0)):
        # ts = self.factory.create_texture_sprite(renderer=self.texture_renderer, size=(width,height),
        #                       pformat=sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
        #                       access=sdl2.render.SDL_TEXTUREACCESS_STATIC )
        # print("New texture created: %s " % ts.texture)
        # return ts

        t =  sdl2.render.SDL_CreateTexture(self.texture_renderer.renderer, sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
                                                                  sdl2.render.SDL_TEXTUREACCESS_TARGET,
                                                                  width, height)
        sdl2.SDL_SetTextureBlendMode(t, sdl2.SDL_BLENDMODE_BLEND)

        self.texture_clear(t, color)
        #print("New texture created: %s " % t.contents)
        return sdl2.ext.TextureSprite(t.contents)


        # ss = self.factory.create_software_sprite(size=(width, height))
        # t = self.factory.from_surface(ss.surface,free=False)
        # #del ss
        # print("New texture created: %s " % t.texture)
        # return t #sdl2.ext.TextureSprite(t.contents)

    #dot_tex = factory.create_texture_sprite(texture_renderer, (dots_w*10,dots_h*10), pformat=sdl2.SDL_PIXELFORMAT_RGBA8888, access=sdl2.SDL_TEXTUREACCESS_TARGET) 
    #sdl2.SDL_SetTextureBlendMode(dot_tex.texture,sdl2.SDL_BLENDMODE_BLEND)


    def texture_from_surface(self, surface):
        """ generates a TextureSprite from either a SDL_Surface or SoftwareSprite """
        if(isinstance(surface,sdl2.ext.SoftwareSprite)):
            texture = sdl2.render.SDL_CreateTextureFromSurface(self.texture_renderer.renderer, surface.surface)
        else:
            texture = sdl2.render.SDL_CreateTextureFromSurface(self.texture_renderer.renderer, surface)
        if not texture:
            raise sdl2.ext.SDLError()
        t = sdl2.ext.TextureSprite(texture.contents)

        #sdl2.surface.SDL_FreeSurface(surface)
        #del surface
        return t




def loadAnimationFromPNGSeq(factory, file_name_prefix):
    sprite_list = list()
    for idx in range(0,14):
        name = "%s_%03d.png" % (file_name_prefix, idx)
        print("Loading %s" % name)
        sprite_list.append(factory.from_image(name))
        print(sprite_list[idx].texture)
    anim = {'frames':sprite_list, 'current':0, 'length':idx}
    return anim

def do_something(disp_mgr, i, tx_list, diff, tx_sprite):
    if i <= 150:
        t0 = time.clock()
        ct = 0

        tx2 = disp_mgr.new_texture(450,225)
        print("INFO: Tx2 created (big open canvas)")

        disp_mgr.texture_clear(tx2, (0,0,255,255))
        print("INFO: Tx2 Cleared blue")
        # sdl2.SDL_Delay(100)
        
        disp_mgr.blit(source_tx=tx_sprite, dest_tx=tx2, dest=(i*5,i,0,0))#, area=(0,0,50,50))
        print("INFO: blitted source sprite into tx2")
        # sdl2.SDL_Delay(100)

        disp_mgr.clear((255,0,0))
        print("INFO: screen red filled")
        # sdl2.SDL_Delay(100)
        tx_list.append(tx2)

        disp_mgr.screen_blit(source_tx=tx2, expand_to_fill=True)#, area=(10,10,400,200))

        #textsurf = disp_mgr.font_render_text("Took: % 3.10fms" % diff, font_alias="HHSam_30", size=None, width=None, color=(0,128,0,255), bg_color=None)
        ##textsurf = disp_mgr.font_render_bordered_text("Took: % 3.10fms" % diff, font_alias="HHSam_30", size=50, width=None, color=(255,0,0,255), bg_color=None, border_color=(0,255,0,255), border_width=2)

        (A, B) = disp_mgr.font_render_bordered_text_dual("Took: % 3.10fms" % diff, font_alias="HHSam_30", size=80, width=None, color=(255,255,255,255), bg_color=(0,0,0,255), border_color=(0,255,0,255), border_width=1) 
        C = disp_mgr.combine(A ,B, tx_sprite)
        # disp_mgr.screen_blit(source_tx=bordersurf)
        disp_mgr.screen_blit(source_tx=C, x=2, y=2)
        disp_mgr.flip()

        now = time.clock()
        diff = now - t0
        print "[%d] blit to texture took: % 3.10fms" % (ct, diff)
        print("INFO: blitted TX2 into screen")
        print("INFO: screen flipped")
        print("INFO: =================")
        # sdl2.SDL_Delay(100)

        # del tx2        
    else:
        diff = 0
        tx_tmp = tx_list[(i-30) % len(tx_list)]
        disp_mgr.clear((128,0,128,255))
        # c = sdl2.ext.convert_to_color((128,0,128,255))
        # sdl2.render.SDL_SetRenderDrawColor(disp_mgr.texture_renderer.renderer, c.r, c.g, c.b, c.a)
        # sdl2.render.SDL_RenderClear(disp_mgr.texture_renderer.renderer)
        print("SHOWING %s [%s]" % (tx_tmp, tx_tmp.texture))
        disp_mgr.screen_blit(source_tx=tx_tmp, expand_to_fill=True)#, area=(10,10,400,200))

        disp_mgr.flip()
        # sdl2.render.SDL_RenderPresent(disp_mgr.texture_renderer.renderer)
        # sdl2.SDL_Delay(100)
    
    return diff

def main():
    ### INIT STUFF FROM OLD MAIN

    # print(match_font("Courier"))
    # return

    disp_mgr = sdl2_DisplayManager(450,225,2)

    # sw_sprite = disp_mgr.load_surface("assets/dmd/smile.png")
    # sw_sprite = disp_mgr.load_surface("assets/dmd/t800-war_one.gif")
    sw_sprite = disp_mgr.load_surface("tmp/flames_flipped.png")
    tx_sprite = disp_mgr.texture_from_surface(sw_sprite)

    intro = loadAnimationFromPNGSeq(disp_mgr.factory, "tmp/flames")

    # fm = sdl2.ext.FontManager(font_path = "assets/HH_Samuel.ttf", alias="HHSam_44", size = 44, color=sdl2.ext.Color(255,0,255,0))
    # fm.add(font_path = "assets/T2.ttf", alias="T2_30", size=30)

    # tsurf = fm.render("This is text", alias="HHSam_44", size=None, width=None, color=None, bg_color=None)
    # ssurf = sdl2.ext.SoftwareSprite(tsurf, True)
    # textsurf = disp_mgr.texture_from_surface(ssurf)
    #Text = factory.from_text("THIS IS TTF TEXT!!!",fontmanager=fm) # Creating TextureSprite from Text
   
    disp_mgr.fonts_init("assets/HH_Samuel.ttf", default_font_alias="HHSam_44", size = 44)
    disp_mgr.font_add(font_path="assets/T2.ttf", font_alias="T2_30", size=30)#, color=None, bgcolor=None)
    f = disp_mgr.font_add(font_path="assets/HH_Samuel.ttf", font_alias="HHSam_30", size=30)#, color=None, bgcolor=None)
    #disp_mgr.font_manager.default_font = f
    # ret = sdl2.sdlttf.TTF_SetFontOutline(f, 15)
    # if(not ret):
    #     print(sdl2.sdlttf.TTF_GetError())
    #     raise sdl2.ext.SDLError(sdl2.sdlttf.TTF_GetError())

    # textsurf = disp_mgr.font_render_text("this is ttf", font_alias=None, size=None, width=None, color=None, bg_color=None)

    tx_list = list()
    ################
    running = True
    i = 0
    max = 35 # season to taste
    diff = 0
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
        diff = do_something(disp_mgr, i, tx_list, diff, tx_sprite)
        i=i+1
        if(i>max):
            running = False
        sdl2.SDL_Delay(33)
    return 0


if __name__ == '__main__':
    main()
