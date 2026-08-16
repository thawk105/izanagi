---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-perf-optional
seq: 1
title: 探索 campaign を perf 非依存にし、8c の閂とされていた実行時 attestation が既に解消済みであることを実機で確定した (コード + テスト + docs、branch worktree-dev-wave-perf-optional)
---

## 本文

- **ユーザー方針 (2026-08-16)**: 「perf 導入は前提にしない。perf があってもなくてもうまく
  やれるものを izanagi は目指す」。あわせて、凍結権限束の完成を待つ形は明確に否定された
  (「無期限凍結って何？バカな真似はするな」)。床値 pilot の承認方式は「どうでもいい」として
  AI 側の運用裁定に委ねられた。
- **D143 / F97 の裁定材料が陳腐化していたことを実測で確定した。** D143 決定 (2) は
  「計算ノードで実行時 attestation が全 campaign を build 前に止める」と結論しているが、
  その実測は 2026-08-04 (request 882490) であり、取得経路が方式 α
  (`_collect_rotating_cpuinfo`, k=5 / 50ms / affinity 交差) へ結線されたのは**翌 08-05** である。
  保全されていた使い捨て driver を現行 HEAD で再走させたところ
  (request `0:913859.nqsv`、`bnode006`)、**required attestation は通過し、
  build_done と verify_done (`verdict=serializable` / `certified=true` /
  commits 283,497 / aborts 9,272) まで到達した。** 中断したのは bench の段で、
  理由は `perf not found for kernel 5.15.0-173` である。
  attestation 通過の根拠は、`loop.py` の `_authorize_measurement` が最初の WAL 書込みより前に
  `attest_and_build_receipt` を通すこと、pegasus 契約が `attestation_mode="required"` であること、
  WAL に `build_start` 以降が実在することの 3 点。
- **登録済み較正 2 本の自己整合を読み取りで測った** (certified な測定ではない)。
  受理帯は g1 / g2 とも中央値 2101.0 ± 2% = [2058.98, 2143.02]。
  g1 (`753f535a`) は 48 本中 1 本が帯外 (index 40 = 3080.935) で自分の述語を通らない (F97 の実体)。
  g2 (`94a4b79f`、`bnode048` / request 892707.nqsv で取得) は 0 本で、自分の述語を通る。
  `effective_clock.method` の比較は「双方が非空文字列」で恒真なので、契約が g1 を束縛したままでも
  方式名の差では落ちない。
- **D143 本文の「裁定後に同じ使い捨て driver を再走させれば追加実装なしで確かめられる」は偽だった。**
  12 日分の drift を 4 件実測した — (i) `calibrator/runner.py` の絶対 import 化で
  `ModuleNotFoundError`、(ii) `pipeline.py` の `from ..calibrator...` で
  `attempted relative import beyond top-level package`、(iii) `_campaign_for()` が
  keyword-only の `contract` を要求、(iv) `IZANAGI_EXPLORATION_OUTPUT_ROOT` が未設定かつ
  `dev-wave-jobs` 自身が git repository のため exploration root を置けない。
  適応は使い捨て worktree の作業コピーだけに施し、repo へは入れていない。
  一次資料は `/work/1/SFC/tanab/dev-wave-jobs/wave-a-smoke-rerun-20260816/`。
- **perf の結線が非対称だった。** 床値 campaign だけが `perf_preflight` を消費し degrade できる。
  探索経路 (`loop.py` / `pipeline.py` / `p3_s4_loop*` / `p3_autonomous_workload_trial`) は
  preflight を一度も呼ばず `use_perf` が既定 True のままだったため、perf 不在が直ちに abort になる。
  本 wave はここを塞いだ。official 経路の受理集合は広げていない。
- **床値 v2 の「sanctioned な発行経路が存在しない」という記述は実測と合わない。**
  `_derive_protocol_bytes` は承認定数だけから canonical に組み立てており、
  凍結時にユーザーが決める自由値は残っていない。現行 protocol との差は `ccbench_pin` の 1 欄
  (`d706650c…` → 承認済み `511c9538…`)。前提ゲートは 3 つとも通る —
  v1 freeze bytes 一致 / ccbench gitlink 一致 / T-080 receipt が `active-valid`・refusals 空
  (submodule を初期化した worktree で実測。未初期化だと旧 pin の blob が引けず `invalid` に見える)。
  残るのは設計上あえて人間に置かれた 1 手 (`freeze-protocol --confirm-user-freeze` を対話 shell から、
  create-only なので旧 protocol を退けた上で) だけである。
- 段 5 実装子は sandbox の制約で pytest を起動できず (`dispatch infrastructure failure`)、
  **実走はすべて親が計算ノードで行った**。子の非実走を緑と記録していない。
  login の bounded local 実行は [T-604] の既知事象 (bounded scope の memory.max /
  memory.oom.group を走行中に attest できない) で停止するため、dispatch 経由で走らせた。

## 次の一手差分

### 新規

- {{T:perf-optional-official-series}} **P1・新規**: 正式系列 (official) が perf 不在の
  計算ノードに当たったときの扱いを決める。本 wave が perf 非依存にしたのは探索経路だけで、
  official は `use_perf is True` を要求したままである。床値 campaign も official mode では
  no-perf を拒否する。leading indicators を欠いた official 計測を認めるか、
  official だけは perf 実在を要求するかは、材料レポートの水準に直接効く。
- {{T:wal-binding-commitment-keyerror}} **P2・新規**: build 前の中断が
  `p3_s4_loop_trigger_gating.py` の `_wal_binding_commitment` で
  `KeyError: 'build_start'` に化け、本当の中断理由が例外に隠れる。
  2026-08-16 の実機走 (leg A = `legacy+s2`) で実測した。[T-1175] と同族の診断可能性の欠陥である。
- {{T:floor-protocol-reissue}} **P1・新規**: 床値 v2 の protocol 再発行を完了する。
  自由値はゼロ、差分は `ccbench_pin` 1 欄、前提ゲートは 3 つとも通ることを実測済み。
  実凍結は設計上ユーザーの対話 shell 手順 (`freeze-protocol --confirm-user-freeze`) であり、
  create-only のため旧 protocol を退ける必要がある。実行後は `ccbench_pin` 以外が
  1 byte も動いていないことを確認する。
- {{T:floor-pilot-wrapper-flag}} **P2・新規**: 標準投入経路から床値 pilot が 1 回も走れない。
  `tools/pegasus/floor_campaign.sh` は `--mode pilot` だけを渡し
  `--confirm-irreversible-pilot-holdout` を渡さないが、driver は pilot をそのフラグ無しで拒否する。
  floor run 実績 0 件の原因である。承認方式はユーザーから AI の運用裁定に委ねられた。
