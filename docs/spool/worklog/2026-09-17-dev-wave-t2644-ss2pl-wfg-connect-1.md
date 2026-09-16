---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2644-ss2pl-wfg-connect
seq: 1
title: [T-2644] SS2PL の待ちグラフ計器と runner の検証器を接続し、計算ノード 1 走の実データで D791 の 4 条件を独立判定した (コード + docs、branch worktree-dev-wave-t2644-ss2pl-wfg-connect、変異 matrix = 本文末尾)
---

## 本文

- ユーザー依頼は「patches/ の SS2PL 計器と `tools/pegasus/run_ss2pl_lock_study.py` の検証器を接続する —
  伝達、node と辺の field 名 4 箇所、出力先 flag。接続後に計装 build で 1 走だけ計算ノードで通し、検証器が D791 の
  4 条件を独立に判定できることを実データで確かめる。計器は既定 OFF の compile-time スイッチのまま (規律 1)。
  Codex author (D95) + 変異事前登録。本題の接続だけ。規律 2 を緩めない」。
- 一次資料は `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md`。計算ノード 3 走の受領証、login の gate CLI
  出力、実走の stdout / durable file、段 1〜6 の逐語、probe 本体の逐語を同 dir に保全した。
- **断絶は起票の 3 件でなく 6 件だった。** 段 1 の前提実測で (5) build 軸の表示行 `ShowOptParameters()` が全 worker join 後
  にしか出ず hang して kill された走行では `_admit_output` が必ず落ちること、段 2 の plan で (6) 排他 lock (`KIND=0`) で計器が
  read 操作を `read` と出し検証器が read/read を両立と判定して実閉路を拒否しうることを見つけた。(5) は起動時に軸行を出す
  (`#if SS2PL_WFG_DIAG` 内)、(6) は mode を実 lock mode (`write`) で出す、で直した。検証器の述語は 1 行も変えていない。
- **実データ: request 0:2339.nqsv (bnode007) の高競合点 1 走で、production の `_run_phase_trial` が thread 16 ⇄ 21 の
  write/write 閉路を tick 5/6/7 の 3 snapshot で受理した** (`accepted_cycle` 非 None、`timed_out=True`、SIGKILL、
  commit 0 / abort 0 / attempt 1)。条件 1 は holder の `held_locks` との照合と非両立の再導出、条件 2 は 3 枚の node
  signature と edge topology、条件 3 は counter、条件 4 は `_run_process` の timeout、と判定材料を分けて受領証に残した。
  独立性の射程 (registry の正しさは信頼境界、条件 3 は attempt 不変と冗長、kill まで閉路が持続したとは言わない) は
  一次資料 §2。同じ走で性能 arm S を build し production の `_wfg_absence_evidence` が緑 (規律 1 の実測)。
- **段 3 の 2 レンズが親の brief を 2 点訂正した。** `held_locks` は registry の写しで独立観測源ではない (I2 の表現を
  「照合枝」へ)。generic dispatch の clean env は `PBS_JOBID` を子へ渡さない (probe は best-effort で記録し hostname で
  login を拒む形へ)。段 6 のレビュー 2 本は must-fix 0。
- **計算ノード 1 走目・2 走目は runner の既存不整合で止まった。** 統合 commit の後追いではなく T-2018 (2026-08-27) の
  condition gate 導入以来 SS2PL runner の `build_target` が一度も実走していなかったことによる: inert arm は stock 木対照で
  `ycsb_ss2pl.exe` の owner TU が解決できず、非 inert arm は header / marker define の切替が「define 1 個だけの差」を
  要求する gate と構造的に合わない (`dependency-closure-drift` / `compile-command-drift`)。さらに pristine な
  thirdparty staging では masstree の `config.h` 不在で gate の前処理が落ちる。1 走は probe が `masstree_build` を
  warm-up し gate を通さない production 部品の build で得た (F29 の差は一次資料 §4)。記録は {{F:gate-integrated-driver-never-run-live}}。
- **2 走目の不在性検査は job dir 名の `wfg` に当たった偽陽性だった** (`_wfg_text_hits` は path 文字列も総当たりする)。
  scratch と thirdparty を `wfg` を含まない path へ移して 3 走目で緑。
- `tools/pegasus/ss2pl_lock_study.sh:207` は policy の `<name>_source_path` を文字列連結で組んで読むため、T-548 の
  「読み手 0」の literal 検索から漏れ、launcher は `dependency_policy` 段で落ちる。記録は {{F:constructed-key-escapes-consumer-grep}}。
- 親が probe dispatch の in-flight 中に同一 worktree から焦点走を投げ orphan hold rc=16 を踏んだ (F656 の再発。子は起動せず
  実害なし。impl-a worktree から投げ直した)。
- 設計判断は {{D:ss2pl-wfg-transport-and-mode}}。
- **変異 matrix (統合 commit `3204f48b2` の detached worktree、`run_tests.py test_ss2pl_lock_study.py --force-dispatch`、
  11 変異): baseline PASSED、負例 10 件すべて KILLED、期待 node と観測 node 11/11 一致、等価 m0 SURVIVED、MISMATCH 0。**
  probe 走で集めた観測 node は段 6 レビュー B の静的予測 (集合 S 9 node / (e) / (d)) と完全一致した。C++ 側の変異は
  Python test で検出できないので登録せず、実 stdout の逐語 fixture との一致を契約感度の根拠にした (一次資料 §6)。
- 工数: codex 子 10 本 (plan 1、consult 2、author 2、review 2、fix 3。全段 `gpt-6-astra` / `medium`)。計算ノード job:
  probe 3、provenance 監査 1、変異 24 走 (probe 12 + 本走 12)、受入 (回数は land の受領証が持つ)。login の gate CLI 2 回。

## 次の一手差分

### 完了

- [T-2644] 計器と検証器を接続し、計算ノード 1 走の実データで D791 の 4 条件を独立判定した。残る不足 (gate との不整合、
  phase2 counter、launcher) は別項へ切り出した。
  remaining: none
  base: 73c8452754008f1ce384f7a3bfc599992bf4377e082b6d45b4e775a905e47c86

### 新規

- {{T:ss2pl-runner-build-gate-incompat}} **P2・ユーザー裁定待ち**: SS2PL runner の `build_target` は condition gate
  (T-2018) と patch の設計が構造的に合わず全 arm を拒否し (stock 対照の owner TU 不在、header / marker 切替による
  `dependency-closure-drift` / `compile-command-drift`)、pristine な thirdparty staging では masstree `config.h` 不在で
  gate の前処理が落ちる。`controls` mode は現行のまま動かない。gate の適用範囲を軸ごとに絞るか、patch の軸を
  define だけの差へ再設計するか、runner が warm-up を持つか、の択一。一次資料 §5 の 1〜3。
- {{T:wfg-text-hits-path-false-positive}} **P3・新規**: `_wfg_text_hits` は前処理出力の行マーカと binary の path 文字列に
  含まれる `wfg` を hit にする。path を除いて検査するか、hit の出所 (identifier / literal / path) を分けて判定する。
- {{T:verifier-request-mode-missing-both-sides}} **P3・新規**: `validate_deadlock_evidence` は node と edge の両側で
  `request_mode` が欠けると `None == None` で通す。欠落を拒否する強化 (受理集合の縮小、規律 2 の向き)。
- {{T:ss2pl-phase2-acquisition-paths}} **P3・新規**: phase2 (No-Wait) の `_phase2_counters` が要求する `acquisition_paths`
  event を計器が出さない。terminal JSON の取得回数を stdout event にも出す接続。
- {{T:ss2pl-launcher-source-path-key}} **P3・新規**: `tools/pegasus/ss2pl_lock_study.sh` の `dependency_policy` 段を T-548 の
  hydrate 済み staging root 解決へ付け替える (T-548 が数え落とした consumer)。
