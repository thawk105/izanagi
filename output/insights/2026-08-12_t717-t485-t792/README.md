# dev-wave [T-717]/[T-485]/[T-792] — worklog 440 裁定束の実施

- **branch:** `worktree-dev-wave-t717-t485-t792`
- **実装 commit:** `67693c12`
- **依頼:** worklog 440 で「実施へ」となった 4 件 ([T-717] [T-485] [T-792] [T-800]) のうち、
  稼働中 wave と射程が重なる項を除いて実施する。

## 除外した項

**[T-800] は実装しなかった。** 裁定文自身が「[T-798]/[T-799]/[T-820]/[T-821]/[T-393] と同じ wave で
1 度に閉じる」と routing しており、その fold transaction wave
(`worktree-dev-wave-t798-t799-finalize`) が稼働中で `tools/dev_wave_land.py` の `_rollback_fold` を
書き換え済みだった (`git diff main...` で 317 行、うち T-800 が対象とする state 検査ブロックを
`expected_transaction_id` 照合込みで全面書換え)。別 branch で同一行を触れば land で衝突する。

## 段 1 前提実測

| 前提 | 実測 | 結果 |
|---|---|---|
| [T-717] `run_tests.py` から walltime を上げられない | `grep -n walltime tools/run_tests.py` = hit 0 | 成立 |
| [T-792] 選択走で 2 node が赤 | request `904675.nqsv` (28S) で **2 failed / 2 selected**、いずれも `ModuleNotFoundError: No module named 'tests'` | 成立 |

## 段 5 で判明した新事実 — 裁定 (b) は 4 行では閉じない

初回の実装子は**実装せず停止**し、新事実を報告した。親が逐語で裏取りして real と裁定した。

- `test_s8b_protocol_builder.py:37` が `from tests import repo_tree_util` を持つ。
- node 1 は `mock.patch.object(repo_tree_util, ...)` で**自分が import した module object の属性**を
  差し替え、SUT はその module 属性を呼ぶ。node 側だけを `orchestrator.tests` へ移すと
  patch 対象と被 patch 対象が別 object になり `len(helper_calls) == 1` が落ちる。
- さらに焦点範囲では `tests` が解決できないため、SUT の import 中に同じ `ModuleNotFoundError` が再発する。

裁定の選択肢は (b) のまま、**親の実装契約を 6 行 (2 ファイル) へ広げて**閉じた。
`from tests import` / `from tests.` の全出現は repo 全体で 3 ファイル 7 行しかなく、
うち 6 行が編集面である (grep 実測)。

## 実測

| 走行 | 範囲 | 結果 |
|---|---|---|
| 修正前 焦点走 | `test_real_repo_serialization.py` 単独 | 2 failed / 2 selected (`904675.nqsv`) |
| 修正後 焦点走 | 上記 + `test_pegasus_dispatch_compute.py` + `test_s8b_protocol_builder.py` | **175 passed / rc=0** (`904845.nqsv`) |
| 全史 provenance | 実装 commit 後 | rc=0 |

## 変異 matrix

spec = `mutation-spec.json` (sha256 `d3ad2b4ece3feb62ffa2bbcd6c773b9949b53ef29b59b67c6cb9fe95f19d3b74`)、
台帳 = `mutation-ledger.json`。anchor commit `67693c12`、
runner = `test_pegasus_dispatch_compute.py` + `test_real_repo_serialization.py` の 2 ファイル
(`test_reflux_ir.py` を含めると M3 が `sys.path` 副作用で SURVIVED になるため意図的に外した)。
baseline rc=0 / 失敗 node 0。

| id | 変異 | 結果 |
|---|---|---|
| M1 | `DEFAULT_WALLTIME` を `"00:20:00"` (下限 2261.25 秒未満) へ | **KILLED** (期待完全一致) |
| M2 | qsub argv の `elapstim_req={walltime}` を旧 literal へ | **KILLED** (期待完全一致、2 node) |
| M3 | 修正した 6 import を `from tests` 系へ戻す | **MISMATCH** (下記 erratum) |

### erratum — M3 が MISMATCH になった理由は検出力の欠落ではない

M3 は意図した 2 node をきちんと落とした。観測 node 集合は期待と**接尾辞 1 つを除いて同一**である。

```
expected: ...::test_protocol_builder_repo_tree_guard_is_wired_to_real_root
observed: ...::test_protocol_builder_repo_tree_guard_is_wired_to_real_root@real-repo
```

接尾辞を付けた形で再登録して再走したところ、harness は**起動前**に
`期待 node が pytest collection に実在しない` で中止した (rc=2、成果物ゼロ)。

`tools/mutation_harness.py` のコードで裏取りした結果、これは harness の実 defect である。

- `_normalize_node()` (`:956`) は `@<group>` 接尾辞を落とさない。
- `_failed_nodes()` (`:974`) は `-rf` の `FAILED <node>` 行を読むため、xdist の loadgroup が
  付ける `@<group>` 込みの node を得る。
- `_collected_nodes()` (`:991`) は `--collect-only -q` を読むため接尾辞なしの node を得る。
- 事前検査 (`:1140`〜`:1147`) は後者と照合するので、**`xdist_group` marker の付いたテストは
  期待 node としてどちらの形でも登録できない** (接尾辞なしなら照合で外れ、接尾辞ありなら
  事前検査で弾かれる)。

`test_real_repo_serialization.py` の node は `real-repo` group に属するため、この wave の
M3 は原理的に KILLED として記録できない。本 wave では harness を直さず所見として返す。

## T-717 に値の変異が無いこと (意図された検出力の欠落)

裁定の再訪条件が「receipt 解決の短縮が効いたら 40 分へ戻す」であるため、
「60 分」という値を pin するテストを新設しなかった。したがって値そのものに対応する実効 gate は
存在せず、変異も登録していない。M1 が pin しているのは値ではなく
「受入実測 1809 秒の 1.25 倍以上」という下限の不等式である。

## scope 外として返す real 所見

`orchestrator/tests/test_s8b_approved.py:31` の `from tests.skiputil import Skip, skip` も
同じ `sys.path` 副作用に依存しており、同ファイル単独の焦点走では同型の偽赤を生む。
本裁定の対象 node ではないため実装しなかった。
