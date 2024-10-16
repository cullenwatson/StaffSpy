from enum import Enum
from typing import Optional


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"


class DriverType:
    def __init__(
        self, browser_type: BrowserType, executable_path: Optional[str] = None
    ):
        self.browser_type = browser_type
        self.executable_path = executable_path
