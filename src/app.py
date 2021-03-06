import pygame as pg

from threading import Thread
from .game import Game
from .objects import vec
from .settings import SettingsMenu
from .leaderboard import LeaderBoard

import scoreunlocked


class LoadingThread(Thread):

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        self.loaded = {"Display": False,
                       "Objects": False,
                       "Map": False,
                       "Camera": False,
                       "Background": False,
                       "UI": False}
        self.exception = None

    def run(self) -> None:
        try:
            self.instance.game = Game(self.instance, self)
        except Exception as e:
            self.exception = e


class PostingThread(Thread):

    def __init__(self, app, name, score):
        super(PostingThread, self).__init__()
        self.client = app.client
        self.client_name = name
        self.score = score
        self.app = app

    def run(self) -> None:
        self.client.connect("fks124", self.app.ldb_key)
        self.client.post_score(name=self.client_name, score=self.score)
        self.app.leader_board_menu.refresh()


class App:
    def __init__(self) -> None:
        if not pg.get_init():
            pg.mixer.pre_init()
            pg.init()
            pg.mixer.init()

        self.window_flags = pg.SCALED

        self.window_size = 1200, 700

        self.vsync = True
        if len(size := pg.display.get_desktop_sizes()) == 1:
            w, h = size[0]
            if w < self.window_size[0] or h < self.window_size[1]:
                self.window_flags = pg.SCALED | pg.FULLSCREEN

        self.screen = pg.display.set_mode(self.window_size, self.window_flags, vsync=self.vsync)
        pg.display.set_caption("Cube's hidden dimensions")
        pg.display.set_icon(pg.image.load("assets/sprites/icon.png"))
    
        self.running = True
        self.game: Game | None = None

        # special running functions (intended for debugging purposes)
        self.special_args = {"wasd": self.preset_wasd, "WASD": self.preset_wasd,
                             "zqsd": self.preset_zqsd, "ZQSD": self.preset_zqsd,
                             None: self.preset_wasd}

        self.key_preset = "Arrow Keys"
        self.settings_menu = None
        self.leader_board_menu = None

        # frame rate
        self.clock = pg.time.Clock()
        self.FPS = 60
        self.dt = 0

        self.play_sound = True
        self.play_music = True

        try:
            self.client = scoreunlocked.Client()
        except:
            self.client = None

        self.ldb_key = 'cubes-hidden-dimensions'
        self.client_name = ''
        self.leader_board = ''

        self.connect("")

    @staticmethod
    def quit_():
        pg.quit()
        raise SystemExit

    def connect(self, user_name):
        if self.client is not None:
            self.client.connect('fks124', self.ldb_key)
            self.leader_board = self.client.get_leaderboard()

        if self.client is not None and user_name != '':
            self.client_name = user_name

    def post_score(self, score: int):
        if self.client is not None and self.client_name != "":
            PostingThread(self, self.client_name, score).start()

    def get_leaderboard(self):
        if self.client is not None:
            self.leader_board = sorted(ldb, key=lambda x: -x[1]) \
                if isinstance(ldb := self.client.get_leaderboard(), list) else None

    def get_rank(self, user_name) -> int:
        ldb = self.leader_board
        for idx, rank in enumerate(ldb):
            if rank[0] == user_name:
                return idx
        return -1

    def preset_wasd(self):
        self.key_preset = "WASD"
        self.game.player.KEYS["Left"] = pg.K_a
        self.game.player.KEYS["Right"] = pg.K_d
        self.game.player.KEYS["Jump"] = pg.K_w
        self.game.player.KEYS["Dash"] = pg.K_LSHIFT

    def preset_zqsd(self):
        self.key_preset = "ZQSD"
        self.game.player.KEYS["Left"] = pg.K_q
        self.game.player.KEYS["Right"] = pg.K_d
        self.game.player.KEYS["Jump"] = pg.K_z
        self.game.player.KEYS["Dash"] = pg.K_LSHIFT

    def loading_screen(self):

        thread = LoadingThread(self)
        thread.start()

        title_font = pg.font.Font("assets/fonts/RedPixel.otf", 150)
        title = title_font.render("Cubic Engine", True, (0, 255, 0))
        title_rect = title.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//3))

        font = pg.font.Font("assets/fonts/Consolas.ttf", 25)
        rect = pg.Rect(0, 0, self.screen.get_width() * 2 / 3, 50)
        rect.center = self.screen.get_width() // 2, self.screen.get_height() // 2
        last_sum = 0
        progression = 0
        dx = 0.1

        while progression < len(thread.loaded):

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit_()

            self.screen.fill((0, 0, 0))
            n_dots = (pg.time.get_ticks() // 500 % 3) + 1

            self.screen.blit(title, title_rect)

            pg.draw.rect(self.screen, (0, 255, 0), rect, 3)
            pg.draw.rect(self.screen, (0, 255, 0), [rect.topleft,
                                                    (progression*rect.w/len(thread.loaded), rect.h)])
            if (new_sum := sum(thread.loaded.values())) != last_sum:
                progression += dx
                if progression > new_sum:
                    last_sum = new_sum
                    progression = last_sum

            dy = 0
            for idx, val in enumerate(thread.loaded.items()):
                key, item = val
                output = f"{key}: {'Loaded' if item and progression > idx else 'Loading'+('.'*n_dots)}"
                color = (255, 255, 255) if not item and progression <= idx else (0, 255, 0)
                if thread.exception is not None and not item:
                    output = f"{key}: ERROR -> {thread.exception}"
                    color = (255, 0, 0)
                rendered = font.render(output, True, color)
                rect2 = rendered.get_rect(topleft=(vec(rect.bottomleft)+pg.Vector2(2, 50 + dy)))
                self.screen.blit(rendered, rect2)
                if not item:
                    break
                dy += rendered.get_height() + 10

            pg.display.update()
            self.clock.tick(self.FPS)

    def settings(self):
        self.settings_menu.run(self.screen.copy())

    def run(self, special_arg=None):
        self.loading_screen()

        if special_arg in self.special_args:
            self.special_args[special_arg]()
            self.game.init_ui_menu()

        self.game.objects[0].do_binding()
        self.settings_menu = SettingsMenu(self)
        self.leader_board_menu = LeaderBoard(self)

        while self.running:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    print(self.get_leaderboard())
                    self.quit_()

                self.game.handle_events(event)

            self.game.routine()
            pg.display.update()
            self.dt = self.clock.tick(self.FPS) / 1000
