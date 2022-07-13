import pygame as pg

from .objects import Button, Text, vec


def switch_on_off(button: Button, settings_instance):
    button.off = not button.off
    button.on = not button.on

    if button.on:
        button.colors = {
            "normal": pg.Color(0, 255, 0),
            "hover": pg.Color(0, 200, 0),
            "click": pg.Color(0, 200, 0)
        }
        button.texts["normal"].modify_content(
            button.texts["normal"].text[:-3] + "On"
        )

        if button.tag != "none":
            match button.tag:
                case "on_wasd":
                    if settings_instance.ui_objects[3].on:
                        switch_on_off(settings_instance.ui_objects[3], settings_instance)
                case "on_zqsd":
                    if settings_instance.ui_objects[2].on:
                        switch_on_off(settings_instance.ui_objects[2], settings_instance)

    else:
        button.colors = {
            "normal": pg.Color(255, 0, 0),
            "hover": pg.Color(200, 0, 0),
            "click": pg.Color(200, 0, 0)
        }
        button.texts["normal"].modify_content(
            button.texts["normal"].text[:-2] + "Off"
        )
    return button


class SettingsMenu:

    def __init__(self, app):
        self.app = app
        self.running = True
        self.w, self.h = self.app.screen.get_size()
        self.black_layer = pg.Surface(app.screen.get_size())
        self.black_layer.set_alpha(128)

        self.on_fullscreen = self.app.window_flags & pg.FULLSCREEN == pg.FULLSCREEN
        self.on_wasd = self.app.key_preset == "WASD"
        self.on_zqsd = self.app.key_preset == "ZQSD"
        self.on_arrows = self.app.key_preset == "Arrow Keys"

        title_font = pg.font.Font("assets/fonts/DISTROB_.ttf", 55)
        subtitles_font = pg.font.Font("assets/fonts/DISTRO__.ttf", 35)
        sub_subtitles_font = pg.font.Font("assets/fonts/DISTRO__.ttf", 20)
        self.ui_objects = [
            Text((self.w // 2, self.h / 10), title_font, "Settings", pg.Color(255, 255, 255), shadow_=(2, 2),
                 centered=True),
            Button((self.w // 2, self.h * 2 / 7), (500, self.h / 10), Text((0, 0), subtitles_font,
                   f"Fullscreen : {'On' if self.on_fullscreen else 'Off'}", pg.Color(255, 255, 255), shadow_=(2, 2)),
                   on=self.on_fullscreen, off=not self.on_fullscreen, click_func=switch_on_off, click_func_args=("self", self),
                   centered=True, shadow=(5, 5), border_radius=(8, 8, 8, 8), exec_type="up",
                   normal_color=pg.Color(255, 0, 0) if not self.on_fullscreen else pg.Color(0, 255, 0)),
            Button((self.w // 2, self.h * 3 / 7), (500, self.h / 10),
                   Text((0, 0), subtitles_font, f"WASD preset : {'On' if self.on_wasd else 'Off'}",
                        pg.Color(255, 255, 255), shadow_=(2, 2)),
                   on=self.on_wasd, off=not self.on_wasd, click_func=switch_on_off, click_func_args=("self", self),
                   centered=True, shadow=(5, 5), border_radius=(8, 8, 8, 8), exec_type="up", tag="on_wasd",
                   normal_color=pg.Color(255, 0, 0) if not self.on_wasd else pg.Color(0, 255, 0)),
            Button((self.w // 2, self.h * 4 / 7), (500, self.h / 10),
                   Text((0, 0), subtitles_font, f"ZQSD preset : {'On' if self.on_zqsd else 'Off'}",
                        pg.Color(255, 255, 255), shadow_=(2, 2)),
                   on=self.on_zqsd, off=not self.on_zqsd, click_func=switch_on_off, click_func_args=("self", self),
                   centered=True, shadow=(5, 5), border_radius=(8, 8, 8, 8), exec_type="up", tag="on_zqsd",
                   normal_color=pg.Color(255, 0, 0) if not self.on_zqsd else pg.Color(0, 255, 0)),
            Button((self.w // 2 - 130, self.h * 5 / 7), (240, self.h / 10), Text((0, 0), subtitles_font,
                   f"Sounds : {'On' if self.app.play_sound else 'Off'}", pg.Color(255, 255, 255), shadow_=(2, 2)),
                   on=self.app.play_sound, off=not self.app.play_sound, click_func=switch_on_off, click_func_args=("self", self),
                   centered=True, shadow=(5, 5), border_radius=(8, 8, 8, 8), exec_type="up", tag="on_arrows",
                   normal_color=pg.Color(255, 0, 0) if not self.app.play_sound else pg.Color(0, 255, 0)),
            Button((self.w // 2 + 130, self.h * 5 / 7), (240, self.h / 10), Text((0, 0), subtitles_font,
                                                                                 f"Music : {'On' if True else 'Off'}",
                                                                                 pg.Color(255, 255, 255), shadow_=(2, 2)),
                   on=self.app.play_music, off=not self.app.play_music, click_func=switch_on_off, click_func_args=("self", self),
                   centered=True, shadow=(5, 5), border_radius=(8, 8, 8, 8), exec_type="up", tag="on_arrows",
                   normal_color=pg.Color(255, 0, 0) if not self.app.play_music else pg.Color(0, 255, 0)),
            Button((self.w // 2, self.h * 6 / 7), (250, self.h / 12), Text((0, 0), subtitles_font,
                                                                           f"Quit Settings",
                                                                           pg.Color(255, 255, 255), shadow_=(2, 2)),
                   click_func=self.quit_settings, centered=True, shadow=(5, 5), normal_color=pg.Color(255, 205, 60),
                   hover_color=pg.Color(240, 190, 45), border_radius=(8, 8, 8, 8), exec_type="up"),
            Text((self.w // 2 + 480, self.h * 2 / 7), sub_subtitles_font,
                 "Warning : FULLSCREEN might not work properly.", pg.Color(255, 255, 255), shadow_=(2, 2),
                 centered=True),
        ]

    def quit_settings(self):
        self.running = False

        if self.on_fullscreen != self.ui_objects[1].on:
            self.on_fullscreen = self.ui_objects[1].on
            if self.on_fullscreen:
                self.app.window_flags = pg.FULLSCREEN
                self.app.screen = pg.display.set_mode((0, 0), self.app.window_flags, vsync=self.app.vsync)
            else:
                self.app.screen = pg.display.set_mode(self.app.window_size, vsync=self.app.vsync)
        match self.get_selected_preset():
            case "zqsd":
                self.app.preset_zqsd()
            case "wasd":
                self.app.preset_wasd()
        self.app.game.player.do_binding()
        self.app.game.init_ui_menu()

        self.app.play_sound = self.ui_objects[4].on
        self.app.play_music = self.ui_objects[5].on
        if not self.app.play_music:
            pg.mixer.music.unload()

    def get_selected_preset(self):
        buttons = self.ui_objects[2:4]
        for button in buttons:
            if button.on:
                return button.tag[3:]
        return buttons[0].tag[3:]

    def run(self, background: pg.Surface):
        self.running = True

        while self.running:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit

                for ui_object in self.ui_objects:
                    ui_object.handle_events(event)

            self.app.screen.fill((0, 0, 0))
            self.app.screen.blit(background, (0, 0))
            self.app.screen.blit(self.black_layer, (0, 0))

            buttons = self.ui_objects[2:4]
            for button in buttons:
                if button.on:
                    break
            else:
                switch_on_off(buttons[0], self)

            self.app.play_sound = self.ui_objects[4].on
            self.app.play_music = self.ui_objects[5].on

            if not self.app.play_music:
                pg.mixer.music.unload()
            elif not pg.mixer.music.get_busy():
                pg.mixer.music.load('assets/music/' + self.app.game.musics[0])
                pg.mixer.music.play()
                self.app.game.music_index = 1

            for ui_object in self.ui_objects:
                if hasattr(ui_object, "update"):
                    ui_object.update()
                if isinstance(ui_object, Button):
                    ui_object.draw(self.app.screen, play_sound=self.app.play_sound)
                else:
                    ui_object.draw(self.app.screen)

            pg.display.update()
