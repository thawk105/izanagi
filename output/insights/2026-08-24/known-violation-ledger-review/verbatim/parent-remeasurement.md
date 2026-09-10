# 段 3 sol の指摘を受けた親の再測定 (段 4 の入力)

sol レンズが親の測定方法に 4 点の欠陥を指摘した。親が該当箇所を測り直した結果を記録する。
**これは段 4 裁定の一次資料であり、追補 2 の該当箇所を上書きする。**

## 指摘 2 (`_commit_paths()` は finding 対象 path 集合ではない) — 妥当。ただし値は変わらなかった

sol は正しい。`_commit_paths()` は変更 path 全部を返し、`validate_implementation_author()` が
その後 `_is_implementation_path()` で絞る。親の 3 本の script はこの絞りを入れていなかった。

`remeasure.py` で実装面 path だけへ絞って案 B の防止可能件数を測り直した。
**結果は 12 件で変わらない。** 防げない 7 件は、いずれも台帳以外に実在する実装面 path を持つ:
- `b0a0767273` `2c1929533a` `333605d680` — `output/insights/**/*.py` (解析 script)
- `8ceebcdbe4` — `external/ccbench` (gitlink)
- `311d463f89` — `orchestrator/campaign/s8b_oracle_driver.py`
- `649fe5a060` — `orchestrator/tests/test_backoff_sweep.py` 他
- `25614f868c` — `tools/check_docs.py`

## 指摘「growth.py は構文解析していない」 — 妥当。ただし値は変わらなかった

`remeasure.py` で `ast` により `KNOWN_PROVENANCE_VIOLATIONS` の tuple 要素数を各 blob で
数え直した。**軌跡は完全に一致した。**
増加 20 回・減少 2 回、最終値 53。2026-08-21T22:49 `e0ac92775c` で 53→34 (−19)、
2026-08-23T19:29 `bc927d03c4` で 53 へ復帰。44.7 時間、約 10 件/日。
**この値は構文解析による厳密値として確定した。**

## 指摘 8 (生成器分類の誤り) — 妥当。分類を訂正した

`reclassify.py` で missing-ai-agent 11 件を「trailer 完全欠落」と
「AI-Agent 行は本文に在るが最終 trailer block に入っていない」へ分けた。
**`3f2c43d758` の 1 件だけが後者。** 親の `classify.py` はこれを G6 (manager 直接 commit) へ
誤って落としていた。

訂正後の生成器別内訳 (53 findings / 52 unique commits):
- G1 trailer の綴り誤り (2026-08-09 単一事故、literal 同一): 22
- G2 role の綴り誤り (`role=fix`): 1
- G3 `--no-edit` merge で trailer 完全欠落: 8
- G4 trailer 完全欠落 (revert / ユーザー直接 commit): 2
- G4b trailer block の配置誤り: 1
- G5 台帳自身の競合を親が手解決した merge: 11
- G6 manager が実装面を直接 commit: 8

G6 の 8 件はさらに実体が分かれる (段 7 の記録用):
- 解析 script を `output/insights/` へ置いたため実装面判定に当たった: 3
- submodule gitlink の前進: 1
- 台帳登録 commit そのもの: 2
- その他の直接 commit: 2

## 指摘 1 (`merge-file` は忠実な代理でない) — 妥当。主張を弱める

親は「10 件は実際の merge で競合し人が手解決した」と書いたが、これは
`git merge-file` という blob 単位の低水準 merge の結果であり、rename 検出・
`.gitattributes` の custom merge driver・実際の strategy を再現しない。
**正しい主張は「素の blob 単位 3-way merge では 10 件とも競合した。実際の解決過程は未確定」。**
D721 と整合はするが、D721 を実測で証明したことにはならない。

## 指摘 3 (4 件は plan v1 の述語を測っていない) — 妥当。ただし論点は消滅した

親の script は `splitlines()` を使い末尾 LF の差を潰し、出現回数条件も実装していなかった。
よって「4 件」は plan v1 の述語では未実証である。
**ただし sol の指摘 4 により案 A 自体が倒れたため、この数を確定させる必要はない。**
撤去可能件数は 0 である。

## 指摘 4 (案 A の反例) — 妥当。案 A は倒れた

sol の反例: 親 P1 が `@audit`、親 P2 が `@authorize` を持ち、結果が両方を並べる。
全行が親由来、両親とも結果の subsequence、出現回数も上限内。
それでも `audit(authorize(check))` という**相対順序を決めたこと自体が実装著作**である。
同一行の重複 (`hooks.append(register)` を 2 回置く) はさらに直接的で、二重登録という
新しい挙動を merge author が作っている。

述語をどう強めても最終 blob からは救えない。**案 A は却下。撤去 0、台帳は 53 件維持。**

## 指摘 5・6・7 (案 B / 案 C) — 段 4 で luna と合わせて裁定する

- 指摘 5: 案 B の「docs-only になる」は利点でなく Codex author gate の抜け道。
  データ置き場を実装面として分類することが最低条件。その場合、防止可能 12 件のうち
  台帳登録 commit 2 件 (`94815c5797` `3a5e5feb5f`) は防げない。**正味 10 件。**
- 指摘 6: 案 B は schema 同値性・file discovery・HEAD 束縛が未定義。
  特に `649fe5a060` は 1 commit に 2 finding があるため `<sha>.json` では同名衝突する。
- 指摘 7: 案 C は却下。`ruling` / `note` は受理判定に使われないため全史監査が改変を検出できず、
  逐語ミラーが唯一の検出器である。畳めば裁定根拠を偽造・消去できる。
  sol の代案は「逐語保証を削らず、独立 oracle も entry 単位へ分割する」。
