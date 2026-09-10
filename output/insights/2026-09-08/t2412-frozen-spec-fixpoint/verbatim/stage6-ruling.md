# 段 6 裁定 — T-2412 敵対レビュー所見

段 4 裁定 (`ruling.md`) はそのまま有効。以下はその追補である。

| # | 所見 | 判定 | 扱い |
|---|---|---|---|
| RA-1 | `_git_changed_paths` が `--ignore-submodules=none` を持たないため、`.gitmodules` の `ignore=all` 下で gitlink 変更が差分から消え、spec-only 判定を通る | real | **採用 (must-fix)** |
| RA-2 | `test_blob_queries_use_the_once_resolved_loaded_head` が「1 件以上あり全件が解決済み OID」しか見ないため、calibration / build receipt の blob 比較を丸ごと削除しても緑になる | real | **採用 (must-fix)** |
| RB-1 | issuer の synthetic summary が `loaded_head` を旧定数 (= 親 `C`) のまま持ち、実際に load した `H` と食い違う | real | **採用 (must-fix、test 側のみ)** |
| RB-2 | 台帳の所要値が実走 JUnit に結び付いていない | **refuted** | 親が実走で生成済み。下記の証拠を記録する |

## RA-1 の裏取り

この repository は `external/ccbench` を submodule として持つ (`.gitmodules` に実在)。現在 `ignore`
設定は無く `git config` にも `diff.ignoreSubmodules` は無いが、`ignore=all` は `.gitmodules` に
書ける tracked 設定であり、親 commit `C` に置けば freeze commit `H` で gitlink を差し替えても
`diff-tree` の出力から消える。**本 wave が新設した述語自身の穴**であり、外部の仮想リスクに対する
gate 追加ではないため scope 内とする。

## RB-1 の扱い

production 側 (`p3_b4_floor_artifact_issuer.py:869`) は `summary["loaded_head"]` を検証なしで
成果物へ転記する。これは本 wave 以前から同じであり、本 wave が悪化させたものではない。
production への比較追加は新設 gate にあたりユーザー明示の scope 外条件に触れるため実装しない
(レビュー B 自身も「production への一般 gate 追加は不要」と書いている)。裁定パッケージへ返す。
本 wave では **test fixture の食い違いだけ**を直す。

## RB-2 が refuted である証拠

親は `tools/run_tests.py orchestrator/tests/test_floor_pair_driver.py -q --junitxml=...` を実走し、
`209 passed in 4.11s` を得た。その JUnit XML
(`$CLAUDE_JOB_DIR/tmp/t2412/junit-fpd.xml`, 33228 bytes) を canonical 生成器
`tools/update_acceptance_duration_ledger.py --add-only` へ渡して 209 件を登録した。
登録後 `test_acceptance_schedule_order.py` は 79 passed。
レビュー B が見たのは実装子の報告 (rc=16 で未実走) だけで、親の実走は射影されていなかった。

## must-fix (fix2)

1. `_git_changed_paths` の argv へ `--ignore-submodules=none` を足す。模擬 git の argv 期待も更新する。
   `ignore=all` を親 commit に置き、freeze commit で gitlink と spec を同時に変える実 git 負例を
   1 本足す (submodule の clone は不要。`git update-index --add --cacheinfo 160000,<sha>,<path>` で
   gitlink を直に作れる)。実 git で作れない場合は、作れない理由を報告に書いて止める。
2. `test_blob_queries_use_the_once_resolved_loaded_head` を、blob query の **exact な multiset**
   (spec + calibration + 一意な build receipt 全件) を要求する形へ強める。どれか 1 つの比較を
   削除したら赤になること。
3. issuer の fixture の `loaded_head` を `driver_tests.HEAD` にし、既存の consumer test で
   `summary["loaded_head"]` が実際に load した spec の `loaded_head` と一致することを確かめる。

## 変異事前登録の追補 (DW-M01)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M08 | `_git_changed_paths` の argv | `--ignore-submodules=none` を除去 | KILLED (gitlink 負例) |
| M09 | `_read_tracked_bound` の呼出し | calibration の blob 比較を除去 | KILLED (強化した M06 test) |
