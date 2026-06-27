/*
 * kivy_ios_bootstrap.m — dual-mode iOS bootstrap.
 *
 * When SDL3 is available (Kivy wheel embedded in Frameworks/) SDL_RunApp
 * drives the UIKit lifecycle.  When SDL3 is absent (pure-Python / no-Kivy
 * apps) a minimal UIApplicationDelegate does the same job without the SDL
 * dependency.  The right path is chosen at compile time by __has_include so
 * the same source file works in both configurations without any ifdef noise
 * in generated projects.
 *
 * Python headers  → Python.xcframework (always present)
 * SDL3 headers    → Frameworks/SDL3.xcframework (only for Kivy apps)
 *
 * HEADER_SEARCH_PATHS is managed by `toolchain build`; it adds SDL3 paths
 * only when SDL3.xcframework is present, which is exactly the condition
 * __has_include tests.
 */

/* ── common ─────────────────────────────────────────────────────────────── */
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <Python.h>
#include "kivy_ios_bootstrap.h"

typedef struct {
    const char *entry_module;
    const char *app_dir;
    const char *python_ver;
} _BootstrapArgs;

static _BootstrapArgs _g_args;

static void _crash(NSString *message) {
    NSLog(@"kivy-ios bootstrap fatal: %@", message);
    exit(1);
}

/* Shared Python initialisation — no SDL dependency. */
static void _run_python(void) {
    NSString *resourcePath = [[NSBundle mainBundle] resourcePath];
    NSString *pythonHome   = [resourcePath stringByAppendingPathComponent:@"python"];
    NSString *appPath      = [resourcePath stringByAppendingPathComponent:
                                  [NSString stringWithUTF8String:_g_args.app_dir]];
    NSString *pipDeps      = [resourcePath stringByAppendingPathComponent:@"pip-deps"];
    NSString *pyVer        = [NSString stringWithUTF8String:_g_args.python_ver];

    setenv("PYTHONHOME", [pythonHome UTF8String], 1);
    /* sys.platform == "ios" triggers Kivy's iOS code paths. */
    setenv("KIVY_BUILD", "ios", 1);

    NSString *stdlib   = [pythonHome stringByAppendingPathComponent:
                              [@"lib/python" stringByAppendingString:pyVer]];
    NSString *dynload  = [stdlib stringByAppendingPathComponent:@"lib-dynload"];
    NSString *pythonPath = [@[stdlib, dynload, appPath]
                                componentsJoinedByString:@":"];
    setenv("PYTHONPATH", [pythonPath UTF8String], 1);

    PyStatus status;
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;
    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) _crash(@"Py_PreInitialize failed");

    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    config.buffered_stdio          = 0;
    config.write_bytecode          = 0;
    config.install_signal_handlers = 1;
    config.use_environment         = 1;
    PyConfig_SetBytesString(&config, &config.home, [pythonHome UTF8String]);

    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) _crash(@"Py_InitializeFromConfig failed");

    NSString *addsite = [NSString stringWithFormat:
        @"import site; site.addsitedir(\"%@\")", pipDeps];
    if (PyRun_SimpleString([addsite UTF8String]) != 0)
        _crash(@"failed to add pip-deps as a site directory");

    PyObject *module = PyImport_ImportModule(_g_args.entry_module);
    if (module == NULL) {
        PyErr_Print();
        _crash([NSString stringWithFormat:
            @"failed to import entry module \"%s\"", _g_args.entry_module]);
    }
    Py_DECREF(module);
    Py_Finalize();
}

/* ── SDL3 path — Kivy apps ──────────────────────────────────────────────── */
#if __has_include(<SDL3/SDL_main.h>)

#define SDL_MAIN_HANDLED
#include <SDL3/SDL_main.h>
#include <SDL3/SDL.h>

static int _sdl_callback(int argc, char *argv[]) {
    @autoreleasepool { _run_python(); }
    return 0;
}

int kivy_ios_main(
    int         argc,
    char       *argv[],
    const char *entry_module,
    const char *app_dir,
    const char *python_ver)
{
    _g_args.entry_module = entry_module;
    _g_args.app_dir      = app_dir;
    _g_args.python_ver   = python_ver;
    return SDL_RunApp(argc, argv, _sdl_callback, NULL);
}

/* ── headless path — pure-Python / no-Kivy apps ─────────────────────────── */
#else

/*
 * Without SDL there is no UI toolkit driving the app, so Python runs directly
 * on the main thread.  We deliberately do NOT call UIApplicationMain: doing so
 * starts the UIKit app lifecycle, which (a) emits "UIScene lifecycle will soon
 * be required" for a delegate that has no scene, and (b) triggers CoreAnimation
 * app-launch measurements that can never complete because a headless app never
 * presents a first frame.  Running Python directly keeps pure-Python apps clean
 * and matches their console/headless nature.  Kivy apps take the SDL path above,
 * where SDL_RunApp owns the full UIKit lifecycle.
 */
int kivy_ios_main(
    int         argc,
    char       *argv[],
    const char *entry_module,
    const char *app_dir,
    const char *python_ver)
{
    (void)argc;
    (void)argv;
    _g_args.entry_module = entry_module;
    _g_args.app_dir      = app_dir;
    _g_args.python_ver   = python_ver;
    @autoreleasepool { _run_python(); }
    return 0;
}

#endif /* __has_include(<SDL3/SDL_main.h>) */
