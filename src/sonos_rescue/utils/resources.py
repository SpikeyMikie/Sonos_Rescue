from importlib.abc import Traversable
from importlib.resources import files


def resource_path(filename: str) -> Traversable:
    return files("sonos_rescue.resources").joinpath(filename)
