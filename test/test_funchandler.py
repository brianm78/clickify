import pytest

from clickify import CLIApplication

type ComplexType = int
type SimpleType = int


@pytest.fixture
def app():
    app = CLIApplication()

    @app.registry.register()
    def complex_handler(*args: int, flag: bool = False) -> ComplexType:
        """Complex handler
        Arguments:
            args: list of numbers
            flag: If True, always returns zero. Otherwise return sum.
        """
        if flag:
            return 0
        return sum(args, start=0)

    @app.registry.register()
    def simple_handler(arg: int) -> SimpleType:
        """Simple handler."""
        return arg * 10
