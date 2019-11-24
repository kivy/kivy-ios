"""
def __bootstrap__():
    global __bootstrap__, __loader__, __file__
    import sys, pkg_resources, imp
    __file__ = pkg_resources.resource_filename(__name__, '_sqlite3.cpython-37m-darwin.so')
    __loader__ = None; del __bootstrap__, __loader__
    print("demo")
    imp.load_dynamic(__name__,__file__)
__bootstrap__()
"""
