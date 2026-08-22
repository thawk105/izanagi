---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-runtime-opt
seq: 5
title: 取り残し branch を回収し、受入 wall を専有に近い計算ノードで測り直して指定候補の交換レートを確定した (docsのみ、branch worktree-dev-wave-acceptance-runtime-opt)
---

## 本文

- ユーザーが 2026-08-23 に「スイート全体は最悪 5 分」「同種の性能問題では該当テストの除外を
  優先」「正しさ検証機構の再設計・高速化は別途扱う」と裁定し、
  `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` (単独 87.46 秒) を
  優先対象に指定した。本 wave はこの前提を実測し直した結果、**指定の根拠になった 87.46 秒が
  再現しない**ことを確認した (27.65 秒)。裁定は親が不採用にせず、交換レートを添えて
  ユーザー再裁定へ返した。正本 = {{D:acceptance-wall-measured-on-dedicated-node}}。
- 段 2 (codex plan) は親の費用算定を独立に再導出して一致した。段 3 の 2 レンズ (sol = 正しさ境界、
  luna = 整合性・実効性) は計 15 所見を返し、**親はすべて real として採用した。棄却した所見は無い。**
  主な是正は次の 4 点。
  - 親が最初に出した「総直列 5943.8 秒」は失敗ダイジェスト部の数値を巻き込んでいた。
    厳密集計は 8351 相・5917.79 秒。以後この値を使う。
  - 「wall 0.576 秒短縮」は均等配分モデルの値であって実測ではない。親は当初これを
    「自分の実測で反証した」と書きかけていた。実際の差は 0 〜 27.65 秒の幅がある。
  - 87.46 秒と 27.65 秒の差を混雑だけに帰せない (HEAD が異なり、総 item 数も 14364 対 14378)。
    「混雑を含む未切り分け」と書く。
  - 「検出力を保った高速化候補は存在しない」と「本 wave では安全性未証明のため実装しない」を
    混同しない。前者は誤りで、`--ff` / `--nf` の 2 subprocess の有界並列化という受理集合不変の
    候補が実在する (期待短縮は wall 約 0.19 秒で、単独では投資に見合わない)。
- 実装差分はゼロで裁定した (段 5・6 を飛ばし 4→7→8→9)。変異 matrix は「実装しない裁定 +
  実装差分ゼロ」により免除、受入全走は免除していない。
- 本 wave が最上位候補として挙げた 2 件は、いずれも**既に専任 wave が担当中**と確認した
  (`ListAgents` と稼働 process の実査、2026-08-23 04:55)。新規起票はしない。
  - `tools/check_acceptance_reds.py` の赤 1 件ごとの逐次 dispatch (26 件で 41 分以上、
    テスト本体は合計 1.0 秒) → worktree `dev-wave-acceptance-reds-probe-perf`。
  - `orchestrator/tests/test_sort_swo_oracle.py` の恒久除外 → worktree
    `dev-wave-sort-swo-oracle-exclusion`。
- 段 dispatch が必読とする `DW-O27` が branch tip (4969a2e4) に不在で読み込み契約が
  fail-closed したため、段 1 より前に local main 83baeefa を取り込んだ (merge 3aba1320)。
  取り残し branch の再開では「main 取り込み」が段 1 の前提操作になる。
- 前 wave の記録 fragment 3 件は本 wave の land で初めて canonical へ入る。うち
  `test_sort_swo_oracle.py` 26 件の赤を非帰属と判定した根拠は docs-only 差分と
  `config.h` 欠落の推定であり、意味の正しさは spool の形式検査が見ない。専任 wave の
  結論が出るまで provisional として扱う。

## 次の一手差分

### 新規

- {{T:real-repo-priority-hold-user-readjudication}} **P1・ユーザー裁定待ち**:
  `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` を growth-test hold
  registry へ登録して既定 skip にするか否かを裁定する。得るのは wall 0.576 秒 (均等配分モデル、
  実測ではない。実 packing 次第で 0 〜 27.65 秒)、失うのは `--ff` / `--nf` 注入後の最終
  collection 順と parameterize 時の canonical node 境界対照の 3 検査、要する実装は 4 ファイル
  以上と `tools/hold_inventory.py` の単数 `ruling` field の schema 裁定。
  正本 = {{D:acceptance-wall-measured-on-dedicated-node}}。
