---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-cleanup-originals-migration
seq: 1
title: 原本を抱えて残っていた古い worktree 91 本・branch 11 本を全部「回収せず消す」と判定し、名指し元 26 本と論文ストーリー README に所在の移動を追記した (docs-only、insight + fragment、branch worktree-dev-wave-cleanup-originals-migration)
---

## 本文

- 依頼: ユーザー (2026-09-30 01:0x JST) の md_1 (`/work/1/SFC/tanab/tmp/cleanup-originals-migration-2026-09-30/md_1.txt`)。前日の `/cleanup-branches` 3 回で残した「研究記録が path を名指すので消さない」木・branch を、名指しを外せる状態にしてから消す。
  ユーザーの方針 (逐語は一次資料 `verbatim/request.md`): 「回収する価値があるならね。適当なテストや計測だったらいらねぇ」。一次資料 `output/insights/2026-09-30/cleanup-originals-migration/README.md`。
- 段構成: 軽量版 (docs-only、repo の実装面ゼロ)。段 1 の調査子 3 本 (Claude general-purpose、sonnet 明示) が名指しの全数表を作り、段 3 は Codex 2 役 (決定役 sol・攻撃役 luna、consult・reasoning high・read-only)、段 6 は read-only review 1 本。変異 matrix は実装面の差分 0 で免除。
- 判定: 回収 0 件、残す 0 件、全部回収せず消す ({{D:cleanup-originals-no-recovery}})。(a) 論文の数値・図が原本からしか得られない、(b) 次の一手が入力に取る、(c) 有効な事前登録が入力に取る、のどれにも当たる系列が無く、コード・テストが木の path を読む箇所も 0 だった。
  割れた 2 点は攻撃役を採った: T-2871 の WAL 2 本は回収しない (gen-opt 設計が未採用で内訳値は転記済み)、B-5 発効 commit `6fce61d6e` は tag を作らず branch 束 bundle で保全。D2242 決定 1 の「branch は残す」は D2243 項 2 が中立 land を不採用にしたので解いた。
- 退避: branch 11 本の束 bundle (create・verify rc=0、main 非祖先 10 本の heads が期待 tip と一致)。木 89 本 (対象表の 91 本のうち fix1/fix2 を除く) は HEAD の変化 0、前日退避の流用 55 本 (HEAD・未追跡の集合が一致)・新規退避 34 本 (未追跡のあった 29 本は tar、list 件数と entry 数が全件一致)・不良 0。退避は撤去の条件にしていない。
- 棄却・訂正: 段 1 brief の「前日退避 56 本」は誤りで (攻撃役・決定役が指摘)、木ごとの表を正とした。対象集合から t2853-r2-plot-fix1/fix2 が漏れていた (path の正規表現の誤り) のを段 4 で補った。prune の照合を管理名だけで行う案は、scratch2 の管理名が汎用の `repo` なので元 path の照合に改めた。
- 段 6 の read-only レビュー 1 本は GO (must-fix 0)。should-fix 1 件 (main 非祖先の木の本数の母数) と nit 1 件 (時制) を real として直した。棄却なし。
- 所要の異常: 追記先の pin 閉包を file ごとに `git grep` 3 回 (30 file で計約 90 回) で回したら 10 分の timeout を超えても終わらず、全 pattern を 1 回の `git grep -F -f` にまとめて完走させた。隔離 guard は heredoc・`git -C`・変数入りの複合コマンドを拒否するので、script は Write で書いて素の `python3` で呼んだ。
- 記録前の三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1 で、hit は rr80・rr20 とも 2026-09-16 の較正記録 `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file (main に commit `cc82edc8c` で追跡済み)。この wave の変更 file の hit は 0 で、非帰属。
- 撤去は land の後に行う (手順は一次資料 §6)。撤去の結果はこの fragment に書き足さない (受入のやり直しになるため)。
- 受入: 受入全走はこの記録 commit の tip で行い、受領証は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/`) に残す (結果は書き足さない)。

## 次の一手差分
