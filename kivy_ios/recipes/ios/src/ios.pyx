'''
IOS module
==========

IOS module is wrapping some part of the IOS features.

'''

from cpython cimport Py_INCREF, Py_DECREF
from os.path import basename

cdef extern from "ios_wrapper.h":
    ctypedef void (*ios_send_email_cb)(char *, void *)
    ctypedef struct padding:
        float top
        float bottom
        float right
        float left
    int ios_send_email(char *subject, char *text, char *mimetype, char
            *filename, char *filename_alias, ios_send_email_cb cb, void *userdata)
    void ios_open_url(char *url)
    void load_url_webview(char *url, int x, int y, int width, int height)
    float ios_uiscreen_get_scale()
    int ios_uiscreen_get_dpi()
    padding ios_get_safe_area()

cdef void _send_email_done(char *status, void *data):
    cdef object callback = <object>data
    callback(status)
    Py_DECREF(callback)

#
#Support for iOS webview
#
class IOSWebView(object):
    def open(self, url, x, y, width, height):
        open_url_wbv(url, x, y, width, height)


def open_url_wbv(url, x, y, width, height):
    '''
    OPEN URL in webview

    :Parameters:
        `url`: str
            URL string

        `height`: int
            Height of the window

        `width`: int
            Width of the window

    Example for opening up a web page in WKWebview::

        import ios
        url = "http://www.google.com"
        ios.IOSWebView().open(url, x, y, width, height)
    '''
    load_url_webview(url, x, y, width, height)

#
# Support for webbrowser module
#

class IosBrowser(object):
    def open(self, url, new=0, autoraise=True):
        open_url(url)
    def open_new(self, url):
        open_url(url)
    def open_new_tab(self, url):
        open_url(url)

import webbrowser
try:
    # python 2
    webbrowser.register('ios', IosBrowser, None, -1)
except:
    # python 3
    webbrowser.register('ios', IosBrowser, None, preferred=True)
#
# API
#

__version__ = (1, 1, 0)

def open_url(url):
    '''Open an URL in Safari

    :Parameters:
        `url`: str
            The url string
    '''
    cdef char *j_url = NULL

    if url is not None:
        if type(url) is unicode:
            url = url.encode('UTF-8')
        j_url = <bytes>url

    ios_open_url(j_url)


def send_email(subject, text, mimetype=None, filename=None, filename_alias=None, callback=None):
    '''Send an email using the IOS api.

    :Parameters:
        `subject`: str
            Subject of the email
        `text`: str
            Content of the email
        `mimetype`: str
            Mimetype of the attachment if exist
        `filename`: str
            Full path of the filename to attach, must be used with mimetype.
        `filename_alias`: str
            Name of the file that will be shown to the user. If none is set, it
            will use the basename of filename.
        `callback`: func(status)
            Callback that can be called when the email interface have been
            removed. A status will be passed as the first argument: "cancelled",
            "saved", "sent", "failed", "unknown", "cannotsend".

    .. note::

        The application must have the window created to be able to use that
        method. Trying to send an email without the application running will
        crash.

    Example for sending a simple hello world::

        ios.send_email('This is my subject',
            'Hello you!\n\nThis is an hello world.')

    Send a mail with an attachment::

        from os.path import realpath
        ios.send_email('Mail with attachment',
            'Your attachment will be just after this message.',
            mimetype='image/png',
            filename=realpath('mylogo.png'))

    Getting the status of the mail with the callback

        from kivy.app import App

        class EmailApp(App):
            def callback_email(self, status):
                print 'The email have been', status

            def send_email(self, *largs):
                print 'Sending an email'
                ios.send_email('Hello subject', 'World body',
                    callback=self.callback_email)

            def build(self):
                btn = Button(text='Click me')
                btn.bind(on_release=self.send_email)
                return btn

        if __name__ == '__main__':
            EmailApp().run()

    '''
    cdef char *j_mimetype = NULL
    cdef char *j_filename = NULL
    cdef char *j_subject = NULL
    cdef char *j_text = NULL
    cdef char *j_title = NULL
    cdef char *j_filename_alias = NULL

    if subject is not None:
        if type(subject) is unicode:
            subject = subject.encode('UTF-8')
        j_subject = <bytes>subject
    if text is not None:
        if type(text) is unicode:
            text = text.encode('UTF-8')
        j_text = <bytes>text
    if mimetype is not None:
        j_mimetype = <bytes>mimetype
    if filename is not None:
        j_filename = <bytes>filename

        if filename_alias is None:
            filename_alias = basename(filename)
        if type(filename_alias) is unicode:
            filename_alias = filename_alias.encode('UTF-8')
        j_filename_alias = <bytes>filename_alias


    Py_INCREF(callback)

    ret = ios_send_email(j_subject, j_text, j_mimetype, j_filename,
            j_filename_alias, _send_email_done, <void *>callback)
    if ret == 0:
        callback('failed')
        return 0
    elif ret == -1:
        callback('cannotsend')
        return 0

    return 1

def get_scale():
    '''Return the UIScreen scale (1 on iPad, 2 on iPad 3)
    '''
    return ios_uiscreen_get_scale()

def get_dpi():
    '''Return the approximate DPI of the screen
    '''
    return ios_uiscreen_get_dpi()

def get_safe_area():
    '''Return the safe area bounds
    '''
    return ios_get_safe_area()


from pyobjus import autoclass, selector, protocol
from pyobjus.protocols import protocols

NSNotificationCenter = autoclass('NSNotificationCenter')

protocols["KeyboardDelegates"] = {
    'keyboardWillShow': ('v16@0:4@8', "v32@0:8@16"),
    'keyboardDidHide': ('v16@0:4@8', "v32@0:8@16")}


class IOSKeyboard(object):
    '''Get listener for keyboard height.
    '''

    kheight = 0

    def __init__(self, **kwargs):
        super(IOSKeyboard, self).__init__()
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, selector("keyboardWillShow"), "UIKeyboardWillShowNotification", None)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, selector("keyboardDidHide"), "UIKeyboardDidHideNotification", None)

    @protocol('KeyboardDelegates')
    def keyboardWillShow(self, notification):
        self.kheight = get_scale() * notification.userInfo().objectForKey_(
            'UIKeyboardFrameEndUserInfoKey').CGRectValue().size.height
        from kivy.core.window import Window
        Window.trigger_keyboard_height()

    @protocol('KeyboardDelegates')
    def keyboardDidHide(self, notification):
        self.kheight = 0
        from kivy.core.window import Window
        Window.trigger_keyboard_height()

iOSKeyboard = IOSKeyboard()

def get_kheight():
    return iOSKeyboard.kheight
