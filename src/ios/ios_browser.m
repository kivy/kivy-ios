/*
 * Browser support
 */

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include "ios_wrapper.h"

void ios_open_url(char *url)
{
	NSString *nsurl = [NSString stringWithCString:(char *)url encoding:NSUTF8StringEncoding];
	[[UIApplication sharedApplication] openURL:[NSURL URLWithString: nsurl]];
}
