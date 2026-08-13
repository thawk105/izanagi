# [T-1048] 段 2 実装プラン

以下の行番号は現行 HEAD 基準。変更後は後続行が移動する。

## 1. 変更面

### 1.1 凍結 epilogue 定数

[axis_trigger_gating.py:27-50](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/axis_trigger_gating.py:27) の `FROZEN_TEMPLATE_BLOCK_BYTES` 直後、`FLAG` より前へ次を追加する。

```python
FROZEN_TEMPLATE_EPILOGUE_BYTES = (
    b"#if BACKOFF_TRIGGER_GATING\n"
    b"  if (izanagi_gate_pass) {\n"
    b"    Backoff::backoff(FLAGS_clocks_per_us);\n"
    b"  }\n"
    b"#endif\n"
)
```

逐語値は patch の [107-111 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/patches/silo-backoff-trigger-gating-variant.patch:107) から追加行の先頭 `+` だけを除いた 108 bytes。末尾 LF を含み、末尾空白はない。

既存の次の値は一切変更しない。

- `FROZEN_TEMPLATE_HOLE_BYTES`
- `FROZEN_TEMPLATE_BLOCK_BYTES`
- `PREDICATE_HOLE_INDENT`
- `TEMPLATE_PATCH`
- `patches/silo-backoff-trigger-gating-variant.patch`

### 1.2 build admission

[build_admission.py:34-40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:34) で `FROZEN_TEMPLATE_EPILOGUE_BYTES` を import する。

[build_admission.py:169-199](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:169) の署名は変えない。

```python
def _require_materialized_trigger_axis_predicate(
    evidence: SourceEvidence,
) -> None:
```

新しい検査は、marker 件数・順序を拒否する現行 [185-186 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:185) の直後、`block = ...` と pristine の早期 `return` より前へ差し込む。

予定する分岐は次のとおり。

```python
epilogue_start = ends[0].end()
epilogue_end = epilogue_start + len(FROZEN_TEMPLATE_EPILOGUE_BYTES)
if raw[epilogue_start:epilogue_end] != FROZEN_TEMPLATE_EPILOGUE_BYTES:
    _reject_trigger_axis()
if raw[
    epilogue_end:epilogue_end + len(FROZEN_TEMPLATE_EPILOGUE_BYTES)
] == FROZEN_TEMPLATE_EPILOGUE_BYTES:
    _reject_trigger_axis()
```

これにより、END 行末の LF の次 byte から逐語 epilogue が始まらなければ拒否する。2 本目の同一 epilogue が直後に連結された場合も拒否する。

その後の pristine/block-hole 検査は現行のまま残す。`_TRIGGER_EXPECTED_HOLE_BYTES`、`_TRIGGER_TEMPLATE_PREFIX/SUFFIX`、`_reject_trigger_axis()`、拒否メッセージも変更しない。

関数 docstring には次を明記する。

- raw bytes の frame と epilogue を検査するだけで、生きた C++ であることは保証しない。
- コメント化、raw string の囮、前処理器による識別子の置換は残存限界。
- C++ 字句解析、BOM/NUL/decode の全体検査は行わない。
- ABA 窓は従来どおり残る。

### 1.3 test helper と新規テスト

[test_build_admission.py:21-29](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:21) に新定数を import する。

[test_build_admission.py:122-126](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:122) は次の概念上の署名へ広げる。

```python
def _trigger_source_bytes(
    block: bytes,
    *,
    epilogue: bytes = FROZEN_TEMPLATE_EPILOGUE_BYTES,
    after: bytes = b"int izanagi_after_block = 0;\n",
) -> bytes:
```

既定値では `marker_explanation + block + epilogue + after` を返す。これにより既存の block 変異テストが「epilogue 欠落」という別理由で通る恒真化を防ぐ。

[test_campaign.py:5361-5383](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_campaign.py:5361) の `_write_materialized_trigger_source(...) -> str` は署名を変えず、`base_text` を次から作る。

```python
(
    axis_trigger_gating.FROZEN_TEMPLATE_BLOCK_BYTES
    + axis_trigger_gating.FROZEN_TEMPLATE_EPILOGUE_BYTES
).decode("utf-8")
```

`render_hole`、`hole_line` 上書き、CRLF/CR fixture の処理は維持する。

### 1.4 記録面

段 7 で親が新 wave insight の `README.md` に次を残す。T-897 の歴史記録は書き換えない。

- 変更後の受理言語
- R2 のうち閉じた区間
- R1、前処理器迂回、R3 が残ること
- global な epilogue 出現回数検査を採らなかった理由

## 2. 変更後の受理言語全文

`B0` を既存 `FROZEN_TEMPLATE_BLOCK_BYTES`、`h0` を既存 hole、`P` と `S` を `B0.partition(h0)` の prefix/suffix、`H32` を現行 32 個の `_TRIGGER_EXPECTED_HOLE_BYTES`、`E` を新 epilogue とする。

### source 不在・axis 不在

現行三分岐をそのまま維持する。

1. `TRIGGER_SOURCE_REL` が存在しない場合は受理。
2. `FileNotFoundError` 以外の読取失敗は拒否。
3. BEGIN/END directive が双方 0 件の場合:

   - `BACKOFF_TRIGGER_GATING` または `izanagi_gate_pass` があれば拒否。
   - 両 token ともなければ stock/non-trigger source として受理。

### marker がある場合

次をすべて満たす場合だけ受理する。

1. BEGIN と END が各 1 件だけ存在し、BEGIN が END より前。
2. BEGIN 行頭から END 行末までの block が、次のどちらか一方。

   - pristine: `B == B0`
   - materialized hole: `B == P + h + S` かつ `h ∈ H32`

3. `raw[END.end():END.end()+len(E)] == E`。
4. その直後から同じ `E` がもう一度始まらない。

block より前の bytes と、正しい 1 本の `E` より後の bytesは、直後の完全重複を除いて凍結しない。したがって patch に存在する後続空行、`#if ADD_ANALYSIS`、その他の正当な後続コードは受理される。

### 明示的な拒否集合

上記以外を拒否する。今回純増する拒否は次である。

- epilogue の全削除または途中切断
- epilogue 5 行の任意 byte 改変
- END と epilogue の間への空白、空行、コメント、代入、directive などの挿入
- END 直後の epilogue の完全重複
- epilogue が別位置にだけ存在する source
- block は pristine/H32 でも epilogue が一致しない source

global な `raw.count(E) == 1` は採らない。別関数、コメント、raw string 内の同一 bytes まで拒否して T-897 で実証済みの過剰拒否を再導入するためである。重複負例は凍結境界に直結した `END + E + E` とする。

### 受理集合が広がらない証明

現行 marker あり受理集合は `B == B0` または `B == P + h + S, h ∈ H32` の二言語だけである。変更後はその同じ条件へ `E` の隣接一致と直後非重複を論理積で加える。

したがって、

```text
Lnew(markerあり) ⊂ Lold(markerあり)
```

である。source 不在・marker/token 三分岐は不変なので、どの入力についても旧拒否を新受理へ反転させる分岐はない。

## 3. fixture の完全棚卸し

| ファイル・fixture | 現在の epilogue | 新 gate 到達 | 新たに赤くなる箇所 | 計画 |
|---|---|---:|---|---|
| [test_build_admission.py:122](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:122) `_trigger_source_bytes` | 欠落 | 到達 | exact-emitter 2 case [288](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:288)、pristine [297](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:297)、one-read [489](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:489)、runtime recheck の初回 derive [508](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:508) | helper 既定へ `E` を追加 |
| 同 helper を使う frame/noncanonical 負例 [414](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:414)、[456](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:456)、precedence [540](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:540) | 欠落 | 到達 | 期待は元から reject なので表面上は赤くならないが、拒否理由が epilogue 欠落へ退化する | helper 更新で本来の変異帰属を維持 |
| [test_campaign.py:5361](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_campaign.py:5361) `_write_materialized_trigger_source` | 欠落 | 一部到達 | positive build-start [5575](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_campaign.py:5575) が abort、crossed mask [5622](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_campaign.py:5622) が期待する binding 層より手前の axis error になる | base を `BLOCK + E` にする |
| 同 helper の outer-space〜CR-only 10 負例 [5445-5572](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_campaign.py:5445) | 欠落 | `_require_materialized_trigger_predicate` を直接呼ぶため非到達 | 新たな赤なし | helper 更新のみ。binding 層の狙いを維持 |
| [test_s8a_trigger_sweep.py:166-188](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_s8a_trigger_sweep.py:166) `_TEMPLATE` | [181-186](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_s8a_trigger_sweep.py:181) に exact `E` あり | quarantine のみ | なし | 変更不要 |
| [test_s1_direct_comparison.py:81-95](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_s1_direct_comparison.py:81) `_FAKE_GATE_TRANSACTION_CC`、[174-190](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_s1_direct_comparison.py:174) `_fixture_gate_patch` | 欠落 | source digest/quarantine のみ。後者は resolver fake | なし。block 自体も旧凍結 block ではないので epilogue だけが新原因ではない | 変更不要 |
| [test_p3_s4_loop_trigger_gating.py:76-103](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:76) `_TEMPLATE` | [96-100](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:96) に exact `E` あり | sink は spy/no-build | なし | 変更不要 |
| [test_p3_exploration_namespace.py:306-332](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_exploration_namespace.py:306) trigger inline fixture | [325-329](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_exploration_namespace.py:325) に exact `E` あり | `run_campaign` は spy | なし | 変更不要 |
| [test_p3_autonomous_workload_trial.py:627-638](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_autonomous_workload_trial.py:627) preview fixture、[1012-1031](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_p3_autonomous_workload_trial.py:1012) no-build CLI fixture | 欠落 | preview/quarantine または `--no-build` | なし。block も縮小版で旧 admission 正例ではない | 変更不要 |

したがって実装差分が必要な fixture file は `test_build_admission.py` と `test_campaign.py` の 2 本だけである。

## 4. 新設・強化するテスト

[test_build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:287) に集約する。

1. 正例

   - `test_trigger_axis_semantic_admission_accepts_exact_emitter_bytes_without_binding` を mask `0..31` 全件へ拡張し、全件 `BLOCK(mask) + E` で受理。
   - pristine `B0 + E` の受理を維持。
   - `test_trigger_axis_semantic_admission_does_not_freeze_bytes_after_epilogue` を追加し、`E` 後の空行や通常コードが受理されることを固定する。

2. 負例

   `test_trigger_axis_semantic_admission_rejects_noncanonical_epilogue` を parameterize する。

   - `deleted`: `epilogue=b""`
   - `modified`: 条件行または gated call の 1 byte 改変
   - `gap-before`: `epilogue=b"\n" + E`
   - `duplicated-adjacent`: `epilogue=E + E`

   いずれも canonical pristine blockを使い、拒否原因を epilogue だけへ単離する。

3. patch 整合

   既存 [test_frozen_trigger_block_matches_template_patch_bytes:554](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:554) の兄弟として、次を追加する。

   ```python
   def test_frozen_trigger_epilogue_matches_template_patch_bytes():
   ```

   patch の `+END` の直後 5 行がすべて追加行であることを確認し、先頭 `+` を除いて連結した bytes が `FROZEN_TEMPLATE_EPILOGUE_BYTES` と完全一致することを断言する。END との隣接性もこのテストで固定する。

4. 回帰維持

   - source は 1 回だけ読む。
   - derive/require は再検査するが receipt replay は再検査しない。
   - gateway 呼出し数の AST 制約は不変。
   - 既存 frame/hole 負例は canonical epilogue を伴わせ、元の拒否理由を維持する。

## 5. provisional 裁定への推奨

| 裁定 | 推奨 | 理由 |
|---|---|---|
| P1 epilogue 側だけ凍結 | 採る | 32 hole はすべて無条件代入であり、gate-on 時は BEGIN 前の初期値を上書きする。gate-off 時は既存 `#else` の stock backoff が実行される。prologue 凍結は純増保証を持たず、過剰拒否だけを増やす。 |
| P2 exact adjacency | 採る | search 型では END と epilogue の間への再代入・directive 挿入を許す。`ends[0].end()` を唯一の開始位置にする。 |
| P3 現行三分岐維持 | 採る | stock/non-trigger source を新たに止めず、marker 消去だけは skeleton token で従来どおり拒否できる。 |
| P4 後続空行を凍結しない | 採る | `#endif\n` までで gated call は完了する。後続空行や `ADD_ANALYSIS` を凍結しても R2 保証は増えず、正当 source の過剰拒否になる。 |
| P5 R1 を閉じない | 採る | コメント、raw string、前処理器を正しく判定するには再び C++ 字句・前処理解析が必要になる。T-897 の偽受理と過剰拒否を再導入しない。残存限界を docstring と insight に明記する。 |

## 6. scope 外

新規の裁定パッケージ候補はない。既知の次の境界は実装しない。

- R1: block/epilogue 全体のコメント化、raw string 囮
- `#define izanagi_gate_pass` など前処理器による迂回
- R3: evidence 取得から compiler read までの ABA 窓
- source 全体での epilogue 出現回数検査
- S8b portable binary と admission receipt の束縛
- quarantine 専用の縮小 fixture を full frozen block へ統一する整理

実装後の焦点確認は親が `tools/run_tests.py` 経由で上記 7 test file を走らせ、その後に規定の全受入を行う。この read-only 段では pytest 実走結果を主張しない。

## 総括

- 新定数は `FROZEN_TEMPLATE_EPILOGUE_BYTES`、patch 由来の逐語 108 bytes とする。
- 検査は END marker の行末直後、既存 pristine 早期 return より前へ置く。
- 現行 pristine と hole 32 通りは一切変えず、隣接 epilogue 条件を論理積で足す。
- 削除、改変、END 後 gap、直結重複を拒否し、epilogue 後の空行は受理する。
- 新たに赤くなる実 fixture は `test_build_admission.py` と `test_campaign.py` の helper 由来だけである。
- patch、既存 block/hole、受理 hole 集合、三分岐は変更しない。
- R1、前処理器迂回、R3 は残存限界として明記し、C++ 字句解析は再建しない。