//
//  main.m
//  iOS-python-test
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <python2.7/Python.h>
#include "SDL/SDL_main.h"
#include <dlfcn.h>

int main(int argc, char *argv[]) {
    int ret = 0;
    
    NSAutoreleasePool * pool = [[NSAutoreleasePool alloc] init];

    // Change the executing path to YourApp
    chdir("YourApp");
    
    // Special environment to prefer .pyo, and don't write bytecode if .py are found
    // because the process will not have write attribute on the device.
    putenv("PYTHONOPTIMIZE=2");
    putenv("PYTHONDONTWRITEBYTECODE=1");
    putenv("PYTHONNOUSERSITE=1");
    
    // Kivy environment to prefer some implementation on ios platform
    putenv("KIVY_BUILD=ios");
    putenv("KIVY_WINDOW=sdl");
    putenv("KIVY_IMAGE=imageio");
    
    NSString * resourcePath = [[NSBundle mainBundle] resourcePath];
    NSLog(@"PythonHome is: %s", (char *)[resourcePath UTF8String]);
    Py_SetPythonHome((char *)[resourcePath UTF8String]);

    NSLog(@"Initializing python");
    Py_Initialize();    
    PySys_SetArgv(argc, argv);

    // If other modules are using thread, we need to initialize them before.
    PyEval_InitThreads();

    // Search and start main.py
    const char * prog = [
        [[NSBundle mainBundle] pathForResource:@"YourApp/main" ofType:@"py"] cStringUsingEncoding:
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
    
    // Look like the app still runn even when we leaved here.
    exit(ret);
    return ret;
}
