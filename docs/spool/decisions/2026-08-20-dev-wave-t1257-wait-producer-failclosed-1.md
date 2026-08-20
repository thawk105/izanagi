---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1257-wait-producer-failclosed
seq: 1
---

## {{D:producer-receipt-fails-closed}}. producer 完了の確定は signal handler でなく durable receipt の実在で行う

**決定:** `tools/dev_wave_wait.py producer` の完了確定は、signal handler による明示的な失敗記録ではなく、
成功時にだけ atomic に書く durable receipt (`--check-only --receipt-file`) の実在で行う。receipt の
staleness 対策に run-id は導入せず、呼び出しごとの一意な receipt-file path という既存規約
(done-file/artifact-file と同型) に委ねる。

**理由:**
- SIGKILL/OOM/cgroup reap は signal handler で捕捉できないため、「途中終了時に失敗を明示的に書く」
  設計では原理的に穴が残る。核心は「プロセスを生かす」ことではなく「成功の永続証拠が無ければ
  成功を受理しない」ことに置くべき、と段2プランが指摘し段4裁定で採用した。
- run-id 方式は、receipt-file が常に呼び出しごとに一意な path へ書かれる既存規約 (done-file/
  artifact-file と同型) の上では不要な複雑さになる。`--check-only` は常に非キャッシュで
  再検査し、成功時のみ現在の mtime を記録した receipt を上書きするため、古い receipt を
  読んで分岐する経路自体が存在しない。

**却下した選択肢:**
- producer 分岐へ SIGTERM handler を追加し、途中終了時に明示的な失敗 receipt を書く案 —
  段3敵対相談レンズAが「SIGKILL 等は捕捉できず受理判定の根拠にできない」と指摘し、
  成功 receipt の不在だけで安全側に倒せるため不採用。
- receipt に run-id/wave-id を含めて再利用を検知する案 — 呼び出し側が一意 path 規約を守る
  前提の下では不要。呼び出し側への一意 path 要求は運用注記で明文化する (次の一手参照)。
