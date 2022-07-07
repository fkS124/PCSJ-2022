import pygame as pg
from .dyn_and_stat_objects import DynamicObject, vec


class Particle(DynamicObject):

    ABSOLUTE_DRAW = True

    def __init__(self, app, pos: tuple[int, int], size: tuple[int, int], color: pg.Color, initial_vel: vec,
                 life_span: int):
        super(Particle, self).__init__(app, pos, pg.Surface(size))
        self.surface.fill(color)
        self.vel = initial_vel
        self.initial_vel = initial_vel
        self.friction = 1
        self.gravity = 1
        self.initialized_time = pg.time.get_ticks()
        self.life_span = life_span

    def update(self):
        self.vel.x += 1 if self.vel.x < 0 else (-1 if self.vel.x > 0 else 0)
        self.gravity += 1
        self.vel.y += self.gravity
        if pg.time.get_ticks() - self.initialized_time > self.life_span:
            return "kill"
        return super(Particle, self).update()

