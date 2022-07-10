import random

import pygame as pg
from random import randint, gauss
from .objects import Object2d, vec
from pygame.gfxdraw import filled_polygon


def s_scale(img: pg.Surface, k: float) -> pg.Surface:
    return pg.transform.smoothscale(img, (img.get_width() * k, img.get_height() * k))


def load(path: str):
    return pg.image.load(path).convert()


def load_a(path: str):
    return pg.image.load(path).convert_alpha()


class CloudSprite(Object2d):

    scaling = {
        1: 0.2,
        2: 0.3,
        3: 0.4
    }
    scrolling = {
        1: 2.5,
        2: 5.5,
        3: 7.5
    }

    def __init__(self, pos: tuple[int, int], tag: int):
        super(CloudSprite, self).__init__(pos, (100, 100))
        self.tag = tag
        self.surface = pg.Surface((random.randrange(2, 6)*100, 100 * self.scaling[tag]))
        self.surface.fill((246, 246, 246))
        self.rect = self.surface.get_rect(center=pos)
        self.x = self.rect.x

        self.w, self.h = 1920, 1080

    def update(self, camera_dxy: vec = vec(0, 0)):
        self.x += (1 + 1 / self.tag) - camera_dxy.x / self.scrolling[self.tag]
        self.rect.x = round(self.x)
        if self.rect.x > self.w:
            self.x = -self.rect.w
        elif self.rect.right < 0:
            self.x = self.w
        if self.rect.y > self.h:
            self.rect.bottom = 0
        elif self.rect.bottom < 0:
            self.rect.y = self.h

    def draw(self, display: pg.Surface, offset=vec(0, 0)) -> None:
        self.w, self.h = display.get_size()
        return super(CloudSprite, self).draw(display, offset)


class Background:

    def __init__(self, n_layers: int = 4):
        self.layers: list[list[Object2d]] = [[] for _ in range(n_layers)]

    def draw(self, display: pg.Surface, camera_dxy: vec = vec(0, 0)):
        for layer in self.layers:
            for sprite in layer:
                sprite.update(camera_dxy)
                sprite.draw(display)


class NormalBackground(Background):

    def __init__(self):
        super(NormalBackground, self).__init__(3)

        n_clouds = [3, 5, 6, 0]
        for i in range(3):
            for _ in n_clouds:
                self.layers[i].append(
                    CloudSprite((randint(0, 1400), randint(0, 700)), i+1)
                )

    def draw(self, display: pg.Surface, camera_dxy: vec = vec(0, 0)):
        vanishing_point = vec(display.get_size())/2
        length3d = 5
        for layer in self.layers:
            for sprite in layer:
                sprite.update(camera_dxy)
                pos = vec(sprite.rect.topleft)
                w, h = sprite.rect.w, sprite.rect.h

                vector = vanishing_point - pos
                cond = vector[0] > w / 2, vector[1] > h / 2
                way = ['bottom' if cond[1] else 'top', 'right' if cond[0] else 'left']

                vector -= vec(w * cond[0], h * cond[1])
                pos += vec(w * cond[0], h * cond[1])

                vectors = {'left': vec(vector - vec(w, 0)) / length3d,
                           'right': vec(vector + vec(w, 0)) / length3d,
                           'top': vec(vector - vec(0, h)) / length3d,
                           'bottom': vec(vector + vec(0, h)) / length3d}

                vector /= length3d

                point = {'left': vec(w, 0),
                         'right': -vec(w, 0),
                         'top': vec(0, h),
                         'bottom': -vec(0, h)}

                colors = {
                    'left': (200, 200, 200),
                    'right': (200, 200, 200),
                    'top': (200, 200, 200),
                    'bottom': (200, 200, 200)}

                conditions = {'left': vector[0] < 0,
                              'right': vector[0] > 0,
                              'top': vector[1] < 0,
                              'bottom': vector[1] > 0}
                for i in range(0, 2):
                    if conditions[way[i]]:
                        filled_polygon(display, (pos, pos + point[way[-i + 1]],
                                        pos + point[way[-i + 1]] + vectors[way[-i + 1]],
                                                                pos + vector), colors[way[i]])
                sprite.draw(display)

