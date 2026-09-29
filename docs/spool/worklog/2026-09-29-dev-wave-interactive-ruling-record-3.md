---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-interactive-ruling-record
seq: 3
title: 対話型 dev-wave を研究の主経路にする 2026-09-29 の裁定と、高速化計画から外した項目を決定台帳に記録し、roadmap §1・§2 を協議改訂し、README.md に研究の進め方と削除したものの探し方を足した (docs のみ、branch dev-wave-interactive-ruling-record)
---

## 本文

- 依頼: 並行 wave の md_1 (`/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_1.txt`、共通指示 `common.txt`)。一次資料は裁定の控え `2026-09-29-interactive-evolution-verdicts.md` と相談記録 `interactive-evolution-consult-20260929/`。repo 外の原本が片づけで消えても引けるよう、bytes 一致の写しを `output/insights/2026-09-29/interactive-dev-wave-ruling/` に置いた。
- ユーザー裁定 (2026-09-29、受領の逐語「よし。ここら辺は推奨通りで良い。」): 対話型 dev-wave を当面の研究の主経路にし、8c の元の達成条件と未達は変えず ComSys 締切後に無人の多世代ループを小さく試して再裁定、論文では「人間が介在する逐次探索」と書く、人間の判断と投入時間を無人の成果と分けて記録する ({{D:interactive-dev-wave-main-path}})。
- 高速化計画から外した項目と削除の記録方式は {{D:speedup-plan-exclusions}}。これは親セッションが Codex 2 本 (計画検査・反論) の一致で計画を修正した記録で、各項の個別のユーザー裁定ではない。
- roadmap は協議改訂として in-place (版上げ・history 凍結なし)。§1 の主張階層 4 の直後、§2「システム合成と無人自律を名乗るための要件」、§2 探索戦略の用語予約の段落に追記した。§10 の用語予約は文言を変えていない。
- README.md: 「研究の進め方」節を新設、アーキテクチャ図の層 2 に但し書き、「削除したものの探し方」節を新設。削除 commit の一覧は依頼文の `--grep='^prune'` ではなく `--grep='^prune('` と書いた — `^prune` は本文の行頭にも一致し、実測で無関係な commit b36da2b09 (本文 6 行目が「prune は…」) を拾ったため。README の引き方は既存の削除例で実行して確かめた — `git log --diff-filter=D --name-only -- docs/archive/token-management-strategy.md` が削除 commit d855a6827 を返し、`git show d855a6827^:<同 path>` が削除前の中身を返し、`output/PRUNED-INDEX.jsonl` 先頭行の `git show <commit>:<path>` が索引の size (4058) と blob に一致する中身を返した。`--grep='^prune('` は誤りなく走り 0 件 (この題の規約は 2026-09-29 からで、既存の削除 commit は持たない。README にそう書いた)。
- `docs/phase3.md` は未了のチェック項目が 0 件で、この裁定に対応するチェックが無いので変えていない。ComSys 後の試行は下の新規項目に置いた。`docs/README.md` は触っていない。
- 段構成: 軽量版 (段 2・3 なし、実装面なしで段 5 の実装子と変異 matrix なし)。一次資料から事実を再抽出する docs wave なので段 6 の read-only レビュー 1 本を残した。
- 段 6: レビュー 1 本 (2 レンズ) が NO-GO — must-fix 1 (削除条件の文が D2179 の一回限り tool 用の条件を全対象の恒久規則に読め、`output/` の D2297 と食い違う)、should-fix 2 (`prune(` 題は既存の削除に 0 件なのに既存分も探せるように読める、索引の `git show` を存在確認しかしていないのに「動くことを確かめた」と書いた)。親が直し、焦点 1 巡目が NO-GO — 新規 must-fix 2 (D2179 は 15 対への裁定で一般条件として引けない、D2297 の第 2 類型の「名前では引かれていない」を落とした)。親が直し、焦点 2 巡目で GO (全 5 件 closed)。残った should-fix 1 (「新しい基準は足さない」と「適用を本決定が定める」の食い違い) は文言だけ直し、再レビューはしていない。費用: codex 3 本 (gpt-6-sol、13 + 6 + 4 call、各 2〜4 分)。
- 背景 job の `EnterWorktree(name)` は「Could not read the repository git config」で失敗し、手動の `git worktree add -b` で作った (checkout に約 15 分)。その後 `EnterWorktree(path)` も `worktree list` の 10 秒上限で 3 回失敗し (worktree 約 230 本、一覧 21.6 秒)、絶対 path で作業した。checkout の間に main が 14 commit 進み、開始 gate の 1 回目は NG、`--ff-only` で揃えて通した。

## 次の一手差分

### 新規

- {{T:unattended-loop-feasibility}} **P3・新規 (ComSys 締切 2026-10-30 の後)**: 無人の多世代ループの実現可能性を小さな予算で試し、その結果で 8c の継続・延期・目標変更をユーザーに再裁定してもらう ({{D:interactive-dev-wave-main-path}} 決定 2)。8c の元の達成条件は変えない。計算が 1 タスク合計 2 node 時間以上になる見込みなら投入前に確認を取る。
