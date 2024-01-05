from typing import List, Final

__all__: Final[List[str]] = ["Route"]


class Route:
    def __init__(self) -> None:
        self.method: str = ""
        self.path: str = ""
        self.args: dict = {}
