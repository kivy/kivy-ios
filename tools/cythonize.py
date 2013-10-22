#!/usr/bin/env python

import os
import sys
import subprocess

# resolve cython executable
cython = None

def resolve_cython():
    global cython
    for executable in ('cython', 'cython-2.7'):
        for path in os.environ['PATH'].split(':'):
            if not os.path.exists(path):
                continue
            if executable in os.listdir(path):
                cython = os.path.join(path, executable)
                return

def do(fn):
    print 'cythonize:', fn
    parts = fn.split('/')
    assert(parts[-1].endswith('.pyx'))
    if parts[0] == '.':
        parts.pop(0)
    modname = parts[-1][:-4]
    package = '_'.join(parts[:-1])

    # cythonize
    subprocess.Popen([cython, fn], env=os.environ).communicate()

    if not package:
        print 'no need to rewrite', fn
    else:
        # get the .c, and change the initXXX
        fn_c = fn[:-3] + 'c'
        with open(fn_c) as fd:
            data = fd.read()
        modname = modname.split('.')[-1]
        pat1 = 'init{}(void)'.format(modname)
        sub1 = 'init{}_{}(void)'.format(package, modname)
        pat2 = 'PyInit_{}(void)'.format(modname)
        sub2 = 'PyInit{}_{}(void)'.format(package, modname)
        pat3 = 'Pyx_NAMESTR("{}")'.format(modname)
        sub3 = 'Pyx_NAMESTR("{}_{}")'.format(package, modname)

        print '1: {} -> {}'.format(pat1, sub1)
        print '2: {} -> {}'.format(pat2, sub2)
        print '3: {} -> {}'.format(pat3, sub3)
        data = data.replace(pat1, sub1)
        data = data.replace(pat2, sub2)
        data = data.replace(pat3, sub3)

        print 'rewrite', fn_c
        with open(fn_c, 'w') as fd:
            fd.write(data)

if __name__ == '__main__':
    print '-- cythonize', sys.argv
    resolve_cython()
    for fn in sys.argv[1:]:
        do(fn)
