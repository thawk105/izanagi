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

## 受入 1 回目の赤と、その後のユーザー裁定 (追記)

1 回目の受入全走 (request `905034.nqsv`) は **2 failed**。失敗は
`test_t793_report.py` の 2 node で、`docs/decisions.md` の D291 後継走査が
`("D292",)` を期待するのに `("D292", "D305")` を得る同一原因だった。
`git diff main...HEAD -- docs/decisions.md` は空、D305 も当該テストも main `427da17c`
に存在するため **main 自体が赤**であり、本 wave は原因でも増幅でもない。

ユーザーは当初「既存の赤は免除リストに入れて」と指示したが、受入の赤を無視する機構は
repo に存在せず (`DW-S04` はむしろ「受入全走は免除せず」)、新設は受入判定に触れる。
そこで択一を提示し、**(c) テスト側を直す**が選ばれた。

修正は自作せず、並行 wave [T-827] の `292151a5` を `-x` 付きで cherry-pick した
(本 branch では `ac994a33`)。こちらの Codex author も同型の修正を書き終えていたが、
相手側だけが実走 9 passed と「D292 を落とす変異で KILLED」の裏取りを済ませており、
同一ファイルへ非同一の修正が 2 本あると land で衝突するため自作分を破棄した。

修正の形は「伸びる集合の完全一致」を捨て、`status` の完全一致 + `"D292"` の membership +
構造性質 (重複なし・番号昇順) に置き換えるもので、D291 に言及する decision が増えても
壊れない。精度 (誤検出しないこと) は凍結 blob を使う既存 6 node が引き続き担う。

採用後の焦点走 = **9 passed / rc=0** (request `905197.nqsv`)。

## [T-717] の再訪条件に関する peer 実測 (追記)

[T-827] から、受入全走が **558 → 188 秒**になったとの実測を受領した。
裁定の再訪条件は「receipt 解決の短縮が効いたら 40 分へ戻す」であり、本 wave では
裁定どおり 60 分へ上げた実装を撤回しない。残る律速は `test_codex_reasoning_ab` 259 秒、
`test_s8b_floor_campaign` 727 秒/8 node (いずれも peer 実測)。戻しの起票判断の材料として残す。
