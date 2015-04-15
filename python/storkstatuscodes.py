# status codes used by stork.py when exiting. They are combined into a bitmap.
# successful completion always returns 0. STATUS_PACKAGES_INSTALLED and
# STATUS_PACKAGES_REMOVED are only returned when an error also occurs.

STATUS_ERROR = 1
STATUS_ALREADY_RUNNING = 2
STATUS_BAD_OPTION = 4
STATUS_ALREADY_DONE = 8
STATUS_PACKAGES_INSTALLED = 16
STATUS_PACKAGES_REMOVED = 32
STATUS_NOT_FOUND = 64

