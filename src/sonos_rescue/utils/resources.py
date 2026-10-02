from importlib.resources import files
from importlib.resources.abc import Traversable


def resource_path(filename: str) -> Traversable:
    return files("sonos_rescue.resources").joinpath(filename)
