from refundout.power_analysis import cluster_rate, contrasts


def test_bootstrap_clusters_repeats_not_individual_decisions():
    rows = [
        {"base_id": b, "hit": h} for b, h in [("a", 0), ("b", 1)] for _ in range(10)
    ]
    v = cluster_rate(rows, lambda r: r["hit"])
    assert v["k"] == 10 and v["n"] == 20 and v["bases"] == 2 and v["ci95"] == [0, 1]


def test_paired_contrast_preserves_shared_base():
    rows = [
        {"base_id": b, "wording_type": t, "action": a}
        for b in ["a", "b"]
        for t, a in [("action", "refuse"), ("answer", "transfer_to_human")]
    ]
    v = contrasts(rows)
    assert v["difference"] == 1 and v["ci95"] == [1, 1] and v["bases"] == 2
