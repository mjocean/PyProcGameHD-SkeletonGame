import sys, random, os
from dmd import Layer, Frame
import sdl2
from sdl2_displaymanager import sdl2_DisplayManager
import time

class Particle(object):
    def __init__(self, x, y, emitter):
        self.x = x 
        self.y = y 
        self.parent = emitter
        self.life = random.randint(int(self.parent.max_life*0.80),self.parent.max_life)

        self.dx = random.randint(-5,5)
        self.dy = random.randint(-5,5)

        # self.r = int(random.randint(0,255))
        # self.g = int(random.randint(0,255))
        # self.b = int(random.randint(0,255))

        self._r = 255
        self._g = 255
        self._b = 255
        self._a = 255

        self.tx_num = 0
        self.color_changed = True
        self.alpha_changed = True

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, value):
        self._r = value
        self.color_changed = True

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, value):
        self._g = value
        self.color_changed = True

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b = value
        self.color_changed = True

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._a = value
        self.alpha_changed = True


    def update(self):
        self.life = self.life - 1

        self.update_location()
        self.update_appearance()

    def update_location(self):
        self.x = int(self.x + self.dx)
        self.y = int(self.y + self.dy)

    def update_appearance(self):
        if(self.life < .8 * self.parent.max_life):
            self.b = 0
            self.g = int(self.life/float(self.parent.max_life) * 220) + 35

        self.a = ((self.life/float(self.parent.max_life)) * 255)
        #print("Life=%d, Alpha=%d" % (self.life, self.a))

class SnowParticle(Particle):
    def __init__(self, x, y, emitter):
        self.x = x + random.randint(-450,450)
        super(SnowParticle, self).__init__(self.x,y,emitter)
        self.r = 225
        self.g = 225
        self.b = 255


    def update_location(self):
        self.dx = random.randint(-20,20)
        self.dy = random.randint(0,20)
        super(SnowParticle, self).update_location()

    def update_appearance(self):
        pass
        # if(self.life < .8 * self.parent.max_life):
        #     self.b = 0
        #     self.g = int(self.life/float(self.parent.max_life) * 255)

        # self.a = ((self.life/float(self.parent.max_life)) * 255)
        #print("Life=%d, Alpha=%d" % (self.life, self.a))


class FireParticle(Particle):
    def __init__(self, x, y, emitter):
        super(FireParticle, self).__init__(x,y,emitter)
        self.dx = random.randint(-5,5)
        self.dy = random.randint(-4,4)

    def update_location(self):
        self.dx = random.randint(-3,3)
        self.dy = random.randint(-5,1)
        super(FireParticle, self).update_location()

class FireworkParticle(Particle):
    def __init__(self, x, y, emitter):
        super(FireworkParticle, self).__init__(x,y,emitter)
        self.dy = random.randint(-5,3)
        self.dx = random.randint(-10,10)
        self.a = 192

    def update_location(self):
        if(self.life < .75 * self.parent.max_life):
            self.dy = 3# random.randint(3,10)
            self.dx = 0
        super(FireworkParticle, self).update_location()

    def update_appearance(self):
        if(self.life < .8 * self.parent.max_life):
            self.g = 0
            self.b = int(self.life/float(self.parent.max_life) * 220) + 35
            self.r = self.b

class ParticleEmitter(object):
    def __init__(self, x, y, max_life=60, max_particles=200, particles_per_update=5, total_creations=None, particle_class=Particle, random_next=False, dx=0, dy=0):
        self.x = x
        self.y = y
        self.orig_x = x
        self.orig_y = y
        self.dx = dx
        self.dy = dy


        self.particle_class = particle_class
        self.random_next = random_next

        self.particles = list()
        self.particles_per_update = particles_per_update
        self.max_particles = max_particles
        self.max_life = max_life
        self.total_creations = total_creations
        self.creations_remaining = total_creations
        self.stopped = False

        for i in range(0,particles_per_update):
            p = self.particle_class(x,y, emitter=self)
            p.update()
            self.particles.append(p)
        
        if(self.total_creations is not None):
            self.creations_remaining = self.creations_remaining - particles_per_update
        else:
            self.creations_remaining = self.max_particles

        cwd = os.path.dirname(__file__)
        sprImg8 = sdl2_DisplayManager.inst().load_surface(os.path.join(cwd,"exp8.png"))
        sprImg16 = sdl2_DisplayManager.inst().load_surface(os.path.join(cwd,"exp16.png"))

        self.txImg8 = sdl2_DisplayManager.inst().texture_from_surface(sprImg8)
        self.txImg16 = sdl2_DisplayManager.inst().texture_from_surface(sprImg16)

        (self.p8_w,self.p8_h) = self.txImg8.size
        (self.p16_w,self.p16_h) = self.txImg16.size

        sdl2.SDL_SetTextureBlendMode(self.txImg8.texture, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetTextureBlendMode(self.txImg16.texture, sdl2.SDL_BLENDMODE_BLEND)

        del sprImg8
        del sprImg16

    def reset(self, new_x=None, new_y=None):
        self.stopped = False
        if(new_x is not None):
            self.x = new_x
        else:
            self.x = self.orig_x

        if(new_y is not None):
            self.y = new_y
        else:
            self.y = self.orig_y

        for x in xrange(len(self.particles)-1,0,-1):
            p = self.particles[x]
            self.particles.remove(p)
            del p
        self.creations_remaining = self.total_creations

    def update(self):
        if(self.total_creations is None) and (not self.stopped):
            self.creations_remaining = self.max_particles

        for p in self.particles:
            p.update()

        for x in xrange(len(self.particles)-1,-1,-1):
            p = self.particles[x]
            if(p.life <= 0):
                self.particles.remove(p)
                del p

        if(self.stopped):
            return

        if(self.creations_remaining <= 0):
            if(self.random_next):
                if(len(self.particles)==0):
                    self.reset(new_x = random.randint(0,200), new_y = random.randint(0,200))
            return
            
        for r in range(0,min(self.particles_per_update, self.max_particles-len(self.particles), self.creations_remaining)):
            p = self.particle_class(self.x, self.y, emitter=self)
            p.update()
            self.particles.append(p)
            self.creations_remaining = self.creations_remaining - 1

        self.x = self.x + self.dx
        self.y = self.y + self.dy

    def stop(self, immediate_stop = False):
        self.creations_remaining = 0
        self.stopped = True
        if(immediate_stop):
            for x in xrange(len(self.particles)-1,-1,-1):
                p = self.particles[x]
                self.particles.remove(p)
                del p


    def draw(self, destination_texture = None):
        # for p in self.particles:
        for x in xrange(0,len(self.particles)): #xrange(len(self.particles)-1,0,-1):
            p = self.particles[x]
            tx = None
            if(p.life > self.max_life * 0.55):
                tx = self.txImg16
                (self.p_w, self.p_h) = (self.p16_w,self.p16_h)
            else:
                tx = self.txImg8
                (self.p_w, self.p_h) = (self.p8_w,self.p8_h)

            if(p.color_changed):
                sdl2.SDL_SetTextureColorMod(tx.texture, p.r,p.g,p.b)
                p.color_changed = False

            # sdl2.SDL_SetTextureAlphaMod(tx.texture, 192) #int(p.a))
            if(p.alpha_changed):
                sdl2.SDL_SetTextureAlphaMod(tx.texture, int(p.a))
                p.alpha_changed = False

            if(destination_texture is None):
                sdl2_DisplayManager.inst().screen_blit(tx, x=p.x, y=p.y, expand_to_fill=False)
            else:
                sdl2_DisplayManager.inst().blit(source_tx = tx, dest_tx=destination_texture, dest=(p.x,p.y,self.p_w, self.p_h))                

class ParticleSystem(object):
    def __init__(self, emitters=None, destination_texture=None):
        self.emitters = emitters
        self.dest_tx = destination_texture

    def update(self):
        for e in self.emitters:
            e.update()

    def draw(self):
        for e in self.emitters:
            e.draw(self.dest_tx)

    def reset(self):
        for e in self.emitters:
            e.reset()

class ParticleLayer(Layer):
    """
    A ParticleSystem as a Layer...
    """
    def __init__(self, width, height, emitters, duration=None, num_hold_frames=1):
        super(ParticleLayer, self).__init__()
        self.buffer = Frame(width, height)
        self.start_time = None
        self.duration = duration
        self.width = width
        self.height = height
        self.num_hold_frames = num_hold_frames
        self.stalls = self.num_hold_frames
        # FIRE
        # def emitter_dx(x): return random.randint(-10,10)
        # def emitter_dy(x): return random.randint(-3,3)
        # def dither_dx(x): return random.randint(-10,0)
        # def dither_dy(x): return (x - 0.35)
        
        # self.ps = ParticleEmitter(width/2, height/2, max_life=20, max_particles=200, particles_per_update=100, total_creations=400, particle_class=Particle)
        self.ps = ParticleSystem(emitters=emitters, destination_texture=self.buffer.pySurface)

    
    def next_frame(self):
        # Assign the new script item:
        if(self.start_time is None):
            self.start_time = time.time()
        elif(self.duration is not None and (self.start_time + self.duration > time.time())):
            return None
        self.stalls = self.stalls - 1
        if(self.stalls <= 0):
            self.stalls = self.num_hold_frames
        else:
            return self.buffer

        self.buffer.clear()
        self.ps.update()
        self.ps.draw()
        return self.buffer
        
    def reset(self):
        """Resets the animation back to the first frame."""
        self.start_time = None
        self.stalls = self.num_hold_frames
        self.buffer.clear()
        self.ps.reset()


def main():

    sdl2_DisplayManager.Init(450,225,2)

    # # FIRE
    # def emitter_dx(x): return random.randint(-10,10)
    # def emitter_dy(x): return random.randint(-3,3)
    # def dither_dx(x): return random.randint(-10,0)
    # def dither_dy(x): return (x - 0.35)
    
    #ps = ParticleEmitter(450,225, max_life=20, max_particles=400, particles_per_update=20, particle_class=Particle)
    ps1 = ParticleEmitter(450, 225, max_life=20, max_particles=200, particles_per_update=40, total_creations=None, particle_class=FireParticle)
    # ps2 = ParticleEmitter(250, 115, max_life=30, max_particles=500, particles_per_update=40, total_creations=2000, particle_class=SnowParticle)
    # ps2 = ParticleEmitter(450, 0, max_life=35, max_particles=500, particles_per_update=16, total_creations=None, particle_class=SnowParticle)
    ps2 = ParticleEmitter(20, 20, max_life=20, max_particles=300, particles_per_update=100, total_creations=300, particle_class=FireworkParticle, random_next=True)

    ps3 = ParticleEmitter(300, 220, max_life=20, max_particles=300, particles_per_update=100, total_creations=300, particle_class=FireworkParticle, random_next=True)
    
    # ps = ParticleSystem(emitters=[ps1,ps2, ps3])

    ps = ParticleSystem(emitters=[ps1, ps2, ps3])

    # def emitter_dx(x): return random.randint(-10,10)
    # def emitter_dy(y): return random.randint(-6,6)
    # def dither_dx(x): return x #random.randint(-6,6)
    # def dither_dy(y): return y #(x - 0.35)
    
    # ps = ParticleEmitter(450,200, max_life=20, max_particles=200, particles_per_update=5, emitter_dx_fn=emitter_dx, emitter_dy_fn=emitter_dy, dither_dx_fn=dither_dx, dither_dy_fn=dither_dy)


    running = True

    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_r:
                    ps.reset()
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
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
