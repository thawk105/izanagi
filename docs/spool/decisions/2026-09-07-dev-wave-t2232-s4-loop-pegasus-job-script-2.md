---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2232-s4-loop-pegasus-job-script
seq: 2
---

## {{D:s4-loop-compute-only-job-body}}. 段 4 loop の Pegasus job body は compute-only とし、third-party は scratch 複製で事前構築する

**決定:** `tools/pegasus/p3_s4_loop_pegasus.sh` は親が直接 `qsub` する compute-only の job body であり、
投入器を持たない。入力は環境変数 (`IZANAGI_S4_REPO_ROOT` / `IZANAGI_S4_EXPECTED_HEAD` /
`IZANAGI_S4_EVIDENCE_ROOT` / `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT`、任意で proposal path と fixture 値)
だけとし、raw qsub の `-o` / `-e` は evidence root (repo 外) へ向ける。job body は host gate を
PATH sanitize より前に置き、`/.claude/worktrees/` `/.codex/worktrees/` を含む REPO_ROOT と repo 配下の
evidence root を rc=2 で拒否し、`python3.10` exact の shim (`python3` のみ) を PATH 先頭に置く。
masstree の `config.h` は hydrate 済み source を scratch へ `cp -a` した複製に対して
`buildcache.prepare_masstree_fetchcontent` で事前構築し、receipt を create-only で残す。
`git status` による clean 検査は 3 箇所とも rc を明示検査し、失敗は clean ではなく rc=2 とする。
登録簿 class は `dispatch-required`、証拠は `static job-body classification`。

**理由:**
- F813: PATH の CMake wrapper で third-party を注入すると build identity が壊れる。FetchContent の
  準備を job 内で行えば注入が要らない。
- hydrate 済み source root の中で configure すると durable な staged source が汚れる
  (`ThirdParty.cmake` が `config.h` と archive を source 側に生成する)。複製先だけを汚す。
- `pegasus` 契約は `single_process=True` で reservation 束縛と claim root を build 前に要求する。
  A-2 と同じ形で束縛すれば driver 側の変更が要らない。
- `[[ -n "$(git status ...)" ]]` は失敗を clean と読む。fail-closed でなければ汚れた tree で計測が走る。

**却下した選択肢:**
- 投入器 (submitter) を同梱する — A-1 型の投入器は登録簿 class が変わり、job body の静的分類が崩れる。
- PATH に CMake wrapper を置いて third-party を差し込む — F813 の再発。
- hydrate root で直接 configure し、後で `git checkout` で戻す — 失敗時に汚れが残り、identity が壊れる。
- attestation の exact 照合をこの wave で先回りする — 未実測の障害であり、ユーザー指示で scope 外。
