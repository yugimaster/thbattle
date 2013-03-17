# -*- coding: utf-8 -*-

import pyglet
from pyglet.media import Player
from .base.interp import InterpDesc, LinearInterp

from utils import instantiate


@instantiate
class SoundManager(object):
    volume = InterpDesc('_volume')  # 实际音量 
    def __init__(self):
        self.cur_bgm = None
        self.bgm_next = None
        self.bgm_switching = False
        self.bgm_player = Player()
        self.bgm_volume = 1.0  # BGM音量
        self.bgm_player.eos_action = Player.EOS_LOOP
        self.muted = False

    def switch_bgm(self, bgm):
        if self.muted:
            self.bgm_next = bgm
            return

        if not self.cur_bgm:
            self.instant_switch_bgm(bgm)
            return

        if bgm is self.cur_bgm:
            return 

        self.volume = LinearInterp(1.0, 0.0, 1.0)

        self.bgm_next = bgm
        if not self.bgm_switching:
            self.bgm_switching = True
            pyglet.clock.schedule_interval(self._set_vol, 0.1)
            pyglet.clock.schedule_once(self._bgm_fade_out_done, 1.0)

    def _bgm_fade_out_done(self, _=None):
        pyglet.clock.unschedule(self._set_vol)
        self.bgm_player.next()
        self.bgm_player.queue(self.bgm_next())
        self.volume = 1.0
        self._set_vol()
        self.bgm_player.play()
        self.bgm_switching = False
        self.cur_bgm = self.bgm_next
        self.bgm_next = None

    def instant_switch_bgm(self, bgm):
        pyglet.clock.unschedule(self._bgm_fade_out_done)
        self.bgm_next = bgm
        if not self.muted:
            self._bgm_fade_out_done()

    def mute(self):
        self.muted = True
        self.volume = 0.0
        self.bgm_player.pause()
        pyglet.clock.unschedule(self._set_vol)
        pyglet.clock.unschedule(self._bgm_fade_out_done)
        self.bgm_next = self.cur_bgm
        self.cur_bgm = None

    def unmute(self):
        self.muted = False
        self.bgm_next and self.instant_switch_bgm(self.bgm_next)

    def play(self, snd):
        snd.play()

    def set_volume(self, vol):
        self.bgm_volume = vol
        self._set_vol()

    def _set_vol(self, _=None):
        self.bgm_player.volume = self.volume * self.bgm_volume
