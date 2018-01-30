'''
Notifications module
====================

Wrapper for local notifications in iOS
'''

cdef extern from "ios_notif.h":
	void notif(char *title, char *body)

class IOSNotif(object):
	def show(self, title, body):
		show_notif(title, body)

def show_notif(title, body):
	'''
	Show local notifications
	:Parameters:
		`title`: str
			Title string
		`body`: str
			Body of the notification

	Example for showing a local notification::
		import notifications
		title = "Title"
		body = "Body"
		notifications.IOSNotif().show(title, body)
	'''
	notif(title, body)
