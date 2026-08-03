---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-t189-reasoning-allowlist
seq: 2
---

## {{D:effort-allowlist-inside-supervisor-digest}}. 受理集合の正本は完全性閉包の内側に置く

**決定:** 子起動の reasoning / effort 許可リストの正本は `tools/dev_waves/effort_levels.py` に置く。
`tools/dev_waves/daemon.py` の `_supervisor_digest()` が同 directory 直下の `*.py` / `*.json` を
hash しており、そこへ置くことで受理集合の変更が supervisor の完全性 digest に必ず現れる。
定数は製品別に 2 本 (`CLAUDE_EFFORTS` / `CODEX_REASONING_EFFORTS`) 置き、
`orchestrator/codex_roles/launcher.py` と `spec.py` の既存 role policy 集合は
**値を変えずに命名だけ**与え、正本の部分集合であることを機械検査する。

**理由:**
- `_supervisor_digest()` は run manifest に記録され、checker が run 内の before/after 等号で
  trust-root pass を出す。正本を閉包の外へ置くと、**受理集合だけが変わって
  `supervisor_code_sha256` が同値のまま**という経路が残る。
- `tools/dev_waves/` は `orchestrator.*` を import しておらず、逆向きに置くと新規依存辺が生まれ、
  `codex_roles/__init__.py` の eager import を dev_waves の standalone テスト収集へ持ち込む。
- `tools/codex_worker_launch.py` は既に `tools.dev_waves.schema` を import しているため、
  この配置で新しい依存辺は増えない。
- role policy 集合 (`{low,medium,high,xhigh}` と `{medium,high}`) は capability 集合ではない。
  正本で置き換えると受理集合が広がるため、部分集合検査だけで束縛する。

**却下した選択肢:**
- `orchestrator/codex_roles/` 配下の新規 leaf — 完全性閉包の外で、上記の穴が残る。
- `_supervisor_digest()` を拡張して外部 leaf を含める — 完全性コード自体の改変になり、
  ファイルを閉包内へ置くだけの案より risk が高い。
- 単一の平坦集合 — Claude と Codex は根拠が別 (前者は `claude --help` の文書化語彙、
  後者は F56 の実測) であり、将来 Codex 側だけを model capability へ分解できなくなる。
