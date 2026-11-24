from .build_info import BUILD_ID
from .diagnostic_logging import start, attach, record

from pathlib import Path

_developer_install = (Path(__file__).parent / "user_files" / "enable-suggestion-lab").is_file()
if _developer_install:
    start(BUILD_ID)
record("addon_import_started")
try:
    from . import reviewer_overlay
    record("addon_import_complete")
    record("addon_install_started")
    reviewer_overlay.install()
    if _developer_install:
        attach(reviewer_overlay.controller)
except BaseException as error:
    record("addon_load_exception", error=type(error).__name__)
    raise
