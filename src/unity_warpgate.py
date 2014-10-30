# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

import gevent  # noqa
import gevent.hub  # noqa
import gevent.event  # noqa
import gevent.lock  # noqa

from utils.misc import instantiate

'''
Commands:
    call_executive(func_name, *args_for_executive_func)
    complete_input(Inputlet)

Emits:
    ['user_input', trans -> InputTransaction, ilet -> Inputlet]
    ['game_event', evt_name -> str, arg -> object]  // Game.emit_event
    ['system_event', evt_name -> str, args -> tuple]  // See Executive
'''


@instantiate
class Warpgate(object):

    def init(self, peer):
        import options
        from UnityEngine import Debug

        L = lambda s: Debug.Log("PyWrap: " + s)
        L("init")

        self.peer = peer
        self._exit = False
        self.commands = []

        # should set them
        options.no_update
        options.no_crashreport
        options.show_hidden_mode
        options.debug_console

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

        import threading
        logic = threading.Thread(target=self.run)
        logic.start()

    def run(self):
        # Temp, for debug
        try:
            self._run()
        except:
            import traceback
            from UnityEngine import Debug
            Debug.Log(traceback.format_exc())

    def _run(self):
        from game import autoenv
        autoenv.init('Client')

        import gevent
        from gevent.hub import get_hub

        hub = get_hub()
        self.noti = noti = hub.loop.async()

        import options
        if options.debug_console:
            from gevent.backdoor import BackdoorServer
            bds = BackdoorServer(('127.0.0.1', 12345))
            gr_bds = gevent.spawn(bds.serve_forever)

        from UnityEngine import Debug
        import options

        L = lambda s: Debug.Log("PyWrap: " + s)
        L("begin loop")
        try:
            while True:
                hub.wait(noti)
                if self._exit:
                    L("RedSwitch pulled down, closing WarpGate")
                    return

        except:
            if not options.no_crashreport:
                from crashreport import do_crashreport_unity
                do_crashreport_unity()

            raise

        finally:
            if options.debug_console:
                gr_bds.kill()
                bds.close()

    def redswitch(self):
        self._exit = True
        self.noti.send()

    def command(self, cmd, *args):
        self.commands.append((cmd, args))
        self.noti.send()
