#ifndef __IOS_WRAPPER
#define __IOS_WRAPPER

typedef struct {
	float top;
	float bottom;
	float right;
	float left;
} padding;

float ios_uiscreen_get_scale(void);
int ios_uiscreen_get_dpi(void);
padding ios_get_safe_area(void);
void ios_open_url(char *url);
void load_url_webview(char *url, int x, int y, int width, int height);

typedef void (*ios_send_email_cb)(char *, void *);

int ios_send_email(char *subject, char *text, char *mimetype, char *filename,
	char *filename_alias, ios_send_email_cb callback, void *userdata);

#endif
