import pygame as pg
from .objects import Text, Button


class LeaderBoard:

    def __init__(self, app):
        self.app = app
        self.w, self.h = self.app.screen.get_size()
        self.running = True

        title_font = pg.font.Font("assets/fonts/DISTROB_.ttf", 55)
        self.button_font = pg.font.Font("assets/fonts/DISTROB_.ttf", 35)
        self.board_font = pg.font.Font("assets/fonts/DISTRO__.ttf", 20)

        quit_text = Text((0, 0), self.button_font, "Quit", pg.Color(255, 255, 255), shadow_=(2, 2))
        refresh_text = Text((0, 0), self.button_font, "Refresh", pg.Color(255, 255, 255), shadow_=(2, 2))

        self.leader_board = self.app.leader_board
        self.ui_objects = [
            Text((self.w // 2, self.h / 10), title_font, "Leaderboard", pg.Color(255, 255, 255), shadow_=(2, 2),
                 centered=True),
            Button((self.w // 2 - self.w / 12, self.h * 9 / 10), (self.w / 6 - 20, self.h / 10), quit_text,
                   click_func=self.quit, exec_type="up", normal_color=pg.Color(255, 205, 60),
                   border_radius=(8, 8, 8, 8), shadow=(5, 5), centered=True),
            Button((self.w // 2 + self.w / 12, self.h * 9 / 10), (self.w / 6 - 20, self.h / 10), refresh_text,
                   click_func=self.refresh, exec_type="up", normal_color=pg.Color(255, 205, 60),
                   border_radius=(8, 8, 8, 8), shadow=(5, 5), centered=True)
        ]

        self.data_length = 1

    def text_template(self, dx, dy, txt):
        return Text((dx, dy), self.board_font, txt, pg.Color(255, 255, 255), shadow_=(2, 2))

    def input_text(self, last_frame) -> str:
        running = True
        black_layer = pg.Surface(last_frame.get_size())
        black_layer.set_alpha(128)
        font = pg.font.Font("assets/fonts/DISTRO__.ttf", 30)
        info = font.render("Type your username.", True, (0, 0, 0))
        info2 = font.render("Press ENTER to confirm and ESCAPE to cancel.", True, (0, 0, 0))
        txt = ""

        while running:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit

                if event.type == pg.KEYDOWN:
                    output = event.unicode
                    if event.key == 13:
                        return txt
                    elif event.key == pg.K_ESCAPE:
                        running = False
                    elif event.key == pg.K_BACKSPACE:
                        if len(txt) > 0:
                            txt = txt[:-1]
                    elif output != "_":
                        txt += output

            self.app.screen.blit(last_frame, (0, 0))
            self.app.screen.blit(black_layer, (0, 0))
            pg.draw.rect(self.app.screen, (255, 205, 60), [self.w // 2 - self.w // 4,
                                                           self.h // 2 - self.h // 4,
                                                           self.w // 2,
                                                           self.h // 2],
                         border_radius=8)
            txt_render = self.button_font.render(txt, True, (255, 255, 255))
            self.app.screen.blit(txt_render, txt_render.get_rect(center=(self.w // 2, self.h // 2 + 25)))
            self.app.screen.blit(info, info.get_rect(center=(self.w // 2, int(self.h // 2 - self.h * 1.5 / 9))))
            self.app.screen.blit(info2, info2.get_rect(center=(self.w // 2, self.h // 2 - self.h // 10)))

            if pg.time.get_ticks() // 900 % 2 == 0:
                if txt == "":
                    pg.draw.rect(self.app.screen, (255, 255, 255), [self.w // 2, self.h // 2 + 25 - 20, 2, 40])
                else:
                    pg.draw.rect(self.app.screen, (255, 255, 255), [self.w // 2 + txt_render.get_width() // 2, self.h // 2 + 25 - 20, 2, 40])

            pg.display.update()

        return ""

    def generate_board(self):
        if self.app.client is None or self.app.leader_board is None:
            return [
                Text((self.w // 2, self.h // 2), self.board_font, "An error occurred when loading the leaderboard.",
                     pg.Color(255, 0, 0), centered=True, shadow_=(2, 2))
            ]

        texts = []
        h = self.h - self.h * 2 / 10 - 50
        board = self.app.leader_board
        dy = self.h * 2 / 10 + 25

        for i in range(7):
            if i > len(board) - 1:
                user_name, score = "...", "..."
            else:
                user_name, score = board[i]
            texts.append(self.text_template(self.w // 6, dy, str(i + 1)+"."))
            texts.append(self.text_template(self.w // 6 + 50, dy, user_name))
            texts.append(self.text_template(self.w * 8 / 10, dy, str(score)))
            dy += h / 10

        if self.app.get_rank(self.app.client_name) != -1:
            texts.append(self.text_template(self.w // 6, dy, str(self.app.get_rank(self.app.client_name)+1)+"."))
            texts.append(self.text_template(self.w // 6 + 50, dy, self.app.client_name+" (You)"))
            texts.append(self.text_template(self.w * 8 / 10, dy, str(self.leader_board[self.app.get_rank(self.app.client_name)][1])))
        else:
            texts.append(self.text_template(self.w // 6, dy, "You are unranked."))

        self.data_length = len(texts)

        return texts

    def quit(self):
        self.running = False

    def refresh(self):
        if self.app.client is not None:
            self.app.get_leaderboard()
            self.leader_board = self.app.leader_board
            if len(self.ui_objects) > 3:
                self.ui_objects = self.ui_objects[:-self.data_length]
        else:
            self.ui_objects = self.ui_objects[:-1]
        self.ui_objects.extend(self.generate_board())

    def run(self, last_frame: pg.Surface):
        self.refresh()
        black_layer = pg.Surface(last_frame.get_size())
        black_layer.set_alpha(200)

        while self.running:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    raise SystemExit

                for ui_object in self.ui_objects:
                    ui_object.handle_events(event)

            self.app.screen.blit(last_frame, (0, 0))
            self.app.screen.blit(black_layer, (0, 0))
            self.leader_board = self.app.leader_board

            for ui_object in self.ui_objects:
                if hasattr(ui_object, "update"):
                    ui_object.update()
                ui_object.draw(self.app.screen)

            pg.display.update()
