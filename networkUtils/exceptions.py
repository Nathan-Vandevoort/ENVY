class ConnectionNotFoundError(Exception):
    def __init__(self, message='Connection does not exist'):
        self.message = message
        super().__init__(self.message)


class OperationFailed(Exception):
    def __init__(self, message='Attempted Operation Failed'):
        self.message = message
        super().__init__(self.message)