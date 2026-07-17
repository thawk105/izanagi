# -*- coding: utf-8 -*-
"""中立 leaf ``s8b_freeze_io`` の loader 契約を characterization で固定する。

strictness は現行 (移行前 s8b_oracle_driver.load_verified_freeze) と同値である:
NaN/Infinity 拒否 + expected_hash 束縛 + top-level object 検査のみ。duplicate key
拒否・encoding 追加検査など現行に無い検査は足さない (F6/F7 裁定後の
load_ratified_freeze の責務)。各期待は現行実装が実際に返す/投げるものを実測して
pin している (期待の先決めをしない)。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

from campaign import s8b_freeze_io as fio  # noqa: E402


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# 受理拒否行列 (characterization)                                               #
# --------------------------------------------------------------------------- #

def test_accepts_wellformed_object_and_returns_byte_sha256(tmp_path):
    doc = {"floor": None, "budget": None, "x": 1}
    path = _write(tmp_path / "ok.json", json.dumps(doc))
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    verified = fio.load_verified_freeze(path)
    assert isinstance(verified, fio.VerifiedFreeze)
    assert verified.document == doc
    assert verified.sha256 == expected


def test_expected_hash_match_accepts_mismatch_rejects(tmp_path):
    path = _write(tmp_path / "ok.json", json.dumps({"a": 1}))
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    assert fio.load_verified_freeze(path, expected_hash=expected).sha256 == expected

    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path, expected_hash="0" * 64)
    assert "expected_hash" in str(exc.value)


def test_rejects_nan_constant(tmp_path):
    path = _write(tmp_path / "nan.json", '{"x": NaN}')
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "非数値定数" in str(exc.value) and "NaN" in str(exc.value)


def test_rejects_infinity_constant(tmp_path):
    path = _write(tmp_path / "inf.json", '{"x": Infinity}')
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "非数値定数" in str(exc.value) and "Infinity" in str(exc.value)


def test_rejects_malformed_json(tmp_path):
    path = _write(tmp_path / "mal.json", "{not json")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "strict parse できない" in str(exc.value)


def test_rejects_non_utf8_bytes(tmp_path):
    path = tmp_path / "bin.json"
    path.write_bytes(b"\xff\xfe{}")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    # decode は strict parse ブロック内で起きるため strict parse 経路の message になる。
    assert "strict parse できない" in str(exc.value)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(tmp_path / "absent.json")
    assert "読めない" in str(exc.value)


def test_rejects_non_object_top_level(tmp_path):
    path = _write(tmp_path / "arr.json", "[1, 2, 3]")
    with pytest.raises(fio.FreezeIOError) as exc:
        fio.load_verified_freeze(path)
    assert "top-level が object でない" in str(exc.value)


def test_duplicate_key_is_accepted_not_rejected(tmp_path):
    """characterization: 現行 loader は duplicate key を拒否しない (last-wins)。

    F6/F7 裁定後の load_ratified_freeze が dup-key 拒否を持つべきで、本 leaf には
    追加しない。この受理は「strictness を勝手に上げていない」ことの機械固定である。
    """
    path = _write(tmp_path / "dup.json", '{"a": 1, "a": 2}')
    verified = fio.load_verified_freeze(path)
    assert verified.document == {"a": 2}


# --------------------------------------------------------------------------- #
# 単一 read の positive control                                                 #
# --------------------------------------------------------------------------- #

def test_reads_bytes_exactly_once(tmp_path, monkeypatch):
    path = _write(tmp_path / "ok.json", json.dumps({"a": 1}))
    real_read_bytes = pathlib.Path.read_bytes
    calls: list[Path] = []

    def counting_read_bytes(self):
        calls.append(Path(self))
        return real_read_bytes(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", counting_read_bytes)
    fio.load_verified_freeze(path)
    assert calls == [path]


# --------------------------------------------------------------------------- #
# import-edge 負テスト (手順 0 と同じ subprocess 方式)                          #
# --------------------------------------------------------------------------- #

def test_floor_alone_does_not_import_oracle_driver():
    """G-9: floor 単独 import が oracle_driver を巻き込まないこと。

    移行前は floor が oracle_driver から NUMACTL/VerifiedFreeze/load_verified_freeze
    を import していたため、この assert は赤だった (中立 leaf 化前の positive control)。
    """
    script = (
        f"import sys; sys.path.insert(0, {str(ORCHESTRATOR)!r}); "
        "import campaign.s8b_floor_campaign; "
        "sys.exit(0 if 'campaign.s8b_oracle_driver' not in sys.modules else 1)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stdout, proc.stderr)


def test_oracle_alone_still_imports():
    """oracle_driver 単独 import は健全 (leaf を経由して loader を得る)。"""
    script = (
        f"import sys; sys.path.insert(0, {str(ORCHESTRATOR)!r}); "
        "import campaign.s8b_oracle_driver as d; "
        "import campaign.s8b_freeze_io as fio; "
        "sys.exit(0 if d._freeze_io is fio else 1)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stdout, proc.stderr)


# --------------------------------------------------------------------------- #
# 実再エクスポート排除                                                          #
# --------------------------------------------------------------------------- #

def test_driver_does_not_re_export_loader_names():
    from campaign import s8b_oracle_driver as driver
    assert not hasattr(driver, "VerifiedFreeze")
    assert not hasattr(driver, "load_verified_freeze")


def test_floor_does_not_re_export_loader_names():
    from campaign import s8b_floor_campaign as floor
    assert not hasattr(floor, "VerifiedFreeze")
    assert not hasattr(floor, "load_verified_freeze")


# --------------------------------------------------------------------------- #
# class identity は単一 (dataclass を二重定義しない)                            #
# --------------------------------------------------------------------------- #

def test_verified_freeze_class_identity_is_single():
    from campaign import s8b_oracle_driver as driver
    from campaign import s8b_floor_campaign as floor
    assert driver._freeze_io.VerifiedFreeze is fio.VerifiedFreeze
    assert floor._freeze_io.VerifiedFreeze is fio.VerifiedFreeze


# --------------------------------------------------------------------------- #
# NUMACTL 配線                                                                  #
# --------------------------------------------------------------------------- #

def test_floor_numactl_is_p2_2_numa_identity():
    from campaign import s8b_floor_campaign as floor
    from campaign import p2_2
    assert floor.NUMACTL is p2_2.NUMA
    assert floor.NUMACTL == ["numactl", "--interleave=all"]


def test_measure_fn_closure_passes_numactl_to_measure_point():
    """``measure_fn=None`` 経路の closure が ``measure_point`` に ``numactl=NUMACTL``
    を渡す配線を固定する。

    縮小の判断 (報告済み): 実 closure の起動は run_campaign の完走 (12 セル実ビルド +
    runner) を要し過大なため、identity assert (上) + closure ソース検査に縮小する。
    ソース検査は closure が ``measure_point`` に ``numactl=NUMACTL`` を渡すことを
    静的に固定する (`s8b_floor_campaign.py` の当該分岐)。
    """
    import inspect
    from campaign import s8b_floor_campaign as floor
    src = inspect.getsource(floor.run_campaign)
    assert "if measure_fn is None:" in src
    assert "measure_point(" in src
    assert "numactl=NUMACTL" in src


if __name__ == "__main__":
    # 自走 harness: `python3 test_s8b_freeze_io.py` で実際に pytest を回す (素の runner
    # による 0 件実行の偽緑を防ぐ。test_plain_runner_coverage の契約)。
    sys.exit(pytest.main([__file__, "-q"]))
