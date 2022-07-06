import pygame as pg
from copy import copy
from math import floor
from random import choice, randint
from .objects import StaticObject, vec, Object2d, DynamicObject


def darker(color: tuple[int, ...] | pg.Color, degree: int) -> pg.Color:
    new_color = [color[0] + degree, color[1] + degree, color[2] + degree]
    for idx, col in enumerate(new_color):
        if col > 255:
            new_color[idx] = 255
        elif col < 0:
            new_color[idx] = 0
    return pg.Color(new_color)


class SpriteLoader:

    def __init__(self, app, tile_w, tile_h):
        self.app = app

        self.sprites: dict[str, pg.Surface] = {
            "moon": self.resize(tile_w, tile_h, self.load("assets/sprites/moon_1.png")),
            "star": self.resize(tile_w, tile_h, self.load("assets/sprites/star_1.png"))
        }

        self.color_animations = {
            "green-magenta": {"color1": (0, 255, 0), "color2": (255, 0, 255), "delay": 1250},
            "white-red": {"color1": (150, 0, 0), "color2": (255, 0, 0), "delay": 500},
        }
        self.current_color_animations = {}
        self.last_count = 0

        for key, animation in self.color_animations.items():
            self.setup_color_animation(key)

    @staticmethod
    def resize(w, h, img: pg.Surface):
        return pg.transform.smoothscale(img, (w, h))

    @staticmethod
    def load(path: str):
        return pg.image.load(path).convert()

    @staticmethod
    def calc_color(animation, advance) -> pg.Color:
        return pg.Color(
            floor(animation["color1"][0] + advance * animation["dr"] / animation["delay"]),
            floor(animation["color1"][1] + advance * animation["dg"] / animation["delay"]),
            floor(animation["color1"][2] + advance * animation["db"] / animation["delay"]),
        )

    def setup_color_animation(self, key):
        color_a = self.color_animations[key]
        self.current_color_animations[key] = color_a["color1"]
        self.color_animations[key]["dr"] = color_a["color2"][0] - color_a["color1"][0]
        self.color_animations[key]["dg"] = color_a["color2"][1] - color_a["color1"][1]
        self.color_animations[key]["db"] = color_a["color2"][2] - color_a["color1"][2]

    def calculate_color_animations(self):
        for key, animation in self.color_animations.items():
            advance = pg.time.get_ticks() % animation["delay"]
            self.current_color_animations[key] = self.calc_color(animation, advance)
            if pg.time.get_ticks() // animation["delay"] > self.last_count:
                self.last_count += 1
                color2 = self.color_animations[key]["color2"]
                self.color_animations[key]["color2"] = self.color_animations[key]["color1"]
                self.color_animations[key]["color1"] = color2
                self.setup_color_animation(key)


class TileSprite(StaticObject):

    """
    Animated Color documentation :
    color_anim = {
        "color1": pg.Color or (r, g, b, a),
        "color2": pg.Color or (r, b, b, a),
        "delay": int (in milliseconds)
    }
    """
    special_color_set: dict[str, dict[str, pg.Color]] = {
        "stone": {"default": pg.Color(110, 110, 110)},
        "grass": {"default": pg.Color(124, 94, 66), "top": pg.Color(0, 200, 50)}
    }

    def __init__(self, pos: vec, size: vec, tag: str, sprite_loader: SpriteLoader, color=pg.Color(37, 31, 77),
                 color_anim: str | None = None, unbreakable=False):
        super(TileSprite, self).__init__(pos, pg.Surface(size, pg.SRCALPHA))

        self.unbreakable = unbreakable

        # SPRITE ANIMATION ------------------------------
        self.sprite_loader = sprite_loader
        self.color = color
        self.tag = tag
        if tag in self.sprite_loader.sprites:
            self.surface = self.sprite_loader.sprites[tag]
        elif tag in self.special_color_set:
            self.color = self.special_color_set[tag]["default"]
            for key, item in self.special_color_set[tag].items():
                if key in self.colors:
                    self.colors[key] = item
            self.surface.fill(self.color)
        elif tag == "beacon":
            self.surface.fill(self.color)
            self.color = color
            self.pressed = False
        elif tag == "animated_color":
            if color_anim is not None:
                self.surface.fill(self.sprite_loader.current_color_animations[color_anim])
                self.color_anim = color_anim

        elif tag == "color":
            self.surface.fill(self.color)

        self.dying = False
        self.death_time = 0

    def kill(self):
        if not self.dying:
            self.dying = True
            self.death_time = pg.time.get_ticks()
            
    def update(self) -> None | str:
        if self.tag == "animated_color":
            self.color = self.sprite_loader.current_color_animations[self.color_anim]
            self.surface.fill(self.color)
        elif self.tag == "beacon":
            if self.pressed:
                new_color = darker(self.color, 80)
                self.surface.fill(new_color := (new_color[0], new_color[1], 0))
            else:
                self.surface.fill(self.color)

        if self.dying:
            if pg.time.get_ticks() - self.death_time > 500:
                return "kill"

        return super().update()


class Map:

    g = 10
    s = 11
    b = 12

    menu_map = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, b, g, g, g, b, g, g, g, b, g, g, g, g]]
    menu_map_gen = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g]]

    def __init__(self, app):

        self.screen = app.screen
        self.horizontal_only = False
        self.vertical_only = True
        self.app = app
        self.tile_size = vec(80, 80)
        self.sprite_loader = SpriteLoader(app, self.tile_size.x, self.tile_size.y)
        self.chunk_size = 15
        self.grid = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]]

        self.translate = {
            # 3: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "star", self.sprite_loader)),
            # 2: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "moon", self.sprite_loader)),
            # 1: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "color", self.sprite_loader)),
            3: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "color", self.sprite_loader,
                                              unbreakable=True)),
            2: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "animated_color", self.sprite_loader,
                                              color_anim="white-red")),
            1: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "animated_color", self.sprite_loader,
                                              color_anim="white-red")),
            10: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "grass", self.sprite_loader)),
            11: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "stone", self.sprite_loader)),
            12: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "beacon", self.sprite_loader,
                                               color=pg.Color(150, 150, 0)))
        }

        self.chunks: dict[tuple[int, int], list[list[int, ...]], ...] = {
            (0, 0): copy(self.grid),
            "menu": copy(self.menu_map)
        }
        self.generated_chunks = {}
        self.menu = False

    def generate_menu(self):
        self.menu = True
        self.chunk_size = 32
        return self.generate_new_chunk("menu")

    def quit_menu(self):
        self.generated_chunks = {}
        self.menu = False
        self.chunk_size = 15

    def get_index_from_co(self, pos: vec):
        chunk_id = floor(pos.x / (self.chunk_size * self.tile_size.x)), \
                   floor(pos.y / (self.chunk_size * self.tile_size.y))
        col = floor(((pos.x - chunk_id[0] * self.tile_size.x * self.chunk_size) / self.tile_size.x))
        row = floor(((pos.y - chunk_id[1] * self.tile_size.y * self.chunk_size) / self.tile_size.y))
        return row, col, chunk_id[0], chunk_id[1]

    def get_chunk(self, pos: vec):
        return (floor(pos.x / (self.chunk_size * self.tile_size.x)),
                floor(pos.y / (self.chunk_size * self.tile_size.y)))

    def init_game(self):
        self.generate_new_chunk((0, 0))

    def has_neighbour(self, direction: str, obj):
        translate = {'left': (0, -1), 'right': (0, 1), 'top': (-1, 0), 'bottom': (1, 0)}
        row, col, chunk_id_x, chunk_id_y = self.get_index_from_co(vec(obj.rect.topleft))

        print(row, col, chunk_id_x, chunk_id_y)

        if self.menu:
            row += translate[direction][0]
            col += translate[direction][1]
            if 0 <= row < len(self.menu_map) and 0 <= col < len(self.menu_map[1]):
                return self.menu_map[row][col] != 0
            else:
                return False if row != len(self.menu_map)-1 else True

        if 0 <= row + translate[direction][0] < self.chunk_size and 0 <= col + translate[direction][1] < self.chunk_size:
            row += translate[direction][0]
            col += translate[direction][1]
            return self.chunks[(chunk_id_x, chunk_id_y)][row][col] != 0

        if row == 0 and direction == "top":
            if (new_id := (chunk_id_x, chunk_id_y - 1)) in self.chunks:
                return self.chunks[new_id][self.chunk_size-1][col] != 0
        elif row == self.chunk_size - 1 and direction == "bottom":
            if (new_id := (chunk_id_x, chunk_id_y + 1)) in self.chunks:
                return self.chunks[new_id][0][col] != 0
        elif col == 0 and direction == "left":
            if (new_id := (chunk_id_x - 1, chunk_id_y)) in self.chunks:
                return self.chunks[new_id][row][self.chunk_size - 1] != 0
        elif col == self.chunk_size - 1 and direction == "right":
            if (new_id := (chunk_id_x + 1, chunk_id_y)) in self.chunks:
                return self.chunks[new_id][row][0] != 0

    def translate_chunk(self, id_: tuple[int, int], special_key: str = None) -> list[Object2d]:
        chunk_w, chunk_h = self.chunk_size * self.tile_size.x, self.chunk_size * self.tile_size.y
        translated = []
        matrix = self.chunks[id_]
        if special_key == "menu":
            id_ = 0, 0
        for r, row in enumerate(matrix):
            for c, col in enumerate(row):
                if col != 0:
                    translated.append(
                        self.translate[col](self,
                                            id_[0] * chunk_w + c * self.tile_size.x,
                                            id_[1] * chunk_h + r * self.tile_size.y)
                    )
        return translated

    def get_current_chunk(self, pos: vec):
        return (floor(pos.x / (self.chunk_size * self.tile_size.x)),
                floor(pos.y / (self.chunk_size * self.tile_size.y)))

    def get_current_chunk_objects(self, chunk_id_x: int, chunk_id_y: int) -> (list[Object2d], bool):
        if self.menu and chunk_id_x == 0 and chunk_id_y == 0:
            return self.generated_chunks["menu"], False

        if (id_ := (chunk_id_x, chunk_id_y)) in self.generated_chunks:
            return self.generated_chunks[id_], False
        else:
            return self.generate_new_chunk(id_), True

    def generate_new_chunk(self, id_) -> list[Object2d]:
        if id_ == "menu":
            output = self.translate_chunk(id_, special_key="menu")
        else:
            if id_ not in self.chunks:
                if self.menu:
                    self.chunks[id_] = copy(self.menu_map_gen)
                else:
                    # TODO: add a generation algorithm
                    self.chunks[id_] = copy(self.grid)
            output = self.translate_chunk(id_)
        self.generated_chunks[id_] = output
        return output
