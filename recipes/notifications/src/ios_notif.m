#import <UserNotifications/UserNotifications.h>
#include "ios_notif.h"

void notif(char *title, char *body){
    UNUserNotificationCenter *center = [UNUserNotificationCenter currentNotificationCenter];
    
    UNAuthorizationOptions options = UNAuthorizationOptionAlert + UNAuthorizationOptionSound;
    [center requestAuthorizationWithOptions:options
        completionHandler:^(BOOL granted, NSError * _Nullable error) {
        if (!granted) {
            NSLog(@"Something went wrong");
        }
        else
            NSLog(@"Already access granted");
    }];
    
    UNMutableNotificationContent *content = [UNMutableNotificationContent new];
    NSString *nstitle = [NSString stringWithCString:(char *)title encoding:NSUTF8StringEncoding];
    NSString *nsbody = [NSString stringWithCString:(char *)body encoding:NSUTF8StringEncoding];
    NSString *nsid = @"LocalNotification";
    content.title = nstitle;
    content.body = nsbody;
    content.sound = [UNNotificationSound defaultSound];

    UNNotificationAction *action = [UNNotificationAction
                                actionWithIdentifier:@"LAUNCH_ACTION"
                                title:@"Launch App"
                                options:UNNotificationActionOptionForeground];
    UNNotificationCategory *category = [UNNotificationCategory categoryWithIdentifier:@"CAT_LAUNCH_ACTION"
        actions:@[action] intentIdentifiers:@[]
        options:UNNotificationCategoryOptionNone];
    NSSet *categories = [NSSet setWithObject:category];
    [center setNotificationCategories:categories];
    content.categoryIdentifier = @"CAT_LAUNCH_ACTION";

    UNTimeIntervalNotificationTrigger *trigger = [UNTimeIntervalNotificationTrigger triggerWithTimeInterval:5
                                  repeats:false];
    NSLog(@"Done adding trigger");
    UNNotificationRequest *request = [UNNotificationRequest requestWithIdentifier:nsid
                                  content:content trigger:trigger];

    NSLog(@"Done initing notif request");
    [center addNotificationRequest:request withCompletionHandler:^(NSError * _Nullable error) {
        if (error != nil) {
            NSLog(@"Something went wrong while adding to center");
        }
        else
            NSLog(@"Done adding notif request");
    }];
    
}
