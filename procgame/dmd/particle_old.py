import sys, random
from dmd import Layer, Frame
import sdl2
from sdl2_displaymanager import sdl2_DisplayManager
import time

class Particle(object):
    def __init__(self, x, y, parent):
        self.x = x 
        self.y = y 
        self.color = 0
        self.parent = parent
        self.life = random.randint(int(self.parent.max_life*0.80),self.parent.max_life)
        self.dx = 0
        self.dy = 0

        # self.r = int(random.randint(0,255))
        # self.g = int(random.randint(0,255))
        # self.b = int(random.randint(0,255))

        self.r = 255# int(random.randint(0,255))
        self.g = 255#int(random.randint(0,255))
        self.b = 255#int(random.randint(0,255))


        self.dx = parent.emitter_dx_fn(self.dx)
        self.dy = parent.emitter_dy_fn(self.dy)


    def update(self):
        self.life = self.life - 1

        self.x = int(self.x + self.dx)
        self.y = int(self.y + self.dy)


        self.dx = self.parent.dither_dx_fn(self.dx)
        self.dy = self.parent.dither_dy_fn(self.dy)

        if(self.life < .8 * self.parent.max_life):
            self.b = 0
            self.g = int(self.life/float(self.parent.max_life) * 255)

        self.alpha_value = ((self.life/float(self.parent.max_life)) * 255)
        #print("Life=%d, Alpha=%d" % (self.life, self.alpha_value))


class ParticleSystem(object):
    def __init__(self, x, y, max_life=60, max_particles=200, particles_per_update=5,
            emitter_dx_fn=None, emitter_dy_fn=None, dither_dx_fn=None, dither_dy_fn=None):
        self.x = x
        self.y = y

        self.particles = list()
        self.particles_per_update = particles_per_update
        self.max_particles = max_particles
        self.max_life = max_life

        self.emitter_dx_fn = emitter_dx_fn
        self.emitter_dy_fn = emitter_dy_fn

        self.dither_dx_fn = dither_dx_fn
        self.dither_dy_fn = dither_dy_fn

        for i in range(0,particles_per_update):
            p = Particle(x,y, parent=self)
            p.update()
            self.particles.append(p)
        sprFire = sdl2_DisplayManager.inst().load_surface("assets/dmd/fire.png")
        sprWhite = sdl2_DisplayManager.inst().load_surface("assets/dmd/white.png")
        sprYellow = sdl2_DisplayManager.inst().load_surface("assets/dmd/fire_yellow.png")

        sprSmoke = sdl2_DisplayManager.inst().load_surface("assets/dmd/exp.png")

        self.txFire = sdl2_DisplayManager.inst().texture_from_surface(sprFire)
        self.txWhite = sdl2_DisplayManager.inst().texture_from_surface(sprWhite)
        self.txYellow = sdl2_DisplayManager.inst().texture_from_surface(sprYellow)
        self.txSmoke = sdl2_DisplayManager.inst().texture_from_surface(sprSmoke)

        (self.p_w,self.p_h) = self.txSmoke.size

        sdl2.SDL_SetTextureBlendMode(self.txFire.texture, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetTextureBlendMode(self.txWhite.texture, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetTextureBlendMode(self.txYellow.texture, sdl2.SDL_BLENDMODE_BLEND)

        sdl2.SDL_SetTextureBlendMode(self.txSmoke.texture, sdl2.SDL_BLENDMODE_BLEND)

        del sprFire
        del sprWhite
        del sprYellow
        del sprSmoke

    def reset(self):
        for x in xrange(len(self.particles)-1,0,-1):
            p = self.particles[x]
            self.particles.remove(p)
            del p

    def update(self):
        for p in self.particles:
            p.update()
        for r in range(0,min(self.particles_per_update, self.max_particles-len(self.particles))):
            p = Particle(self.x, self.y, parent=self)
            p.update()
            self.particles.append(p)
        for x in xrange(len(self.particles)-1,0,-1):
            p = self.particles[x]
            if(p.life <= 0):
                self.particles.remove(p)
                del p

    def draw(self, destination_texture = None):
        # for p in self.particles:
        for x in xrange(0,len(self.particles)): #xrange(len(self.particles)-1,0,-1):
            p = self.particles[x]
            tx = None
            # if(p.life > self.max_life * 0.55):
            #     tx = self.txYellow
            # elif(p.life > self.max_life * 0.25):
            #     tx = self.txFire
            # else:
            #     tx = self.txWhite
            tx = self.txSmoke

            sdl2.SDL_SetTextureColorMod(tx.texture, p.r,p.g,p.b)

            # sdl2.SDL_SetTextureAlphaMod(tx.texture, 192) #int(p.alpha_value))
            sdl2.SDL_SetTextureAlphaMod(tx.texture, int(p.alpha_value))
            if(destination_texture is None):
                sdl2_DisplayManager.inst().screen_blit(tx, x=p.x, y=p.y, expand_to_fill=False)
            else:
                sdl2_DisplayManager.inst().blit(source_tx = tx, dest_tx=destination_texture, dest=(p.x,p.y,self.p_w, self.p_h))                

class ParticleLayer(Layer):
    """
    A ParticleSystem as a Layer...
    """
    def __init__(self, width, height, duration=None):
        super(ParticleLayer, self).__init__()
        self.buffer = Frame(width, height)
        self.start_time = None
        self.duration = duration
        # FIRE
        def emitter_dx(x): return random.randint(-10,10)
        def emitter_dy(x): return random.randint(-3,3)
        def dither_dx(x): return random.randint(-10,0)
        def dither_dy(x): return (x - 0.35)
        
        self.ps = ParticleSystem(width/2, height/2, max_life=20, max_particles=400, particles_per_update=20, emitter_dx_fn=emitter_dx, emitter_dy_fn=emitter_dy, dither_dx_fn=dither_dx, dither_dy_fn=dither_dy)
    
    def next_frame(self):
        # Assign the new script item:
        self.start_time = time.time()

        self.buffer.clear()
        self.ps.update()
        self.ps.draw(self.buffer.pySurface)
        return self.buffer
        
    def reset(self):
        """Resets the animation back to the first frame."""
        self.buffer.clear()
        self.ps.reset()

def main():

    sdl2_DisplayManager.Init(450,225,2)

    # FIRE
    def emitter_dx(x): return random.randint(-10,10)
    def emitter_dy(x): return random.randint(-3,3)
    def dither_dx(x): return random.randint(-10,0)
    def dither_dy(x): return (x - 0.35)
    
    ps = ParticleSystem(450,225, max_life=20, max_particles=400, particles_per_update=20, emitter_dx_fn=emitter_dx, emitter_dy_fn=emitter_dy, dither_dx_fn=dither_dx, dither_dy_fn=dither_dy)

    # def emitter_dx(x): return random.randint(-10,10)
    # def emitter_dy(y): return random.randint(-6,6)
    # def dither_dx(x): return x #random.randint(-6,6)
    # def dither_dy(y): return y #(x - 0.35)
    
    # ps = ParticleSystem(450,200, max_life=20, max_particles=200, particles_per_update=5, emitter_dx_fn=emitter_dx, emitter_dy_fn=emitter_dy, dither_dx_fn=dither_dx, dither_dy_fn=dither_dy)


    running = True

    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
        ps.update()
        ps.draw()
        sdl2_DisplayManager.inst().flip()
        sdl2.SDL_Delay(33)
        sdl2_DisplayManager.inst().clear()

    return 0

if __name__ == '__main__':
    main()
