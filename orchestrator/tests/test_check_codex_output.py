# -*- coding: utf-8 -*-
"""tools/check_codex_output.py の成果物 gate テスト。"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = _ROOT / "tools" / "check_codex_output.py"
_SPEC = importlib.util.spec_from_file_location("check_codex_output_under_test", _CHECKER)
assert _SPEC and _SPEC.loader
CCO = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CCO)


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_normal_output_is_accepted(tmp_path: Path) -> None:
    """P3: 通常本文と fence 外の総括を持つ正当な成果物は rc=0。"""
    target = _write(tmp_path / "output.txt", "本文です。" * 100 + "\n## 総括\n完了\n")
    assert CCO.main([str(target)]) == 0


def test_minimum_uses_raw_bytes_not_character_count(tmp_path: Path) -> None:
    target = _write(tmp_path / "multibyte.txt", "界" * 170 + "\n## 総括\n完了\n")
    assert len(target.read_text(encoding="utf-8")) < 500
    assert len(target.read_bytes()) >= 500
    assert CCO.main([str(target)]) == 0


def test_small_fragment_is_rejected_even_with_heading(tmp_path: Path) -> None:
    """V8: min-bytes 検査を恒真化するとこの負例が通って赤になる。"""
    target = _write(tmp_path / "small.txt", "短い\n## 総括\n完了\n")
    assert CCO.main([str(target)]) == 1


def test_fenced_heading_does_not_satisfy_requirement(tmp_path: Path) -> None:
    """V9: fence 除去を外すと fence 内見出しだけで通り、この負例が赤になる。"""
    target = _write(
        tmp_path / "fenced.txt",
        "本文" * 200 + "\n````markdown\n## 総括\n````\n",
    )
    assert CCO.main([str(target)]) == 1


def test_missing_heading_is_rejected(tmp_path: Path) -> None:
    target = _write(tmp_path / "missing.txt", "本文" * 200)
    assert CCO.main([str(target)]) == 1


def test_size_and_heading_failures_are_both_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write(tmp_path / "two-errors.txt", "tiny\n")
    assert CCO.main([str(target)]) == 1
    stderr = capsys.readouterr().err
    assert "raw byte" in stderr
    assert "必須見出し" in stderr


def test_non_utf8_output_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """V16: strict decode を errors='replace' に戻すとこの負例が通って赤になる。"""
    target = tmp_path / "non-utf8.txt"
    target.write_bytes(b"\xff" * 500 + "\n## 総括\n".encode())
    assert CCO.main([str(target)]) == 1
    assert "非 UTF-8 成果物" in capsys.readouterr().err


@pytest.mark.parametrize(
    "kind",
    [
        "directory",
        "symlink",
        pytest.param(
            "fifo",
            marks=pytest.mark.skipif(
                not hasattr(os, "mkfifo"), reason="os.mkfifo is unavailable"
            ),
        ),
    ],
)
def test_non_regular_files_are_rejected_without_reading(tmp_path: Path, kind: str) -> None:
    target = tmp_path / kind
    if kind == "directory":
        target.mkdir()
    elif kind == "symlink":
        regular = _write(tmp_path / "regular.txt", "x" * 520 + "\n## 総括\n")
        target.symlink_to(regular)
    else:
        os.mkfifo(target)
    assert CCO.main([str(target)]) == 1


def test_read_limit_rejects_file_larger_than_ten_megabytes(tmp_path: Path) -> None:
    """V11: 上限を 20MB へ倍化すると有効 fixture が rc=0 になって赤になる。"""
    target = tmp_path / "large.txt"
    heading = "\n## 総括\n".encode("utf-8")
    target.write_bytes(b"x" * (10 * 1024 * 1024 + 1 - len(heading)) + heading)
    assert CCO.main([str(target)]) == 1


def test_check_uses_open_fd_instead_of_path_reread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write(tmp_path / "target.txt", "本文" * 200)
    replacement = _write(
        tmp_path / "replacement.txt", "本文" * 200 + "\n## 総括\n完了\n"
    )
    real_fstat = CCO.os.fstat
    exchanged = False

    def exchange_after_open(fd: int):
        nonlocal exchanged
        metadata = real_fstat(fd)
        if not exchanged:
            target.unlink()
            target.symlink_to(replacement)
            exchanged = True
        return metadata

    monkeypatch.setattr(CCO.os, "fstat", exchange_after_open)
    assert CCO.main([str(target)]) == 1


def test_growth_after_fstat_is_rejected_by_bounded_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write(tmp_path / "growing.txt", "本文" * 200 + "\n## 総括\n")
    real_fstat = CCO.os.fstat
    grown = False

    def grow_after_fstat(fd: int):
        nonlocal grown
        metadata = real_fstat(fd)
        if not grown:
            with target.open("ab") as stream:
                stream.truncate(10 * 1024 * 1024 + 1)
            grown = True
        return metadata

    monkeypatch.setattr(CCO.os, "fstat", grow_after_fstat)
    assert CCO.main([str(target)]) == 1


def test_no_nofollow_support_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write(tmp_path / "output.txt", "本文" * 200 + "\n## 総括\n")
    monkeypatch.delattr(CCO.os, "O_NOFOLLOW")
    assert CCO.main([str(target)]) == 1


def test_custom_heading_regex_is_supported(tmp_path: Path) -> None:
    target = _write(tmp_path / "english.txt", "details\n# Summary\n")
    assert CCO.main([
        str(target),
        "--min-bytes", "1",
        "--require-heading", r"^# Summary$",
    ]) == 0


@pytest.mark.parametrize(
    "args",
    [
        ["missing.txt", "--min-bytes", "0"],
        ["missing.txt", "--require-heading", "["],
    ],
)
def test_invalid_arguments_return_argparse_error(args: list[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        CCO.main(args)
    assert raised.value.code == 2


def test_help_discloses_semantic_consistency_is_out_of_scope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        CCO.main(["--help"])
    assert raised.value.code == 0
    output = capsys.readouterr().out
    assert "意味" in output
    assert "scope 外" in output


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
