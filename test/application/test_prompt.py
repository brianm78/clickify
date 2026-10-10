from click.testing import CliRunner

from clickify.application import CLIApplication
from clickify.types import Prompt


def test_prompt():
    app = CLIApplication()

    @app.command()
    def test(val: Prompt[int] = 0):
        print(f"Got: {val}")

    runner = CliRunner()
    # Normal arg
    res = runner.invoke(test, ["--val", "1"])
    assert res.exit_code == 0
    assert res.output == "Got: 1\n"

    # Read value from stdin
    res = runner.invoke(test, [], input="123\n")
    assert res.exit_code == 0
    assert res.output == "Val [0]: 123\nGot: 123\n"

    # Ensure default works OK
    res = runner.invoke(test, [], input="\n")
    assert res.exit_code == 0
    assert res.output == "Val [0]: \nGot: 0\n"
