import pytest

from src.providers.defillama import get_chains_tvl, get_total_defi_tvl

pytestmark = pytest.mark.live


def test_get_chains_tvl_returns_list():
    chains = get_chains_tvl()

    assert isinstance(chains, list)
    assert len(chains) > 0


def test_get_total_defi_tvl_returns_positive_number():
    total_tvl = get_total_defi_tvl()

    assert isinstance(total_tvl, float)
    assert total_tvl > 0
