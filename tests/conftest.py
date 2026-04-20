import subprocess
from pathlib import Path
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-mode",
        action="store",
        choices=("all", "build", "test"),
        default="all",
        help="Select whether to run build only, tests only, or both.",
    )

@pytest.fixture(scope="module", autouse=True)
def build(request):
    run_mode = request.config.getoption("--run-mode")
    if run_mode == "test":
        return

    subprocess.run(
        ["arduino-cli", "compile", "-e"],
        cwd=Path(request.fspath).parent,
        check=True,
    )

@pytest.fixture(autouse=True)
def skip_test_execution_in_build_mode(request, build):
    if request.config.getoption("--run-mode") == "build":
        pytest.skip("skipped test execution in build-only mode")
