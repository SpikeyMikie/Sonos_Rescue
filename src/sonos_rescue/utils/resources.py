from importlib.resources import files


def resource_path(filename: str):
    return files("sonos_rescue.resources").joinpath(filename)
