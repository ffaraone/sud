class SudException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self) -> str:
        return self.message
