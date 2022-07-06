import pygame as pg

from threading import Thread
from .game import Game
from math import floor


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


class App:
    def __init__(self) -> None:
        if not pg.get_init():
            pg.init()

        self.screen = pg.display.set_mode((1400, 860), pg.SCALED, vsync=True)
        self.running = True
        self.game: Game | None = None

        # special running functions (intended for debugging purposes)
        self.special_args = {"wasd": self.preset_wasd, "WASD": self.preset_wasd,
                             "zqsd": self.preset_zqsd, "ZQSD": self.preset_zqsd,
                             None: self.preset_wasd}

        # framerate
        self.clock = pg.time.Clock()
        self.FPS = 60
        self.dt = 0

    @staticmethod
    def quit_():
        pg.quit()
        raise SystemExit

    def preset_wasd(self):
        self.game.player.KEYS["Left"] = pg.K_a
        self.game.player.KEYS["Right"] = pg.K_d
        self.game.player.KEYS["Jump"] = pg.K_w
        self.game.player.KEYS["Dash"] = pg.K_LSHIFT

    def preset_zqsd(self):
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
                rect2 = rendered.get_rect(topleft=(rect.bottomleft+pg.Vector2(2, 50 + dy)))
                self.screen.blit(rendered, rect2)
                if not item:
                    break
                dy += rendered.get_height() + 10

            pg.display.update()
            self.clock.tick(self.FPS)

    def run(self, special_arg=None):
        self.loading_screen()

        if special_arg in self.special_args:
            self.special_args[special_arg]()
            self.game.init_ui_menu()

        self.game.objects[0].do_binding()

        while self.running:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit_()

                self.game.handle_events(event)

            self.game.routine()
            pg.display.set_caption(f"{self.clock.get_fps()}")
            pg.display.update()
            self.dt = self.clock.tick(self.FPS) / 1000
