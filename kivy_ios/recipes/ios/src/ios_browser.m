/*
 * Browser support
 */

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <WebKit/WebKit.h>
#include "ios_wrapper.h"

void ios_open_url(char *url)
{
	NSString *nsurl = [NSString stringWithCString:(char *)url encoding:NSUTF8StringEncoding];
	[[UIApplication sharedApplication] openURL:[NSURL URLWithString: nsurl]];
}

/*
 * Webview support
 */
void load_url_webview(char *url, int x, int y, int width, int height)
{
    NSString *nsurl = [NSString stringWithCString:(char *)url encoding:NSUTF8StringEncoding];
    WKWebView *webView = [[WKWebView alloc] initWithFrame: CGRectMake(x, y, width, height)];
    UIWindow *window = [[UIApplication sharedApplication] keyWindow];
    UIView *view = [window.rootViewController view];
    [view addSubview:webView];
    NSURL *ur = [[NSURL alloc] initWithString: nsurl];
    NSURLRequest *req = [[NSURLRequest alloc] initWithURL: ur];
    [webView loadRequest: req];
    [req release];
    [ur release];
  
    UIButton *button = [UIButton buttonWithType:UIButtonTypeRoundedRect];
    [button setTitleColor:[UIColor blackColor] forState:UIControlStateNormal];
    [button setTitle:@"X" forState:UIControlStateNormal];
    button.frame = CGRectMake(0.0, 0.0, 40, 40);
    [button addTarget:webView
         action:@selector(removeFromSuperview) forControlEvents:UIControlEventTouchDown];
    [webView addSubview:button];
    [button release];
    [webView release];
}
