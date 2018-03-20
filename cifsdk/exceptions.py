
class CIFException(Exception):
    def __init__(self, msg='Unknown'):
        self.msg = "{}".format(msg)

    def __str__(self):
        return self.msg


class CIFConnectionError(CIFException):
    pass


class StoreSubmissionFailed(CIFException):
    pass


class AuthError(CIFException):
    def __init__(self, msg='Unauthorized'):
        self.msg = msg


class TimeoutError(CIFException):
    pass


class InvalidSearch(CIFException):
    def __init__(self, msg='Invalid Search'):
        self.msg = msg


class NotFound(CIFException):
    def __init__(self, msg='Not Found'):
        self.msg = msg


class SubmissionFailed(CIFException):
    def __init__(self, msg='Submission Failed'):
        self.msg = msg


class CIFBusy(CIFException):
    def __init__(self, msg='The system is extremely busy at the moment, try again later.'):
        self.msg = msg
