---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2702-digest-indicator-consistency
seq: 1
title: [T-2702] digest の leading indicator 行から latency を外し、偶数 reps の abort_rate / latency_ns を throughput と同じ中央値演算に揃えた (コード + テスト、branch worktree-dev-wave-t2702-digest-indicator-consistency、変異 matrix = 2 spec・baseline PASSED・runner 用 6/6 KILLED + 等価 1 件 SURVIVED (登録どおり)・digest 用 1/1 KILLED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **依頼の scope**: 本題の 2 点だけ。(a) `latency_ns` は CCBench の通常出力で `1e9 * thread_num / throughput` の
  恒等変換なので critic digest の列から外す (WAL には残す)。(b) 偶数有効 reps で代表 rep が上側中央 (速い側) へ
  寄り、同じ行の throughput (真の中央値) と abort_rate / latency_ns (代表 rep) が別の量になるのを、
  throughput と同じ中央値演算 (中央 2 rep の算術平均、一方でも欠損なら None) に揃える。gate・検査・台帳・
  一般化の追加は scope 外 (ユーザー指示)。CCBench は改変しない。Codex author 1 本 (gpt-6-astra / medium) +
  文言 fix 1 本。設計択一が割れたので段 2 plan・段 3 敵対 2 レンズ・段 6 レビュー 2 レンズを省かなかった。
- **裁定 (段 4)**: (b) の修正形は案 A' = abort_rate / latency_ns だけを平均し、counters / walltime / maxrss の
  単一 rep field と奇数有効 reps は現行の規則 (上側中央、同値なら実行順で先) を保つ。段 3 が real と示した
  2 点を採用した — (i) counters まで「実行順が先」へ変えると perf_preflight の counter_status 分類と
  calibrator の飽和点・下限点選択に届き本題の外、(ii) 片側 None を採る規則は「同じ rep 集合・同じ演算」に
  例外を作り screening の欠損時挙動も変える。**不変条件の言い直し**: verifier の判定規則・fitness の式・
  certified の条件 (全 verify 通過) は不変だが、bench-first screening (`pipeline.py:2366-2375`) は abort_rate を
  読むので偶数有効 reps の境界事例で screen-reject ↔ verify 送りが両方向に入れ替わりうる。「certified 集合が
  不変」とは主張しない。screening の改変と新テストは scope 外として足していない。
- **refuted / 撤回**: 親の「P3' は None を増やす方向にしか動かない」は同値 tie に反例があり撤回 (段 6 レビュー A)。
  「奇数 reps では bytes 不変」は「奇数**有効** reps」に限定 (偶奇は要求 reps でなく有効 throughput の個数)。
  brief の runner.py 2 経路の名称は逆だった (段 2 plan が訂正)。
- **残件 (裁定パッケージ候補、触っていない)**: role 文書 4 箇所 (`.claude/agents/critic.md:14,26-27,36`、
  `critic-experiment.md:36-37`) が latency を独立指標として列挙・帰属例に使い digest と食い違う (役割入力の
  変更は K0/K1/B-4 の射程裁定と同時に、T-2703 と同型)。8c の役割 payload (`s8c_generation_projection` の
  latency_ns key、D118 の閉列挙) は残る。過去 WAL と T-2588 の人手射影 (abort 7.75%) は直らない —
  完了条件は critic digest と今後の runner 集約に限る。詳細と consumer / producer の全列挙は insight
  `output/insights/2026-09-16/t2702-digest-indicator-consistency/README.md`。
- **実測 (記録前)**: 焦点走 (変更 module を参照する test 43 file + `test_plain_runner_coverage.py`、
  tip 106c0ec04、Pegasus request 1963.nqsv) 6135 passed / 12 skipped / 失敗 0。変異は probe 走 (8 件 SURVIVED 登録で
  観測 node を収集、tip 106c0ec04) の後、fix commit d586abff5 で本走 2 spec: runner 用 (M1〜M6 KILLED /
  M8 等価 SURVIVED、runner argv = `test_calibrator.py`) と digest 用 (M7 KILLED、`test_critic.py`)。結果は runner 用 baseline PASSED・6/6 KILLED・M8 SURVIVED・MISMATCH 0・期待 node 完全一致、digest 用 baseline PASSED・1/1 KILLED・MISMATCH 0。
  runner.py は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob 束縛なので、runner 変異では
  `test_critic.py` の admission 系 46 node が contract-loader-drift で赤になる (等価変異 M8 でも同じ 46 node、
  M1〜M6 と集合が完全一致)。これは検出ではないので spec を file 別に分け、kill には数えていない。全件が
  構造化値の pin で受理集合の変化は観測しない (DW-M03/M08 の diagnostic sensitivity pin)。
- **commit**: 106c0ec04 (実装 5 file、Codex author) → d586abff5 (文言 fix、Codex author + reviewer)。
  全史 provenance 監査は 106c0ec04 で 10603 件・新規違反なし (request 1944.nqsv)。d586abff5 で 10604 件・新規違反なし (login node)。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。

## 次の一手差分

### 完了

- [T-2702] critic digest の指標列から latency_ns を外し、偶数有効 reps の abort_rate / latency_ns を
  throughput と同じ中央値演算 (中央 2 rep の平均、片側欠損なら None) に揃えた。role 文書・8c payload・
  過去 WAL は残件として insight に記録。
  remaining: none
  base: 0a42624f351590403a53c4edfbd20e8497957f5caaed7ca1f1ee0e8e5c3d6072

### 新規

- {{T:critic-role-latency-wording}} **P2・新規**: critic の役割文書 (`.claude/agents/critic.md:14,26-27,36`、
  `.claude/agents/critic-experiment.md:36-37`) が latency を独立指標として列挙し帰属例に使うが、[T-2702] 以後の
  digest には latency 列が無い。役割入力の変更は K0 / K1 / B-4 のアーム条件を変えるので、[T-2703] と同じ射程裁定の
  中で直す。同時に 8c 役割 payload の `latency_ns` key (D118 の閉列挙) と、counters / walltime / maxrss の代表 rep が
  偶数有効 reps で上側中央のままである点 (平均化は perf_preflight の分類と calibrator の点選択に届く) を裁定する。
