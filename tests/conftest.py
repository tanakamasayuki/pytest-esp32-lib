import os
import subprocess
from pathlib import Path
import tomllib

import pytest
from pytest_metadata.plugin import metadata_key

TESTS_DIR = Path(__file__).parent
DOTENV_FILES = (TESTS_DIR / ".env", TESTS_DIR / ".env.local")


# Register the small set of project-level CLI options we support.
def pytest_addoption(parser):
    parser.addoption(
        "--run-mode",
        action="store",
        choices=("all", "build", "test"),
        default="all",
        help="Select whether to run build only, tests only, or both.",
    )
    parser.addoption(
        "--profile",
        action="store",
        help="Arduino CLI sketch profile name passed to `arduino-cli compile -m`.",
    )


# Load simple KEY=VALUE pairs from local dotenv files under tests/.
def load_dotenv_values():
    values = {}

    for path in DOTENV_FILES:
        if not path.is_file():
            continue

        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue

            if value and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]

            values[key] = value

    return values


DOTENV_VALUES = load_dotenv_values()
# Use local dotenv files as defaults without overriding real environment variables.
for key, value in DOTENV_VALUES.items():
    os.environ.setdefault(key, value)


# Read the optional Arduino sketch profile selected for this pytest run.
def get_profile_name(config):
    return config.getoption("--profile")


# Map each test app to a profile-specific build output directory.
def get_build_dir(config, app_path):
    profile = get_profile_name(config)
    build_root = Path(app_path) / "build"
    if profile:
        return str(build_root / profile)

    return str(build_root / "default")


# Load test-app-specific define mappings when present.
def load_build_config(app_path):
    config_path = Path(app_path) / "build_config.toml"
    if not config_path.is_file():
        return {}

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    defines = data.get("defines", {})
    if not isinstance(defines, dict):
        raise ValueError(f"'defines' in {config_path} must be a table")

    return defines


# Quote define values safely for arduino-cli build properties.
def format_define_value(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# Convert configured environment values into arduino-cli build properties.
def get_build_properties(config, app_path):
    defines = load_build_config(app_path)
    extra_flags = []

    for setting_name, define_name in defines.items():
        # Forward selected environment values into the sketch as compile-time defines.
        value = os.getenv(setting_name)
        if value is None:
            continue

        extra_flags.append(f"-D{define_name}={format_define_value(value)}")

    if not extra_flags:
        return []

    return [
        "--build-property",
        f"build.extra_flags={' '.join(extra_flags)}",
    ]


def pytest_configure(config):
    profile = get_profile_name(config) or "default"

    config.stash[metadata_key]["Profile"] = profile


# Show the active profile in the pytest session header.
def pytest_report_header(config):
    return [f"profile: {get_profile_name(config) or 'default'}"]


@pytest.fixture
# Expose the build directory to pytest-embedded.
def build_dir(request):
    return get_build_dir(request.config, Path(request.fspath).parent)


@pytest.fixture(scope="module", autouse=True)
# Build each sketch automatically unless the run is test-only.
def build(request):
    config = request.config
    run_mode = request.config.getoption("--run-mode")
    if run_mode == "test":
        return

    # Keep build outputs separated by test app and selected profile.
    app_path = Path(request.fspath).parent
    build_dir = get_build_dir(config, app_path)
    command = [
        "arduino-cli",
        "compile",
        "--build-path",
        build_dir,
    ]

    profile = get_profile_name(config)
    if profile:
        command.extend(["-m", profile])

    command.extend(get_build_properties(config, app_path))

    subprocess.run(command, cwd=app_path, check=True)


@pytest.fixture(autouse=True)
# Skip Python-side DUT execution when running in build-only mode.
def skip_test_execution_in_build_mode(request, build):
    if request.config.getoption("--run-mode") == "build":
        pytest.skip("skipped test execution in build-only mode")
