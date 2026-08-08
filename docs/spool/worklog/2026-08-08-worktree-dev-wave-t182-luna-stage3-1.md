---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: worktree-dev-wave-t182-luna-stage3
seq: 1
title: 段 3 敵対相談を sol/luna 混成にし model の単一権威を不在検査で pin した — 全 luna はレビュー NO-GO を受けたユーザー再裁定で不採用 (コード + docs、受入 7373 passed / 20 skipped、変異 6/7 KILLED・SURVIVED 0・MISMATCH 1、branch worktree-dev-wave-t182-luna-stage3)
---

## 本文

- **ユーザー裁定 (2 段階)。** 初回は「段 3 敵対相談を luna@max に置き換えてほしい。luna が 91% の
  能力を発揮しトークン効率を 30% よくしているならば」という条件付きの**全置換**。段 3 の敵対
  レビュー 2 本が NO-GO を返し、親が一次資料の読み違いを訂正して三案 (全 luna / 混成 /
  [T-189] の A/B 待ち) を再提示した結果、**混成 (レンズ 1 本目 sol、2 本目 luna)** が選ばれた。
  段 2 / 5 / 6 は sol のまま。裁定と却下理由は {{D:stage3-hybrid-model-user-ruling}}
- **採用根拠はユーザー裁定だけである。** [T-182] の 91% / −31.6% は同 ID 自身が
  「循環・非盲検・事前登録なし・n=1 のため policy 根拠にしない」と記録しており、本 wave も
  採用根拠にしていない。[T-184] / [T-189] は supersede も carve-out もせず据え置いた
- **親の erratum 1 (前提の誤り)。** brief と段 3 レンズ B への入力で「luna は sol が出さなかった
  所見を 2 件出した」と書いたのは誤り。一次資料
  `output/insights/2026-07-29_t182-model-routing-shadow-pilot.md` の「shadow-only の所見 2 件」は
  **luna 1 件 + mini 1 件**であり、luna のその 1 件も**別の sol run (レンズ A の所見 9) が独立に
  到達**していた。sol を 2 本走らせる現行構成に対する luna の純増所見は **0 件**である
- **親の erratum 2 (裁定文の誇張)。** 段 4 裁定で「混成なら sol の検出集合を 1 件も失わない」と
  書いたのは誤り (段 6 レビュー R2 が指摘)。T-182 の比較はレンズ B の同一 prompt に対するもので、
  luna を割り当てたレンズでは sol が出したはずの所見を落としうる。**無損失は主張しない**
- **親の erratum 3 (変異事前登録の過剰決定)。** 変異 M5 (slug 正規表現を backtick 付きだけに限定)
  の expected_nodes を 4 件と登録したが、実際は 9 件が赤になり MISMATCH。`DW-M02` に従い初回結果を
  消さず erratum として残し、単一理由の M7 (`authority_residue` 検査の除去、期待 2 node) へ
  再照準した。M7 は期待と完全一致で KILLED
- **段 3 の敵対レビュー 2 本が NO-GO (BLOCKER 3 + 4、refuted 0)。** 全 luna 化は D207 が
  「検出力を下げる変更は規律 2 の対象」と明記する型に当たる、91% は見落とし確率ではない、
  文書 pin が実起動を縛らない、F56 で served model を attest できない、など
- **段 6 の敵対レビュー 2 本も NO-GO (BLOCKER 4 + 5、refuted 0)。** 決め手は「dispatcher の
  literal pin が `in` 判定だけで件数も可視性も見ない」「`DW-O01` に `-m <model>` が在ることを
  pin していないので placeholder ごと消せる」「slug 不在検査が 3 節に閉じており `DW-S05-A` に
  第二の権威を置ける」。fix は 3 巡
- **設計を wave 途中で変えた。** 当初は model 権威を dispatcher の「凍結境界」へ置いたが、
  local main を取り込んだところ同 file が別 wave の編集で 9,457 / 9,500 bytes になっており
  入らなくなった (その wave も「本文編集は予算不足で裁定へ返す」としている)。権威を
  `DW-O01` へ移した結果、段 6 レビュー R2 の BLOCKER (権威が起動直前の必読集合に無い) も
  同時に閉じた。設計判断は {{D:dev-wave-model-single-authority-absence-pin}}
- **byte は削らずに捻出した。** `DW-S02` の「read-only 固有のテスト帰属は `DW-O05` に従う。」
  1 文を外した。同義務は段 2 preflight の dispatch 表 (`check_docs.py` の
  `_pairs(_OPERATIONS, ..., "DW-O05")`) と条件 05 で二重に機械強制されており、prose を外しても
  義務は失われない。最終 = dev-wave reference 25,180 / 25,200、dispatcher 9,457 / 9,500
- **本 wave 自身の段 2 / 3 / 5 / 6 はすべて `gpt-5.6-sol` で走った** (混成契約が未 land のため)。
  本 wave の敵対所見を luna の成果として読んではならない。F56 のとおり
  `requested_model` は記録できるが `served_model` は unknown である
- **段 1 生死確認**: `codex exec -m gpt-5.6-luna -c model_reasoning_effort="max" -s read-only`
  は rc=0、CLI reported 13,017 token。F56 (b) の「消費 0 の見せかけ成功」ではない
- **裁定パッケージ (scope 外、ユーザーへ返す)**: (i) 実起動の runtime binding —
  `-m` の実引数と権威行の機械照合。Claude の hook は Codex 経路に未配線のため両経路を覆う設計が要る。
  (ii) served model の attest (F56、[T-189] 所有)。(iii) EOL 正規化の欠如 — 4 reference を
  CRLF 化すると byte gate が別環境で壊れる。(iv) `orchestrator/codex_roles/` の model allowlist
  (`spec.py` の `{gpt-5.6-sol, gpt-5.6-terra}`) に luna が無い。(v) dev-wave reference と
  dispatcher の byte 予算が慢性的に逼迫し、複数 wave が編集を断念している
- 実測はすべて計算ノード。受入全走は 3 回。1 回目 (実装 tip `03f1487b`) = 7373 passed /
  20 skipped (1174.40s、job `895950.nqsv`)。記録 commit が実 repo を読むテストへ影響しうるため
  tip ごとに再走し、2 回目 (`dd17b571`) = 7372 passed / **1 failed** / 20 skipped
  (1161.74s、job `895953.nqsv`)、3 回目 (`9a99fede`) = **7373 passed / 20 skipped・赤ゼロ**
  (1210.04s、job `895995.nqsv`)。**land 対象 tip の権威値は 3 回目**である。
  land 直前の最終 amend 1 commit だけは docs のみで、`DW-S07` / F34 に従い
  repo scan invariant (`check_docs` / `check_ai_provenance` / spool fold dry-run) で閉じた。
  `orchestrator/tests/test_check_docs.py` = 325 passed。`check_docs` 違反なし。
  `check_ai_provenance` 新規違反なし
- **2 回目の赤 1 件はフレークと実測した。**
  `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table` は
  本 wave の差分が到達しないファイルであり、1 回目の全走では緑、単独再走でも
  **64 passed** で再現しなかった。`DW-O18` に従い実装差分へ帰属させない。
  再現条件は不明で、同 test の非決定性は本 wave では追わない
- エージェント工数: Codex 8 session (probe 1 / plan 1 / 段 3 相談 2 / 実装 1 / 段 6 レビュー 2 /
  fix 3 = 計 10、うち probe は claude 親が採点)。正確には probe 1 + plan 1 + 相談 2 + 実装 1 +
  レビュー 2 + fix 3 = 10 session。親 = brief・裁定・docs 編集・統合 commit・main 取り込み・
  変異 2 走・受入全走・記録
- 一次資料 = `output/insights/2026-08-08_t182-luna-stage3-hybrid.md`、
  逐語と変異台帳 = 同 `-verbatim/`

## 次の一手差分

### 新規

- {{T:dev-wave-model-runtime-binding}} **P2・新規**: dev-wave が起動する codex の `-m` 実引数を
  `DW-O01` の権威行と機械照合する層を設計する。Claude の PreToolUse hook は Codex 経路に
  未配線であり、両経路を覆う配線か、両経路が必ず通る launcher への集約が要る。
  served model の attest は [T-189] の所有のまま切り離す
- {{T:codex-worker-launch-truth-table-flake}} **P3・新規**:
  `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table` が
  受入全走で 1 度だけ赤になり、単独再走 (64 passed) と直前の全走では緑だった。
  非決定性の源を特定し、再現条件を固定するか test を決定的にする。
  実装差分とは無関係の観測であり、再現は 1 例のみ
- {{T:dev-wave-docs-budget-relief}} **P2・新規**: dev-wave reference (25,200) と dispatcher
  (9,500) の byte 予算逼迫を、上限引き上げ以外の手段で恒久的に緩める。複数の wave が
  同じ壁で本文編集を断念している。陳腐化ルールの削除と、prose の機械検査への移管
  (テスト化) の 2 経路で候補を棚卸しする
