---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t189-reasoning-allowlist
seq: 1
title: "[T-189] 子起動 CLI 3 面の reasoning / effort を許可リストで機械強制した — 正本の置き場所は敵対レビューが supervisor digest 閉包の外だと突いて差し替えた ({{D:effort-allowlist-inside-supervisor-digest}}、コード + docs、branch worktree-dev-wave-t189-reasoning-allowlist、受入全走 = Pegasus gen_S 計算ノード request 878534.nqsv で 5244 passed / 19 skipped、変異本走 = 11/11 KILLED)"
---

## 本文

- ユーザー裁定は択 (a) — 不正な reasoning 値の拒否だけ先に実装し、served model の attest 経路が
  無い点 (F56) は実験の限界として明記する。model routing の比較実験は本 wave の scope 外とした
- **親の provisional 裁定 (P1) が段 1 の実測で反証された。** 親は「`max` を許すのは codex 経路だけ」と
  したが、`claude --help` は `--effort` の正当値として `low, medium, high, xhigh, max` を表示する。
  `max` は Claude 側でも文書化された値であり、codex に限る理由がなかった。
  ただし段 3 が「help の記載は文書化された語彙であって実受理集合の実測ではない」と正しく限定した
- **敵対レビュー 4 本 (段 3 の 2 レンズ、段 6 の 2 レンズ) はすべて NO-GO を返したが、実装本体の
  欠陥は 0 件だった。** 止めたのは (a) 正本の置き場所と (b) テストの検出力である
  - 段 3 レンズ A が段 2 案 (`orchestrator/codex_roles/` 配下) を blocker で却下した。
    `_supervisor_digest()` は `tools/dev_waves/` 直下しか hash しないため、そこへ置かないと
    受理集合だけが変わって `supervisor_code_sha256` が同値のままになる。
    親の provisional 裁定 (P3) も段 2 案を支持していたので、これも親の誤りである
  - 段 6 レンズ R1 が「正例テストが許可集合の定数自身を反復している」を突いた。
    正本から値を消すとテストの入力集合も同時に縮み、消した値を一度も試さずに緑になる
  - 段 6 レンズ R2 が変異 11 件のうち 8 件の帰属不成立を突いた。`schema.py` の membership block が
    同一 bytes で 2 箇所あり短い anchor では harness が止まる、面 1 の正例に実 CLI 起動より手前の
    assertion があり `max` 削除時に subprocess へ到達しない、など
- **焦点再レビューが親の手続き違反を突いた。** 親が書いた変異 spec が段 4 の事前登録から逸脱していた
  (V6 を 2 件に分割、V9 の削除対象を `low` から `xhigh` へ変更)。理由は node 集合を綺麗にするため
  だったが、事前登録の意味を損なう。指摘に従い V1〜V11 の登録どおりへ戻した
- **変異本走で V9 が MISMATCH になった。** 削除した `low` を消費する既存テスト
  (`test_export_is_create_only_and_contains_only_sanitized_wal_view`) を期待 node に入れ忘れていた。
  変異自体は期待方向へ効いており誤りは登録側である。新しい失敗型として
  {{F:positive-mutation-node-enumeration}} に記録し、期待 node を補正した erratum 走で
  KILLED・node 完全一致を得た。初回結果は消していない
- 同じ MISMATCH に `test_all_repo_policy_reasoning_values_are_accepted[xhigh]` も含まれていたが、
  これは Codex 側定数を使う経路であり `CLAUDE_EFFORTS` の変異からは到達しえない。
  erratum 走で再現せず、`DW-O18` に従いフレークとして {{T:codex-launch-fake-flake}} へ起票した
- scope 外と裁定した real 所見は 4 件で、いずれも裁定パッケージとして新規 T に起こした。
  特に `gpt-5.4-mini` × `max` は本 wave 後も admission される — 平坦な集合しか見ないためであり、
  これは F56 恒久対応 (c) の未実装分である
- エージェント工数: codex 子 10 本 (段 2 plan 1、段 3 敵対 2、段 5 実装 3、段 6 レビュー 2、
  段 6 fix 1、焦点再レビュー 1)。計算ノード dispatch は 6 回 (baseline / 統合後 / fix 後 /
  変異本走 / 変異 erratum / 受入全走)

## 次の一手差分

### 更新

- [T-189] **許可リスト部分は実装完了 → 残りは比較実験の設計**: 3 面 (codex worker launcher の
  `--reasoning`、dev-waves serve の `--effort`、worker spec / child argv) に値域検査が入り、
  正本は `tools/dev_waves/effort_levels.py` に 1 本化した。残件は元の主題である
  **妥当な model routing 比較実験の設計** (独立 oracle、held-out 複数 task、block randomization、
  cache 条件の分離、価格 version、盲検裁定、事前非劣性 margin)。[T-182] の pilot は n=1・非盲検・
  後付け採点のため採用根拠にしない
  base: 96b000d83ada866d636658b6a6ed3da9ae0329885d06cc7bc701a823f6eee6d4

### 新規

- {{T:model-reasoning-compat-gate}} **P2・裁定パッケージ**: model×reasoning の非対応組を起動前に
  落とす。F56 (c) のとおり Codex の受理集合は model 依存で、`gpt-5.4-mini` は `max` を拒否し
  `none` を受理する。本 wave の平坦な許可集合は `gpt-5.4-mini` × `max` を通してしまう。
  実装所有は T-183 / T-184 にあるため、着手前に所有の重複を裁定する
- {{T:effort-vocabulary-subset-binding}} **P2・裁定パッケージ**: reasoning / effort の値が
  `orchestrator/codex_roles/manifest.json`、`.claude/agents/*.md` の frontmatter 13 件、
  `docs/dev-wave/workers.md` の条文にも散っている。本 wave はコード側 2 集合の部分集合検査までしか
  束縛しておらず、`workers.md` の `reasoning=max` を `ultra` に書き換えても `check_docs.py` は通る
- {{T:task-runs-reasoning-validity}} **P3・裁定パッケージ**: `tools/task_runs/cli.py --reasoning` は
  値域検査なしで台帳へ入る。ただし観測台帳であり失敗した起動も記録する性質上、拒否ではなく
  `requested_reasoning` と validity の分離が妥当という論点がある。設計択一として裁定へ返す
- {{T:profile-effort-early-check}} **P3・裁定パッケージ**: 永続 profile 経由で不正な effort を渡すと、
  worktree / worker spec artifact を作った後に child argv 構築で拒否される。fail-closed は
  成立しているが「不正値が artifact に一切入らない」は成立しない
- {{T:devwave-m01-shrink-mutation-enumeration}} **P2・新規**: `DW-M01` の事前登録契約へ
  「受理集合を縮小する変異は、削除する値のリテラルを runner scope 全体へ機械検索してから
  期待 node を確定する」を足す。{{F:positive-mutation-node-enumeration}} の手順側恒久対応であり、
  `docs/dev-wave/` が本 wave の no-touch 対象 (T-328 走行中) のため所有を分けた
- {{T:devwave-s01-provisional-refutation-probe}} **P3・新規 (段 8 自己改善候補)**: `DW-S01` は
  「承認済み裁定の前提を実測する」と書くが、**親自身の provisional 裁定 `(Pn)` を反証する実測**は
  義務化していない。本 wave では P1 (`max` は codex 経路だけ) を親の段 1 実測が、
  P3 (正本を `orchestrator/codex_roles/` へ) を段 3 レンズ A が反証した。`(Pn)` を立てるとき
  「その P を反証しうる最も安い実測」を 1 つ併記する義務を足せば、段 3 を待たずに親が自分の
  誤りを潰せる。`docs/dev-wave/` が本 wave の no-touch 対象のため条文追加は本 ID が所有する。
  発火実績は本 wave の 2 件のみで同一 wave 内であり、`DW-G03` の独立 2 例を満たさないため
  制度化はユーザー裁定に委ねる
- {{T:codex-launch-fake-flake}} **P3・新規**: 変異本走 V9 で
  `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[xhigh]` が
  変異と無関係に赤になった (rc=1、`invalid choice` の rc=2 ではない)。erratum 走では再現せず。
  fake Codex child を使う起動テストの不安定性を単独再走で切り分ける
