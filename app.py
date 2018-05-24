import sys
import logging

import owa
import pyweb

logging.StreamHandler(stream=sys.stdout)


if __name__ == '__main__':
    app = pyweb.WSGIApplication()
    app.add_module(owa)
    app.run()