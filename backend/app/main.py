import sys
import devnote.app.main as _real_main

sys.modules[__name__] = _real_main
