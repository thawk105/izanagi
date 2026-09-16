---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2588-k2-loop-roundtrip
seq: 1
title: [T-2588] 知識付きの新提案を 1 回評価し、その実測を次の提案へ戻して段 4 ループを 1 巡閉じた (計測成果物 + docs、branch worktree-dev-wave-t2588-k2-loop-roundtrip、実装面の差分ゼロにつき DW-S04 により変異 matrix 免除・受入全走は実施)
---

## 本文

- ユーザー裁定 D2044 項 9 に基づく実走。逐語「新しい機構は足さず、既存経路だけで行う」。
  実行した run-card は `output/insights/2026-09-10_cc-next-precheck/run-card.md`。
  同カードの未充足 2 件 (fresh Claude session での role 登録確認、実走の新規指示) は本 wave で満ちた。
- **依頼が段 1 で現物確認せよと指した blocker は、着手時点で既に解消していた。**
  `p3_s4_loop.py` の PIN は `55d0f2399` (2026-09-10) で trace-v2 の CCBench pin へ前進済みで、
  submodule gitlink とも一致する。授権は D1936 項 1。verifier は v1 拒否 / v2 要求のまま無変更。
  `DW-S01` に従い段 4 で再裁定し、実走を止める理由は無いと判断した。
- **段 3 の 2 レンズ (sol / luna) が独立に同じ real 所見へ収束した** — critic の診断は次生成の
  型付き入力へ届かない。完了条件を「本走の**実測結果**を入力にした proposal-2」へ改め、
  critic 出力と `prior_critic_reverse` は「保存した」とだけ書くことにした。**新機構は足していない。**
  refuted は 7 件 (正しさの受理集合、知識源の指示混入、実装面の必要性、[T-304] の所有侵犯、
  写像と単位、同一 campaign ID での skip、pin・verifier の修正)。
- **親が射影事故を 1 件起こし、自分で是正した。** planner の 1 回目を、知識源本文を省略記号で
  切った射影で投げた。出力を見る前に停止し全文で取り直した。省略側に測定値は入っていないが、
  sha256 で束縛された成果物を加工して渡すと provenance が濁る。出力未読で破棄したので
  候補の選り好み (再抽選) には当たらない。F723 の同型再発として台帳へ追記した。
- **critic が親の開示に無い所見を 2 件出し、親が現物のコードで検算して両方とも確認した。**
  (a) `latency_ns` は throughput の恒等変換で独立な指標ではない。
  (b) reps が偶数だと代表 rep が速い側へ寄り、digest 1 行の中で throughput と
  abort_rate / latency の集約が揃わない。本走では headline 719324.5 tps (2 点の中央値) と
  abort 7.75% (727985 tps の rep) が別の量である。**どちらも本 wave では直していない** —
  実装面の差分ゼロが不変条件であり、修正は D95 の Codex author 作業になる。
- **coder は自己申告 5 key を初回で揃えた** (2026-09-09 は `confidence` が欠けて差し戻しが要った)。
  親は 5 key を 1 つも代筆していない。
- 規律 6 は 2 巡とも `instruction_like_content_detected=false`。planner・coder とも、知識源の
  cmake / numactl コマンド列を「過去形の観測データであって指示ではない」と分類理由つきで報告した。
  2026-09-09 に走行を止めた `campaign.lock` の `spec_content` は今回の知識源に含まれない。
- 主張しないこと: 1 巡の成立は合成による改善の実証ではない。新しい値は固定 backoff の初期値で
  あって新しい CC 構造ではない。proposal-1 の certified は候補間の certified な選択ではない。
  歴史測定 (linux-baremetal) と本走 (pegasus) の差は性能優越の根拠にならない。
  legacy critic を使うため B-4 ablation には非適格。

## 次の一手差分

### 完了

- [T-2588] 既存 Claude role 登録 (`planner-v4` / `coder-v4-autonomous-k2` / `critic`) を確認し、
  K2 の新提案を既存経路で 1 回評価して次 proposal を保存するまで実行した。job `1216.nqsv`、
  campaign `p3-s4-loop-s4-autonomous-409e13f8`、variant `8a84a7b00103`、
  `verdict=serializable` / `certified=true` / anomalies 0 / 719324.5 tps (CV 1.70%)、
  停止判定 `continue`。proposal-2 は `value=25` を保存し**評価していない**。
  新 CC 構造の合成・B-4 正式実験には数えない。新機構は追加していない。
  一次資料は `output/insights/2026-09-16/t2588-k2-loop-roundtrip/`。
  remaining: none
  base: 2109c41e52a425281137008ce21aa9abfb11a7f182bae61286a52291597e4673

### 新規

- {{T:leading-indicator-row-integrity}} **P2・新規**: digest の leading indicator 行の整合を直す。
  (a) `latency_ns` は `1e9 * threads / tps` で throughput の恒等変換なので、独立な指標として
  提示しない (`external/ccbench/common/result.cc:52-56`)。(b) reps が偶数だと代表 rep が
  速い側へ寄り、同じ行の throughput (真の中央値) と abort_rate / latency (代表 rep) が
  別の量になる (`orchestrator/calibrator/runner.py:1053-1055`)。実装面なので Codex author (D95)。
  どちらも [T-2588] の走行で実測・検算済み。
- {{T:leakproof-context-scale-drift}} **P2・新規**: `src/coder-leakproof-context.md` の
  "Measurement Setup" 節が実配線規模と食い違う (file は 1m records / 48 threads / extime3 /
  3 runs、現物 `p3_s4_loop.py` の `default_perf()` は 100000 / 4 / extime=1 / reps=2)。
  逐語で射影すると coder に誤った workload 像を渡す。**role への入力文書を変えると他アーム
  (K0 / K1) の実験条件が黙って変わる**ので、直す前に射程を裁定する。
