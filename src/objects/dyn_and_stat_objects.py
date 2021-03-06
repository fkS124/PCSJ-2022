import pygame as pg
from .object2d import Object2d, vec


class StaticObject(Object2d):

    def __init__(self, pos, img: pg.Surface):
        super().__init__(pos, img.get_size())
        self.surface.blit(img, (0, 0))
        # the custom collider is a modifier for the rect, in the collision algorithm

        self.custom_collider = [0, 0, 0, 0]

    def set_custom_collider(self, c_c: list[int, int, int, int]):
        self.custom_collider = c_c


class DynamicObject(StaticObject):

    def __init__(self, app, pos, img: pg.Surface):
        super().__init__(pos, img)

        # ---------- Move
        self.vel = vec(0, 0)  # each frame, add this velocity to the object
        self.last_vel = self.vel.copy()

        self.static_x = False
        self.static_y = False

        self.app = app  # reference to the app instance

    def update(self):
        # apply delta time (framerate independence)
        self.vel *= 60 / self.app.clock.get_fps()
        self.vel = vec(round(self.vel.x), round(self.vel.y))
        # apply the collision algorithm
        self.app.game.collision_algorithm(self)

        self.static_x = self.vel.x == 0
        self.static_y = self.vel.y == 0
        self.last_vel = self.vel.copy()

        # the algorithm will have changed velocity if needed (in case of an incoming collision)
        # so just apply the velocity to the object
        self.rect.topleft += self.vel
        self.vel = vec(0, 0)
