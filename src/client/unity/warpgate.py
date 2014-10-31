# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

from utils.misc import instantiate

'''
Emits:
    ['user_input', trans -> InputTransaction, ilet -> Inputlet, complete -> function]
    ['game_event', evt_name -> str, arg -> object]  // Game.emit_event
    ['system_event', evt_name -> str, args -> tuple]  // See Executive
'''


class ExecutiveWrapper(object):
    def __init__(self, executive, warpgate):
        self.executive = executive
        self.warpgate = warpgate

    def __getattr__(self, k):
        return getattr(self.executive, k)

    def __setattr__(self, k, v):
        setattr(self.executive, k)

    def connect_server(self, addr):
        self.executive.connect_server(addr, self.warpgate.queue_system_event)


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
        import gevent
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
                self.events.append(("tick",))

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
        pass

    def queue_system_event(self, evt_name, *args):
        self.events.append(('system_event', evt_name, args))
