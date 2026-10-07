from importlib.metadata import requires

import wflow_api
import wflow_cli


def test_both_packages_carry_one_version():
    assert wflow_api.__version__ == wflow_cli.__version__


def test_the_cli_pins_the_library_it_ships_with():
    assert f"wflow-api=={wflow_api.__version__}" in (requires("wflow-cli") or [])
