---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2654-t316-hydrate-base
seq: 1
title: [T-2654] t316 の条件関門と両 build を hydrate 済み staging + prepare_masstree_fetchcontent の準備済み base へ合流させ、計算ノード実経路で S6 go に到達した (コード + テスト + docs、branch worktree-dev-wave-t2654-t316-hydrate-base、変異 matrix = baseline PASSED・負例 13/13 KILLED 期待 node 完全一致・対照 M0 と冗長 gate 対照 M7b SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「t316 の条件関門 (`FETCHCONTENT_SOURCE_DIR_*` が永続 third-party cache の生成物を直接指す) を、既に緑の
  2 例と同じ準備済み base (hydrate staging) を使う形へ揃える。既存機構への合流で新しい仕組みは作らない。過去の測定事実は
  無効化しない (規律 7)。着手直前の local main から fresh worktree。実装面は Codex author (D95)、変異事前登録要。計算ノード
  実走は既存 probe の経路で 1 回。規律 2 を緩めない。本題の合流だけ。追加の gate・台帳は scope 外」(D2044 項 27 の実装手番)。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2654-t316-hydrate-base/README.md`。設計判断は {{D:t316-hydrate-prepare-base}}。
  実装 commit `f296e42bc` (Codex author、3 file)、受領証 commit `ef958a7e1`。
- **計算ノード実経路 (request `0:4163.nqsv`、bnode064、Elapse 108 秒) で S6 go に到達した。** hydrate は `/scr` で 1.37 秒、prepare は
  11.39 秒、両 build の configure は staging を指し cache を指さない。supply 腕は `stock-inert-preprocess-root-location-only` の緑、
  family admission は admitted。overall no-go は修正前の 3 走と同じ S3 inconclusive / S5 no-go (本 wave の変更面と無関係)。
- **親の brief の誤りを段 3 が 2 件正した。** (a) `test_ccbench_spawn_sites.py` の台帳登録が要るとしたが、走査範囲は orchestrator
  配下で prepare は sink に当たらない (登録不要)。(b) `_verify_pristine_floor_dependency_sources` を使わない理由に D2085 を引いたが、
  D2085 は gflags / glog の使用直前検査に限る決定で二重検査一般の禁止ではない。理由を「hydrate 自身が生成時に検証・A-2 の複製経路を
  導入しない・追加 gate は scope 外」へ改めた。時間予算は見積りに降格し、変異 (g) は 2 置換へ再照準した。
- **段 6 レビュー 2 本は must-fix なし。** should-fix (prepare 失敗時に呼び出し入力が受領証に残らない) を fix 子で直した。
  関門例外時に新観測 2 key が消える点 (既存の例外設計) と、prepare の固定 configure が共有 configure の ccache / launcher 抑制を
  持たない点、timeout が子孫停止・撤去まで保証しない点は限界として insight に記した。
- **テストコストが増えた。** `test_t316_sandbox_probe.py` は login で 166 passed / 112 秒 → 180 passed / 271 秒。単独計測では fixture の
  git repo 構築 2.8 秒 + 実 hydrate CLI 3.3 秒が live test 1 本あたりの増分の主因 (12 本)。seed 共有で削れるのは 2.8 秒/本で、
  実 CLI を使う限り残りは残る。直近受入で t316 file は最短の shard-2 (175 秒、max shard は 336 秒) に入るため本 wave では
  fixture 共有化を実装せず {{T:t316-fixture-seed-sharing}} に置いた。計算ノードでは同 file の baseline が 48.9 秒。
- 実走: t316 単独 180 passed / 271 秒 (login)、t316 + consumer 6 file 897 passed / 2 skipped (既存 growth hold) / 711 秒 (login)、
  fix 後 33 node 再走緑、provenance full 11076 件・新規違反なし。受入全走は docs commit 後の最終 tip に land 前に 1 回。
- **変異 matrix (container worktree、`run_tests.py` で `test_t316_sandbox_probe.py` 1 file、probe と本走で各 16 run = baseline + 15 変異、
  計算ノード dispatch)。** probe 走で観測 node を集めてから本走。本走は baseline PASSED (52.7 秒)、負例 13 件 (M1〜M6、M6b、M7〜M12)
  すべて KILLED で期待 node と観測 node が完全一致 (matching 15/15)、等価変異 M0 (comment) と冗長 gate 対照 M7b (hydrate の rc 検査だけ
  外す — JSON 解読失敗の層が遮る) は SURVIVED、MISMATCH 0、TIMEOUT 0、全 anchor 1 箇所。専属 killer: M7 (rc 検査 + JSON 失敗処理の
  2 置換) → `test_s6_hydrate_failure_stops_before_identity_and_gate`、M8 (inside でも prepare) / M12 (identity を cache から) →
  `test_s6_live_offline_source_paths_and_prepare_order`、M10 (prepare 失敗後も関門) → `test_s6_prepare_failure_stops_before_gate[…]`、
  M6 / M6b (束縛 1 件落とし) → 束縛 literal 同期 test + dirty 拒否 node。M1 / M3 / M4 / M5 / M9 (cache 直指し・build だけ cache・S を
  scratch 内・ro-bind 落とし・BASE_DIR を S) は observer の call 境界の inline assert が build 失敗より前に赤にする。M2 の 10 node の
  うち 1 本は変異文字列 `and not inside` に当たる既存の静的 pin で付随的 (機構の kill は 9 本)。
- セッション異常: wave 開始時の `EnterWorktree(name)` が `cannot create directory ... Interrupted system call` で失敗し branch だけ
  残った (Lustre の EINTR、F672 と同族の一過性)。既存 branch で手動 `git worktree add` → `EnterWorktree(path)` で復旧。1 件のみで
  F 化しない。段 5 の実装子と段 6 の fix 子は sandbox の hook で pytest を起動できず静的検査のみ (前 wave と同じ)。実走はすべて親。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、全段 `gpt-6-astra` / `medium`)。親の実測: 焦点走 4 (login)、
  変更前計測 1、hydrate 単独 1、fixture コスト 1、計算ノード実走 1、変異 2 走 (32 run)、provenance full 1。

## 次の一手差分

### 完了

- [T-2654] t316 の条件関門と両 build を hydrate 済み staging + prepare の準備済み base へ合流させ、計算ノード実経路で S6 go を確認した。
  remaining: none
  base: 2880b45670a5e33a28ee0d08be4d8ca5a157190da25f8a1e2122961a27926ea2

### 新規

- {{T:t316-fixture-seed-sharing}} **P3・新規**: `test_t316_sandbox_probe.py` の live fixture (cache の git repo 5 本 + 依存 2 本) を
  session で 1 回だけ構築して test ごとに複製する形にし、1 本あたり約 2.8 秒 (login 実測) を削る。実 hydrate CLI・実 prepare・実 bwrap は
  維持する (test の意味を弱めない)。受入の壁 (max shard) に効くと実測で分かった場合に着手する。
- {{T:t316-gate-exception-observation}} **P3・新規**: t316 の `_require_condition_gate` が例外で抜けるとき、直前までの
  `third_party_staging` / `masstree_prepare` 観測が受領証に残らない (既存の例外設計、`run_probe` が `attempted=False` に置き換える)。
  関門の拒否理由 (D1995 の stderr 診断) を保ちつつ供給側の観測を保持する形を、受理集合を変えずに設計する。
