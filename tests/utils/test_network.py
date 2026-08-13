import socket as real_socket
import pytest
from types import SimpleNamespace

from sonos_rescue.utils import network


def test_get_local_ip_fallback_and_success(
    monkeypatch: pytest.MonkeyPatch,
):
    """Exercise `get_local_ip` with a fake socket that returns a known IP and one that raises OSError to exercise the fallback path."""

    network_mod = network

    class FakeSock:
        def connect(self, addr: tuple[str, int]) -> None:
            pass

        def getsockname(self):
            return ("192.0.2.1", 12345)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(
        network_mod,
        "socket",
        SimpleNamespace(
            AF_INET=real_socket.AF_INET,
            SOCK_DGRAM=real_socket.SOCK_DGRAM,
            socket=lambda *_args, **_kwargs: FakeSock(),  # pyright: ignore[reportUnknownLambdaType]
        ),
    )

    ip = network_mod.get_local_ip()
    assert ip == "192.0.2.1"

    class SockErr:
        def connect(self, addr: tuple[str, int]) -> None:
            raise OSError("network unreachable")

        def getsockname(self):
            return ("0.0.0.0", 0)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(
        network_mod,
        "socket",
        SimpleNamespace(
            AF_INET=real_socket.AF_INET,
            SOCK_DGRAM=real_socket.SOCK_DGRAM,
            socket=lambda *_args, **_kwargs: SockErr(),  # pyright: ignore[reportUnknownLambdaType]
        ),
    )

    ip2 = network_mod.get_local_ip()
    assert ip2 == "127.0.0.1"
