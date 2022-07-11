import pygame as pg
from . import vec
from copy import copy


def s_scale(img: pg.Surface, k: float) -> pg.Surface:
    return pg.transform.smoothscale(img, (img.get_width() * k, img.get_height() * k))


def resize(img: pg.Surface, new_size: tuple[int, int]) -> pg.Surface:
    return pg.transform.smoothscale(img, new_size)


class UiObject:
    FIXED = False
    IN_BACKGROUND = False

    """
    Base class for every UI object.
    Attributes :
    - surface: pg.Surface
    Basically the surface that is being drawn on the screen when calling  UiObject.draw()
    Every child object should draw on this surface.
    - rect: pg.Rect
    Stores the position and the size of the ui object
    """

    def __init__(self, pos: tuple[int, int], size: tuple[int, int], alpha=True):
        self.surface = pg.Surface(size, pg.SRCALPHA) if alpha else pg.Surface(size)
        self.rect = self.surface.get_rect(topleft=pos)

    def handle_events(self, event: pg.event.Event):
        pass

    def draw(self, display: pg.Surface, offset=pg.Vector2(0, 0)):
        display.blit(self.surface, self.rect.topleft + offset)


class BlackLayer(UiObject):

    IN_BACKGROUND = False
    FIXED = True

    def __init__(self, pos, size, alpha=125):
        super(BlackLayer, self).__init__(pos, size)
        self.surface.fill((0, 0, 0))
        self.surface.set_alpha(alpha)


class Text(UiObject):
    """
    A text object that can be drawn on screen.
    """

    def __init__(self, pos: tuple[int, int], font: pg.font.Font, text: str, color: pg.Color, resize_=(0, 0), scale_=0,
                 shadow_: tuple[int, int] | None = None, centered=False):
        self.font = font
        self.color = color
        self.text = text

        rendered_text = font.render(text, True, color)
        super(Text, self).__init__(pos, rendered_text.get_size(), alpha=True)
        if centered:
            self.rect.center = pos
        self.surface.blit(rendered_text, (0, 0))

        if resize_ != (0, 0):
            self.resize_ = resize_
            self.surface = resize(self.surface, resize_)
            self.rect = self.surface.get_rect(topleft=pos)
        elif scale_ != 0:
            self.scale_ = scale_
            self.surface = s_scale(self.surface, scale_)
            self.rect = self.surface.get_rect(topleft=pos)

        if shadow_ is not None:
            self.shadow_surf = font.render(text, True, (0, 0, 0))
            self.shadow_rect = self.shadow_surf.get_rect(center=self.rect.center+pg.Vector2(shadow_))
            self.original_img_shadow = self.shadow_surf

        self.original_img = self.surface
        self.current_scale = 1

    def scale(self, n: float):
        self.current_scale = n
        self.surface = s_scale(self.original_img, n)
        self.rect = self.surface.get_rect(center=self.rect.center)
        if hasattr(self, "shadow_surf"):
            self.shadow_surf = s_scale(self.original_img_shadow, n)
            self.shadow_rect = self.shadow_surf.get_rect(center=self.shadow_rect.center)

    def modify_content(self, new_text: str):
        self.text = new_text
        self.surface = self.font.render(new_text, True, self.color)
        if hasattr(self, "resize_"):
            self.surface = resize(self.surface, self.resize_)
        elif hasattr(self, "scale_"):
            self.surface = s_scale(self.surface, self.scale_)
        self.rect = self.surface.get_rect(topleft=self.rect.topleft)
        self.original_img = self.surface

    def draw(self, display: pg.Surface, offset=pg.Vector2(0, 0)):
        if hasattr(self, "shadow_surf"):
            display.blit(self.shadow_surf, self.shadow_rect.topleft + offset)
        return super(Text, self).draw(display, offset)


class Title(Text):

    IN_BACKGROUND = True

    def __init__(self, pos: tuple[int, int], font: pg.font.Font, text: str, color: pg.Color, big_scale: float = 2,
                 scaling_delay: int = 500, resize_=(0, 0), scale_=0, shadow_=None):
        super(Title, self).__init__(pos, font, text, color, resize_, scale_, shadow_)
        self.big_scale = big_scale
        self.scaling_delay = scaling_delay
        self.scaling = False
        self.descaling = False
        self.scaled = False
        self.phase_begin_time = 0
        self.current_scale = 1

    def start_scaling(self):
        if not self.scaling and not self.descaling:
            self.scaling = True
            self.phase_begin_time = pg.time.get_ticks()
            self.current_scale = 1
            return True
        return False

    def start_descaling(self):
        if not self.descaling and not self.scaling:
            self.descaling = True
            self.current_scale = self.big_scale
            self.phase_begin_time = pg.time.get_ticks()
            return True
        return False

    def draw(self, display: pg.Surface, offset=pg.Vector2(0, 0)):
        advance = pg.time.get_ticks() - self.phase_begin_time
        if self.scaling:
            if pg.time.get_ticks() - self.phase_begin_time > self.scaling_delay:
                self.scaling = False
                self.current_scale = self.big_scale
            else:
                self.current_scale = 1 + (self.big_scale - 1) * advance / self.scaling_delay
                self.scale(self.current_scale)
        elif self.descaling:
            if pg.time.get_ticks() - self.phase_begin_time > self.scaling_delay:
                self.descaling = False
                self.current_scale = 1
            else:
                self.current_scale = self.big_scale - (self.big_scale - 1) * advance / self.scaling_delay
                self.scale(self.current_scale)

        return super(Title, self).draw(display, offset)


def create_bg_text(pos: tuple[int, int], font: pg.font.Font, text: str, color: pg.Color, resize_=(0, 0), scale_=0,
                   shadow_=None):
    txt = Text(pos, font, text, color, resize_, scale_, shadow_)
    txt.IN_BACKGROUND = True
    return txt


class Button(UiObject):
    """
    A button, usable anywhere
    """
    IN_BACKGROUND = False
    FIXED = True

    def __init__(self,
                 pos: tuple[int, int],
                 size: tuple[int, int],
                 text: Text,
                 hover_text: Text | None = None,
                 click_text: Text | None = None,
                 hover_color: pg.Color | None = None,
                 click_color: pg.Color | None = None,
                 normal_color: pg.Color = pg.Color(0, 0, 0),
                 border_radius: tuple[int, int, int, int] | None = None,
                 button: int = 1,
                 exec_type: str = "down",
                 click_func=None,
                 click_func_args: tuple = None,
                 hover_func=None,
                 hover_func_args: tuple = None,
                 shadow: tuple = None
                 ):
        super(Button, self).__init__(pos, size, True)

        self.state = "normal"
        self.button = button
        self.exec_type = exec_type

        self.colors: dict[str, pg.Color] = {"normal": normal_color,
                                            "hover": hover_color if hover_color is not None else normal_color}
        self.colors["click"] = click_color if click_color is not None else self.colors["hover"]

        self.texts: dict[str, Text] = {"normal": text, "hover": text if hover_text is None else hover_text}
        self.texts["click"] = click_text if click_text is not None else self.texts["hover"]

        self.func = {"click": click_func, "hover": hover_func}
        self.args = {"click": click_func_args, "hover": hover_func_args}

        self.border_radius = border_radius

        self.shadow = shadow

        self.press_time = 0
        self.press_delay = 25

    def handle_events(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == self.button and self.rect.collidepoint(event.pos):
                self.exec_func("down", "click")
                self.state = "click"
                self.press_time = pg.time.get_ticks()
        elif event.type == pg.MOUSEBUTTONUP and (pg.time.get_ticks() - self.press_time > self.press_delay):
            if event.button == self.button and self.rect.collidepoint(event.pos):
                self.exec_func("up", "click")
            self.state = "hover" if self.rect.collidepoint(event.pos) else "normal"

    def exec_func(self, click_type: str, exec_type: str):
        if self.exec_type == click_type:
            if self.func[exec_type] is not None:
                if self.args[exec_type] is not None:
                    self.func[exec_type](*self.args[exec_type])
                else:
                    self.func[exec_type]()

    def draw(self, display: pg.Surface, offset=pg.Vector2(0, 0)):
        mouse_pos = pg.mouse.get_pos()
        self.surface.fill((0, 0, 0, 0))

        if self.state != "click":
            last_state = copy(self.state)
            self.state = "hover" if self.rect.collidepoint(mouse_pos) else "normal"
            if self.state != last_state and self.state == "hover":
                self.exec_func(self.exec_type, "hover")

        # get colors and texts
        color = self.colors[self.state]
        text = self.texts[self.state]

        if self.shadow is not None and self.border_radius is not None:
            pg.draw.rect(display, (0, 0, 0), self.rect.move(self.shadow), border_radius=self.border_radius[0])
        elif self.shadow is not None:
            pg.draw.rect(display, (0, 0, 0), self.rect.move(self.shadow))

        if self.border_radius is not None:
            pg.draw.rect(self.surface, color, [0, 0, *self.surface.get_size()],
                         border_top_left_radius=self.border_radius[0],
                         border_top_right_radius=self.border_radius[1],
                         border_bottom_left_radius=self.border_radius[2],
                         border_bottom_right_radius=self.border_radius[3])
        else:
            pg.draw.rect(self.surface, color, [0, 0, *self.surface.get_size()])
        if hasattr(text, "shadow_surf"):
            self.surface.blit(text.shadow_surf, text.shadow_surf.get_rect(
                center=(self.rect.w / 2 + text.shadow_rect.x - text.rect.x,
                        self.rect.h / 2 + text.shadow_rect.y - text.rect.y)))
        self.surface.blit(text.surface, text.surface.get_rect(center=(self.rect.w / 2, self.rect.h / 2)))

        if self.state != "click" or self.shadow is None:
            display.blit(self.surface, self.rect)
        else:
            if (dxy := (pg.time.get_ticks() - self.press_time) / self.press_delay) <= 1:
                display.blit(self.surface, self.rect.move(
                    vec(self.shadow) * dxy
                ))
            else:
                display.blit(self.surface, self.rect.move(self.shadow))
