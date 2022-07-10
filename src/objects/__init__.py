from .object2d import Object2d, vec
from .dyn_and_stat_objects import DynamicObject, StaticObject
from .auto_and_user_objects import UserObject, AutonomousObject
from .player import Player
from .monster import Monster, Canon, Bullet
from .ui import UiObject, Button, Text, create_bg_text, Title, BlackLayer
from .particles import Particle


obj_type = Object2d | DynamicObject | StaticObject | Player
