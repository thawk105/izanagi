結論として、P1 の境界認識は正しいです。trigger 述語の畳み込みは共有 `quarantine` 内だけで行い、U-2 は `prepare_cell` に独立した固定 allowlist を置くのが最小かつ fail-closed です。

## U-1 — 正準 bytes への畳み込み

### 正準化 API

[trigger_gate_binding.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:12) と [trigger_gate_binding.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:75) を変更する。

- 公開関数名: `canonicalize_predicate`
- 署名: `canonicalize_predicate(text: object) -> str`
- 戻り値: `emit_predicate(TriggerGateIR(mask))` が返した正準文字列そのもの
- 失敗: 非 exact `str`、正準集合外なら既存 `_reject()` を使い、`TriggerGateBindingError("invalid trigger gate binding")` を `from None` で送出
- `__all__` に追加する
- `is_canonical_predicate` の strip 同値受理は変更しない

正準表は次の二層にする。

1. private な `_build_canonical_predicate_index(emitted) -> dict[str, str]` で、`emitted.strip()` をキー、未 strip の emitter 出力を値にする。
2. `CANONICAL_PREDICATES` は従来どおりそのキー集合の `frozenset` とし、公開値と受理集合を変えない。

同じ strip key が複数 mask から生成された場合は import 時 `RuntimeError` に倒す。これにより P2 の「`text.strip()` を返すのではなく emitter bytes を返す」が構造上明確になる。[expected_predicate_sha256:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:75) は変更しない。

### 呼び出し境界

[p3_s4_loop.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:202) の既存 membership reject を保ち、その成功直後にだけ次を入れる。

```python
implementation = trigger_gate_binding.canonicalize_predicate(implementation)
```

これは [render_hole:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:225) より前なので、`edited_text`、`working_diff`、`write=True` の実ファイルがすべて正準化される。`render_hole` 自体は軸共通なので変更しない。

本番コードで `render_hole` を呼ぶのはこの1箇所だけであり、trigger の source materialize に別経路はない。確認した入口は以下のすべてで、いずれも同じ `quarantine` に合流する。

- S8a sweep: [s8a_trigger_sweep.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:421)、[同:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:443)
- trigger loop／preview: [p3_s4_loop_trigger_gating.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_trigger_gating.py:404)、[同:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_trigger_gating.py:776)、[同:888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_trigger_gating.py:888)
- autonomous trial preview: [p3_autonomous_workload_trial.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_autonomous_workload_trial.py:660)
- S-1 materializer: [s1_direct_comparison.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:551)
- extime calibration: [s1_verify_extime_calibration.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_verify_extime_calibration.py:339)

`pipeline._require_materialized_trigger_predicate` は [pipeline.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:71) の読取検証であり materializer ではない。freeze 生成時の文字列保存は U-3/T-492 の面なので触れない。

### 3 consumer の判定

| consumer | 畳み込み | 理由 |
|---|---:|---|
| [s1_direct_comparison.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:521) | 不要 | 早期診断用 membership。実 materialize は同:551 から共有境界へ入る。ここで畳むと既存の「quarantine へ逐語渡し」契約も不要に変える。 |
| [s1_verify_extime_calibration.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_verify_extime_calibration.py:222) | 不要 | freeze と構築対象の意味検査。source 化は同:339 の `quarantine` が担当する。 |
| [p3_s4_loop.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:202) | 必要 | 唯一の共有 source-hole materialize 境界。membership 成功後、render 前に畳む。 |

### comparator 不変条件

trigger marker は [axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/axis_trigger_gating.py:23)、sort marker は [p3_s4_loop_sort.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_sort.py:96) で別値である。正準化代入を `marker_id == TRIGGER_MARKER_ID` ブロック内に閉じ、sort/backoff には一切適用しない。

実 freeze の comparator は [known_axes_freeze.json:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/output/s1-freeze/known_axes_freeze.json:167) などで先頭空白を持つ。既存の逐語引き渡し検査 [test_s1_direct_comparison.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:454) は変更しない。

## U-2 — configuration allowlist

### 定数と拒否位置

[s1_direct_comparison.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:47) 付近に、次の module-private 定数を追加する。

```python
_PREPARE_CELL_CONFIGURATIONS: frozenset[str] = frozenset({
    "backoff_fixed_best",
    "ident_all",
    "p2_2_flag_opt",
    "sort_best",
    "stock_common",
    "system_gate",
})
```

既存の同値集合は [s1_measurement_freeze.CONFIGURATIONS:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_measurement_freeze.py:40) と [s8b_holdout_freeze.VARIANT_NAMES:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_holdout_freeze.py:76) にある。ただし、どちらも producer schema であり、将来の schema 拡張を materializer が自動許可すると U-2 の独立閉包を失う。したがって runtime authorization には直接流用せず、固定集合を意図的に独立させる。共有定数へ移動する案は、自己 hash 対象の `s1_measurement_freeze.py` を変更して freeze cascade を起こすため採らない。

[prepare_cell:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:494) の `variant/configuration` 型検査直後、flags 解釈や checkout より前に次を置く。

```python
if configuration not in _PREPARE_CELL_CONFIGURATIONS:
    raise DriverError(f"未知の freeze configuration: {configuration!r}")
```

例外は既存 [DriverError:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:75)。新しい例外型は作らない。

`stock_common` と `p2_2_flag_opt` 用の分岐は追加しない。既存4分岐を通らず、[source_digest.resolve:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:562) から flags-only `PreparedCell` を yield する現行挙動を維持する。

## S8b caller 棚卸し

| 経路 | `configuration` の由来 | 影響判定 |
|---|---|---|
| `s8b_materialization` | [binding_entry:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:103) で `entries[configuration_id]` を引き、[prepared_binding:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:135) で同じ ID を `cell["configuration"]` に設定する。改名・別名化なし。 | active freeze の6値は全受理。未知 ID は意図どおり拒否。 |
| `s8b_floor_campaign` | [floor_contract.enumerate_cells:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_floor_contract.py:328) が `variant_binding.entries` の key を列挙し、[build_cells:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_floor_campaign.py:982) がその `configuration_id` をそのまま渡す。 | active freeze は `VARIANT_NAMES` の6値で、verify も [s8b_holdout_freeze.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_holdout_freeze.py:809) で再構成一致を要求するため壊れない。 |
| `s8b_oracle_driver` | [run_block:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1155) が既定で実 `prepare_cell` を選び、[schedule row:1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1301) の `configuration_id` を [同:1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1316) から共有 wrapper へ渡す。 | 実 freeze と oracle fixture はともに6値。未知 schedule は materializer で恒久 prepare refusal になる。 |

注入経路も確認済み。

- S-1 本番は [run_role:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:623) の既定 `prepare_cell` を [同:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:757) で呼ぶ。既存テストは通常 `_prepared` 等を注入している。
- floor は [s8b_floor_campaign.py:2742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_floor_campaign.py:2742) で実関数を既定化する。実関数を通す slow canary は [test_s8b_floor_campaign.py:2560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_floor_campaign.py:2560) と [同:2603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_floor_campaign.py:2603) で、どちらも `stock_common`。
- oracle の実関数 canary は [test_s8b_oracle_driver.py:3877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_oracle_driver.py:3877) から [同:3902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_oracle_driver.py:3902) までで、`stock_common`。
- [test_s8b_materialization.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_materialization.py:183) などの `"stock"` fixture は独自 fake `prepare_fn` を渡しており、実 `prepare_cell` を通らないため壊れない。
- `s8b_materialization.prepare_binding` の既定値は [s8b_materialization.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:145) の実関数だが、現行の唯一の repo 内 caller は [test_s8b_oracle_driver.py:1247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s8b_oracle_driver.py:1247) で明示 fake を渡している。

## 追加テスト

既存期待値は書き換えず、以下を追加する。

1. [test_trigger_gate_binding.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_trigger_gate_binding.py:215)
   - `test_canonicalize_predicate_returns_emitter_bytes_for_outer_whitespace_equivalents`
   - 全32 mask ×代表的な外周空白を正準 emitter 出力へ解決すること。
   - private index builder へ外周空白付き synthetic emitter 出力を渡し、値側の空白を保存することも固定する。
2. 同ファイル
   - `test_canonicalize_predicate_rejects_nonmember_with_uniform_error`
   - 非正準文、bytes、`None`、`str` subclass が既存の単一エラー fingerprint になること。
3. [test_p3_s4_loop.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:171)
   - `test_trigger_quarantine_materializes_outer_whitespace_equivalents_identically`
   - exact／space／tab／CRLF／NBSP／U+3000 入力の `edited_text` と `working_diff` が byte-exact に同一になること。
4. 同ファイル
   - `test_sort_quarantine_preserves_outer_whitespace_bytes`
   - sort marker では外周空白付き comparator と strip 版の `edited_text` が異なり、元 comparator が逐語保持されること。
5. [test_s1_direct_comparison.py:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:409)
   - `test_prepare_whitespace_equivalent_gate_has_same_src_token_and_variant_id`
   - 実 `quarantine` と fixture source を使い、materialized file bytes から token を返す fake resolver を置く。exact／空白付きで同じ `PreparedCell.src_token` と `pipeline.variant_id` になること。
6. 同ファイル
   - `test_prepare_accepts_exact_six_configuration_allowlist`
   - 分岐ごとに有効な variant を与え、6構成すべてが yield すること。
7. 同ファイル
   - `test_prepare_flags_only_configurations_do_not_apply_patch_or_quarantine`
   - `stock_common`／`p2_2_flag_opt` で patch・quarantine が呼ばれず、flags がそのまま Genome になること。
8. 同ファイル
   - `test_prepare_rejects_unknown_configuration_before_checkout`
   - `"system-gate"` と有効 flags を直接 `prepare_cell` に渡し、checkout より前に exact `DriverError` とメッセージで拒否すること。
9. 同ファイル
   - `test_prepare_configuration_allowlist_matches_producer_domains`
   - local allowlist、`s1_measurement_freeze.CONFIGURATIONS`、`s8b_holdout_freeze.VARIANT_NAMES` が現時点で同じ6値であること。将来の producer 拡張を自動認可せず、明示レビューを要求する drift guard とする。

## 凍結 golden を壊さない根拠

- [FROZEN_MANIFEST:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_frozen_artifacts.py:38) の対象は output 23件であり、本案はそれらを編集・再生成しない。
- 現行6件の `gate_predicate` は emitter exact bytes なので、正準化前後の source bytes は同一。
- comparator 3件は外周空白付きだが、trigger marker 限定なので一切変化しない。
- [s1_expected_goldens.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/s1_expected_goldens.py:624) 以下が固定する6構成、述語、comparator の値は変更しない。
- U-2 は既存6構成をすべて受理し、未知だけを新たに拒否する。既存 freeze の materialization 結果は変わらない。

これは静的根拠であり、pytest の実測結果ではない。

## 変異検査候補

| 変異 | 赤くするテスト | 単一理由性 |
|---|---|---|
| `quarantine` の正準化代入を削除／`implementation` 自身を返す | `test_trigger_quarantine_materializes_outer_whitespace_equivalents_identically`、identity 統合テスト | 外周空白は現行 membership と diff quarantine の双方を通るため、materialized bytes 差だけで赤になる。 |
| trigger marker guardを外して全 marker を正準化 | `test_sort_quarantine_preserves_outer_whitespace_bytes` | sort は upstream membership を通らない直接境界入力。comparator 改変だけで赤になる。 |
| index の値を `emitted` から `emitted.strip()` に変更 | synthetic index-builder test | synthetic emitter の外周空白だけが差となり、現行 emitter の strip 恒等性による equivalent mutant を避ける。 |
| allowlist reject を削除 | `test_prepare_rejects_unknown_configuration_before_checkout` | freeze verifier を通さない直接入力で、flags は有効。現行なら flags-only yield まで到達するため新 gate だけを測れる。 |
| `stock_common` または `p2_2_flag_opt` を集合から削除 | 6構成正例／flags-only テスト | 各 fixture は分岐固有条件を満たしており、allowlist 欠落だけで赤になる。 |
| `"system-gate"` を集合へ追加 | 未知構成負例 | 有効 flags と fake resolver を用いるため、追加時は他層に止められず flags-only で通過する。 |
| `DriverError` を別例外・別メッセージへ変更 | 未知構成負例 | checkout 前の直接呼び出しで例外契約だけを固定する。 |

## P1〜P4 評価

- P1: 正しい。source-hole materialize の唯一の共有境界は `p3_s4_loop.quarantine`。ただし freeze JSON 生成層は U-3 であり、本 wave の「materialize」は source materialize に限定すると明記する。
- P2: 正しい。正準値は strip 入力ではなく emitter 出力を値に持つ index から返すべき。
- P3: 例外型の判断は正しい。配置は「4分岐の直前」より厳密に、型検査直後・flags 解釈／checkout 前とする。既存 producer 定数を runtime 認可へ直接流用しない点も補足が必要。
- P4: 方向は正しいが不足。trigger identity、sort comparator 非干渉、flags-only 2構成、S8b 実関数 seam、単一理由変異まで追加して初めて裁定条件を固定できる。

pytest、build、freeze 再生成は実行していない。静的な読取・呼び出し追跡のみである。

## 総括

- U-1 は `trigger_gate_binding.canonicalize_predicate(object) -> str` を新設する。
- emitter 出力を値、strip 同値形をキーにし、失敗は既存 `TriggerGateBindingError` とする。
- 呼び出しは trigger marker の `p3_s4_loop.quarantine` 内、render 前の1箇所だけでよい。
- sort comparator、backoff、freeze 生成層には広げない。
- U-2 は `prepare_cell` 固有の固定6構成 `frozenset` を型検査直後に適用する。
- S8b の本番・real canary は全て6構成内で、flags-only 2構成も維持できる。
- golden は編集不要で、追加テストと単一理由変異で差分を固定する。