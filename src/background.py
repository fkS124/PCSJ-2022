import random

import pygame as pg
from random import randint
from .objects import Object2d, vec
from pygame.gfxdraw import filled_polygon


def s_scale(img: pg.Surface, k: float) -> pg.Surface:
    return pg.transform.smoothscale(img, (img.get_width() * k, img.get_height() * k))


def load(path: str):
    return pg.image.load(path).convert()


def load_a(path: str):
    return pg.image.load(path).convert_alpha()


def darker(color: tuple[int, ...] | pg.Color, degree: int):
    new_color = [color[0] + degree, color[1] + degree, color[2] + degree]
    for idx, col in enumerate(new_color):
        if col > 255:
            new_color[idx] = 255
        elif col < 0:
            new_color[idx] = 0
    return pg.Color(new_color)


class CloudSprite(Object2d):

    def __init__(self, pos: tuple[int, int]):
        super(CloudSprite, self).__init__(pos, (100, 100))
        self.offset = vec(0, 0)
        self.vel = random.randrange(1, 3)
        self.length = random.random()+2
        self.scrolling = random.randint(2, 10)
        self.surface = pg.Surface((random.randint(200, 600), random.randint(40, 80)))
        color = 225
        self.color = (color, color, color)
        self.surface.fill(self.color)
        self.rect = self.surface.get_rect(center=pos)
        self.x = self.rect.x
        self.perspective_x = 0

        self.w, self.h = 1920, 1080

    def update(self, camera_dxy: vec = vec(0, 0)):
        self.x += self.vel - camera_dxy.x / self.scrolling
        self.rect.x = round(self.x)
        if self.rect.x + self.perspective_x + self.offset.x > self.w:
            self.x = -self.rect.w - abs(self.perspective_x) - self.offset.x

    def draw(self, display: pg.Surface, offset=vec(0, 0)) -> None:
        self.w, self.h = display.get_size()
        self.offset = offset
        return super(CloudSprite, self).draw(display, offset)


class Background:

    def __init__(self, n_layers: int = 4):
        self.sprites: list[Object2d] = []

    def draw(self, display: pg.Surface, camera_dxy: vec = vec(0, 0), offset: vec = vec(0, 0)):
        for sprite in self.sprites:
            sprite.update(camera_dxy)
            sprite.draw(display, offset)


class StarSprite(Object2d):

    def __init__(self, pos: tuple[int, int]):
        super(StarSprite, self).__init__(pos, (100, 100))
        self.offset = vec(0, 0)
        self.scrolling = random.randint(2, 10)
        self.size = randint(2, 15)
        self.surface = pg.Surface((self.size, self.size))
        self.surface.fill((255, 255, 255))
        self.rect = self.surface.get_rect(center=pos)
        self.x = self.rect.x
        self.perspective_x = 0

        self.w, self.h = 1400, 1080

    def update(self, camera_dxy: vec = vec(0, 0)):
        self.x -= camera_dxy.x / self.scrolling
        self.rect.x = round(self.x)
        if self.rect.right < 0:
            self.x = self.w

    def draw(self, display: pg.Surface, offset=vec(0, 0)) -> None:
        self.w, self.h = display.get_size()
        return super(StarSprite, self).draw(display, offset)


class MoonBackground(Background):

    def __init__(self):
        super(MoonBackground, self).__init__()
        for _ in range(30):
            self.sprites.append(StarSprite((randint(0, 1200), randint(0, 700))))

    def update_alpha(self, degree):
        for sprite in self.sprites:
            sprite.surface.set_alpha(255 * degree)


class NormalBackground(Background):

    def __init__(self):
        super(NormalBackground, self).__init__()

        for _ in range(5):
            self.sprites.append(CloudSprite((randint(0, 1200), 100*_+50)))

    def draw(self, display: pg.Surface, camera_dxy: vec = vec(0, 0), offset: vec = vec(0, 0)):
        vanishing_point = vec(display.get_size())/2
        for sprite in self.sprites:
            sprite.update(camera_dxy)
            pos = vec(sprite.rect.topleft) + offset
            w, h = sprite.rect.w, sprite.rect.h

            vector = vanishing_point - pos
            cond = vector[0] > w / 2, vector[1] > h / 2
            way = ['bottom' if cond[1] else 'top', 'right' if cond[0] else 'left']

            vector -= vec(w * cond[0], h * cond[1])
            pos += vec(w * cond[0], h * cond[1])

            vectors = {'left': vec(vector - vec(w, 0)) / sprite.length,
                       'right': vec(vector + vec(w, 0)) / sprite.length,
                       'top': vec(vector - vec(0, h)) / sprite.length,
                       'bottom': vec(vector + vec(0, h)) / sprite.length}

            vector /= sprite.length
            sprite.perspective_x = vector.x

            point = {'left': vec(w, 0),
                     'right': -vec(w, 0),
                     'top': vec(0, h),
                     'bottom': -vec(0, h)}

            colors = {
                'left': darker(sprite.color, -20),
                'right': darker(sprite.color, 20),
                'top': darker(sprite.color, 40),
                'bottom': darker(sprite.color, -40)}

            conditions = {'left': vector[0] < 0,
                          'right': vector[0] > 0,
                          'top': vector[1] < 0,
                          'bottom': vector[1] > 0}
            for i in range(0, 2):
                if conditions[way[i]]:
                    filled_polygon(display, (pos, pos + point[way[-i + 1]],
                                             pos + point[way[-i + 1]] + vectors[way[-i + 1]],
                                             pos + vector), colors[way[i]])
            sprite.draw(display, offset=offset)

