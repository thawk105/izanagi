---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2830-b5-node-local-lock
seq: 2
---

## {{D:b5-node-local-lock-and-per-job-trees}}. B-5 mode の bench lock は B-5 分岐内でだけ job 固有 scratch に置き、試走 launcher は arm ごとの検証済み checkout を env と qsub の cwd の両方へ配線する

**決定:**

- job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) は B-5 分岐内、driver 起動の直前にだけ `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を設定する
  (B-10 / A-5 の job body と同じ値)。非 B-5 の 3 経路 (proposal 単独 / proposal + pair / fixture) の driver argv と環境は変えない。
  bench lock を取るのは driver 以下 (`pipeline.py` の performance verify pass と bench) だけで、job body の prebuild は取らないので、
  この位置で B-5 mode の全取得を覆う。slot の subprocess は環境を継承する。
- この lock が排他するのは同じ job の中だけである (`TMPDIR` は job ID ごとの path)。job 間の単独性は gen_S の割当て (リクエストごとに
  CPU 48/48) に依り、専有はスケジューラの保証外 (`docs/pegasus-runbook.md` §1)。machine-wide な排他からの縮小であり、B-10 / A-5 と
  同じ限界を持つ。計算ノード上の単独性確認の役割は変えない。
- 試走 launcher (`tools/pegasus/b5_contrast_launch.py`) は `launch(jobs, trees_by_arm, ...)` とし、各 job に対応する検証済み `SubmitTree` を
  `IZANAGI_S4_REPO_ROOT` と qsub の cwd の**両方**に使う。CLI は `--repo-root-<arm>` 4 本を必須とし、共通の `--expected-head` で既存の
  `validate_submit_tree` を arm ごとに呼ぶ。単一 `--repo-root` の fallback と互換層は持たない。
- 新しい拒否条件は足さない。4 path の重複と common repo の一致は検査しない。同じ path を 4 回渡すと共有 cache に戻るのは呼出し側の
  責任とし、README の手順 (arm ごとに 4 checkout を用意する) で担う。

**理由:**

- D2199 / D2200 項 1: 試走では session wall の 59% (台帳区間とコードからの推定で、flock の待ちを直接測った値ではない) が home 共有 lock の
  待ちに帰属し、並列 job を増やしても総 wall が縮まない形だった。本走の launcher を job ごとの submit-tree にすることは D2200 項 1 (6) で確定済み。
- job ごとの tree の根拠は「lock を node-local にすると build の同時性が上がる」ではない (段 3 の敵対相談で誤りと判明: build は bench lock の
  外で走り、系列開始 stock の build は現行でも並行に到達しうる)。共有 submit-tree では cache root (submit-tree 内の CCBench 配下) を 4 job が
  共有し、build claim は待機・retry なしで失敗するので、tree を分ければその競合が構造的に消える。
- B-5 mode に限るのは、依頼の「既存 3 経路の argv・bytes 不変」と「本題だけ」に合わせ、非 B-5 経路 (K2 手動 loop) の挙動変化を scope 外に置くため。

**却下した選択肢:**

- job 全体で設定する (B-10 / A-5 と同形) — 非 B-5 経路の挙動も変わり、本走の前提でもない。
- 共有 submit-tree のまま cache 公開の競合を検査する — 事前の検査は後から起きる同時 claim を防げず、D2200 項 1 (6) も分離を決めている。
- launcher に path 重複・common repo 一致の拒否を足す — 依頼が検査の追加を scope 外とし、実測された欠陥もない。common repo 一致は
  別 clone 4 本という正当な配置も拒否する。
- `launch` の中で git 検証を行う — 検証責務の移設で、試走の API 利用 (呼出し側が検証してから渡す) と整合しない。
