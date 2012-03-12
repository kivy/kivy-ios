#ifndef __IOS_WRAPPER
#define __IOS_WRAPPER

typedef void (*ios_send_email_cb)(char *, void *);

int ios_send_email(char *subject, char *text, char *mimetype, char *filename,
	ios_send_email_cb callback, void *userdata);

#endif
