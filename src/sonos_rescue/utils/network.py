import socket


def get_local_ip() -> str:
    """
    Determine the local IPv4 address of this machine.

    A UDP socket is used only to discover the preferred network interface.
    No data is actually sent to the remote address (google).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except OSError:
            ip = "127.0.0.1"
    return ip
