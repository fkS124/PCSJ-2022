import pygame as pg
from typing import Callable
from pygame.gfxdraw import filled_polygon, aapolygon
from .objects import (
    DynamicObject,
    StaticObject,
    Object2d,
    AutonomousObject,
    UserObject,
    vec,
    Player,
    Text,
    Button,
    UiObject,
    BlackLayer,
    create_bg_text,
    obj_type,
    Title,
    Particle,
    Monster
)
from .background import Background, NormalBackground, MoonBackground
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


def neon_polygon(display: pg.Surface, color, points: list[vec, ...] | tuple[vec, ...]):
    filled_polygon(display, points, (0, 0, 0))
    aapolygon(display, points, (255, 255, 255))


def load(path: str):
    return pg.image.load(path).convert()


def load_a(path: str):
    return pg.image.load(path).convert_alpha()


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
        self.monsters: list[Monster] = []
        self.player = self.objects[0]
        self.drawing_objects = [self.player]
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
        self.backgrounds: dict[str, Background] = {
            "menu": NormalBackground(),
            "normal": NormalBackground(),
            "moon": MoonBackground()
        }
        loading_thread.loaded["Background"] = True

        # UI OBJECTS -------------------------
        self.ui_objects: list[UiObject] = []
        self.init_ui_menu()
        self.beacons: dict[str, list[TileSprite | Title | bool]] = {}
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
        self.monsters = []
        self.collider_objects = []
        self.ui_objects = []
        self.drawing_objects = []
        self.collision_rects = []

    def go_back_to_menu(self):
        self.player.dead = False
        self.reset_object_lists()
        menu_objects = self.map.generate_menu()
        for menu_object in menu_objects:
            self.add_object(menu_object)
        self.init_ui_menu()
        self.game_mode = "menu"
        self.player.rect.center = (530, 650)

    def start_settings(self):
        self.app.settings()

    def _quit(self):
        self.app.quit_()

    def get_scroll(self) -> vec:
        if self.game_mode == "menu":
            self.camera_fixed_y = 440
            looking_point = vec(self.camera_following_object.center)
            self.camera_free = False
        else:
            looking_point = vec(self.player.rect.center)
            if looking_point.y > 760:
                looking_point.y = 760
            self.camera_fixed_y = None
            self.camera_fixed_x = None

        if self.camera_fixed:
            self.camera_looking_at = looking_point
        elif self.camera_following:
            if (distance := looking_point.distance_to(self.camera_looking_at)) > 5:
                self.cam_dxy = ((looking_point - self.camera_looking_at).normalize() *
                                self.camera_vel * distance / 100) * 60 / self.app.clock.get_fps()
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
        fonts = {"normal": pg.font.Font("assets/fonts/DISTRO__.ttf", 30),
                 "bold": pg.font.Font("assets/fonts/DISTROB_.ttf", 35),
                 "title_bold": pg.font.Font("assets/fonts/DISTROB_.ttf", 50)}
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
            font = fonts["normal"] if len(data) < 3 else fonts[data[-1]]
            self.ui_objects.append(create_bg_text(data[0], font, data[1], pg.Color(255, 255, 255), shadow_=(2, 2)))
        for pos, title, font_id in titles:
            self.ui_objects.append(Title(pos, fonts[font_id], title, color=pg.Color(255, 255, 255),
                                         big_scale=1.5, scaling_delay=120, shadow_=(3, 3)))

        all_beacons = [obj for obj in self.objects if hasattr(obj, "tag") and obj.tag == "beacon"]
        self.beacons = {dat[0]: [dat[1], self.ui_objects[9 + idx], False] for idx, dat in
                        enumerate(zip(["Play", "Settings", "Quit"], all_beacons))}

    def collision_algorithm(self, moving_object: DynamicObject):
        environment = self.map.get_environment(moving_object)
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

            if environment != "neon":
                if vel.y >= 0:
                    if abs(c_rect.top - n_rect.bottom) <= vel.y and moving_object.gravity > 0:
                        moving_object.vel.y = c_rect.top - rect.bottom
                        moving_object.gravity = 0
                        moving_object.jumping = False
                        break
                elif vel.y < 0:
                    if abs(c_rect.bottom - n_rect.top) <= - vel.y:
                        moving_object.vel.y = c_rect.bottom - rect.top
                        if moving_object.jumping:
                            moving_object.gravity = 0
            else:
                if vel.y > 0:
                    if abs(c_rect.top - n_rect.bottom) <= vel.y:
                        moving_object.vel.y = c_rect.top - rect.bottom
                        if moving_object.jumping:
                            moving_object.gravity = 0
                        break
                elif vel.y <= 0:
                    if abs(c_rect.bottom - n_rect.top) <= - vel.y and moving_object.gravity < 0:
                        moving_object.vel.y = c_rect.bottom - rect.top
                        moving_object.gravity = 0
                        moving_object.jumping = False

    def add_object(self, obj: Object2d):
        # every time you add an object to the game, add it with this method
        self.objects.append(obj)
        if isinstance(obj, StaticObject) and not isinstance(obj, DynamicObject):
            self.collider_objects.append(obj)
        elif isinstance(obj, Monster):
            self.monsters.append(obj)

    def handle_events(self, event: pg.event.Event):
        # handle events for every object in the game
        for obj in self.objects:
            obj.handle_events(event)

        for ui_object in self.ui_objects:
            ui_object.handle_events(event)

        if event.type == pg.KEYDOWN:
            if event.key == 13:
                if not self.player.dead:
                    for key, beacon in self.beacons.items():
                        if beacon[0].pressed:
                            self.beacons_funcs[key]()
                else:
                    self.go_back_to_menu()
            elif event.key == pg.K_ESCAPE:
                self.go_back_to_menu()

    def draw_perspective(self):
        vanishing_point = vec(self.screen.get_size()) / 2
        screen_rect = pg.Rect(-100, -100, self.screen.get_width() + 200, self.screen.get_height() + 200)

        self.drawing_objects.sort(key=lambda x: (x.rect.centery, abs(x.rect.centerx-self.player.rect.x)), reverse=True)
        if self.player in self.drawing_objects:
            self.drawing_objects.remove(self.player)
            self.drawing_objects.append(self.player)

        for obj in self.drawing_objects:
            if not obj.rect.move(self.scroll).colliderect(screen_rect) or obj.DONT_DRAW_PERSPECTIVE:
                continue

            length3d = obj.length3d if hasattr(obj, "length3d") else 10

            if hasattr(obj, "tag") and obj.tag == "spike":
                func = polygon if not (hasattr(obj, "style") and obj.style == "neon") else neon_polygon

                pos_left = vec(obj.rect.topleft) + vec(0, obj.surface.get_height()) + self.scroll
                pos_right = vec(obj.rect.topleft) + vec(obj.surface.get_width(), obj.surface.get_height()) + self.scroll
                pos_top = vec(obj.rect.topleft) + vec(obj.surface.get_width() / 2,
                                                      obj.surface.get_height() * 0.13) + self.scroll
                color = obj.color

                vector_left = (vanishing_point - pos_left) / length3d
                vector_right = (vanishing_point - pos_right) / length3d
                vector_top = (vanishing_point - pos_top) / length3d
                vectors = [vector_left, vector_right, vector_top]

                if vector_left[0] > 0 > vector_left[1] and -1.7 < vector_left[1] / vector_left[0] < 0:
                    func(self.screen, change(color, 0.8),
                         (pos_right, pos_right + vector_right, pos_top + vector_top, pos_top))
                    continue
                if vector_right[0] < 0 < vector_right[1] / vector_right[0] < 1.7 and vector_left[1] < 0:
                    func(self.screen, change(color, 0.5),
                         (pos_left, pos_left + vector_left, pos_top + vector_top, pos_top))
                    continue

                if vector_top[1] > 0 and (
                        vector_top[1] / vector_top[0] > 1.7 if vector_top[0] > 0 else vector_top[1] / vector_top[
                            0] < -1.7):
                    func(self.screen, change(color, 0.75),
                         (pos_left, pos_left + vector_left, pos_right + vector_right, pos_right))
                    continue

                vectors = sorted(vectors, key=lambda x: x[0] ** 2 + x[1] ** 2)

                if vectors[0] == vector_left:
                    func(self.screen, change(color, 0.75),
                         (pos_left, pos_left + vector_left, pos_right + vector_right, pos_right))
                    func(self.screen, change(color, 0.5),
                         (pos_left, pos_left + vector_left, pos_top + vector_top, pos_top))
                elif vectors[0] == vector_right:
                    func(self.screen, change(color, 0.75),
                         (pos_left, pos_left + vector_left, pos_right + vector_right, pos_right))
                    func(self.screen, change(color, 0.8),
                         (pos_right, pos_right + vector_right, pos_top + vector_top, pos_top))
                else:
                    func(self.screen, change(color, 0.8),
                         (pos_right, pos_right + vector_right, pos_top + vector_top, pos_top))
                    func(self.screen, change(color, 0.5),
                         (pos_left, pos_left + vector_left, pos_top + vector_top, pos_top))
            else:
                func = neon_polygon if (hasattr(obj, "style") and obj.style == "neon") or \
                                       (self.map.get_environment(self.player) == "neon") else polygon

                pos = vec(obj.rect.topleft) + self.scroll
                w, h = obj.rect.w, obj.rect.h

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
                    'left': obj.get_color('left'),
                    'right': obj.get_color('right'),
                    'top': obj.get_color('top'),
                    'bottom': obj.get_color('bottom')}

                conditions = {'left': vector[0] < 0,
                              'right': vector[0] > 0,
                              'top': vector[1] < 0,
                              'bottom': vector[1] > 0}

                for i in range(0, 2):
                    if (not self.map.has_neighbour(way[i], obj) or obj == self.player) and conditions[way[i]]:
                        func(self.screen, colors[way[i]], (pos, pos + point[way[-i + 1]],
                                                           pos + point[way[-i + 1]] + vectors[way[-i + 1]],
                                                           pos + vector))

    def draw_background(self):
        environment = self.map.get_environment(self.player)
        transition = self.map.get_transition(self.player)

        if environment == "normal":
            self.screen.fill((135, 206, 235))
        elif environment == "transition_to_moon":
            self.screen.fill((135 + (19 - 135) * transition[1], 206 + (17 - 206) * transition[1],
                              235 + (53 - 235) * transition[1]))
        elif environment == "moon":
            self.screen.fill((29, 17, 53))
        elif environment == "transition_to_neon":
            self.screen.fill((29 - 29 * transition[1], 17 - 17 * transition[1], 53 - 53 * transition[1]))
        elif environment == "transition_to_normal":
            self.screen.fill((135 * transition[1], 206 * transition[1], 235 * transition[1]))

        if "transition" in environment:
            match environment:
                case "transition_to_moon":
                    environment = "normal"
                case "transition_to_neon":
                    environment = "moon"
                case "transition_to_normal":
                    environment = "normal"

        if environment in self.backgrounds:
            if transition[0] in ['none', 'transition_to_neon']:
                self.backgrounds[environment].draw(self.screen, self.cam_dxy)
            elif transition[0] == 'transition_to_normal':
                self.backgrounds[environment].draw(self.screen, self.cam_dxy,
                                                   offset=vec(-(1 - transition[1]) * self.screen.get_width() * 2.5, 0))
            elif transition[0] == 'transition_to_moon':
                self.backgrounds[environment].draw(self.screen, self.cam_dxy,
                                                   offset=vec(-transition[1] * self.screen.get_width() * 2.5, 0))

        for ui_object in self.ui_objects:
            if ui_object.IN_BACKGROUND:
                ui_object.draw(self.screen, offset=pg.Vector2(0, 0) if ui_object.FIXED else self.scroll)

        if self.map.get_environment(self.player) == "neon":
            self.screen.fill((0, 0, 0))

    def init_death_screen(self):
        fonts = pg.font.Font("assets/fonts/DISTROB_.ttf", 25), pg.font.Font("assets/fonts/DISTROB_.ttf", 80)
        self.ui_objects = []
        self.ui_objects.extend((BlackLayer((0, 0), self.screen.get_size()),
                                Text((self.screen.get_width()//2, int(self.screen.get_height()*3/7)-50),
                                     fonts[1], "You died !", pg.Color(255, 0, 0), shadow_=(2, 2), centered=True))),
        self.ui_objects[-1].FIXED = True
        self.ui_objects[-1].IN_BACKGROUND = False
        self.ui_objects.append(Text((self.screen.get_width()//2, int(self.screen.get_height()*3/7 + 50)),
                                    fonts[0], f"Your score : {-1}", pg.Color(255, 255, 255), centered=True))
        # TODO : put the real score
        self.ui_objects[-1].FIXED = True
        self.ui_objects[-1].IN_BACKGROUND = False
        self.ui_objects.append(Button(
            (self.screen.get_width() // 2 - 150, int(self.screen.get_height() // 2 + 50)),
            (300, 100), Text((0, 0), fonts[0], "Respawn (Enter)", pg.Color(255, 255, 255), shadow_=(2, 2)),
            click_func=self.go_back_to_menu, normal_color=pg.Color(255, 205, 60), hover_color=pg.Color(240, 190, 45),
            border_radius=(8, 8, 8, 8), shadow=(5, 5), exec_type="up"
        ))

    def kill_player(self):
        self.player.dead = True
        self.init_death_screen()

    def routine(self):
        self.screen = self.app.screen
        # self.game_mode = self.map.get_environment(self.player)
        # print(self.player.rect.center, self.player.vel.x)

        # update the scroll value (for camera)
        self.draw_background()

        # update the camera
        self.scroll = self.get_scroll()

        # get collision rects for this frame
        self.collision_rects = [
            (pg.Rect(
                collider.rect[0] + collider.custom_collider[0] * (cond := (collider.custom_collider != [0, 0, 0, 0])),
                collider.rect[1] + collider.custom_collider[1] * cond,
                collider.custom_collider[2] if cond else collider.rect[2],
                collider.custom_collider[3] if cond else collider.rect[3]), collider) for collider in
            self.collider_objects]

        self.drawing_objects = [self.player] if self.player in self.objects else []
        current_chunk = self.map.get_current_chunk(vec(self.player.rect.topleft))
        translations = [(0, 0), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (-1, 1), (0, -1), (1, -1)]
        if self.map.menu:
            self.drawing_objects.extend(self.map.generated_chunks["menu"])
            translations = [(-1, 0), (1, 0)]
            if current_chunk != (0, 0):
                translations.append((0, 0))
        elif self.map.horizontal_only:
            translations = [(0, 0), (1, 0), (-1, 0)]
        elif self.map.vertical_only:
            translations = [(0, 0), (0, -1), (0, 1)]
        for translation in translations:
            working_chunk = self.map.get_current_chunk_objects(current_chunk[0] + translation[0],
                                                               current_chunk[1] + translation[1])
            if working_chunk[1]:
                for obj in working_chunk[0]:
                    self.add_object(obj)
            self.drawing_objects.extend(working_chunk[0])

        # check for interaction with the beacons (interactive in-game buttons)
        if self.game_mode == "menu":
            for key, beacon in self.beacons.items():
                beacon[0].pressed = self.player.rect.colliderect(beacon[0].button_rect)
                if (new_val := beacon[0].pressed) != beacon[2]:
                    output = beacon[1].start_scaling() if new_val else beacon[1].start_descaling()
                    if output:
                        self.beacons[key][2] = new_val

        # update all objects
        to_remove = []

        # Update all objects, and add them to the draw
        for obj in self.objects:
            upd = obj.update()
            if hasattr(obj, "tag") and obj.tag == "spike":
                if self.map.collide_spike_player(self.player, obj):
                    self.kill_player()

            if upd == "kill":
                to_remove.append((obj, self.map.get_chunk(vec(obj.rect.center))))
            elif obj.ABSOLUTE_DRAW:  # draw the objects that are not included in the map
                self.drawing_objects.append(obj)
            elif obj.DONT_DRAW and obj in self.drawing_objects:
                self.drawing_objects.remove(obj)

        # Remove all the objects that have to be removed
        for obj, chunk in to_remove:
            if obj in self.objects:
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
        for obj in self.drawing_objects:
            if (hasattr(obj, "tag") and obj.tag == "neon") or self.map.get_environment(self.player) == "neon":
                if obj.tag != "spike":
                    neon_polygon(self.screen, obj.color, [
                        vec(obj.rect.topleft) + self.scroll,
                        vec(obj.rect.topright) + self.scroll,
                        vec(obj.rect.bottomright) + self.scroll,
                        vec(obj.rect.bottomleft) + self.scroll
                    ])
                else:
                    neon_polygon(self.screen, obj.color, [
                        vec(obj.rect.bottomleft) + self.scroll,
                        vec(obj.rect.bottomright) + self.scroll,
                        vec(obj.rect.x + obj.rect.w / 2, obj.rect.y + obj.rect.h * 0.13) + self.scroll
                    ])
            else:
                obj.draw(self.screen, self.scroll)

        # draw the UI (the UiObjects not contained in the Background)
        for ui_object in self.ui_objects:
            if not ui_object.IN_BACKGROUND:
                ui_object.draw(self.screen, offset=pg.Vector2(0, 0) if ui_object.FIXED else self.scroll)

        # DEATH CONDITIONS --------------------
        if self.player.rect.y > 1160 and not self.player.dead:
            self.kill_player()
        if not self.player.dead:
            for monster in self.monsters:
                if monster.rect.colliderect(self.player.rect):
                    self.kill_player()
