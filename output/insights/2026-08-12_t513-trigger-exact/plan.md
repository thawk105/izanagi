## 総括

(P1) は **(a) を採用**する。骨格 hole の先頭 2 空白を軸定数 `PREDICATE_HOLE_INDENT = "  "` として pin し、admission は `PREDICATE_HOLE_INDENT + emit_predicate(...)` の UTF-8 bytes と逐語比較する。

- 変更ファイル: 3
  - `orchestrator/campaign/axis_trigger_gating.py`
  - `orchestrator/campaign/pipeline.py`
  - `orchestrator/tests/test_campaign.py`
- 新設・変更テスト: 7 nodeids
- 残る裁定パッケージ候補: 1 件
  - 親 brief 既定の T-515 影響実測・再裁定。今回新たに見つかった未読層由来の候補は 0 件。
- pytest/build は未実行。コード編集も行っていない。

## (P1) の結論

骨格の実バイトは patch 制御 byte `0x2b` (`+`) に続いて `0x20 0x20`、その後に `izanagi_gate_pass = true;` だった。materialized source の正規 hole は、patch の `+` を除いた次の一意な bytes になる。

```text
b"  " + emit_predicate(TriggerGateIR(mask)).encode("utf-8")
```

(a) が優れる理由:

- (a): 各 mask に対して受理する hole line が 1 本だけになる。patch ファイルはテスト時だけ参照し、admission の実行時依存にはしない。
- (b): unified patch の `+` 制御 byte と payload を解析する新しい実行時依存を作る。patch が配備されない、読めない、hunk が再配置される、といった事情が build admission を左右する一方、現在得られる期待値は結局同じ `b"  " + E` である。
- (c): 例えば「先頭 whitespace 任意、末尾 whitespace 禁止」なら、`b"\t"+E`、`b"    "+E`、`E` を引き続き受理する。これは exact 化ではない。

## 実装変更

### 1. 軸定数

[axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/axis_trigger_gating.py:23) の identity 核へ追加する。

```python
MARKER_ID = "silo-backoff-trigger-gating"
SOURCE_REL = "cc/silo/transaction.cc"
TEMPLATE_PATCH = "silo-backoff-trigger-gating-variant.patch"
PREDICATE_HOLE_INDENT = "  "
FLAG = "BACKOFF_TRIGGER_GATING"
```

これは emitter の一部ではなく、骨格が materialization 時に付与する source-level indentation の pin とする。

### 2. `pipeline.py` の逐語変更

[pipeline.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:48) の import。

Before:

```python
from .axis_trigger_gating import (MARKER_ID as TRIGGER_MARKER_ID,
                                  SOURCE_REL as TRIGGER_SOURCE_REL)  # noqa: E402
```

After:

```python
from .axis_trigger_gating import (
    MARKER_ID as TRIGGER_MARKER_ID,
    PREDICATE_HOLE_INDENT as TRIGGER_PREDICATE_HOLE_INDENT,
    SOURCE_REL as TRIGGER_SOURCE_REL,
)  # noqa: E402
```

[pipeline.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:71) の比較本体。

Before:

```python
def _require_materialized_trigger_predicate(
        evidence: SourceEvidence, binding: TriggerGateBinding,
) -> None:
    """Bind one candidate mask to the exact one-line materialized source hole."""
    source_path = os.path.join(evidence.source_root, TRIGGER_SOURCE_REL)
    try:
        marker = parse_template_file(source_path, TRIGGER_MARKER_ID)
        hole_lines = None if marker is None else tuple(marker.hole_text.values())
        expected = emit_predicate(TriggerGateIR(binding.mask)).strip().encode("utf-8")
    except (OSError, UnicodeError, TypeError, ValueError):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None
    if (hole_lines is None or len(hole_lines) != 1
            or hole_lines[0].strip().encode("utf-8") != expected):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None
```

After:

```python
def _require_materialized_trigger_predicate(
        evidence: SourceEvidence, binding: TriggerGateBinding,
) -> None:
    """Bind one candidate mask to the exact one-line materialized source hole."""
    source_path = os.path.join(evidence.source_root, TRIGGER_SOURCE_REL)
    try:
        marker = parse_template_file(source_path, TRIGGER_MARKER_ID)
        hole_lines = None if marker is None else tuple(marker.hole_text.values())
        expected = (
            TRIGGER_PREDICATE_HOLE_INDENT
            + emit_predicate(TriggerGateIR(binding.mask))
        ).encode("utf-8")
    except (OSError, UnicodeError, TypeError, ValueError):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None
    if (hole_lines is None or len(hole_lines) != 1
            or hole_lines[0].encode("utf-8") != expected):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None
```

[pipeline.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:66) の `_TRIGGER_PREDICATE_REJECTION` と、[pipeline.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:777) の呼び出しは変更しない。

## fixture の是正

[test_campaign.py:5324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5324) の直前へ、次の方針の helper を置く。

```python
def _write_materialized_trigger_source(
        source_path: str,
        predicate: str,
        *,
        hole_line: str | None = None,
) -> str:
    from orchestrator.campaign import axis_trigger_gating, p3_s4_loop
    from orchestrator.campaign.diff_quarantine import parse_template_file

    base_text = (
        f"// EVOLVE-BLOCK-BEGIN {axis_trigger_gating.MARKER_ID}\n"
        "#if BACKOFF_TRIGGER_GATING\n"
        f"{axis_trigger_gating.PREDICATE_HOLE_INDENT}"
        "izanagi_gate_pass = true;\n"
        "#else\ntrue;\n#endif\n"
        f"// EVOLVE-BLOCK-END {axis_trigger_gating.MARKER_ID}\n"
    )
    with open(source_path, "w", encoding="utf-8") as stream:
        stream.write(base_text)

    marker = parse_template_file(source_path, axis_trigger_gating.MARKER_ID)
    assert marker is not None
    materialized = p3_s4_loop.render_hole(base_text, marker, predicate)

    lines = materialized.split("\n")
    if hole_line is not None:
        lines[marker.hole_first - 1] = hole_line
        materialized = "\n".join(lines)

    with open(source_path, "w", encoding="utf-8") as stream:
        stream.write(materialized)
    return lines[marker.hole_first - 1]
```

`render_hole` 由来にする案は採用可能で、採るべきである。実 materializer と同じ「元 hole の indent を implementation に付ける」経路を通るため、現在の無インデント fixture との乖離を除ける。テスト専用 helper は実 parser と renderer を使い、軸定数と patch の一致は別の非循環な drift テストで固定する。

### 正常系 fixture

[test_campaign.py:5331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5331)–5339。

Before:

```python
predicate = emit_predicate(TriggerGateIR(20))
with open(source_path, "w", encoding="utf-8") as stream:
    stream.write(
        f"// EVOLVE-BLOCK-BEGIN {axis_trigger_gating.MARKER_ID}\n"
        "#if BACKOFF_TRIGGER_GATING\n"
        f"{predicate}\n"
        "#else\ntrue;\n#endif\n"
        f"// EVOLVE-BLOCK-END {axis_trigger_gating.MARKER_ID}\n"
    )
```

After:

```python
predicate = emit_predicate(TriggerGateIR(20))
hole_line = _write_materialized_trigger_source(source_path, predicate)
assert hole_line == "  " + predicate
```

後続の `result.certified` assert により、正規形 `'  ' + emit_predicate(...)` が admission と build 経路を通ることを確認する。

### crossed fixture

[test_campaign.py:5384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5384)–5392。

Before:

```python
predicate_a = emit_predicate(TriggerGateIR(20))
with open(source_path, "w", encoding="utf-8") as stream:
    stream.write(
        f"// EVOLVE-BLOCK-BEGIN {axis_trigger_gating.MARKER_ID}\n"
        "#if BACKOFF_TRIGGER_GATING\n"
        f"{predicate_a}\n"
        "#else\ntrue;\n#endif\n"
        f"// EVOLVE-BLOCK-END {axis_trigger_gating.MARKER_ID}\n"
    )
```

After:

```python
predicate_a = emit_predicate(TriggerGateIR(20))
hole_line = _write_materialized_trigger_source(source_path, predicate_a)
assert hole_line == "  " + predicate_a
```

binding は従来どおり mask 21 のままにする。これにより、インデント不一致ではなく mask 20/21 の意味的不一致を検査するテストへ戻る。WAL の error 逐語 assert は変更しない。

## pin drift テスト

[test_campaign.py:5324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5324) 付近へ次を新設する。

`orchestrator/tests/test_campaign.py::test_trigger_predicate_hole_indent_matches_template_patch_bytes`

- `patches/<TEMPLATE_PATCH>` を `rb` で読む。
- marker の hunk 内で `+#if BACKOFF_TRIGGER_GATING` と直後の `+#else` を特定する。
- その間が次の 1 行だけであることを assert する。

```python
expected_hole = (
    b"+"
    + axis_trigger_gating.PREDICATE_HOLE_INDENT.encode("utf-8")
    + b"izanagi_gate_pass = true;"
)
assert patch_lines[if_index + 1:else_index] == [expected_hole]
```

これにより、単に同じ行が patch 内の別位置に存在するだけでは通らず、実 hole payload の indent drift を検出する。

## テスト nodeids

変更・新設する 7 nodeids は次のとおり。

1. `orchestrator/tests/test_campaign.py::test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds`
   - `b"  "+E20` の正規 materialization が通る正例を固定する。

2. `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_crossed_materialized_predicate_and_mask`
   - 正規 indent の E20 と binding mask 21 の crossed binding を拒否し、既存 WAL error 逐語を保持する。

3. `orchestrator/tests/test_campaign.py::test_trigger_predicate_hole_indent_matches_template_patch_bytes`
   - pin した `b"  "` と骨格 hole の実 payload bytes の drift を閉じる。

4. `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_outer_spaces`
   - `b"  "+E20+b"  "` を拒否する。

5. `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_leading_tab`
   - `b"\t"+E20` を拒否する。

6. `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_trailing_space`
   - `E20+b" "` を拒否する。

7. `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_four_space_indent`
   - `b"    "+E20` を拒否する。

4–7 は共通 helper で materialized source を作り、hole 1 行だけを指定 bytes に置換して `_require_materialized_trigger_predicate` を直接呼ぶ。各 nodeid を独立させ、素の Python 実行との互換性を崩す pytest parametrization は増やさない。

## 受理集合が縮むことの証明

mask `m` の emitter 出力を `E_m`、parse 済みの唯一の hole line を `h`、`I = "  "` とする。

変更前:

```text
A_old(m) = { source |
  marker が parse 可能
  ∧ hole がちょうど 1 行
  ∧ strip(h) = strip(E_m)
}
```

変更後:

```text
A_new(m) = { source |
  marker が parse 可能
  ∧ hole がちょうど 1 行
  ∧ UTF8(h) = UTF8(I + E_m)
}
```

`I` は whitespace だけなので、

```text
h = I + E_m
⇒ strip(h) = strip(I + E_m)
⇒ strip(h) = strip(E_m)
```

したがって、すべての mask について

```text
A_new(m) ⊆ A_old(m)
```

さらに `h=E_m`、`h="\t"+E_m`、`h=I+E_m+" "` は変更前に通り変更後に落ちるので、包含は真に狭い。新規に通る source は 1 つもない。

## 波及確認

grep 結果:

- `_require_materialized_trigger_predicate` の定義以外の呼び出しは [pipeline.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:777) の 1 箇所だけ。
- reject は [pipeline.py:792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:792) で既存どおり `admission-error` prebuild abort となる。
- materialized source の `marker.hole_text` を admission 判定として読む直接 consumer は、この関数だけだった。
- [p3_s4_loop.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:170) は骨格 hole の indent を読む materializer。
- [p3_s4_loop.py:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:229) と [diff_quarantine.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:333) は template/quarantine consumer であり、materialized predicate と binding の admission consumerではない。
- `s1_verify_extime_calibration.py:342-345` は `quarantine` を経由する間接 materialization producer。変更不要。

`emit_predicate`、`canonicalize_predicate`、正準集合、指定された 8c 結線 wave 所有ファイルには触れない。

## 裁定パッケージ候補

残件は親 brief から継続する T-515 の 1 件だけ。raw hash による reject variant 重複の影響実測後に再裁定し、本プランでは実装しない。

指定外の 8c provenance/source-closure/WAL 層は読まず、そこまで byte 同一性を保証したとは主張しない。ただし今回の限定 grep では、`parse_template_file`、`hole_text`、`hole_first/hole_last` を使う別の materialized-source admission consumer は検出されなかった。