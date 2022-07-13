import pygame as pg

from .auto_and_user_objects import UserObject
from .dyn_and_stat_objects import StaticObject

vec = pg.math.Vector2


class Trail(StaticObject):

    ABSOLUTE_DRAW = True

    def __init__(self, pos, size, color, duration):
        super(Trail, self).__init__(pos, pg.Surface(size))
        self.surface.fill(color)
        self.begin_time = pg.time.get_ticks()
        self.duration = duration

    def update(self):
        if pg.time.get_ticks() - self.begin_time > self.duration:
            return "kill"
        self.surface.set_alpha(255-255*(pg.time.get_ticks()-self.begin_time)/self.duration)


class Player(UserObject):

    KEYS = {
        "Left": pg.K_LEFT,
        "Right": pg.K_RIGHT,
        "Jump": pg.K_UP,
        "Dash": pg.K_LSHIFT
    }
    
    def __init__(self, app, pos):
        super().__init__(app, pos)

        # Velocity management
        self.base_vel = 10
        self.directions = {"left": vec(-1, 0), "right": vec(1, 0)}
        self.direction = "right"

        # Dash
        self.dashing = False
        self.dash_available = True
        self.dash_duration = 100  # ms
        self.dash_countdown = 400  # ms
        self.dash_vel = vec(0, 0)
        self.dash_base_vel = 15
        self.dash_time = 0
        self.length_trail = 350  # ms
        self.dash_last_frames = []
        self.delay_frames = 20
        self.last_frame = 0

        # jump
        self.jumping = True
        self.gravity = 0
        self.d_gravity = 1

        # Custom collider settings (still to be determined)
        # self.set_custom_collider([10, 10, 80, 80])

        self.surface = pg.Surface((80, 80))
        self.rect = self.surface.get_rect(center=self.rect.center)
        self.color = (255, 205, 60)
        self.dead = False

        self.mask = pg.mask.from_surface(self.surface)

        self.dash_sound = pg.mixer.Sound("assets/sounds/SON_DASH.mp3")
        self.dash_sound.set_volume(0.20)

        self.jump_sound = pg.mixer.Sound("assets/sounds/SON_JUMP.mp3")
        self.jump_sound.set_volume(0.25)

        self.pg_chad = pg.image.load("assets/sprites/PG_CHAD.png").convert()
        self.pg_chad_alpha = pg.image.load("assets/sprites/PG_CHAD.png").convert_alpha()
        self.pg_chad_alpha = pg.transform.smoothscale(self.pg_chad_alpha, (80, 80))
        self.pg_chad = pg.transform.smoothscale(self.pg_chad, (80, 80))
        self.chad = False

    def do_binding(self):
        self.reset_binds()
        self.bind(event="key-pressed", func=self.move, args="left", key=self.KEYS["Left"])
        self.bind(event="key-pressed", func=self.move, args="right", key=self.KEYS["Right"])
        self.bind(event="key", func=self.jump, args=(), key=self.KEYS["Jump"])
        self.bind(event="key", func=self.dash, args=(), key=self.KEYS["Dash"])
        self.bind(event="key", func=self.jump, args=(), key=pg.K_SPACE)

    def logic(self):
        self.DONT_DRAW = self.dead
        self.DONT_DRAW_PERSPECTIVE = self.dead

        if self.app.game.map.get_environment(self) == "neon":
            if not self.chad:
                self.surface.fill((0, 0, 0))
            else:
                self.surface = self.pg_chad_alpha
            self.d_gravity = -1
        elif self.app.game.map.get_environment(self) == "moon":
            self.d_gravity = 0.5
            if self.chad:
                self.surface = self.pg_chad
        else:
            if self.chad:
                self.surface = self.pg_chad
            else:
                self.surface.fill(self.color)
            self.d_gravity = 1

        if self.jumping:
            self.vel.y = self.gravity
            self.gravity += self.d_gravity * 60 / self.app.clock.get_fps()
        if self.dashing:
            if pg.time.get_ticks() - self.last_frame > self.delay_frames:
                self.app.game.add_object(Trail(self.rect.topleft, self.rect.size, self.surface.get_at((0, 0)),
                                               self.length_trail))
                self.last_frame = pg.time.get_ticks()
            self.vel += self.dash_vel
            if pg.time.get_ticks() - self.dash_time > self.dash_duration:
                self.dashing = False

        if not self.dash_available:
            if pg.time.get_ticks() - self.dash_time > self.dash_countdown:
                self.dash_available = True

    def jump(self):
        if not self.jumping and not self.dead:
            if self.app.play_sound:
                self.jump_sound.play()
                self.jump_sound.fadeout(300)
            self.jumping = True
            self.gravity = - 24 if self.app.game.map.get_environment(self) != "neon" else 24

    def dash(self):
        if self.dash_available and not self.dead:
            if self.app.play_sound:
                self.dash_sound.play()
            self.dash_vel = self.directions[self.direction] * self.dash_base_vel
            self.dash_available = False
            self.dashing = True
            self.dash_time = pg.time.get_ticks()

    def move(self, direction: str):
        self.vel += self.directions[direction] * self.base_vel * (not self.dead)
        self.direction = direction
