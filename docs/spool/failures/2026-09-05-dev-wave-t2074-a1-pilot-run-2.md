---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-05
wave: dev-wave-t2074-a1-pilot-run
seq: 2
---

## 新規

### {{F:a1-qstat-visibility-regex-never-live-tested}}. A-1 driver の scheduler 可視性判定を実機の `qstat -f` 書式で一度も通さないまま投入 gate に置き、v3 pilot の初回投入が bench 前に失敗した [テスト代表性] [手順漏れ]

- 事象: 2026-09-05 13:12 JST、A-1 pilot (study `paper-story-a1-20260901-balanced5-pilot-v1`) の
  `submit` が write-heavy の qsub を受理させた直後に `qsub request identity/visibility is
  indeterminate` で rc=2 になった。balanced / read-heavy は未投入、attempt-0001 は
  `scheduler-or-infrastructure-failure-before-bench` の failure receipt だけを残した。
- 根本原因: `orchestrator/campaign/paper_story_a1_paired.py` の `_observe_qstat_visibility` が
  PBS-Pro 型の `job_state = Q` / `queue = gen_S` を前提にした正規表現で `qstat -f` を読むが、
  この機体の NQSV は `Current State = Queued` と `Queue = gen_S@nqsv (Execution Queue)` を出す。
  両方とも一致せず、投入は環境によらず決定的に落ちる。この関数は dd6ec73b9 (2026-08-29、Codex
  author) が導入し、以後 v2 / v3 のどの study でも実機で通っていない (8/25 の v2 受領証は
  それ以前の投入器が作った)。テスト fixture は `job_state = F` / `exit_status = 0` の PBS-Pro 型で、
  実機の書式を代表していない。同じ repo の `tools/pegasus/dispatch_compute.py` は
  `Current State` を解釈する実証済みの parser を持つが、A-1 driver はそれを使っていない。
- 恒久対応: memory `nqsv-qstat-f-format-and-a1-driver-regex` (実機書式の逐語と、投入 gate の
  parser は dispatch_compute の実証済み実装へ揃えるという規律)。修正は
  {{T:a1-driver-qstat-observation-fix}} (Codex author) が持ち、実機 `qstat -f` の逐語を fixture に
  した正例・負例を同じ commit で足す。
- 再発検知: 投入 gate に scheduler 出力の parser を足す wave は、段 1 で `qstat -f` の実出力を
  login node で 1 回取り、fixture の書式と突き合わせる (DW-S01 の「別 program 起動物の実在棚卸し」の
  対象に scheduler 出力の書式を含める)。

## 再発

### F849

- **再発: 2026-09-05** — 逆向きの同型。親が A-1 pilot を投入した固定 checkout (job の `PBS_O_WORKDIR`) へ、
  request が待ち行列にいる間に本 wave の spool fragment (untracked) を書いた。1 分後に開始した job body の
  preflight が `working tree is dirty` で 7 秒で終了し、group receipt の 60 秒待ち経路は観測できなかった
  (`output/insights/2026-09-05_t2074-a1-pilot-run/README.md` §7)。測定は §4 の欠陥で既に失われていた。
  対処: 投入専用 worktree と記録用 worktree を同じ SHA で分け、3 job の preflight 通過まで投入元を触らない
  (memory `nqsv-qstat-f-format-and-a1-driver-regex`)。
