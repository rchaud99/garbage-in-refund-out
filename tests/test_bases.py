"""Bases: cancellation turns on insurance alone, owners are unseen, and the draw is spread and reproducible."""

from collections import Counter

from refundout.bases import choose, eligible
from refundout.tau2 import NOW, paid


def test_every_base_is_cancellable_only_through_insurance(airline, bases):
    db = airline.db
    assert len(bases) == 12
    for base in bases:
        r = db["reservations"][base.reservation_id]
        assert r["insurance"] == "no" and r["cabin"] != "business"
        assert r["created_at"] < "2024-05-14T15:00:00"
        for flight in r["flights"]:
            assert db["flights"][flight["flight_number"]]["dates"][flight["date"]]["status"] == "available"
            assert flight["date"] > NOW[:10]
        assert base.user_id not in airline.public_users
        assert base.total_paid == paid(r) and base.passengers == len(r["passengers"])


def test_bases_come_from_different_users_spread_over_passenger_counts(bases):
    assert len({base.user_id for base in bases}) == len(bases)
    assert Counter(base.passengers for base in bases) == {1: 3, 2: 3, 3: 3, 4: 3}


def test_the_draw_is_reproducible_from_its_seed(airline, bases):
    assert choose(airline, seed=0) == bases
    assert choose(airline, seed=1) != bases
    assert {base.reservation_id for base in bases} <= set(eligible(airline))


def test_the_draw_is_prefix_stable_so_skip_never_reuses_earlier_bases(airline, bases):
    """--skip N --bases M takes positions N+1..N+M of one fixed order: every shorter draw is a prefix of a longer one."""
    longest = choose(airline, 60)
    assert len(longest) == 60 and longest[:12] == bases
    for n in (1, 5, 12, 13, 24, 36, 48, 59):
        assert choose(airline, n) == longest[:n]
    fresh = longest[12:60]
    assert not {b.reservation_id for b in fresh} & {b.reservation_id for b in bases}
    assert len({b.user_id for b in longest}) == 60  # no user twice, across the discovery and new bases


def test_the_draw_stays_prefix_stable_to_132_with_no_base_or_user_reused(airline):
    """The follow-up passes take positions 61-108 (a second half for the wording study) and 109-132 (the ledger
    design): each must be a prefix extension of the shorter draws, and share no reservation or user with them."""
    longest = choose(airline, 132)
    assert len(longest) == 132
    for n in (60, 61, 107, 108, 109, 131):
        assert choose(airline, n) == longest[:n]
    blocks = [longest[:12], longest[12:60], longest[60:108], longest[108:132]]
    ids = [{b.reservation_id for b in block} for block in blocks]
    users = [{b.user_id for b in block} for block in blocks]
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            assert not ids[i] & ids[j] and not users[i] & users[j]
    assert len({b.user_id for b in longest}) == 132
