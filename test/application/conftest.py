from collections.abc import Generator

import click
import click.testing
import pytest

from clickify import CLIApplication


@pytest.fixture(scope="function")
def runner() -> Generator[click.testing.CliRunner]:
    yield click.testing.CliRunner()


@pytest.fixture(scope="function")
def app() -> Generator[CLIApplication]:
    yield CLIApplication()
