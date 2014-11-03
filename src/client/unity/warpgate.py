# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

import traceback

import gevent
import gevent.hub

from utils.misc import instantiate

'''
Emits:
    ['user_input', g -> Game, trans -> InputTransaction, ilet -> Inputlet, complete -> function]
    ['game_event', g -> Game, evt_name -> str, arg -> object]  // Game.emit_event
    ['system_event', evt_name -> str, args -> tuple]  // See Executive
'''


@gevent.hub.set_hub
@instantiate
class UnityHub(gevent.hub.Hub):

    def print_exception(self, context, type, value, tb):
        text = ''.join(traceback.format_exception(type, value, tb))
        del tb
        if context is not None:
            if not isinstance(context, str):
                try:
                    context = self.format_context(context)
                except:
                    text += 'Error formatting context\n' + traceback.format_exc()
                    context = repr(context)
            text += ('\n%s failed with %s\n\n' % (context, getattr(type, '__name__', 'exception'), ))

        try:
            from UnityEngine import Debug
            Debug.LogError(text)
        except:
            # fuck
            pass


class UnityLogStream(object):
    def write(self, data):
        from UnityEngine import Debug
        Debug.Log(data)

import logging
logging.basicConfig(stream=UnityLogStream())
logging.getLogger().setLevel(logging.ERROR)


class ExecutiveWrapper(object):
    def __init__(self, executive, warpgate):
        object.__setattr__(self, "executive", executive)
        object.__setattr__(self, "warpgate", warpgate)

    def __getattr__(self, k):
        return getattr(self.executive, k)

    def __setattr__(self, k, v):
        setattr(self.executive, k, v)

    def connect_server(self, host, port):
        from UnityEngine import Debug
        Debug.Log(repr((host, port)))

        @gevent.spawn
        def do():
            Q = self.warpgate.queue_system_event
            Q('connect', self.executive.connect_server((host, port), Q))

    def start_replay(self, rep):
        self.executive.start_replay(rep, self.warpgate.queue_system_event)

    def update(self):
        Q = self.warpgate.queue_system_event

        def update_cb(name, p):
            Q('update', name, p)

        @gevent.spawn
        def do():
            Q('result', self.executive.update(update_cb))


@instantiate
class Warpgate(object):

    def init(self):
        import options
        from UnityEngine import Debug

        L = lambda s: Debug.Log("PyWrap: " + s)
        L("init")

        self.events = []

        # should set them
        options.no_update
        options.no_crashreport
        options.show_hidden_mode

        options.freeplay = False

        if options.no_update:
            import autoupdate
            autoupdate.Autoupdate = autoupdate.DummyAutoupdate

        L("before gevent")
        from gevent import monkey
        monkey.patch_socket()
        monkey.patch_os()
        monkey.patch_select()
        L("after gevent")

        from game import autoenv
        autoenv.init('Client')

        # For debug
        @gevent.spawn
        def beat():
            while True:
                gevent.sleep(1)
                # self.events.append(("tick",))

        from client.core.executive import Executive
        self.executive = ExecutiveWrapper(Executive, self)

    def get_events(self):
        l = self.events
        self.events = []
        return l

    def start_backdoor(self):
        from gevent.backdoor import BackdoorServer
        import gevent
        self.bds = BackdoorServer(('127.0.0.1', 12345))
        self.gr_bds = gevent.spawn(self.bds.serve_forever)

    def stop_backdoor(self):
        self.gr_bds.kill()
        self.bds.close()

    def shutdown(self):
        from client.core.executive import Executive
        if Executive.state == 'connected':
            Executive.disconnect()

    def queue_system_event(self, evt_name, *args):
        self.events.append(('system_event', evt_name, args))
