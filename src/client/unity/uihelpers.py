# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from gevent.event import Event

# -- own --
from game.autoenv import EventHandler


# -- code --
class UnityUIEventHook(EventHandler):
    def __init__(self, warpgate):
        EventHandler.__init__(self)
        self.warpgate = warpgate

    def evt_user_input(self, evt, arg):
        trans, ilet = arg
        evt = Event()
        self.warpgate.events.append(('user_input', trans, ilet, evt.set))
        evt.wait()
        return ilet

    def handle(self, evt, data):
        self.warpgate.events.append(('game_event', evt, data))
