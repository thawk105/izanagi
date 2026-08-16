# [T-1186] — 判定器の版束縛の変異台帳と erratum

wave branch = `worktree-dev-wave-t1186-decider-version-binding`。
変異は `tools/mutation_worktree.py` (固定 commit の使い捨て worktree) から
`tools/mutation_harness.py` を `--runner-mode dispatch` で起動した。runner argv には
`--force-dispatch` と `-rf` を含む (`DW-M07` / `DW-M08`)。

## 走行の履歴

| 走 | 目的 | commit | spec | 結果 |
|---|---|---|---|---|
| 第 3 走 | probe (期待 node の導出) | `2008ab82` | `mutation-spec-run3-probe.json` | baseline PASSED。9 件を全件 `SURVIVED` 期待で登録し、観測された失敗 node を集める形にした。8 件が失敗を出し 1 件が生存 |
| 第 4 走 | **本走** | `2008ab82` | `mutation-spec-run4.json` | baseline PASSED、**9/9 KILLED、MISMATCH 0**、wrapper rc=0 |

第 1 走・第 2 走は起動前に落ちており、変異は 1 件も実行していない
(第 1 走 = `--wrapper-attempt` に非整数を渡した引数エラー、
第 2 走 = 実走に必須の `--detached` を付けていなかったための中止)。
どちらも spec の内容とは無関係な起動形の誤りである。

probe を挟んだ理由は、harness が `KILLED` 期待に**完全な期待 node 集合**を要求し
(`DW-M08`)、期待 node を空にした spec は起動前に中止されるためである。
期待 node は静的に確定できなかったので、`DW-M08` の「初回を probe と明記する」に従った。

## erratum — n8 は等価変異だった (`DW-M02`)

probe に登録した `n8-current-version-type-check-relaxed` は
「実行中の `DECIDER_VERSION` の厳密型検査 (`type(...) is str`) を `isinstance(...)` へ緩める」変異で、
**SURVIVED (失敗 node 0 件)** だった。

原因は他層による mask である。一致判定が `str.__eq__(DECIDER_VERSION, decider_version) is True` と
builtin を直接呼ぶ形になっており、`__eq__` を上書きした `str` 派生型は型検査を緩めても
一致を偽装できない。すなわち型検査は単独では受理集合を動かさない。

`DW-M02` に従って実効 gate へ再照準し、本走では
`n8-type-and-eq-both-layers-relaxed` (category = `both-layers`) として
**型検査の緩和と `str.__eq__` 直接呼出しの通常比較化を同時に**適用する変異へ差し替えた。
期待 node は `test_valid_hostile_str_subclass_cannot_fake_decider_version_match` の 1 件を
事前登録し (`DW-M04` の両層変異の kill 期待事前登録)、本走で一致した。

probe の結果 (`mutation-ledger-run3-probe.json`) は消さずに残してある。

## 登録した変異

| id | category | 壊す対象 | 期待 node 数 |
|---|---|---|---|
| n1-effective-drops-version-conjunct | negative | 発効の連言から版一致を外す | 4 |
| n2-legacy-v1-treated-as-match | negative | legacy v1 tip を一致扱いにする | 1 |
| n3-record-decider-format-unchecked | negative | 記録側の版の形式検査を無効化する | 5 |
| n4-unknown-schema-read-as-v1 | negative | 未知 schema を v1 として読む | 1 |
| n5-projection-blob-mismatch-ignored | negative | 射影の live-vs-commit 不一致を無視する | 1 |
| n6-digest-drops-version-fields | negative | 報告 digest から版 field を落とす | 2 |
| n7-record-document-emits-legacy-v1 | negative | 新規記録を legacy v1 で発行する | 22 |
| n8-type-and-eq-both-layers-relaxed | both-layers | 厳密型検査と `str.__eq__` 直接呼出しを同時に緩める | 1 |
| p1-version-match-never-granted | positive | 版が一致していても常に未束縛を返す (過剰拒否の検出) | 10 |

`p1` は受理集合を**狭める**側の変異である。承認外の過剰拒否をテストが検出できることを示すために
登録した (`DW-M01`)。10 件の期待 node はすべて「版が一致していれば従来どおり発効・capability 発行が
成立する」ことを要求するテストであり、過剰拒否が入れば赤になる。

## runner 範囲

期待 node は次の runner 範囲と対である (`DW-M08`)。

```
orchestrator/tests/test_s8c_preregistration_core.py
orchestrator/tests/test_s8c_preregistration_predicates.py
orchestrator/tests/test_s8c_preregistration_invariant.py
orchestrator/tests/test_reflux_originless_compatibility.py
```

この範囲外のテストが同じ変異で落ちるかどうかは、本台帳は主張しない。
