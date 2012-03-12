'''
IOS module
==========

IOS module is wrapping some part of the IOS features.

'''

from python_ref cimport Py_INCREF, Py_DECREF

cdef extern from "ios_wrapper.h":
    ctypedef void (*ios_send_email_cb)(char *, void *)
    int ios_send_email(char *subject, char *text, char *mimetype, char
            *filename, ios_send_email_cb cb, void *userdata)

cdef void _send_email_done(char *status, void *data):
    cdef object callback = <object>data
    callback(status)
    Py_DECREF(callback)


#
# API
#

__version__ = (1, 0, 0)

def send_email(subject, text, mimetype=None, filename=None, callback=None):
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
        `callback`: func(status)
            Callback that can be called when the email interface have been
            removed. A status will be passed as the first argument: "cancelled",
            "saved", "sent", "failed", "unknown".

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

    if subject is not None:
        j_subject = <bytes>subject
    if text is not None:
        j_text = <bytes>text
    if mimetype is not None:
        j_mimetype = <bytes>mimetype
    if filename is not None:
        j_filename = <bytes>filename

    Py_INCREF(callback)

    if ios_send_email(j_subject, j_text, j_mimetype, j_filename,
            _send_email_done, <void *>callback) == 0:
        callback('failed')
        return 0

    return 1
