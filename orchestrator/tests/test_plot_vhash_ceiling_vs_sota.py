"""Real matplotlib figure with the production point/arm/GC/round shape."""
from __future__ import annotations

import tempfile
from pathlib import Path
import json
import hashlib
import unittest

from orchestrator.campaign import vhash_ceiling_vs_sota as C
from orchestrator.tests.test_vhash_ceiling_vs_sota import row
from tools.plotting import plot_vhash_ceiling_vs_sota as P


class FigureTests(unittest.TestCase):
    def test_real_figure_and_layout(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        rows = []
        for point in ("P1", "P2", "P3", "P4"):
            for gc in (10, 100):
                for round_no in range(1, 4):
                    for arm in C.prelim_arms(point):
                        rows.append(row(point=point, arm=arm, gc=gc, round_no=round_no,
                                        tps=100 if arm == "R" else 130,
                                        batch=10 if arm != "R-noLR" else 0))
        witnesses = {arm: {"status": "certified", "counts": {"batch_c_lines": 1,
                     "hot_hits": 1, "forward_success": 1}} for arm in C.M_ARMS}
        fig, details = P.make_figure(rows, witnesses)
        self.assertEqual(set(details["gc"]), {"P1", "P2", "P3", "P4"})
        self.assertEqual(len(fig.axes), 2)
        P.check_layout(fig)
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "runs.jsonl"
            raw.write_text("".join(json.dumps(item) + "\n" for item in rows))
            witness_file = Path(td) / "witness.json"
            witness_file.write_text(json.dumps(witnesses))
            P.render(raw, Path(td) / "figure", witness_file)
            self.assertTrue((Path(td) / "figure.png").is_file())
            self.assertTrue((Path(td) / "figure.pdf").is_file())
            provenance = json.loads((Path(td) / "figure.provenance.json").read_text())
            self.assertEqual(provenance["input_sha256"], hashlib.sha256(raw.read_bytes()).hexdigest())
        plt.close(fig)

    def test_small_sample_t_interval(self):
        low, high = P.ci95([1.0, 2.0, 3.0])
        self.assertLess(low, 0)
        self.assertGreater(high, 4)
        with self.assertRaises(ValueError): P.ci95([])


def _run():
    unittest.main()


if __name__ == "__main__":
    _run()
