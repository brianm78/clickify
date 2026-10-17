from collections.abc import Generator

import click
import click.testing
import pytest

from clickify import CLIApplication


@pytest.fixture
def runner() -> Generator[click.testing.CliRunner]:
    yield click.testing.CliRunner()


@pytest.fixture
def app() -> Generator[CLIApplication]:
    yield CLIApplication()
