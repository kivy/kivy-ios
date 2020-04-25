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
    print('cythonize:', fn)
    assert(fn.endswith('.pyx'))
    parts = fn.split('/')
    if parts[0] == '.':
        parts.pop(0)
    modname = parts[-1][:-4]
    package = '_'.join(parts[:-1])

    # cythonize
    subprocess.Popen([cython, fn], env=os.environ).communicate()

    if not package:
        print('no need to rewrite', fn)
    else:
        # get the .c, and change the initXXX
        fn_c = fn[:-3] + 'c'
        with open(fn_c) as fd:
            data = fd.read()
        modname = modname.split('.')[-1]
        pac_mod = '{}_{}'.format(package, modname)
        fmts = ('init{}(void)', 'PyInit_{}(void)', 'Pyx_NAMESTR("{}")', '"{}",')
        for i, fmt in enumerate(fmts):
            pat = fmt.format(modname)
            sub = fmt.format(pac_mod)
            print('{}: {} -> {}'.format(i + 1, pat, sub))
            data = data.replace(pat, sub)
        print('rewrite', fn_c)
        with open(fn_c, 'w') as fd:
            fd.write(data)


if __name__ == '__main__':
    print('-- cythonize', sys.argv)
    resolve_cython()
    for fn in sys.argv[1:]:
        do(fn)
