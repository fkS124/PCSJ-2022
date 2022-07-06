import pygame as pg
vec = pg.math.Vector2


def darker(color: tuple[int, ...] | pg.Color, degree: int) -> pg.Color:
    new_color = [color[0] + degree, color[1] + degree, color[2] + degree]
    for idx, col in enumerate(new_color):
        if col > 255:
            new_color[idx] = 255
        elif col < 0:
            new_color[idx] = 0
    return pg.Color(new_color)


class Object2d:

    ABSOLUTE_DRAW = False
    DONT_DRAW = False
    DONT_DRAW_PERSPECTIVE = False
    DONT_COLLIDE = False

    """A generic object, containing a surface and a rectangle that can be updated or
    drawn and can handle events.

    Made to be inherited by all the in game objects."""

    def __init__(self, pos, size) -> None:
        self.surface: pg.Surface = pg.Surface(size)
        self.rect: pg.Rect = pg.Rect(pos, size)
        self.color1, self.color2 = None, None

    def get_color1(self):
        return self.color1 if self.color1 is not None else darker(self.surface.get_at((5, 0)), 40)

    def get_color2(self):
        return self.color2 if self.color2 is not None else darker(self.surface.get_at((5, 0)), 60)

    def draw(self, display: pg.Surface, offset=vec(0, 0)) -> None:
        # offset is in order to add a scrolling camera option
        display.blit(self.surface, self.rect.topleft+offset)

    def update(self) -> None:
        pass

    def handle_events(self, event: pg.event.Event) -> None:
        pass
