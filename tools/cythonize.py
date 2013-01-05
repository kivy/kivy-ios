#!/usr/bin/env python

import sys
import subprocess

def do(fn):
    print 'cythonize:', fn
    parts = fn.split('/')
    assert(parts[-1].endswith('.pyx'))
    if parts[0] == '.':
        parts.pop(0)
    modname = parts[-1][:-4]
    package = '_'.join(parts[:-1])

    # cythonize
    subprocess.Popen(['cython', fn]).communicate()

    if not package:
        print 'no need to rewrite', fn
    else:
        # get the .c, and change the initXXX
        fn_c = fn[:-3] + 'c'
        with open(fn_c) as fd:
            data = fd.read()
        pat1 = 'init{}(void)'.format(modname)
        sub1 = 'init{}_{}(void)'.format(package, modname)
        pat2 = 'PyInit_{}(void)'.format(modname)
        sub2 = 'PyInit{}_{}(void)'.format(package, modname)
        pat3 = 'Pyx_NAMESTR("{}")'.format(modname)
        sub3 = 'Pyx_NAMESTR("{}_{}")'.format(package, modname)
        data = data.replace(pat1, sub1)
        data = data.replace(pat2, sub2)
        data = data.replace(pat3, sub3)

        print 'rewrite', fn_c
        with open(fn_c, 'w') as fd:
            fd.write(data)

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        do(fn)
