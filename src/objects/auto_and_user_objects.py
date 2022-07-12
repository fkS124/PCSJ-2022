import pygame as pg
from typing import Any

from .dyn_and_stat_objects import DynamicObject


class AutonomousObject(DynamicObject):

    def __init__(self, app, pos):
        super(AutonomousObject, self).__init__(app, pos, pg.Surface((100, 100)))

        # Intended to be inherited and add an Animation system

    def behavior(self):
        pass

    def update(self):
        self.behavior()
        return super(AutonomousObject, self).update()


class UserObject(DynamicObject):

    """An object that the user can communicate with, using the bind function (and then the input of the user)

    ---------- Binds documentation -----------
    {
        "event": pg.event.Event,
        "func": callable,
        "button": int,
        "key": int,
        "args": tuple("var-[NAME OF THE VARIABLE]" or value)
    }

    Eg. of bind :

    self.bind(event="key-pressed", func=self.move, args="left", key=pg.K_LEFT)
        -> In this example, if the LEFT key is pressed (continuously), it will call the method move,
           and pass the argument "left".
    self.bind(event="key", func=self.jump, args=(), key=pg.K_UP)
        -> In this example, if the UP key is pressed (once), it will call the method jump, and pass
           no argument.
    """

    def __init__(self, app, pos):
        super(UserObject, self).__init__(app, pos, pg.Surface((100, 100)))

        # Key Binding
        self._binds: list[dict[str: Any]] = []
        self._binds_p: list[dict[str: Any]] = []
        self.listening = True  # if it's set to False, then it will stop applying the controls

    def reset_binds(self):
        self._binds = []
        self._binds_p = []

    def logic(self):
        pass

    def update(self):
        pressing = {
            "key": pg.key.get_pressed(),
            "mouse": pg.key.get_pressed()
        }

        for bind in self._binds_p:
            if not self.listening:
                break

            if isinstance(bind["args"], tuple) and pressing[bind["type"]][bind["key"]]:
                bind["func"](*bind["args"])
            elif pressing[bind["type"]][bind["key"]]:
                bind["func"](bind["args"])

        upd = super(UserObject, self).update()
        self.logic()
        return upd

    def bind(self,
             event: str | int,
             func: callable,
             key: int = None,
             button: int = None,
             args: tuple | Any = None):
        if isinstance(event, str):
            bind = {"type": "key" if "key" in event else "mouse",
                    "func": func}
            destination_list = self._binds_p
        else:
            bind = {"event": event,
                    "func": func}
            destination_list = self._binds
        for kwarg, value in {"key": key, "button": button, "args": args}.items():
            if value is not None:
                bind[kwarg] = value
        destination_list.append(bind)

    def controls(self, event: pg.event.Event):
        for bind in self._binds:
            if event.type == bind["event"]:
                args = ()
                arguments_iteration = True
                if "args" in bind:
                    if isinstance(bind["args"], tuple):
                        args = (value if "var-" not in value else getattr(self, value.split("-")[-1])
                                for value in bind["args"])
                        arguments_iteration = True
                    else:
                        args = bind["args"]
                        arguments_iteration = False

                if "button" in bind:
                    sub_event = "button"
                elif "key" in bind:
                    sub_event = "key"
                else:
                    if arguments_iteration:
                        bind["func"](*args)
                    else:
                        bind["func"](args)
                    break

                if getattr(event, sub_event) == bind[sub_event]:
                    if arguments_iteration:
                        bind["func"](*args)
                    else:
                        bind["func"](args)
                    break

    def handle_events(self, event: pg.event.Event):
        if self.listening:
            self.controls(event)
