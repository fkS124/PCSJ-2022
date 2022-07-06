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
        self.app = app  # reference to the app instance

    def update(self):
        # apply delta time (framerate independence)
        self.vel *= self.app.dt * self.app.FPS
        # apply the collision algorithm
        self.app.game.collision_algorithm(self)
        # the algorithm will have changed velocity if needed (in case of an incoming collision)
        # so just apply the velocity to the object
        self.rect.topleft += self.vel
        self.vel = vec(0, 0)
