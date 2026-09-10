# [T-2123] 変異 harness の比較器へ xdist group 接尾辞の同形化を入れる

- 日付: 2026-09-02
- wave branch: `worktree-dev-wave-t2123-mutation-node-normalize`
- 実装 commit: `0bc1ab724bd7363c692c4b8c5d0ccd1aa7960519`
- 起票の正本: `docs/archive/worklog-phase3-0901-1128.md` の [T-2123]
- 事故台帳: `docs/failures.md` の F71「再発: 2026-09-01」

## 何が壊れていたか

`DW-M08` は「**期待 node は完全集合**で、同形式へ正規化した記録 node との完全一致だけを
KILLED とする」と要求する。しかし比較器がこの正規化を記録側へ適用していなかった。

pytest-xdist は `--dist loadgroup` のとき、`xdist_group` marker を持つ item の nodeid 末尾へ
`@<group 名>` を付ける (`xdist/remote.py:245-253`、実測 version 3.8.0)。一方、
collection 事前検査が読む `--collect-only` の出力は controller 側なので接尾辞が付かない。
**記録側と検査側の非対称は、この 2 経路の差そのものである。**

その結果、`xdist_group` を持つテストは期待 node に**どちらの表記でも書けなかった**。

| 期待 node の書き方 | 起きること |
|---|---|
| 接尾辞なし | 比較器が接尾辞付きの記録 node と突き合わせて `MISMATCH` |
| 接尾辞込み | collection 事前検査が「期待 node が pytest collection に実在しない」で**起動前に中止** |

回避策 (`--deselect` で外す) は当該テストを変異 matrix の被覆から落とすので、
「その gate が効いている」という証拠が台帳から欠落する。すなわち変異検査の**検出力**が
group 付きテストの範囲でゼロになる。

## 直した座

正規化は**比較の座だけ**で行い、記録は観測の姿を保つ (設計判断は decisions を参照)。

| file | 座 | 変更 |
|---|---|---|
| `tools/mutation_harness.py` | `_match_key` | 一段の接尾辞除去を入れる。**test 名部分にだけ**当てる |
| 同 | 初回 collection 事前検査 | 期待側と collection 側の**両方**を `_match_key` へ |
| 同 | resume の collection record 再照合 | 同上。artifact 再抽出値との順序込み完全一致は手前に維持 |
| 同 | `_reject_flaky_hold_expected_nodes` | held registry 側も `_match_key` 化 |
| `tools/mutation_fanout_contract.py` | `_strip_group_suffix` / `_match_key` | 同形の除去を追加 |
| 同 | `_observed_status` | 判定を両側 key の完全一致に |
| 同 | spec の期待 node 重複拒否 | raw と接尾辞除去後の**両方**を課す |
| 同 | collection 再照合 | 期待 node 実在検査を両側 key に |

`_normalize_node` は両 file とも無改変。`tools/mutation_fanout.py` は無改変。

## 除去規則の根拠 — repo の実在 nodeid 全件で検証した

除去条件は「node を最初の `::` で分割した test 名部分について
`rfind("@") > rfind("]")` が成り立つときだけ、その `@` 以降を一段落とす」。

`orchestrator/tests/acceptance_duration_ledger.json` に登録された nodeid **19519 件**を
全件走査した (`head` で切っていない)。

- `@` を含む nodeid: **26 件**
- 規則が接尾辞として落とすもの: **1 件** — 唯一の実在 xdist group 接尾辞
  (`test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding@real-repo`)
- 規則が保つもの: **25 件** — すべて parametrize ID 内の `@`

保たれた側には、この問題に対する敵対的な入力が既に repo 内に在る。
`test_acceptance_schedule_order.py::test_g3_splitter_exactly_matches_loadgroup_scheduler` の
parametrize ID である `[@]`、`[試験::場合@直列]`、`[試験::場合[値@例]]` の 3 件で、
いずれも規則は正しく保った。これらは合成入力ではなく実体として負例に使っている。

**除去を node 全体へ当ててはならない。** path 内の `@` を group と誤認し、
`tests@left/x.py::test_case` と `tests@right/x.py::test_case` が同じ key へ潰れて
**偽 KILLED** が成立する。現行 repo に該当 path は 0 件で到達不能だが、
比較器の受理集合を広げない形を選んだ (絶対規律 2)。

**複数段の `@` へは一般化しない。** xdist は複数 group 名を `_` で連結するので nodeid の `@` は
必ず 1 個であり、repo の xdist_group 名 11 種に `@` を含むものは無い (両方とも実測)。

## 同じ規則を 2 実装へ複製したことによる穴

段 6 の敵対レビューが検出した。同形化規則を harness と fan-out 終端検証器の
2 実装へ複製したのに、敵対的な負例が harness 側の実装しか呼んでいなかった。
fan-out 側で同型欠陥が再発しても追加したテストは緑のままになる。

fan-out 側へ同じ literal を使う負例 3 本を足し、変異も層ごとに登録し直した。
変異事前登録が層を区別していなかったことが根本原因である。

## 変異 matrix

一次資料は `spec-real1.json` (本走の spec) と `real1.json` (本走の台帳)。

- baseline: `PASSED` (rc=0)
- **16 変異すべて `KILLED`、一致 16/16。`SURVIVED` 0、`MISMATCH` 0、`PARSE_ERROR` 0**
- `repo_head` は実装 commit `0bc1ab724` に束縛されている

| ID | 層 | 変異 |
|---|---|---|
| M01 | harness | 比較 key の接尾辞除去を外し恒等へ戻す |
| M02 | harness | 初回 collection 事前検査を raw へ戻す |
| M03 | harness | 除去の条件節を外し無条件にする |
| M04 | harness | 除去の `rfind` を `find` にする |
| M05 | harness | 完全一致を包含へ緩める (**冗長 gate**) |
| M06 | harness | 抽出 0 件の fail-closed を fail-open へ倒す (**冗長 gate**) |
| M07 | harness | 除去を比較 key でなく記録側へ入れる |
| M08 | harness | resume の collection record 再照合を raw へ戻す |
| M09 | harness | 除去を test 名部分でなく nodeid 全体へ当てる |
| M10 | fan-out | 状態判定を raw 比較へ戻す |
| M11 | fan-out | 正規化後の重複拒否を外す |
| M12 | fan-out | 完全一致を包含へ緩める |
| M13 | fan-out | collection 再照合を raw へ戻す |
| M14 | fan-out | 除去の条件節を外し無条件にする (M03 の対) |
| M15 | fan-out | 除去の `rfind` を `find` にする (M04 の対) |
| M16 | fan-out | 除去を node 全体へ当てる (M09 の対) |

### 冗長 gate として明記するもの (`DW-M03`)

M05 と M06 は**既存テストも同時に殺す**ため、本 wave が足した機構を単独で証明しない。

- M05: 既存の `test_failed_nodes_strict_superset_never_counts_as_killed` も赤になる
- M06: 既存の `test_mutation_nonzero_normal_rc_without_failed_nodes_is_parse_error` も赤になる

いずれも「その gate が現に生きている」ことの確認にはなるので、登録したまま走らせている。

### 走行 1 回目・2 回目の erratum

`DW-M08` に従い、初回結果を消さず残している。

- **1 回目** (`spec-probe1.json`、台帳なし): 期待 node に parametrize されたテストの
  bare な関数名を書いたため、harness の起動前検査
  `期待 node が pytest collection に実在しない` で fail-closed 停止した。
  **harness の fail-closed が正しく発火し、作業ツリーも clean に復元された。**
  F71 の再発として台帳に記録した。
- **2 回目** (`spec-probe2.json` / `probe2.json`): 期待 node を計算ノード job stdout 全文から
  採り直して起動できた。**16 変異すべてが rc=1 で赤を出し `SURVIVED` は 0** だったが、
  期待集合が 1 件ずつしか無かった 7 変異は `MISMATCH` になった。
  この走行の `failed_nodes` から完全集合を確定し、本走で再登録した。
  **置換内容は probe2 と 1 byte も変えていない。** 変えたのは `expected_nodes` だけである。

probe2 が明らかにした実測として、比較 key の除去を外す変異 (M01) は
**6 テスト**を落とす — resume、collection、flaky-hold policy、二表記の重複拒否まで含む。
修正が harness の複数の座に効いていることの直接証拠である。

## 親が実測した赤

### 帰属する赤 1 件 (段 6 で解消)

`test_merge_keeps_group_normalized_strict_superset_as_mismatch` が
`shard-000 M1 output tail が不一致` で落ちた。新規 fixture が status `MISMATCH` の record を
組み立てながら `test_output_tail` を空にしており、`_validate_ledger` が要求する
stdout 末尾 80 行を満たさず、**意図した assertion に到達する前**に落ちていた。
fixture を直して解消した (production の tail 要求は緩めていない)。

### 帰属しない赤 2 件 (login node 固有、構造的)

差分 0 byte の作業ツリーで login node 走行すると、
`test_sigterm_handler_stops_child_and_restores_active_mutation` と
`test_completed_record_is_flushed_before_next_runner_sigkill` が必ず落ちる。
どちらも `mutation_harness.py --runner-mode local` の子へ signal を送り `returncode < 0` を
観測するテストだが、login node では `_refusing_local_site` が `PEGASUS_LOGIN` を構造的に
拒否して先に rc=2 で終わるため signal 死に到達しない (実測 assertion: `assert 2 < 0`)。

**計算ノードでは同じ 2 file が 140 passed / 0 failed。** 本 wave の差分とは無関係である。

## 焦点走 (すべて計算ノードへ dispatch、child rc=0)

| 対象 | 結果 |
|---|---|
| 直接 consumer 6 file (fix 後、`test_p3_build_authority_cli.py` を追加した 7 file) | 284 passed / 0 failed |
| repo 全体を AST・内容走査するメタ検査 4 file | 484 passed / 0 failed |
| `test_campaign.py` (repo-wide Python 解析) | 412 passed / 3 skipped / 0 failed |

`test_p3_build_authority_cli.py` は段 6 のレビューが指摘するまで、親・実装子・段 3 の
いずれの一覧からも漏れていた。全 tracked Python を列挙して AST 走査する検査であり、
名前 grep では見つからない。

## 逐語

`verbatim/` に段 2 プラン、段 3 の 2 レンズ、段 5 実装子、段 6 の 2 レビューと fix の
完了報告をそのまま収めている。

## 触っていないもの

- `docs/dev-wave/mutation.md` — F71 の恒久対応欄が「規約の追加ではなく道具を規約へ
  合わせるのが対応」と既に定めており、`DW-M08` の本文は現状で正しい要求を述べている
- `tools/mutation_fanout.py` — 比較器を持たない (段 2・段 3 の 2 レンズとも実測 0 件)
- `_normalize_node` (両 file) — 記録の姿を保つため
- 性能測定・campaign 実走 — 本 wave では一切行っていない
