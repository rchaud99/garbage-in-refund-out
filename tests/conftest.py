import pytest

from refundout.bases import choose
from refundout.tau2 import VENDOR, Airline


@pytest.fixture(scope="session")
def airline() -> Airline:
    if not VENDOR.exists():
        pytest.skip(f"τ²-bench is not cloned into {VENDOR}")
    return Airline.load()


@pytest.fixture(scope="session")
def bases(airline):
    return choose(airline)
