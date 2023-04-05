/*
 * iOS utils
 *
 */

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <sys/utsname.h>
#include "ios_wrapper.h"


float ios_uiscreen_get_scale() {
	float scale = 1.0;
	if ([[UIScreen mainScreen] respondsToSelector:@selector(nativeScale)]) {
		scale = [[UIScreen mainScreen] nativeScale];
	};
	return scale;
}

int ios_uiscreen_get_dpi() {
    /*
     * dpi function from src/video/uikit/SDL_uikitmodes.m (SDL2)
     */

    /*
     * A well up to date list of device info can be found here:
     * https://github.com/lmirosevic/GBDeviceInfo/blob/master/GBDeviceInfo/GBDeviceInfo_iOS.m
     */
    NSDictionary* devices = @{
        @"iPhone1,1": @163,
        @"iPhone1,2": @163,
        @"iPhone2,1": @163,
        @"iPhone3,1": @326,
        @"iPhone3,2": @326,
        @"iPhone3,3": @326,
        @"iPhone4,1": @326,
        @"iPhone5,1": @326,
        @"iPhone5,2": @326,
        @"iPhone5,3": @326,
        @"iPhone5,4": @326,
        @"iPhone6,1": @326,
        @"iPhone6,2": @326,
        @"iPhone7,1": @401,
        @"iPhone7,2": @326,
        @"iPhone8,1": @326,
        @"iPhone8,2": @401,
        @"iPhone8,4": @326,
        @"iPhone9,1": @326,
        @"iPhone9,2": @401,
        @"iPhone9,3": @326,
        @"iPhone9,4": @401,
        @"iPhone10,1": @326,
        @"iPhone10,2": @401,
        @"iPhone10,3": @458,
        @"iPhone10,4": @326,
        @"iPhone10,5": @401,
        @"iPhone10,6": @458,
        @"iPhone11,2": @458,
        @"iPhone11,4": @458,
        @"iPhone11,6": @458,
        @"iPhone11,8": @326,
        @"iPhone12,1": @326,
        @"iPhone12,3": @458,
        @"iPhone12,5": @458,
	@"iPhone12,8": @326,
	@"iPhone13,1": @476,
        @"iPhone13,2": @460,
        @"iPhone13,3": @460,
        @"iPhone13,4": @458,
        @"iPhone14,2": @460,
        @"iPhone14,3": @458,
        @"iPhone14,4": @476,
        @"iPhone14,5": @460,
        @"iPhone14,6": @326,
        @"iPad1,1": @132,
        @"iPad2,1": @132,
        @"iPad2,2": @132,
        @"iPad2,3": @132,
        @"iPad2,4": @132,
        @"iPad2,5": @163,
        @"iPad2,6": @163,
        @"iPad2,7": @163,
        @"iPad3,1": @264,
        @"iPad3,2": @264,
        @"iPad3,3": @264,
        @"iPad3,4": @264,
        @"iPad3,5": @264,
        @"iPad3,6": @264,
        @"iPad4,1": @264,
        @"iPad4,2": @264,
        @"iPad4,3": @264,
        @"iPad4,4": @326,
        @"iPad4,5": @326,
        @"iPad4,6": @326,
        @"iPad4,7": @326,
        @"iPad4,8": @326,
        @"iPad4,9": @326,
        @"iPad5,1": @326,
        @"iPad5,2": @326,
        @"iPad5,3": @264,
        @"iPad5,4": @264,
        @"iPad6,3": @264,
        @"iPad6,4": @264,
        @"iPad6,7": @264,
        @"iPad6,8": @264,
        @"iPad6,11": @264,
        @"iPad6,12": @264,
        @"iPad7,1": @264,
        @"iPad7,2": @264,
        @"iPad7,3": @264,
        @"iPad7,4": @264,
        @"iPad7,5": @264,
        @"iPad7,6": @264,
        @"iPad7,11": @264,
        @"iPad7,12": @264,
        @"iPad8,1": @264,
        @"iPad8,2": @264,
        @"iPad8,3": @264,
        @"iPad8,4": @264,
        @"iPad8,5": @264,
        @"iPad8,6": @264,
        @"iPad8,7": @264,
        @"iPad8,8": @264,
        @"iPad11,1": @326,
        @"iPad11,2": @326,
        @"iPad11,3": @326,
        @"iPad11,4": @326,
        @"iPod1,1": @163,
        @"iPod2,1": @163,
        @"iPod3,1": @163,
        @"iPod4,1": @326,
        @"iPod5,1": @326,
        @"iPod7,1": @326,
        @"iPod9,1": @326,
    };
    struct utsname systemInfo;
    uname(&systemInfo);
    NSString* deviceName = [NSString stringWithCString:systemInfo.machine encoding:NSUTF8StringEncoding];
    id foundDPI = devices[deviceName];
    if (foundDPI) {
        return (float)[foundDPI integerValue];
    } else {
        /*
        * Estimate the DPI based on the screen scale multiplied by the base DPI for the device
        * type (e.g. based on iPhone 1 and iPad 1)
        */
        float scale = ios_uiscreen_get_scale();
        float dpi = 160 * scale;
        if (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPad) {
            dpi = 132 * scale;
        } else if (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone) {
            dpi = 163 * scale;
        }
	    return dpi;
    }
}

padding ios_get_safe_area() {
	padding safearea;
	if (@available(iOS 11.0, *)){
		UIWindow *window = [[[UIApplication sharedApplication] delegate] window];
		safearea.top = window.safeAreaInsets.top;
		safearea.bottom = window.safeAreaInsets.bottom;
		safearea.left = window.safeAreaInsets.left;
		safearea.right = window.safeAreaInsets.right;
	} else {
		safearea.top = 0;
		safearea.bottom = 0;
		safearea.left = 0;
		safearea.right = 0;
	}	
	return safearea;
}
