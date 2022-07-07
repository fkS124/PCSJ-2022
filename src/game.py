import pygame as pg
from typing import Callable
from pygame.gfxdraw import aapolygon, filled_polygon
from .objects import (
    DynamicObject,
    StaticObject,
    Object2d,
    AutonomousObject,
    UserObject,
    vec,
    Player,
    Text,
    UiObject,
    create_bg_text,
    obj_type,
    Title
)
from .map import Map, TileSprite


def reversed_dir(direction: str | None):
    return {"up": "down",
            "left": "right",
            "right": "left",
            "down": "up",
            "top": "bottom",
            "bottom": "top"}[direction]


def polygon(display: pg.Surface, color, points: list[vec, ...] | tuple[vec, ...]):
    filled_polygon(display, points, color)
    aapolygon(display, points, color)


def load(path: str):
    return pg.image.load(path).convert()


def resize(w, h, img: pg.Surface):
    return pg.transform.smoothscale(img, (w, h))


def scale(img: pg.Surface, k: float):
    return resize(img.get_width() * k, img.get_height() * k, img)


def draw_star(pos, size, angle):
    output_pos = pg.Surface((size, size), pg.SRCALPHA)


def change(color: tuple[int, ...] | pg.Color, degree: float) -> pg.Color:
    new_color = [color[0] * degree, color[1] * degree, color[2] * degree]
    for idx, col in enumerate(new_color):
        if col > 255:
            new_color[idx] = 255
        elif col < 0:
            new_color[idx] = 0
    return pg.Color(new_color)


class Game:

    # the collision tolerance is a multiplier that permits to predict collisions way before they happen
    # WARNING : may cause problems with really high velocities

    def __init__(self, app, loading_thread):
        # DISPLAY --------------------------
        self.screen: pg.Surface = app.screen
        self.app = app
        loading_thread.loaded["Display"] = True

        # OBJECTS --------------------------
        self.objects: list[Object2d | Player] = [Player(app, (0, 0))]
        self.player = self.objects[0]
        self.drawing_objects: list[obj_type] = [self.player]
        loading_thread.loaded["Objects"] = True

        # COLLISION ------------------------
        self.collider_objects: list[StaticObject] = []
        self.collision_rects: list[pg.Rect] = []

        # MAP ------------------------------
        self.map = Map(app)
        self.player.rect.topleft = (530, 650)
        menu_objects = self.map.generate_menu()
        for menu_object in menu_objects:
            self.add_object(menu_object)
        self.game_mode = "menu"  # "destruct", "menu"
        loading_thread.loaded["Map"] = True

        # SCRAP ----------------------------
        self.texts = []

        # CAMERA ---------------------------
        self.scroll = vec(0, 0)
        self.camera_free = False
        self.camera_limits: pg.Rect | None = None
        self.camera_fixed = False
        self.camera_following = True
        self.camera_following_object: pg.Rect = self.player.rect
        self.camera_looking_at: vec = vec(0, 0)
        self.cam_dxy: vec = vec(0, 0)
        self.camera_vel: float = 5.0
        self.camera_fixed_y: None | int = None
        self.camera_fixed_x: None | int = None
        self.game_camera_looking_at = 0
        self.game_camera_scroll: float = 3
        loading_thread.loaded["Camera"] = True

        # BACKGROUND ------------------------
        self.all_bg_sprites = []
        self.all_bg_rects = []
        self.rotations = []
        self.types = []
        self.init_background("night")
        loading_thread.loaded["Background"] = True

        # UI OBJECTS -------------------------
        self.ui_objects: list[UiObject] = []
        self.init_ui_menu()
        self.beacons: dict[str, list[TileSprite, Title, bool]] = {}
        self.beacons_funcs: dict[str, Callable] = {
            "Play": self.start_game,
            "Settings": self.start_settings,
            "Quit": self._quit
        }
        loading_thread.loaded["UI"] = True

    def start_game(self):
        self.player.rect.topleft = (400, 400)
        self.game_camera_looking_at = self.player.rect.centerx
        self.game_mode = "normal"
        self.reset_object_lists()
        self.map.quit_menu()
        self.map.init_game()

    def reset_object_lists(self):
        self.objects = [self.player]
        self.collider_objects = []
        self.ui_objects = []
        self.drawing_objects = []
        self.collision_rects = []

    def go_back_to_menu(self):
        self.reset_object_lists()
        menu_objects = self.map.generate_menu()
        for menu_object in menu_objects:
            self.add_object(menu_object)
        self.init_ui_menu()
        self.game_mode = "menu"
        self.player.rect.center = (530, 650)

    def start_settings(self):
        pass

    def _quit(self):
        self.app.quit_()

    def get_scroll(self) -> vec:
        if self.game_mode == "menu":
            self.camera_fixed_y = 440
            looking_point = vec(self.camera_following_object.center)
            self.camera_free = False
        else:
            self.camera_free = False
            self.camera_fixed_y = 730
            looking_point = vec(self.game_camera_looking_at, self.camera_fixed_y)
            self.game_camera_looking_at += self.game_camera_scroll * self.app.dt * self.app.FPS

        if self.camera_fixed:
            self.camera_looking_at = looking_point
        elif self.camera_following:
            if (distance := looking_point.distance_to(self.camera_looking_at)) > 5:
                self.cam_dxy = ((looking_point - self.camera_looking_at).normalize() *
                                self.camera_vel * distance / 100) * self.app.dt * self.app.FPS
                if self.camera_limits is None:
                    self.camera_looking_at += self.cam_dxy
                else:
                    self.camera_looking_at.x += self.cam_dxy.x if self.camera_limits.collidepoint(
                        tuple(self.camera_looking_at + vec(self.cam_dxy.x, 0))) else 0
                    self.camera_looking_at.y += self.cam_dxy.y if self.camera_limits.collidepoint(
                        tuple(self.camera_looking_at + vec(0, self.cam_dxy.y))) else 0
            else:
                self.cam_dxy = vec(0, 0)

        if self.camera_fixed_x is not None:
            self.camera_looking_at.x = self.camera_fixed_x
        if self.camera_fixed_y is not None:
            self.camera_looking_at.y = self.camera_fixed_y

        return -self.camera_looking_at + (1 / 2) * vec(self.screen.get_size())

    def init_ui_menu(self):
        fonts = {
            "normal": pg.font.Font("assets/fonts/DISTRO__.ttf", 30),
            "bold": pg.font.Font("assets/fonts/DISTROB_.ttf", 35),
            "title_bold": pg.font.Font("assets/fonts/DISTROB_.ttf", 50)
        }
        texts = [[(250, 340), "Controls", "bold"],
                 [(200, 400), f"Go left: {pg.key.name(self.player.KEYS['Left']).capitalize()}"],
                 [(200, 440), f"Go right: {pg.key.name(self.player.KEYS['Right']).capitalize()}"],
                 [(200, 480), f"Jump: {pg.key.name(self.player.KEYS['Jump']).capitalize()}"],
                 [(200, 520), f"Dash: {pg.key.name(self.player.KEYS['Dash']).capitalize()}"],
                 [(800, 440), "Go this way ->", "bold"],
                 [(-12200, 340), "Looking for the easter egg huh ?", "bold"],
                 [(-20000, 340), "Really determined aren't you ?", "bold"],
                 [(-28000, 340), "Your determination will pay off...", "bold"]]
        # TODO: place the easter egg around x=-35000
        titles = [[(1520, 440), "Play", "title_bold"],
                  [(1800, 440), "Settings", "title_bold"],
                  [(2150, 440), "Quit", "title_bold"]]

        self.beacons = {}
        self.ui_objects = []
        for data in texts:
            if len(data) < 3:
                font = fonts["normal"]
            else:
                font = fonts[data[-1]]
            self.ui_objects.append(create_bg_text(data[0], font, data[1], pg.Color(255, 255, 255), shadow_=(2, 2)))
        for pos, title, font_id in titles:
            font = fonts[font_id]
            self.ui_objects.append(Title(
                pos, font, title, color=pg.Color(255, 255, 255), big_scale=1.5, scaling_delay=120, shadow_=(3, 3)
            ))

        tags = ["Play", "Settings", "Quit"]
        all_beacons = [obj for obj in self.objects if hasattr(obj, "tag") and obj.tag == "beacon"]
        self.beacons = {dat[0]: [dat[1], self.ui_objects[9+idx], False] for idx, dat in enumerate(zip(tags, all_beacons))}

    def collision_algorithm(self, moving_object: DynamicObject):
        vel = moving_object.vel
        rect = moving_object.rect.copy()
        moving_object.jumping = True
        if moving_object.custom_collider != [0, 0, 0, 0]:
            rect.topleft += vec(moving_object.custom_collider[:2])
            rect.size = moving_object.custom_collider[2:]
        n_rect = rect.move(vel)
        for c_rect, collider in self.collision_rects:
            if collider.DONT_COLLIDE:
                continue
            if not (n_rect.top < c_rect.bottom - 1 and n_rect.bottom > c_rect.top + 1):
                continue
            if vel.x > 0:
                if abs(c_rect.left - n_rect.right) <= vel.x:
                    moving_object.vel.x = c_rect.left - rect.right
                    break
            elif vel.x < 0:
                if abs(c_rect.right - n_rect.left) <= - vel.x:
                    moving_object.vel.x = c_rect.right - rect.left
                    break
            else:
                break

        vel = moving_object.vel
        n_rect = rect.move(vel)
        for c_rect, collider in self.collision_rects:
            if collider.DONT_COLLIDE:
                continue
            if not (n_rect.left < c_rect.right and n_rect.right > c_rect.left):
                continue
            if vel.y >= 0:
                if abs(c_rect.top - n_rect.bottom) <= vel.y and not moving_object.gravity < 0:
                    moving_object.vel.y = c_rect.top - rect.bottom
                    moving_object.gravity = 0
                    moving_object.jumping = False
                    if self.game_mode == "destruct" and hasattr(collider, "kill"):
                        if hasattr(collider, "unbreakable") and not collider.unbreakable:
                            collider.kill()
                    break
            elif vel.y < 0:
                if abs(c_rect.bottom - n_rect.top) <= - vel.y:
                    moving_object.vel.y = c_rect.bottom - rect.top
                    if moving_object.jumping:
                        moving_object.gravity = 0
                break

    def add_object(self, object_: Object2d):
        # every time you add an object to the game, add it with this method
        self.objects.append(object_)
        if isinstance(object_, StaticObject) and not isinstance(object_, DynamicObject):
            self.collider_objects.append(object_)

    def handle_events(self, event: pg.event.Event):
        # handle events for every object in the game
        for object_ in self.objects:
            object_.handle_events(event)

        if event.type == pg.KEYDOWN:
            if event.key == 13:
                for key, beacon in self.beacons.items():
                    if beacon[0].pressed:
                        self.beacons_funcs[key]()
            elif event.key == pg.K_ESCAPE:
                self.go_back_to_menu()

    def draw_perspective(self):
        vanishing_point = vec(self.camera_looking_at)
        length3d = 10
        reference = self.player.rect.center if self.game_mode == "menu" else (self.game_camera_looking_at, self.camera_fixed_y)

        pg.draw.circle(self.screen, (255, 0, 0), reference+self.scroll, 2)
        keys = {"menu": lambda x: (x.rect.y, vec(x.rect.center).distance_to(vec(reference))),
                "normal": lambda x: (vec(x.rect.center).distance_to(vec(reference))),
                "default": lambda x: (vec(x.rect.center).distance_to(vec(reference))),
                }

        for object_ in sorted(self.drawing_objects,
                              key=(keys[self.game_mode] if self.game_mode in keys else keys["default"]),
                              reverse=True):
            if not pg.Rect(object_.rect.topleft + self.scroll, object_.rect.size).colliderect(
                    pg.Rect(-100, -100, self.screen.get_width() + 200, self.screen.get_height() + 200)) \
                    or object_.DONT_DRAW_PERSPECTIVE:
                continue

            pos = vec(object_.rect.topleft) + self.scroll
            w, h = object_.rect.w, object_.rect.h
            color = object_.surface.get_at((5, 0))

            vector = vanishing_point - pos + self.scroll
            cond = vector[0] > w/2, vector[1] > h/2
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
                'left': object_.get_color('left'),
                'right': object_.get_color('right'),
                'top': object_.get_color('top'),
                'bottom': object_.get_color('bottom')}

            conditions = {'left': vector[0] < 0,
                          'right': vector[0] > 0,
                          'top': vector[1] < 0,
                          'bottom': vector[1] > 0}

            for i in range(0, 2):
                if (not self.map.has_neighbour(way[i], object_) or object_ == self.player) and conditions[way[i]]:
                    polygon(self.screen, colors[way[i]], (pos, pos + point[way[-i+1]],
                            pos + point[way[-i+1]] + vectors[way[-i+1]], pos + vector))

    def init_background(self, theme: str):
        pass
        print(self.screen)
        if theme == "night":
            star = scale(load("assets/sprites/only_star_1.png"), 0.1)
            moon = scale(load("assets/sprites/only_moon_1.png"), 0.1)

    def draw_background(self):
        self.screen.fill((111, 93, 231))

        for ui_object in self.ui_objects:
            if ui_object.IN_BACKGROUND:
                ui_object.draw(self.screen, offset=pg.Vector2(0, 0) if ui_object.FIXED else self.scroll)

    def kill_player(self):
        self.go_back_to_menu()

    def routine(self):
        # print(self.player.rect.center)
        # update all the color animations (they're global, so that all the sprites have the same
        self.map.sprite_loader.calculate_color_animations()

        # update the scroll value (for camera)
        self.draw_background()

        font = pg.font.Font("assets/fonts/Consolas.ttf", 40)
        self.scroll = self.get_scroll()
        self.texts = []

        if self.game_mode != "menu":
            # DO HERE ALL THE CHECKING OF GAME STATES
            screen_rect = self.screen.get_rect(center=(self.game_camera_looking_at, self.camera_fixed_y))
            screen_rect.topleft -= vec(300, 0)
            screen_rect.size += vec(600, 0)

            if not self.player.rect.colliderect(screen_rect):
                # PLAYER DIES -> go back to menu -> TODO: put a death screen
                self.kill_player()

        # get collision rects for this frame
        self.collision_rects = [
            (pg.Rect(
                collider.rect[0] + collider.custom_collider[0] * (cond := (collider.custom_collider != [0, 0, 0, 0])),
                collider.rect[1] + collider.custom_collider[1] * cond,
                collider.custom_collider[2] if cond else collider.rect[2],
                collider.custom_collider[3] if cond else collider.rect[3]), collider) for collider in
            self.collider_objects]

        self.drawing_objects = [self.player]
        if self.game_mode == "menu":
            current_chunk = self.map.get_current_chunk(vec(self.player.rect.topleft))
        else:
            current_chunk = self.map.get_current_chunk(vec(self.game_camera_looking_at, self.camera_fixed_y))
        translations = [(0, 0), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (-1, 1), (0, -1), (1, -1)]
        if self.map.menu:
            if current_chunk == (0, 0):
                self.drawing_objects.extend(self.map.generated_chunks["menu"])
                translations = [(-1, 0), (1, 0)]
            else:
                translations = [(0, 0), (-1, 0), (1, 0)]
        elif self.map.horizontal_only:
            translations = [(0, 0), (-1, 0), (1, 0)]
        elif self.map.vertical_only:
            translations = [(0, 0), (0, -1), (0, 1)]
        for translation in translations:
            working_chunk = self.map.get_current_chunk_objects(current_chunk[0] + translation[0],
                                                               current_chunk[1] + translation[1])
            if working_chunk[1]:
                for obj in working_chunk[0]:
                    self.add_object(obj)
            self.drawing_objects.extend(working_chunk[0])

        if self.game_mode == "menu":
            for key, beacon in self.beacons.items():
                print(beacon)
                beacon[0].pressed = self.player.rect.colliderect(beacon[0].button_rect)
                if (new_val := beacon[0].pressed) != beacon[2]:
                    output = beacon[1].start_scaling() if new_val else beacon[1].start_descaling()
                    if output:
                        self.beacons[key][2] = new_val

        # update all objects
        to_remove = []
        for object_ in self.objects:
            upd = object_.update()
            if hasattr(object_, "tag") and object_.tag == "spike":
                if self.map.collide_spike_player(self.player, object_):
                    self.kill_player()

            if upd == "kill":
                to_remove.append((object_, self.map.get_chunk(vec(object_.rect.center))))
            elif object_.ABSOLUTE_DRAW:  # draw the objects that are not included in the map
                self.drawing_objects.append(object_)
            elif object_.DONT_DRAW and object_ in self.drawing_objects:
                self.drawing_objects.remove(object_)

        for obj, chunk in to_remove:
            self.objects.remove(obj)
            if chunk in self.map.generated_chunks and obj in self.map.generated_chunks[chunk]:
                self.map.chunks[chunk][(idx := self.map.get_index_from_co(vec(obj.rect.topleft))[:2])[0]][
                    idx[1]] = 0
                self.map.generated_chunks[chunk].remove(obj)
            if obj in self.collider_objects:
                self.collider_objects.remove(obj)

        # draw perspective
        self.draw_perspective()

        # draw all see able objects
        for object_ in self.drawing_objects:
            object_.draw(self.screen, self.scroll)

        for ui_object in self.ui_objects:
            if not ui_object.IN_BACKGROUND:
                ui_object.draw(self.screen, offset=pg.Vector2(0, 0) if ui_object.FIXED else self.scroll)

        """ DEBUG -------------------------------------------
        for chunk in self.map.chunks:
            self.texts.append(
                (rendering := font.render(f"{chunk}", True, (0, 255, 0)),
                 rendering.get_rect(topleft=(chunk[0] * self.map.chunk_size * self.map.tile_size.x,
                                             chunk[1] * self.map.chunk_size * self.map.tile_size.y)))
            )
            pg.draw.rect(self.screen, (0, 255, 0),
                         [chunk[0] * self.map.chunk_size * self.map.tile_size.x + self.scroll.x,
                          chunk[1] * self.map.chunk_size * self.map.tile_size.y + self.scroll.y,
                          self.map.chunk_size * self.map.tile_size.x,
                          self.map.chunk_size * self.map.tile_size.y], 1)

        for txt, rct in self.texts:
            self.screen.blit(txt, rct.topleft + self.scroll)

        
            rect = object_.rect.copy()
            if hasattr(object_, "custom_collider"):
                rect.topleft += vec(object_.custom_collider[:2])
                if object_.custom_collider != [0, 0, 0, 0]:
                    rect.size = object_.custom_collider[2:]
            pg.draw.rect(self.screen, (255, 0, 0), rect, 1)

        for rect in self.collision_rects:
            pg.draw.rect(self.screen, (0, 255, 0), rect, 1)
        """
