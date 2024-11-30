
class ConfigurationError(Exception):
    """Custom exception raised when configuration validation fails."""

    def __init__(self, message, key=None, value=None):
        super().__init__(message)
        self.key = key      # The key that caused the error
        self.value = value  # The value that caused the error (if applicable)

    def __str__(self):
        base_message = super().__str__()
        if self.key:
            base_message += f" (key: '{self.key}'"
            if self.value is not None:
                base_message += f", value: {self.value}"
            base_message += ")"
        return base_message