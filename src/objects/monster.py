import pygame as pg
from .dyn_and_stat_objects import DynamicObject, StaticObject
from . import vec


class Monster(DynamicObject):

    ABSOLUTE_DRAW = True

    def __init__(self, app, pos, size):
        super(Monster, self).__init__(app, pos, pg.Surface(size))
        self.surface.fill((255, 0, 0))
        self.base_vel = 5
        self.gravity = 0
        self.jumping = False

    def update(self):
        self.vel.x += self.base_vel
        super(Monster, self).update()
        if self.last_vel.x == 0:
            self.base_vel *= -1


class Bullet(Monster):

    ABSOLUTE_DRAW = True

    def __init__(self, app, pos, size, vel: vec, sprite_loader):
        super(Bullet, self).__init__(app, pos, size)
        self.sprite_loader = sprite_loader
        self.rect.centerx = pos[0]
        self.base_vel = vel
        self.length3d = 23
        self.surface.fill((255, 0, 0))

        self.vel = self.base_vel
        self.last_vel = self.vel

    def update(self):
        self.vel += self.base_vel
        DynamicObject.update(self)
        if self.last_vel.length() == 0 or self.rect.y < -500:
            return "kill"


class Canon(StaticObject):

    def __init__(self, app, pos):
        super(Canon, self).__init__(pos, pg.Surface((80, 80)))

        self.app = app
        self.surface = pg.Surface((50, 70))
        self.rect = self.surface.get_rect(center=self.rect.center)
        self.length3d = 15
        self.bullet_size = 15, 30

        self.delay = 750
        self.last_add = 0

    def update(self, *args, **kwargs) -> None:
        if pg.time.get_ticks() - self.last_add > self.delay:
            self.last_add = pg.time.get_ticks()
            self.app.game.add_object(
                Bullet(self.app, (self.rect.centerx, self.rect.y-self.bullet_size[1]), self.bullet_size, vec(0, -10),
                       self.app.game.map.sprite_loader)
            )
