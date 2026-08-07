結論は NO-GO。実効性と検出力に must-fix がある。

### RA-1 — must-fix：decoy の `max` を残せば実指示を `high` にできる

**成果物影響:** A/B 未完了でも低 effort の敵対レビューが production に入り、must-fix の見逃しにより certified 選択・材料レポートの受理集合が黙って広がる。

確認手順:

- 検査は raw な節本文を取り出し、`` `reasoning=max` `` の出現数だけを見る。[tools/check_docs.py:3372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3372)、[tools/check_docs.py:3390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3390)
- `_reference_id_sections()` は fence・引用・HTML comment を除外しない。[tools/check_docs.py:1679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:1679)
- DW-S02 を次の実指示にしても read-only メモリ probe は finding `[]` だった。

  ```markdown
  codex `reasoning=high`、`gpt-5.6-sol`、<!-- `reasoning=max` -->、`sandbox=read-only` で
  ```

  変更後 workers は 4,651 bytes、4 reference 合計は 25,170 bytes で、個別 5,000・総量 25,200 の cap 内。[tools/check_docs.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:176)、[tools/check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:254)
- 同じ節への fenced block・引用・comment 内移動も通る。節外へ移せば count 0 で赤、別節の literal は対象節へ影響しない。
- D207 は運用ログによる引き下げを明示的に禁止している。[docs/decisions.md:9891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9891)

最小修正: `_visible_markdown_text()` 後の節を検査し、可視かつ非引用の `reasoning=<value>` 集合を exact `["max"]` に限定する。`max+high`、comment/fence/引用だけの `max` を負例追加する。

### RA-2 — must-fix：本番配線を外す変異を追加 4 node が検出しない

**成果物影響:** checker の production 呼び出しだけが蒸発しても全追加 node が緑になり、段 2/3 の低 effort 化を受理して certified 選択・材料レポートの受理集合を広げる。

確認手順:

- 本番配線は `_check_command_docs_guard()` 内の一箇所だけ。[tools/check_docs.py:3560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3560)
- `main()` は同 guard を呼ぶ。[tools/check_docs.py:4012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:4012)
- 追加 4 node はすべて private 関数を直接呼び、本番 guard・`main()`・`_run_check()` を通らない。[test_check_docs.py:4795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4795)
- したがって 3562 行の呼び出しだけを削除しても、追加 4 node は一つも赤にならない。DW-M01/M03 の「実効 gate への帰属」を満たさない。[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/mutation.md:5)

最小修正: `_build_min_repo()` の workers を改変して `_run_check()` を走らせ、rc=1 と節別 finding を確認する production-path 負例を少なくとも S02/S03 各一つ追加する。private 単体テストは残してよい。

### RA-3 — must-fix：4 node では claimed exact pin の弱化を閉じない

**成果物影響:** S03 の値欠落や exact-one の弱化が検出されず、既定値経由で段 3 の検出力が下がり、certified 選択・材料レポートの受理集合が広がる。

確認手順:

- per-section の「`reasoning` を含むだけ」へ弱化すると赤になるのは S02-high と S03-high。正例と S02-value削除は通る。[test_check_docs.py:4801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4801)
- S03 pin を完全に落とすと S03-high node が赤になる。
- しかし「S03 は `high` だけ拒否し、値欠落を受理する」弱化は全 4 node を通る。S03-value削除負例がない。
- `count != 1` を `count == 0` に弱め、複数 literal を許しても全 4 node が通る。
- finding の期待値は要求どおり定数参照であり、二重 literal 化されていない。[test_check_docs.py:4811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4811)、[test_check_docs.py:4822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4822)、[test_check_docs.py:4833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4833)

最小修正: 既存期待値は維持し、S03-value削除と duplicate-max の負例を追加する。RA-1 の矛盾・不可視配置負例も同じ matrix に含める。

### RA-4 — should-fix：D207 finding が見出し typography まで pin する

**成果物影響:** certified 選択・レポート・台帳値は変わらないが、意味等価な workers 文書変更の受理集合を承認外に狭める。

確認手順:

- タイトル本文の変更は `—[^\n]*` なので通る。
- 一方、`—` を `–` / ` - ` に変える、または `##` 後の空白を増やすと section 0 件になり D207 finding が立つ。[tools/check_docs.py:1683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:1683)
- 一般の required-heading 検査は空白後の ID を認識するため、例えば `## DW-S02 – 新題` はそちらでは有効。この過剰拒否は新設 pin 固有。[tools/check_docs.py:3614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3614)

最小修正: D207 検査の節抽出を見出しの先頭 ID に束縛し、suffix typography から分離する。題名・区切り変更の正例を追加する。

### 所見外の確認

- `decoded.get(_WORKERS) is None` は現行構成では fail-open ではない。workers は予算 registry に必須で、不在は 3447–3452 行、symlink・非 regular・invalid UTF-8・読取失敗は `_safe_read_text()` が先に finding 化する。[tools/check_docs.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:178)、[tools/check_docs.py:3447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3447)、[tools/check_docs.py:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:579)
- 登録済み `max→high` / 値削除入力については他の effort 検査がなく、byte cap にも掛からないため、節別 pin finding だけに帰属する。DW-M01 の単一理由性はこの限定入力では成立する。
- 新設 loop は DW-S02/S03 だけで、DW-S05 の `reasoning=high` は pin していない。[tools/check_docs.py:3378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3378)、[workers.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:24)
- 段 5・他 reference・target literal を変えない通常の節加筆は、この新設検査の対象外。

## 総括

must-fix 3 件、should-fix 1 件。  
現状は land 不可。  
主因は decoy literal による実指示の回避、本番配線未検査、S03 欠落を許す test matrix の穴。