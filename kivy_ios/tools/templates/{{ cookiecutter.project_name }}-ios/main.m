//
//  main.m
//  {{ cookiecutter.project_name }}
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include "Python.h"
#include "{{ cookiecutter.dist_dir }}/include/common/sdl2/SDL_main.h"
#include <dlfcn.h>

void export_orientation();
void load_custom_builtin_importer();

int main(int argc, char *argv[]) {
    int ret = 0;

    NSAutoreleasePool * pool = [[NSAutoreleasePool alloc] init];

    // Change the executing path to YourApp
    chdir("YourApp");

    // Special environment to prefer .pyo, and don't write bytecode if .py are found
    // because the process will not have a write attribute on the device.
    putenv("PYTHONOPTIMIZE=2");
    putenv("PYTHONDONTWRITEBYTECODE=1");
    putenv("PYTHONNOUSERSITE=1");
    putenv("PYTHONPATH=.");
    putenv("PYTHONUNBUFFERED=1");
    putenv("LC_CTYPE=UTF-8");
    // putenv("PYTHONVERBOSE=1");
    // putenv("PYOBJUS_DEBUG=1");

    // Kivy environment to prefer some implementation on iOS platform
    putenv("KIVY_BUILD=ios");
    putenv("KIVY_WINDOW=sdl2");
    putenv("KIVY_IMAGE=imageio,tex,gif,sdl2");
    putenv("KIVY_AUDIO=sdl2");
    putenv("KIVY_GL_BACKEND=sdl2");

    // IOS_IS_WINDOWED=True disables fullscreen and then statusbar is shown
    putenv("IOS_IS_WINDOWED=False");

    #ifndef DEBUG
    putenv("KIVY_NO_CONSOLELOG=1");
    #endif

    // Export orientation preferences for Kivy
    export_orientation();

    NSString * resourcePath = [[NSBundle mainBundle] resourcePath];
    NSString *python_home = [NSString stringWithFormat:@"PYTHONHOME=%@", resourcePath, nil];
    putenv((char *)[python_home UTF8String]);

    NSString *python_path = [NSString stringWithFormat:@"PYTHONPATH=%@:%@/lib/python3.9/:%@/lib/python3.9/site-packages:.", resourcePath, resourcePath, resourcePath, nil];
    putenv((char *)[python_path UTF8String]);

    NSString *tmp_path = [NSString stringWithFormat:@"TMP=%@/tmp", resourcePath, nil];
    putenv((char *)[tmp_path UTF8String]);

    NSLog(@"Initializing python");
    Py_Initialize();

    wchar_t** python_argv = PyMem_RawMalloc(sizeof(wchar_t *) *argc);
    for (int i = 0; i < argc; i++)
        python_argv[i] = Py_DecodeLocale(argv[i], NULL);
    PySys_SetArgv(argc, python_argv);

    // If other modules are using the thread, we need to initialize them before.
    PyEval_InitThreads();

    // Add an importer for builtin modules
    load_custom_builtin_importer();

    // Search and start main.py
#define MAIN_EXT @"pyc"

    const char * prog = [
        [[NSBundle mainBundle] pathForResource:@"YourApp/main" ofType:MAIN_EXT] cStringUsingEncoding:
        NSUTF8StringEncoding];
    NSLog(@"Running main.py: %s", prog);
    FILE* fd = fopen(prog, "r");
    if ( fd == NULL ) {
        ret = 1;
        NSLog(@"Unable to open main.py, abort.");
    } else {
        ret = PyRun_SimpleFileEx(fd, prog, 1);
        if (ret != 0)
            NSLog(@"Application quit abnormally!");
    }

    Py_Finalize();
    NSLog(@"Leaving");

    [pool release];

    // Look like the app still runs even when we left here.
    exit(ret);
    return ret;
}

// This method reads the available orientations from the Info.plist file and
// shares them via an environment variable. Kivy will automatically set the
// orientation according to this environment value, if it exists. To restrict
// the allowed orientation, please see the comments inside.
void export_orientation() {
    NSDictionary *info = [[NSBundle mainBundle] infoDictionary];
    NSArray *orientations = [info objectForKey:@"UISupportedInterfaceOrientations"];

    // Orientation restrictions
    // ========================
    // Comment or uncomment blocks 1-3 in order the limit orientation support

    // 1. Landscape only
    // NSString *result = [[NSString alloc] initWithString:@"KIVY_ORIENTATION=LandscapeLeft LandscapeRight"];

    // 2. Portrait only
    // NSString *result = [[NSString alloc] initWithString:@"KIVY_ORIENTATION=Portrait PortraitUpsideDown"];

    // 3. All orientations
    NSString *result = [[NSString alloc] initWithString:@"KIVY_ORIENTATION="];
    for (int i = 0; i < [orientations count]; i++) {
        NSString *item = [orientations objectAtIndex:i];
        item = [item substringFromIndex:22];
        if (i > 0)
            result = [result stringByAppendingString:@" "];
        result = [result stringByAppendingString:item];
    }
    // ========================

    putenv((char *)[result UTF8String]);
    NSLog(@"Available orientation: %@", result);
}

void load_custom_builtin_importer() {
    static const char *custom_builtin_importer = \
        "import sys, imp, types\n" \
        "from os import environ\n" \
        "from os.path import exists, join\n" \
        "try:\n" \
        "    # python 3\n"
        "    import _imp\n" \
        "    EXTS = _imp.extension_suffixes()\n" \
        "    sys.modules['subprocess'] = types.ModuleType(name='subprocess')\n" \
        "    sys.modules['subprocess'].PIPE = None\n" \
        "    sys.modules['subprocess'].STDOUT = None\n" \
        "    sys.modules['subprocess'].DEVNULL = None\n" \
        "    sys.modules['subprocess'].CalledProcessError = Exception\n" \
        "    sys.modules['subprocess'].check_output = None\n" \
        "except ImportError:\n" \
        "    EXTS = ['.so']\n"
        "# Fake redirection to supress console output\n" \
        "if environ.get('KIVY_NO_CONSOLE', '0') == '1':\n" \
        "    class fakestd(object):\n" \
        "        def write(self, *args, **kw): pass\n" \
        "        def flush(self, *args, **kw): pass\n" \
        "    sys.stdout = fakestd()\n" \
        "    sys.stderr = fakestd()\n" \
        "# Custom builtin importer for precompiled modules\n" \
        "class CustomBuiltinImporter(object):\n" \
        "    def find_module(self, fullname, mpath=None):\n" \
        "        # print(f'find_module() fullname={fullname} mpath={mpath}')\n" \
        "        if '.' not in fullname:\n" \
        "            return\n" \
        "        if not mpath:\n" \
        "            return\n" \
        "        part = fullname.rsplit('.')[-1]\n" \
        "        for ext in EXTS:\n" \
        "           fn = join(list(mpath)[0], '{}{}'.format(part, ext))\n" \
        "           # print('find_module() {}'.format(fn))\n" \
        "           if exists(fn):\n" \
        "               return self\n" \
        "        return\n" \
        "    def load_module(self, fullname):\n" \
        "        f = fullname.replace('.', '_')\n" \
        "        mod = sys.modules.get(f)\n" \
        "        if mod is None:\n" \
        "            # print('LOAD DYNAMIC', f, sys.modules.keys())\n" \
        "            try:\n" \
        "                mod = imp.load_dynamic(f, f)\n" \
        "            except ImportError:\n" \
        "                # import traceback; traceback.print_exc();\n" \
        "                # print('LOAD DYNAMIC FALLBACK', fullname)\n" \
        "                mod = imp.load_dynamic(fullname, fullname)\n" \
        "            sys.modules[fullname] = mod\n" \
        "            return mod\n" \
        "        return mod\n" \
        "sys.meta_path.insert(0, CustomBuiltinImporter())";
    PyRun_SimpleString(custom_builtin_importer);
}
