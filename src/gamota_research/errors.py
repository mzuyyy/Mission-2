class ResearchError(Exception):
    """Typed error; CPython must be able to mutate its traceback during context unwinding."""

    code: str
    message: str

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
