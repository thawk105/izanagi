---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2502-k2-coder-role-conditional
seq: 1
title: [T-2502] driver の --run-iteration で manifest の sources が非空なら --coder-role を必須にした (D1878、コード + docs、branch worktree-dev-wave-t2502-k2-coder-role-conditional、変異 matrix = baseline PASSED・M0 対照 SURVIVED・負例 5/5 KILLED 期待 node 完全一致・MISMATCH 0)
---

## 本文

- 何をしたか: `orchestrator/campaign/p3_s4_loop.py` の `main()` に、emit 分岐の `return 0` 直後・`build_run_context` と
  `_prepare_knowledge_campaign` (receipt 書き込み) の前で「`--run-iteration` あり・manifest の `sources` 非空・`--coder-role` 無し」
  だけを `ValueError` (sources 件数と欠けている flag を含む) にする 11 行を入れた。空取得 (`sources: []`)・role 付き・manifest 無し・
  `--emit-planner-context`・fixture 経路の受理は変えていない。loader・parser・job body は無変更。テストは負例 N、非空 + role K2 の
  実 loader 正例 P、fixture 経路の過剰拒否正例 F を新設し、既存 identity 共有 test の後半 argv に `--coder-role` を足した。
  `docs/phase3-s4b-runbook.md` の K2 宣言アーム段落に CLI 条件を 1 行追記。実装記録・逐語・変異台帳は
  `output/insights/2026-09-17/t2502-k2-coder-role-conditional/README.md`。
- 実測 (いずれも HEAD c79437d24、Pegasus 計算ノード): 変異登録 6 node 焦点走 6 passed (request 2274)、`test_p3_s4_loop.py`
  単独走 414 passed (2290)、consumer 28 file 3204 passed / 28 skipped (2294)。変異 matrix は固定 commit の `-mut` worktree で
  baseline PASSED、M0 (comment 対照) SURVIVED、M1〜M5 KILLED、失敗 node 集合が事前登録と完全一致 (2291〜2302)。
  敵対レビュー 2 レンズは GO / GO、must-fix 0。fix 子 0 本。受入全走 1 (tip 4b3a8afd5、tested_main 1042a1bc9) は
  child-green・24389 passed / 67 skipped・赤 0・flake 0。その land は 1 巡目 rc=10 (main fa24e6ea8 が先行、固定 SHA merge で
  tip 08ba8f249)、2 巡目 rc=31 (F672 の EINTR 型、別 wave の登録 path、main 無傷) で止まり、F672 の復旧どおり受入を取り直した
  (再発は failures fragment に記録。2 回目の受入と land の結果は land receipt と本エントリの着地 commit が正本)。
- 裁定時に未記録だった新事実 (段 1 で実測、段 3 で real、段 4 で test 追随と裁定): 既存
  `test_emit_context_and_run_iteration_share_manifest_campaign_identity` は後半で sources 非空 manifest を `--run-iteration` + role 無しで
  通し `main == 0` を要求していた。D1878 の「正例を 1 件も壊さずに閉じられる」は意味上の正例 (空取得 + role 無し) には成り立つが、
  この test には成り立たない。決定は動かさず、目的 (campaign identity の一致。`_prepare_knowledge_campaign` は role を見ない) を保った
  まま後半 argv にだけ role を足した。production に例外を設ける案は規律 2 に反し不採用。
- 設計択一 (段 3 の 2 レンズが一致、追加裁定なし): 親 brief の「manifest 解決直後 + run guard」は emit+run 併記を過剰拒否し、
  段 2 plan の「`not a.emit_planner_context` を guard に足して新規 test で殺す」は scope 外の検査追加になる。emit 分岐の return 後に置けば
  制御フローで emit 優先が保たれ、どちらも不要。過剰拒否の正例 F は DW-M01 (受理集合を縮小する wave) が要求する正例であり、
  仮想リスク向けの gate ではない。
- 保証しない範囲 (real だが scope 外): parser の逆向き整合 (非空 sources + `completed_empty`) は検査しない。B-4 projection closure は
  `p3_s4_loop.py` の生 bytes を hash するため本変更で 3 種とも値が変わる — 旧 closure を受理するために gate は緩めず、既存 test golden は
  現行 bytes から計算するので赤にならない (段 6 B が確認)。変更前 sha256 の tracked 全体逆引きは 0 件 (単体 sha の pin 検索に限定)。
- 棄却 finding: 段 4 の「K はどの変異でも sources 空で短絡」は M2 には当てはまらない (反転した sources 条件が真でも role 有りで最後の
  条件が偽)。期待集合は正しい (段 6 A、nit)。持ち越しの最新番号を brief で (1578) と書いたが現物は (1579) (段 3、記述訂正のみ)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全て `gpt-6-astra` / medium、accepted、計 63 calls・約 28 分)、fix 0。
  親 wall は 00:28〜01:28 JST (段 7 記録前まで)。

## 次の一手差分

### 完了

- [T-2502] D1878 を実装した。`--run-iteration` で manifest の `sources` が非空なら `--coder-role` を必須にし、空取得の経路は
  現状のまま通る。既存正例 `test_main_manifest_only_accepts_legacy_flattened_proposal` は無変更で緑。負例・正例・過剰拒否正例と
  変異 matrix (5/5 KILLED、対照 1 SURVIVED) で裏取りした。統合 commit c79437d24。K2 2 巡目の実走認可は別件 ([T-2588] / D2044 項 9) で
  本項には含めない。
  remaining: none
  base: 03ad86155cc6e540443f62733821ed762d74102cf4e1d228193d20224f6f09b8
