import sys

import owa
import pyweb

if __name__ == '__main__':
    app = pyweb.WSGIApplication()
    app.add_module(owa)
    app.run()