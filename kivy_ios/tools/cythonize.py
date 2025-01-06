#!/usr/bin/env python3

import sys
from Cython.Build.Cythonize import main as cythonize_main


def is_cplus(fn):
    # Check if there's the directive to compile as C++
    with open(fn) as fd:
        for line in fd:
            if line.startswith('# distutils: language = c++'):
                return True
    return False


def do(fn):
    print('cythonize:', fn)
    assert fn.endswith('.pyx')
    parts = fn.split('/')
    if parts[0] == '.':
        parts.pop(0)
    modname = parts[-1][:-4]
    package = '_'.join(parts[:-1])

    # cythonize
    cythonize_main([fn])

    if not package:
        print('no need to rewrite', fn)
    else:
        # get the .c, and change the initXXX
        fn_c = fn[:-3] + ('c' if not is_cplus(fn) else 'cpp')
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
    for fn in sys.argv[1:]:
        try:
            do(fn)
        except:  # noqa: E722
            print("Failed to cythonize, this is not necessarily a problem")
            pass
