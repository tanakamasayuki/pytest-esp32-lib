import subprocess
from pathlib import Path
import pytest

@pytest.fixture(scope="module", autouse=True)
def build(request):
    subprocess.run([
        "arduino-cli", "compile", "-e"
    ], cwd=Path(request.fspath).parent,
    check=True)
