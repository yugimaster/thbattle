# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())


def unity_entry():
    import options

    options.no_update  # should set them
    options.no_crashreport
    options.show_hidden_mode

    options.freeplay = False

    if options.no_update:
        import autoupdate
        autoupdate.Autoupdate = autoupdate.DummyAutoupdate

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_os()
    monkey.patch_select()

    from game import autoenv
    autoenv.init('Client')

    from client.core.executive import Executive

    try:
        start_ui()
    except:
        if not options.no_crashreport:
            from crashreport import do_crashreport_unity
            do_crashreport_unity()

        raise  #
