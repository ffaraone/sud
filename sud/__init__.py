import os
from importlib.metadata import PackageNotFoundError, version
from subprocess import check_output

try:
    VERSION = version("sud")
except PackageNotFoundError:
    VERSION = "unknown"


def _get_git_revision(path):
    if not os.path.exists(os.path.join(path, ".git")):
        return None
    try:
        revision = check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            env=os.environ,
        )
    except Exception:
        return None
    return revision.strip().decode("utf-8")


def get_revision():
    package_dir = os.path.dirname(__file__)
    checkout_dir = os.path.normpath(
        os.path.join(package_dir, os.pardir, os.pardir)
    )
    path = os.path.join(checkout_dir)
    if os.path.exists(path):
        return _get_git_revision(path)
    return None


def get_version():
    if __build__:
        return f"{__version__}.{__build__}"
    return __version__


__version__ = VERSION
__build__ = get_revision()

__semantic_version__ = (
    __version__ if __build__ is None else f"{__version__}+{__build__}"
)
