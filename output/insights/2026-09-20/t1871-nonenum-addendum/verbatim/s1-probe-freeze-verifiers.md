# 段 1 probe (逐語、repo 外 job dir で実行、実装面に入れないため .md へ貼る)

実行: `python3 probe_freeze_verifiers.py <worktree>`。結果は README §0 項 2 のとおり。

```python
"""段 1 実測 probe: docs/phase3-main-experiment.md の bytes 変更が production の凍結 verifier に与える効果を実走で観測する。

対象 (すべて実 ROOT の凍結 file を読む production 経路):
  1. s1_known_axes_freeze.verify()            — 8b oracle driver (s8b_oracle_driver.py:515) と
                                                 s1_verify_extime_calibration.validated_target が呼ぶ
  2. s1_measurement_freeze.verify()           — 測定凍結 (known_axes を内包)
  3. s8b_holdout_freeze.verify(v2.g1)         — holdout freeze (known_axes JSON の sha を束縛)

repo には書かない。結果は stdout のみ。
"""
import hashlib
import sys
import traceback
from pathlib import Path

WT = Path(sys.argv[1])
sys.path.insert(0, str(WT))

DOC = WT / "docs/phase3-main-experiment.md"
print("doc sha256 =", hashlib.sha256(DOC.read_bytes()).hexdigest())


def run(label, fn):
    try:
        out = fn()
        print(f"[{label}] OK  held_checks={[m['check_id'] for m in getattr(out, 'held_checks', [])]}")
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).splitlines()[0][:200]
        print(f"[{label}] RED {type(exc).__name__}: {msg}")


from orchestrator.campaign import s1_known_axes_freeze as kaf  # noqa: E402
from orchestrator.campaign import s1_measurement_freeze as smf  # noqa: E402

run("s1_known_axes_freeze.verify()", lambda: kaf.verify())
run("s1_measurement_freeze.verify()", lambda: smf.verify())

try:
    from orchestrator.campaign import s8b_holdout_freeze as shf  # noqa: E402
    v2 = WT / "output/s8b-freeze/holdout_freeze.v2.g1.json"
    run("s8b_holdout_freeze.verify(v2.g1)", lambda: shf.verify(v2, root=WT))
except Exception:  # noqa: BLE001
    traceback.print_exc()
```
