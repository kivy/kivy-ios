/*
 * Email support
 *
 * Very basic, could be upgraded to support HTML, and multiple attachment. No
 * need to let the user manipulate directly uikit API.
 */

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <MessageUI/MessageUI.h>
#include "ios_wrapper.h"

/* guess the view controller from our SDL window.
 */
UIViewController *get_viewcontroller(void) {
	UIWindow *window = [[UIApplication sharedApplication] keyWindow];
	if ( window == NULL ) {
		printf("ios_wrapper: unable to get key window from shared application\n");
		return NULL;
	}
  // return window.rootViewController;
	UIView* view = [window.subviews objectAtIndex:0];
	id nextResponder = [view nextResponder];
	if( [nextResponder isKindOfClass:[UIViewController class]] )
		return (UIViewController *)nextResponder;
	return NULL;
}

@interface InAppEmailViewController : UIViewController <MFMailComposeViewControllerDelegate> {
	ios_send_email_cb callback;
	void * userdata;
}

@property(nonatomic, assign) ios_send_email_cb callback;
@property(nonatomic, assign) void *userdata;

@end

@implementation InAppEmailViewController

@synthesize userdata;
@synthesize callback;

- (void)mailComposeController:(MFMailComposeViewController*)controller didFinishWithResult:(MFMailComposeResult)result error:(NSError*)error {
	static char *statuses[] = {"unknown", "cancelled",  "saved", "sent", "failed"};

	if ( callback != NULL ) {
		char *status = statuses[0];
		switch (result)
		{
			 case MFMailComposeResultCancelled: status = statuses[1]; break;
			 case MFMailComposeResultSaved: status = statuses[2]; break;
			 case MFMailComposeResultSent: status = statuses[3]; break;
			 case MFMailComposeResultFailed: status = statuses[4]; break;
			 default: break;
		}
		callback(status, userdata);
	}

  UIViewController* viewController = [controller presentingViewController];
	[viewController dismissModalViewControllerAnimated:YES];
}

@end

int ios_send_email(char *subject, char *text, char *mimetype, char *filename,
	char *filename_alias, ios_send_email_cb callback, void *userdata)
{
	UIViewController* viewController = get_viewcontroller();
	if ( viewController == NULL ) {
		printf("ios_send_email: unable to get view controller.\n");
		return 0;
	}

	if (! [MFMailComposeViewController canSendMail]) {
		printf("ios_send_email: no available mail provider configured.\n");
		return -1;
	}

	MFMailComposeViewController *controller = [[MFMailComposeViewController alloc] init];
	InAppEmailViewController *inAppVc = [[InAppEmailViewController alloc] init];
	inAppVc.callback = callback;
	inAppVc.userdata = userdata;
	controller.mailComposeDelegate = inAppVc;

	if ( subject != NULL ) {
		NSString *nssubject = [NSString stringWithCString:(char *)subject encoding:NSUTF8StringEncoding];
		[controller setSubject:nssubject];
	}

	if ( text != NULL ) {
		NSString *nstext = [NSString stringWithCString:(char *)text encoding:NSUTF8StringEncoding];
		[controller setMessageBody:nstext isHTML:NO];
	}

	if ( mimetype != NULL && filename != NULL ) {
		NSString *nsmimetype = [NSString stringWithCString:(char *)mimetype encoding:NSUTF8StringEncoding];
		NSString *nsfilename = [NSString stringWithCString:(char *)filename encoding:NSUTF8StringEncoding];
		NSString *nsalias = [NSString stringWithCString:(char *)filename_alias encoding:NSUTF8StringEncoding];
		NSData *myData = [NSData dataWithContentsOfFile:nsfilename];
		[controller addAttachmentData:myData mimeType:nsmimetype fileName:nsalias];
	}

	controller.modalPresentationStyle = UIModalPresentationPageSheet;
	[viewController presentModalViewController:controller animated:YES];
	[controller release];

	return 1;
}