---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1675-budget-approval-user-turn
seq: 1
title: [T-1675] 予算承認をユーザー手番として成立させる — 承認を発行しない preflight まで作り、1 コマンド確定は D287 と衝突するため作らなかった (コード + docs、branch worktree-dev-wave-t1675-budget-approval-user-turn、変異 matrix = baseline PASSED・KILLED 6・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「ユーザーが中身を読んで 1 コマンドで確定できる形まで持っていく」だった。段 2 は
  ratify CLI (承認 JSON を発行し pin 定数を書き換え、承認者を TTY から受け取る) を起草した。
  段 3 のレンズ A が **D287 との正面衝突**を摘発し、親は段 4 で**不採用**と裁定した。
  D287 は「approval を発行する CLI・API・`--approver` 引数・既定補完は作らない」「pinned literal
  なら AI が承認者になるには人間がコード diff をレビューして定数を置くしかない」と定めており、
  本 pin を作った wave 自身の裁定で未 supersede である。D526 も批准台帳へ追記 API・CLI を作らない
  としている。さらに TTY 案は D905 が却下済みの平文承認と同型であり、D905 は「成りすませない
  実行主体の新設だけを採る」「設計が着地するまで批准は進めない」と明記している。
  設計判断は {{D:budget-approval-preflight-only}}。
- そこで scope を「1 コマンドで**検証**」へ縮小し、承認 bytes を置く行為は人間手番に残した。
  `tools/s8b_budget_approval_preflight.py` は `skeleton` (承認者・日時・予算値を持たない骨組みを
  repo 外へ create-only で出す) と `verify` (人間が書いた承認 JSON を検証し sha256 と pin 行を
  表示するだけで file を 1 つも書かない) の 2 副命令だけを持ち、`--approver` を持たない。
- **依頼文の前提 2 件を実測で訂正した。**(a) 裁定は「未 land」ではなく既に D1161 として main に
  着地済みだった。(b) 閂は 1 つでなく 2 つで、承認 JSON の不在に加えて
  `BUDGET_APPROVAL_SHA256 = None` が入力を読む前に `budget-approval-not-ratified` で落とす。
  つまり「草案だけでは gate が開かない」は現行実装で既に構造的に真であり、本 wave の負例は
  新しい防壁ではなくこの性質の固定である。単一理由の gate としては主張していない。
- **予算数値は未裁定のままである。**依頼文の「(b)(c) は D964 / D979 で裁定済み」は D1161 本文の
  引き写しで、D964 は staged 運搬の適格性、D979 は役割横断の生涯観測上限であり、
  T-986 dossier §10 の数値択 (2592/1296、2400/1200) を承認していない。dossier の推奨は保留である。
  したがってユーザー手番の中身は「名前を書くこと」ではなく「数値を決めること」だと確定した。
- **承認だけでは v2 candidate は通らない。**`BUDGET_APPROVAL_REL` を読む consumer は
  `build_v2_g1_candidate` ただ 1 つで、`s8b_floor_campaign.py` / `s8b_budget.py` /
  `s8b_oracle_driver.py` は読まない (grep 0 件)。同 builder は official path 規約を満たす
  eligible な `result.json` と同一 run の `manifest.json` / `journal.jsonl` も要求し、
  `output/env/*/calibration/s8b-floor-official/` は現物に存在しない。承認は official 実行の
  **後**の再凍結で使われる。D1161 の「残る閂は承認 1 件」は、ユーザーが負う最後の判断が
  1 件という意味で読むのが実装と整合する。
- 段 3 レンズ A が親 brief の誤りを 1 件摘発した。brief は
  `test_s8b_holdout_freeze.py` の 2 node を「承認 loader の既存負例」と書いたが、
  両者は pin を `None` にする pin-gate の負例で loader へ到達しない。親が実測して確認し訂正した。
  ただし同レンズの「loader を直接対象にした既存テストが無い」は refuted で、
  pin を実 hash に設定して canonical 比較へ到達する既存 node が在る。partial real として裁定した。
- 段 6 のレビュー B が**親の変異事前登録の誤り**を摘発した。MU-3 を「verify の holdout 集合
  比較を緩める」と登録したが、`verify` に集合比較は無く production の `_validate_budget` へ
  委譲しており、注入位置が存在しなかった。tool が渡す `holdout_ids` を候補側の部分集合へ
  差し替える位置へ再照準した。同レビューは親の焦点走が repo 全体の Python を AST parse する
  検査 7 本を取りこぼしていることも指摘し、親が焦点走へ追加した。
- 段 5 実装子の prompt で親が「`output/` 配下へ書かない」と書いたため、実装子が
  `tools/run_tests.py` の正規の dispatch 記帳で停止し、テストを 1 件も実走できなかった。
  runner 自身の記帳は禁止対象から外すべきだった。Codex sandbox では元々 pytest を実走できず
  実測は親の担当であるため、成果への影響はない。段 6 の fix 子 prompt では除外を明記した。
  段 8 でこれを `docs/dev-wave/` へ収容しようとしたが、**L1.5 層が予算上限に達しており
  87 bytes の最小版すら入らなかった** (9653 > 9566)。安全義務を削って場所を作ることはせず、
  上限も自分で上げず、本 worklog と insight への記録に留めた。層予算の増枠が要るなら親裁定の
  収容表で扱う。段 8 で実際に収容できたのは DW-O03 の 1 件だけである。
- 段 3 レンズ B の待ち手で、harness が「completed (exit code 0)」を通知したのに `.done` が不在で
  待ち手も producer も生存していた事例を実測した。完了を `.done` 非空だけで判定する DW-C00 の
  規律がそのまま効き、未完成の成果物で段 4 へ進むのを防いだ。
- 工数: codex 子 7 本 (plan 1、consult 2、review 2、author 1、fix 1)。いずれも
  `gpt-5.6-sol` / `xhigh`。受入・変異・焦点走は計算ノードへ dispatch した。

## 次の一手差分

### 更新

- [T-1675] **P1・ユーザー手番待ち (数値裁定 + 承認 bytes の設置)**: 承認を発行しない
  preflight (`skeleton` / `verify`) は着地済み。残るユーザー手番は 2 つで、
  (i) 予算数値の裁定 (保留 / 2592・1296 / 2400・1200。現証拠の推奨は保留)、
  (ii) 承認 JSON と pin を人間がコード diff をレビューして置くこと (D287)。
  手順と根拠は `docs/s8b-budget-approval-user-turn.md`。
  なお承認は official floor campaign の起動を塞いでおらず、official 実行後の再凍結で使われる。
  base: 12a061ea7c4d733d6e9561f00487aed4207cb33c50289f7b036238a359833298

### 新規

- {{T:budget-approval-placement-ruling}} **P2・ユーザー裁定待ち**: 承認 bytes を誰が置くかの
  射程衝突を裁定する。D287 は本 pin について「人間がコード diff をレビューして定数を置く」を
  要求し、D758 決定 2 と D905 は enforcement closure 批准について「行の貼り付け・コマンドの
  実行を人間手番に置く設計は採らない」としている。本 wave は D287 を優先して preflight までに
  留めた。択一は (a) D287 を本 pin について維持する (現状)、(b) D905 の「成りすませない実行
  主体」を本 pin へも設計する別 wave を起こす。
