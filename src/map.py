import pygame as pg
from copy import copy
from math import floor
from random import choice
from .dimensions import NormalDimension
from .objects import StaticObject, vec, Object2d, Monster, Canon


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

    @staticmethod
    def resize(w, h, img: pg.Surface):
        return pg.transform.smoothscale(img, (w, h))

    @staticmethod
    def load(path: str):
        return pg.image.load(path).convert()


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
            self.button_rect = pg.Rect(self.rect.x, self.rect.y - 50, self.rect.w, 50)
        elif tag == "spike":
            self.DONT_COLLIDE = True
            self.surface = pg.Surface(size, pg.SRCALPHA)
            self.color = (255, 0, 0)
            pg.draw.polygon(self.surface, self.color, ((0, self.surface.get_height()),
                                                       (self.surface.get_width(), self.surface.get_height()),
                                                       (
                                                       self.surface.get_width() / 2, self.surface.get_height() * 0.13)))
        elif tag == "color":
            self.surface.fill(self.color)

        self.dying = False
        self.death_time = 0

        self.mask = pg.mask.from_surface(self.surface)

    def kill(self):
        if not self.dying:
            self.dying = True
            self.death_time = pg.time.get_ticks()
            
    def update(self) -> None | str:
        if self.tag == "beacon":
            if self.pressed:
                new_color = darker(self.color, 80)
                self.surface.fill((new_color[0], new_color[1], 0))
            else:
                self.surface.fill(self.color)

        if self.dying:
            if pg.time.get_ticks() - self.death_time > 500:
                return "kill"

        return super().update()

class Map:

    ignore_neighbour = [0, 4]
    g = 10
    s = 11
    b = 12
    m = "monster"
    c = 13

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
                    [0, 0, 0, 0, 0, 0, 0, 0, s, 0, 0, 0, 0, 0, 0, 0, 0, 0, s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, s, 0, 0, 0, m, 0, 0, 0, 0, 0, s, c, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g, g]]
    dimensions = {
        "normal": NormalDimension
    }

    def __init__(self, app):

        self.screen = app.screen
        self.horizontal_only = True
        self.vertical_only = False
        self.app = app
        self.tile_size = vec(80, 80)
        self.sprite_loader = SpriteLoader(app, self.tile_size.x, self.tile_size.y)
        self.chunk_size = vec(15, 11)

        self.translate = {
            # 3: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "star", self.sprite_loader)),
            # 2: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "moon", self.sprite_loader)),
            # 1: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "color", self.sprite_loader)),
            4: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "spike", self.sprite_loader,
                                              unbreakable=True)),
            3: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "color", self.sprite_loader,
                                              unbreakable=True)),
            2: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "animated_color", self.sprite_loader,
                                              color_anim="white-red")),
            1: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "animated_color", self.sprite_loader,
                                              color_anim="white-red")),
            10: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "grass", self.sprite_loader)),
            11: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "stone", self.sprite_loader)),
            12: (lambda map_, x, y: TileSprite(vec(x, y), map_.tile_size, "beacon", self.sprite_loader,
                                               color=pg.Color(150, 150, 0))),
            13: (lambda map_, x, y: Canon(map_.app, vec(x, y)))
        }

        self.chunks: dict[tuple[int, int], list[list[int, ...]], ...] = {
            (0, 0): copy(self.dimensions["normal"].empty_preset),
            "menu": copy(self.menu_map)
        }
        self.presets: dict[tuple[int, int], str] = {
            (0, 0): "empty_preset"
        }
        self.generated_chunks = {}
        self.menu = False

    @staticmethod
    def collide_spike_player(player, spike: TileSprite):
        x_offset = spike.rect.x - player.rect.x
        y_offset = spike.rect.y - player.rect.y
        pl_mask = player.mask
        sp_mask = spike.mask
        return pl_mask.overlap(sp_mask, (x_offset, y_offset)) is not None

    def generate_menu(self):
        self.chunks = {
            "menu": copy(self.menu_map),
            (0, 0): copy(self.dimensions["normal"].empty_preset)
        }
        self.presets: dict[tuple[int, int], str] = {
            (0, 0): "empty_preset"
        }
        self.generated_chunks = {}

        self.menu = True
        self.chunk_size = vec(32, 11)
        return self.generate_new_chunk("menu")

    def quit_menu(self):
        self.chunks = {
            "menu": copy(self.menu_map),
            (0, 0): copy(self.dimensions["normal"].empty_preset)
        }
        self.presets: dict[tuple[int, int], str] = {
            (0, 0): "empty_preset"
        }
        self.generated_chunks = {}
        self.menu = False
        self.chunk_size = vec(34, 15)

    def get_index_from_co(self, pos: vec):
        chunk_id = floor(pos.x / (self.chunk_size.x * self.tile_size.x)), \
                   floor(pos.y / (self.chunk_size.y * self.tile_size.y))
        col = floor(((pos.x - chunk_id[0] * self.tile_size.x * self.chunk_size.x) / self.tile_size.x))
        row = floor(((pos.y - chunk_id[1] * self.tile_size.y * self.chunk_size.y) / self.tile_size.y))
        return row, col, chunk_id[0], chunk_id[1]

    def get_chunk(self, pos: vec):
        return (floor(pos.x / (self.chunk_size.x * self.tile_size.x)),
                floor(pos.y / (self.chunk_size.y * self.tile_size.y)))

    def init_game(self):
        # self.generate_new_chunk((0, 0))
        pass

    def has_neighbour(self, direction: str, obj):

        translate = {'left': (0, -1), 'right': (0, 1), 'top': (-1, 0), 'bottom': (1, 0)}
        row, col, chunk_id_x, chunk_id_y = self.get_index_from_co(vec(obj.rect.topleft))

        if self.menu:
            row += translate[direction][0]
            col += translate[direction][1]
            if 0 <= row < len(self.menu_map) and 0 <= col < len(self.menu_map[1]):
                return self.menu_map[row][col] not in self.ignore_neighbour
            else:
                return False if row != len(self.menu_map)-1 else True
        else:
            if (chunk_id_x, chunk_id_y) not in self.chunks:
                return False

        if row == 0 and direction == "top":
            if self.horizontal_only:
                return False
            if (new_id := (chunk_id_x, chunk_id_y - 1)) in self.chunks:
                return self.chunks[new_id][int(self.chunk_size.y-1)][col] not in self.ignore_neighbour
        elif row == self.chunk_size.y - 1 and direction == "bottom":
            if self.horizontal_only:
                return False
            if (new_id := (chunk_id_x, chunk_id_y + 1)) in self.chunks:
                return self.chunks[new_id][0][col] not in self.ignore_neighbour
        elif col == 0 and direction == "left":
            if self.vertical_only:
                return False
            if (new_id := (chunk_id_x - 1, chunk_id_y)) in self.chunks:
                return self.chunks[new_id][row][int(self.chunk_size.x - 1)] not in self.ignore_neighbour
        elif col == self.chunk_size.x - 1 and direction == "right":
            if self.vertical_only:
                return False
            if (new_id := (chunk_id_x + 1, chunk_id_y)) in self.chunks:
                return self.chunks[new_id][row][0]  not in self.ignore_neighbour

        if 0 < row + translate[direction][0] < self.chunk_size.y and 0 < col + translate[direction][1] < self.chunk_size.x:
            row += translate[direction][0]
            col += translate[direction][1]
            return self.chunks[(chunk_id_x, chunk_id_y)][row][col] not in self.ignore_neighbour

    def translate_chunk(self, id_: tuple[int, int], special_key: str = None) -> list[Object2d]:
        chunk_w, chunk_h = self.chunk_size.x * self.tile_size.x, self.chunk_size.y * self.tile_size.y
        translated = []
        matrix = self.chunks[id_]
        if special_key == "menu":
            id_ = 0, 0
        for r, row in enumerate(matrix):
            for c, col in enumerate(row):
                if col == "monster":
                    self.app.game.add_object(
                        Monster(self.app, (id_[0] * chunk_w + c * self.tile_size.x,
                                           id_[1] * chunk_h + r * self.tile_size.y), self.tile_size)
                    )
                elif col != 0:
                    translated.append(
                        self.translate[col](self,
                                            id_[0] * chunk_w + c * self.tile_size.x,
                                            id_[1] * chunk_h + r * self.tile_size.y)
                    )
        return translated

    def get_current_chunk(self, pos: vec):
        return (floor(pos.x / (self.chunk_size.x * self.tile_size.x)),
                floor(pos.y / (self.chunk_size.y * self.tile_size.y)))

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
            if self.horizontal_only and id_[1] != 0:
                return []
            elif self.vertical_only and id_[0] != 0:
                return []

            if id_ not in self.chunks:
                if self.menu:
                    self.chunks[id_] = copy(self.menu_map_gen)
                else:
                    dimension = self.dimensions[self.app.game.game_mode]
                    if self.horizontal_only:
                        last_preset = self.presets.get((id_[0]-1, id_[1]))
                        chosen_preset = choice(dimension.following[last_preset])
                        self.chunks[id_] = getattr(dimension, chosen_preset)
                        self.presets[id_] = chosen_preset
            output = self.translate_chunk(id_)
        self.generated_chunks[id_] = output
        return output
