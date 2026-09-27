from refundout.effort_analysis import rule


def test_preregistered_twenty_point_threshold_needs_positive_ci_and_complete_run():
    assert rule({"difference": 0.20, "ci95": [0.01, 0.39]}, [0, 0, 0, 0], True)
    assert not rule({"difference": 0.199, "ci95": [0.01, 0.39]}, [0, 0, 0, 0], True)
    assert not rule({"difference": 0.25, "ci95": [0, 0.49]}, [0, 0, 0, 0], True)
    assert not rule({"difference": 0.25, "ci95": [0.01, 0.49]}, [0, 0, 0, 0], False)
    assert not rule({"difference": 0.25, "ci95": [0.01, 0.49]}, [0, 0, 0, 0.051], True)
