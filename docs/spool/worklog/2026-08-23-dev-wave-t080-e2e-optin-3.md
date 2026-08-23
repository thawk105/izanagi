---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t080-e2e-optin
seq: 3
title: T-080 stub-free E2E の opt-in を棚卸しし、撤去して受入全走へ戻した (コード + 記録、branch worktree-dev-wave-t080-e2e-optin、変異 matrix = baseline PASSED・MUT-1〜7 7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **依頼と結果。** `orchestrator/tests/test_s8b_oracle_driver.py` の `IZANAGI_T080_E2E=1`
  opt-in skip (6 function / 展開後 11 nodeid) を棚卸しし、(a) 受入全走へ戻す / (b) 別 gate で
  定期実行 / (c) 削除 のいずれかを証拠つきで裁定せよ、というもの。**(a) を採り、opt-in を
  機構ごと撤去した。** 設計判断は {{D:t080-e2e-optin-removal}} と
  {{D:t080-default-execution-probe}}、失敗は {{F:optin-test-rots-against-later-ruling}}、
  {{F:hold-marker-not-exposed-to-caller}}、{{F:test-temp-root-can-become-real-tree-writer}}。
- **依頼が置いた前提は外れていた。** 依頼は「`external/ccbench/.git` が実在するので
  opt-in の理由が依存物不在なら既に解消している可能性がある」としていたが、
  導入 commit `fe34c90f` (2026-08-12) の理由は**依存物ではなく実走コスト**だった
  (fixture 構築 1 回 213.40 秒、4 key 合計 899.69 秒)。ただし「理由が既に解消している」という
  見立て自体は別経路で当たっていた — その律速 (T-080 receipt 履歴検査の per-commit git 起動) は
  **同じ wave の D313 が batch 化して畳んでいた。**
- **走らせたら 2 件が赤だった。** opt-in にした**同じ日**に別の裁定
  `rulings-4th-batch-2026-08-12` が凍結検証保留を入れ、走っているテストにだけ追随改修が入った。
  片方 (`..._single_defects_have_single_exact_reason_b5[ccbench-current]`) は**同じテスト関数の
  3 枝のうち 2 枝だけが対応済み**で 1 枝が取り残される部分適用、もう片方
  (`test_never_issued_generator_tamper_reaches_public_driver_gate_g7`) は refusal 件数が
  4 件から 3 件へ減っていた。**11 日間、ccbench pin 不一致と holdout generator 改竄を
  public gate が拒否しない状態が隠れていた。**
- **(b)(c) の却下根拠は古い記録に寄りかかっていないか、現在の repo で再確認した。**
  (b) の「定期実行の基盤が repo に無い」(D220、2026-08-07) は現在も真で、
  `.claude/settings.json` は hook のみ、CI / cron / timer は無い。
  (c) の「11 件すべてに完全代替は無い」(2026-08-12 の敵対レビュー B) も、直接 helper 検査
  (`test_t080_freeze_migration.py` の artifact bytes / ccbench pin、
  `test_s8b_oracle_driver.py` の direct `_verify_source`) が実 repo・public `verify_receipt`・
  public driver gate を通す E2E と受理集合が異なることを確認して維持した。
- **親 brief の誤りを 3 件、段 3 の敵対相談が確定させた。** (1)「gate は緩めない / 受理集合を
  狭いまま保つ」は事実として誤りで、保留中は ccbench pin 不一致が実際に `active-valid` として
  受理される。正しくは「既にユーザーが裁定した保留以上には広げない」。(2) 不変条件に
  「300 秒超なら撤回」が残っており、D312 に従って改訂した (P4) と自己矛盾していた。削除した。
  (3)「追加 309 worker 秒」は単位の取り違えで、309.17 秒は単一プロセス 2 走の pytest wall 差、
  xdist の worker 秒合計は 471.23 秒である。
- **走行形態由来の偽赤を実測で切り分けた。** 単一プロセス走 (login node、`python3 -m pytest`) では
  13〜14 件の赤が出たが、`tools/run_tests.py` 経由 (計算ノード gen_S、xdist) では**1 件も
  再現せず、赤はちょうど腐り 2 件だけ**だった。自分の worktree で単一プロセス走して出た赤を
  そのまま実在の赤として扱ってはならない。
- **段 6 の敵対レビュー 2 本が blocker 3 件・must-fix 6 件を出し、全件 fix した。**
  blocker は (i) temp root 境界検査が pytest の `tmp_path` 生成より後に走るため本来の攻撃を
  防げない、(ii) probe の `assert rc == 0` が 122 node 全体の rc を 11 node の判定へ流用する
  過剰拒否、(iii) probe が実履歴を読むのに排他鎖の外に居る、の 3 件。
  fix で probe を `--collect-only` (全 file) と `--setup-only` (対象 11 nodeid 限定) の 2 走へ
  分けた結果、**焦点走が 104.87 秒から 72.84 秒へ縮んだ。**
- **閉じないと決めた所見を 3 件、理由つきで記録した。** テスト本体の骨抜き (先頭 `return`、
  本体内 `pytest.skip()`) は probe でも AST でも検出できないが、これは repo の全テストに等しく
  成立する性質で、**骨抜きを検出する機構は変異 matrix である**。probe の子環境は受入全走の
  xdist worker 環境と同値でなく、**受入そのものでない probe に受入での実行を証明させることは
  原理的にできない**。positive control 自身を黙らせる外側の防壁が無いのも同じ層の問題である。
  したがって成果の主張は「既定 collection での沈黙の検出」に限る。
- **変異 matrix: baseline PASSED、7/7 KILLED、SURVIVED 0、MISMATCH 0、期待 node 集合は
  全件完全一致** (`mutation-final.json`、spec sha256
  `a232508bf8b8a762c991e97f68fdf3f601a798b312d5f9dd9045e78a9a4a56b0`、rc=0、HEAD 5c087062)。
  段 2 が挙げた 6 変異は段 4 で全面再照準した — 旧 M1 (marker ID 差し替え) と旧 M6 (env 再追加) は
  **等価変異**で、前者は import 時 count/hash pin が先に落ちて対象 assert へ到達せず、後者は
  consumer 削除後の選択集合を変えない。
- **新旧差分 (DW-M08)。** MUT-4 (module 冒頭 `pytestmark` で沈黙) と MUT-5 (conftest の
  collection hook で沈黙) を殺したのは新設 probe
  `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default` **1 件だけ**で、
  この node は変更前 HEAD `c00a8ae1` に存在しない。MUT-7 を殺した境界負例も同様である。
  **旧 AST 監査は module 冒頭 marker も conftest hook も見ないため、変更前ならこれら 3 変異は
  生存する。** これが本 wave の検出力の純増分である。
- **MUT-7 の blast radius を実測した。** 境界検査を外した状態で負例が実 `output/` へ
  382〜451MB (`output/t080-stub-free-e2e/`) を書き込んだ。境界検査が実効性を持つ直接証拠であると
  同時に、変異走行の残骸が harness の復元対象 (tracked file) の外に残る型でもある。
  probe 走と本走の各 1 回、untracked を確認のうえ撤去した。
- **並行セッションとの調整で 2 件が是正された。** (1) 裁定集約セッションから
  「`test_growth_test_holds_contract.py` の 1 件が main 単独で決定的に赤」と通達を受けたが、
  直後に訂正が入り、正しくは**色出力が有効なときだけ発火する**赤で、色が無効な dispatch 経由の
  受入全走では出ないと確定した。**逆にこれは、受入全走が色有効時だけ発火する欠陥を構造的に
  取り逃すことを意味する。**「受入が緑だから直った」はこの型には成り立たない。
  (2) こちらは D312 (数値目標は達成目標であって合否判定ではない) を見落として
  「予算超過なら撤回」と書いていたのを是正した。
- **oracle の正しさゲートの穴 (別セッション報告の A1/A6) との独立性を確認した。**
  A1/A6 は `orchestrator/campaign/sort_swo_oracle.py` の候補評価の話で、本 wave の 11 nodeid が
  通るのは `s8b_oracle_driver` / `t080_freeze_migration` / `s8b_holdout_freeze` の経路である。
  `test_s8b_oracle_driver.py` は `sort_swo_oracle` を import していない。
  なお A1 の型 (判定に使う witness を候補自身が消せる) は、本 wave が段 4 で
  「証拠の出所が検査対象と同じ層にあると証拠にならない」として call-edge witness を採った話と同型である。

## 次の一手差分

### 新規

- {{T:t080-held-checks-propagation}} **P2・新規**: 凍結保留の marker を
  `GateDecision.held_checks` へ伝播させる。現状は `s8b_holdout_freeze.verify()` が作る marker を
  `s8b_oracle_driver` が戻り値ごと捨てるため、public gate の呼び手から保留が見えず、
  「保留が効いている」と「verifier の呼び出しごと消えた」を区別できない。本 wave は
  production を触らず call-edge witness で後者だけを閉じた。詳細は
  {{F:hold-marker-not-exposed-to-caller}}。
- {{T:t080-acceptance-temp-root-admission}} **P3・新規**: 受入環境の temp root を admission する層を
  設計する。明示 `TMPDIR` が実 repo の `output/` 配下を指すとテスト fixture 自身が実ツリーの
  writer になる。本 wave は fixture 側の import 時境界検査だけを入れた。発火する既存 artifact path も
  計測 ID も書けないため層の実装は見送っている。詳細は
  {{F:test-temp-root-can-become-real-tree-writer}}。
- {{T:mutation-harness-nodeid-suffix}} **P3・新規**: `tools/mutation_harness.py` の nodeid 正規化の
  非対称を解消する。失敗 node は xdist loadgroup の `@<group>` suffix 付きで記録されるが、
  期待 node は suffix の付かない `--collect-only` の結果と突き合わせられるため、xdist で撮った
  観測 node をそのまま期待値へ写すと起動前に中止する。本 wave は変異走行を `-n0` にして回避した。
