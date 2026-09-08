単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s6-review-B.md` — 段 6 レビュー B の逐語。**「環境依存」節の must-fix 2 件**が fix の対象。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s6-review-A.md` — 段 6 レビュー A の逐語 (must-fix 0 件、real の nit 1 件)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — fix 後の実体。対象関数は `test_multi_ww_reason_report_is_hash_seed_deterministic`。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md` — 親の段 4 裁定。読めなければ即停止。

## 状況と、親が既に実行した分担

fix は **commit 済み**である。

- `c3f130e34` — 実装 (`dsg.py` の 1 行) と新テストの追加。
- `fc83788df` — 段 6 レビュー B の must-fix 2 件の fix。

`git show fc83788df` で fix の差分、`git diff c3f130e34~1..fc83788df` で wave 全体の差分が読める。
**commit は親が行った。** 実装子・fix 子は commit していない。

親は fix 後に `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` を自分で実走し、
**106 passed / 0 failed / 0 skipped**、新テストは PASS を確認済みである。

## これは何のための依頼か

これは**私たち自身のリポジトリの、正しさ検査器 (verifier) に入れた変更の焦点再レビュー**である。
fix が所見を本当に閉じたか、閉じる過程で検査を弱めていないかを点検してほしい。
fix を守る立場ではなく、**見落としを指摘する立場**で読むこと。

## 必ず出すもの — 所見ごとの対応表

段 6 の 2 本のレビューが出した**すべての所見**について、次の 3 値のどれかを判定した表を作れ。

- `closed` — 所見が閉じた。
- `partial` — 部分的にしか閉じていない (何が残るかを書く)。
- `regressed` — fix によって別の問題が生じた。

**表を作らずに「閉じた」と書いてはならない。** 判定には必ず fix 後の `file:line` を添えよ。
レビュー A の must-fix は 0 件、real の nit は 1 件 (型契約を破った手製入力での `TypeError`) である。
レビュー B の must-fix は 2 件 (subprocess の timeout、失敗時の stderr) である。
nit として出たものも表に含めること。

## 重点的に見ること

## 1. fix が検査を弱めていないか
fix 前は `check=True` で子の非ゼロ終了を例外にしていた。fix 後は `check=False` にして
自前で `returncode == 0` を assert している。**この置換で見逃しが生まれていないか**を確かめよ。

- 子が非ゼロ終了したとき、必ず失敗するか。
- 子が 0 終了だが stdout が空・壊れている場合、後続の assert が確実に失敗するか。
- `TimeoutExpired` の経路で `assert False` を使っているが、これが最適化 (`python -O`) で
  無効化されうるかを述べよ。この repo のテスト実行が `-O` を使うかも確かめること。

## 2. timeout 120 秒が実行環境に対して妥当か
`DW-O16` は「PATH 構築・interpreter 解決・外部 command 選定など実行環境に依存する実装は、
レビュー通過だけで closed とせず実機で動かすまで確かめる」と定める。
この fix は `sys.executable` と `cwd` に依存する。**実機の構造が推測と食い違っていないか**を、
repo 内の同型の先例と突き合わせて述べよ。親が実走で 106 件緑を確認していることを踏まえること。

## 3. 元の所見が本当に閉じたか
レビュー B の直し方は「`check=False` で受け、`returncode == 0` を seed、rc、stdout、stderr の
bounded tail 付きで assert する。`TimeoutExpired` も捕捉し、保持されている stderr を
assertion message に含める」だった。**fix がこの通りになっているか**を逐語で照合せよ。
足りない要素があれば `partial` と判定せよ。

## 4. 変異の期待が変わっていないか
親は M1 (`sorted` を外す) の期待失敗 node を
`orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic`
ただ 1 件の完全集合として事前登録した。**fix によってこの期待が変わっていないか**を確かめよ。

## 制約

- あなたは `sandbox=read-only` で走る。書込可能な tmp が無いので **pytest を実走しなくてよい**。
  静的検査で足りる。実測は親が行う。**実走していないものを緑と書いてはならない。**
- ファイルを書き換えてはならない。commit してはならない。
- 指摘には必ず `file:line` を添えよ。
- **成果物への影響を 1 行で書けない指摘は must-fix にしてはならない。** nit として区別して書け。
- 仮想リスク向けの gate・検査・台帳・一般化の新設を勧めてはならない (scope 外)。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 所見ごとの対応表
## fix が検査を弱めていないか
## 実行環境への依存
## 変異期待への影響
## 総括
